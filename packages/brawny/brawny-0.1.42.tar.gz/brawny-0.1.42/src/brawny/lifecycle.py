"""Simplified lifecycle dispatcher for job hooks.

Implements 3 lifecycle hooks (on_trigger, on_success, on_failure).
Jobs call alert() explicitly within hooks to send notifications.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from uuid import UUID

from brawny.alerts.routing import resolve_targets
from brawny.alerts.send import AlertConfig, AlertEvent, AlertPayload, JobAlertSender
from brawny.http import ApprovedHttpClient
from brawny.jobs.kv import DatabaseJobKVStore, DatabaseJobKVReader
from brawny.logging import LogEvents, get_logger, log_unexpected
from brawny.metrics import BACKGROUND_TASK_ERRORS, get_metrics
from brawny.tx_hash import normalize_tx_hash
from brawny.model.contexts import (
    AlertContext,
    BlockContext,
    TriggerContext,
    SuccessContext,
    FailureContext,
)
from brawny.model.errors import (
    ErrorInfo,
    FailureStage,
    FailureType,
    HookType,
    TriggerReason,
)
from brawny.model.types import BlockInfo, Trigger, HookName
from brawny.network_guard import job_network_guard

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny.jobs.base import Job, TxInfo, TxReceipt, BlockInfo as AlertBlockInfo
    from brawny.model.types import TxAttempt, TxIntent
    from brawny._rpc.clients import ReadClient
    from brawny.alerts.contracts import ContractSystem, SimpleContractFactory
    from brawny.alerts.events import EventDict
    from brawny.telegram import TelegramBot

logger = get_logger(__name__)


class LifecycleDispatcher:
    """Dispatch job lifecycle hooks.

    Lifecycle Hooks (3):
        - on_trigger: Job check returns Trigger, BEFORE build_tx
        - on_success: Transaction confirmed on-chain
        - on_failure: Any failure (intent may be None for pre-intent failures)

    Jobs call alert() explicitly within hooks to send notifications.
    All hook invocations go through dispatch_hook() for consistent context setup.
    """

    def __init__(
        self,
        db: Database,
        rpc: ReadClient,
        config: Config,
        jobs: dict[str, Job],
        contract_system: ContractSystem | None = None,
        telegram_bot: "TelegramBot | None" = None,
    ) -> None:
        self._db = db
        self._rpc = rpc
        self._config = config
        self._jobs = jobs
        self._contract_system = contract_system
        self._telegram_bot = telegram_bot
        self._http_client = ApprovedHttpClient(config.http)
        self._global_alert_config = self._build_global_alert_config()

    # =========================================================================
    # Hook Dispatch (Single Entry Point)
    # =========================================================================

    def dispatch_hook(self, job: Job, hook: HookName, ctx: Any) -> None:
        """Dispatch a lifecycle hook with proper alert context setup.

        All hook invocations must go through this method to ensure
        alert() works correctly within hooks.

        Args:
            job: The job instance
            hook: Hook name ("on_trigger", "on_success", "on_failure")
            ctx: The context to pass to the hook (TriggerContext, SuccessContext, FailureContext)
        """
        from brawny.scripting import set_job_context

        hook_fn = getattr(job, hook, None)
        if hook_fn is None:
            return

        try:
            with self._alert_context(ctx):
                set_job_context(True)
                with job_network_guard():
                    hook_fn(ctx)
        except Exception as e:
            # RECOVERABLE
            # Job hook failures should not crash the executor.
            log_unexpected(
                logger,
                "lifecycle.hook_crashed",
                job_id=job.job_id,
                hook=hook,
                error=str(e)[:200],
            )
            if self._has_alert_config():
                self._send_hook_error_alert(job.job_id, hook, e)
        finally:
            set_job_context(False)

    @contextmanager
    def _alert_context(self, ctx: Any):
        """Set alert context for duration of hook execution with token-based reset."""
        from brawny._context import set_alert_context, reset_alert_context

        token = set_alert_context(ctx)
        try:
            yield
        finally:
            reset_alert_context(token)

    # =========================================================================
    # Public API
    # =========================================================================

    def on_triggered(
        self,
        job: Job,
        trigger: Trigger,
        block: BlockInfo,
        intent_id: UUID | None = None,
    ) -> None:
        """Called when job check returns a Trigger. Runs BEFORE build_tx."""
        # Build TriggerContext
        block_ctx = BlockContext(
            number=block.block_number,
            timestamp=block.timestamp,
            hash=block.block_hash,
            base_fee=0,
            chain_id=block.chain_id,
        )
        ctx = TriggerContext(
            trigger=trigger,
            block=block_ctx,
            kv=DatabaseJobKVStore(self._db, job.job_id),
            logger=logger.bind(job_id=job.job_id, chain_id=self._config.chain_id),
            http=self._http_client,
            job_id=job.job_id,
            job_name=job.name,
            chain_id=self._config.chain_id,
            alert_config=self._get_alert_config_for_job(job),
            telegram_config=self._config.telegram,
            telegram_bot=self._telegram_bot,
            job_alert_to=getattr(job, "_alert_to", None),
            _alert_sender=self._make_job_alert_sender(job),
        )
        self.dispatch_hook(job, "on_trigger", ctx)

    def on_submitted(self, intent: TxIntent, attempt: TxAttempt) -> None:
        """Log submission for observability. No job hook."""
        logger.info(
            "tx.submitted",
            intent_id=str(intent.intent_id),
            attempt_id=str(attempt.attempt_id),
            tx_hash=normalize_tx_hash(attempt.tx_hash),
            nonce=attempt.nonce,
            job_id=intent.job_id,
            chain_id=self._config.chain_id,
        )

    def on_replaced(self, intent: TxIntent, attempt: TxAttempt) -> None:
        """Called when a replacement attempt is broadcast. No job hook."""
        # Replacement already emits a detailed log event; keep this a no-op.
        return None

    def on_confirmed(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        receipt: dict[str, Any],
    ) -> None:
        """Called when transaction is confirmed on-chain."""
        job = self._jobs.get(intent.job_id)
        if not job:
            return

        # Build SuccessContext
        alert_receipt = self._build_alert_receipt(receipt)
        block_ctx = self._to_block_context(self._fetch_block(receipt.get("blockNumber")))
        events = self._decode_receipt_events(alert_receipt) if self._contract_system else None

        ctx = SuccessContext(
            intent=intent,
            receipt=alert_receipt,
            events=events,
            block=block_ctx,
            kv=DatabaseJobKVReader(self._db, job.job_id),
            logger=logger.bind(job_id=job.job_id, chain_id=self._config.chain_id),
            http=self._http_client,
            job_id=job.job_id,
            job_name=job.name,
            chain_id=self._config.chain_id,
            alert_config=self._get_alert_config_for_job(job),
            telegram_config=self._config.telegram,
            telegram_bot=self._telegram_bot,
            job_alert_to=getattr(job, "_alert_to", None),
            _alert_sender=self._make_job_alert_sender(job),
        )
        self.dispatch_hook(job, "on_success", ctx)

    def on_failed(
        self,
        intent: TxIntent,
        attempt: TxAttempt | None,
        error: Exception,
        failure_type: FailureType,
        failure_stage: FailureStage | None = None,
        cleanup_trigger: bool | None = None,
    ) -> None:
        """Called on any terminal failure with intent. Error is required."""
        del cleanup_trigger
        job = self._jobs.get(intent.job_id)
        if not job:
            return

        # Build FailureContext
        block_ctx = self._to_block_context(self._get_block_for_failed(attempt, None))

        ctx = FailureContext(
            intent=intent,
            attempt=attempt,
            error=error,
            failure_type=failure_type,
            failure_stage=failure_stage,
            block=block_ctx,
            kv=DatabaseJobKVReader(self._db, job.job_id),
            logger=logger.bind(job_id=job.job_id, chain_id=self._config.chain_id),
            http=self._http_client,
            job_id=job.job_id,
            job_name=job.name,
            chain_id=self._config.chain_id,
            alert_config=self._get_alert_config_for_job(job),
            telegram_config=self._config.telegram,
            telegram_bot=self._telegram_bot,
            job_alert_to=getattr(job, "_alert_to", None),
            _alert_sender=self._make_job_alert_sender(job),
        )
        self.dispatch_hook(job, "on_failure", ctx)

    def on_check_failed(
        self,
        job: Job,
        error: Exception,
        block: BlockInfo,
    ) -> None:
        """Called when job.check() raises an exception. No intent exists."""
        block_ctx = BlockContext(
            number=block.block_number,
            timestamp=block.timestamp,
            hash=block.block_hash,
            base_fee=0,
            chain_id=block.chain_id,
        )
        ctx = FailureContext(
            intent=None,
            attempt=None,
            error=error,
            failure_type=FailureType.CHECK_EXCEPTION,
            failure_stage=None,
            block=block_ctx,
            kv=DatabaseJobKVReader(self._db, job.job_id),
            logger=logger.bind(job_id=job.job_id, chain_id=self._config.chain_id),
            http=self._http_client,
            job_id=job.job_id,
            job_name=job.name,
            chain_id=self._config.chain_id,
            alert_config=self._get_alert_config_for_job(job),
            telegram_config=self._config.telegram,
            telegram_bot=self._telegram_bot,
            job_alert_to=getattr(job, "_alert_to", None),
            _alert_sender=self._make_job_alert_sender(job),
        )
        self.dispatch_hook(job, "on_failure", ctx)

    def close(self) -> None:
        self._http_client.close()

    def on_build_tx_failed(
        self,
        job: Job,
        trigger: Trigger,
        error: Exception,
        block: BlockInfo,
    ) -> None:
        """Called when job.build_tx() raises an exception. No intent exists."""
        block_ctx = BlockContext(
            number=block.block_number,
            timestamp=block.timestamp,
            hash=block.block_hash,
            base_fee=0,
            chain_id=block.chain_id,
        )
        ctx = FailureContext(
            intent=None,
            attempt=None,
            error=error,
            failure_type=FailureType.BUILD_TX_EXCEPTION,
            failure_stage=None,
            block=block_ctx,
            kv=DatabaseJobKVReader(self._db, job.job_id),
            logger=logger.bind(job_id=job.job_id, chain_id=self._config.chain_id),
            http=self._http_client,
            job_id=job.job_id,
            job_name=job.name,
            chain_id=self._config.chain_id,
            alert_config=self._get_alert_config_for_job(job),
            telegram_config=self._config.telegram,
            telegram_bot=self._telegram_bot,
            job_alert_to=getattr(job, "_alert_to", None),
            _alert_sender=self._make_job_alert_sender(job),
        )
        self.dispatch_hook(job, "on_failure", ctx)

    def on_deep_reorg(
        self, oldest_known: int | None, history_size: int, last_processed: int
    ) -> None:
        """System-level alert for deep reorg. Not job-specific."""
        if not self._has_alert_config():
            return
        message = (
            f"Deep reorg detected. History window is insufficient "
            f"to safely verify the chain.\n"
            f"oldest_known={oldest_known}, history_size={history_size}, "
            f"last_processed={last_processed}"
        )
        payload = AlertPayload(
            job_id="system",
            job_name="Deep Reorg",
            event_type=AlertEvent.FAILED,
            message=message,
            parse_mode=self._default_parse_mode(),
            chain_id=self._config.chain_id,
        )
        self._fire_alert(payload, self._global_alert_config)


    def _send_hook_error_alert(self, job_id: str, hook_type: str, error: Exception) -> None:
        """Send fallback error alert when a hook fails."""
        message = f"Alert hook failed for job {job_id}: {error}"
        payload = AlertPayload(
            job_id=job_id,
            job_name=job_id,
            event_type=AlertEvent.FAILED,
            message=message,
            parse_mode=self._default_parse_mode(),
            chain_id=self._config.chain_id,
        )
        self._fire_alert(payload, self._global_alert_config)

    def _default_parse_mode(self) -> str:
        """Get default parse mode for alerts."""
        return self._config.telegram.parse_mode or "Markdown"

    def _fire_alert(self, payload: AlertPayload, config: AlertConfig) -> None:
        """Fire alert asynchronously. Fire-and-forget."""
        from brawny.alerts import send as alerts_send

        try:
            alerts_send.enqueue_alert(payload, config)
        except Exception as exc:
            # RECOVERABLE alert enqueue failures should not block execution.
            metrics = get_metrics()
            metrics.counter(BACKGROUND_TASK_ERRORS).inc(task="alert_send")
            log_unexpected(logger, "alert.enqueue_failed", error=str(exc)[:200])

    def _handle_alert_task_result(self, task: "asyncio.Task[object]") -> None:
        import asyncio

        if task.cancelled():
            return
        try:
            task.result()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # RECOVERABLE alert task failures should not crash lifecycle.
            metrics = get_metrics()
            metrics.counter(BACKGROUND_TASK_ERRORS).inc(task="alert_send")
            log_unexpected(self._log, "alert.task_failed", error=str(exc)[:200])

    def _build_global_alert_config(self) -> AlertConfig:
        """Build global AlertConfig from application config (legacy compatibility)."""
        tg = self._config.telegram
        admin_chat_ids = resolve_targets(tg.admin, tg.chats, [])
        chat_ids = admin_chat_ids
        return AlertConfig(
            telegram_token=tg.bot_token,
            telegram_chat_ids=chat_ids,
        )

    def _get_alert_config_for_job(self, job: Job) -> AlertConfig:
        """Resolve per-job overrides into job-scoped AlertConfig (legacy compatibility)."""
        job_chat_ids = getattr(job, "telegram_chat_ids", None)
        if job_chat_ids:
            # Job-level targets override global (legacy API)
            return AlertConfig(
                telegram_token=self._config.telegram.bot_token,
                telegram_chat_ids=list(job_chat_ids),
            )
        return self._global_alert_config

    def _has_alert_config(self) -> bool:
        """Check if any alert transport is configured."""
        return bool(
            self._global_alert_config.telegram_token
            and self._global_alert_config.telegram_chat_ids
        )

    def _make_job_alert_sender(self, job: Job) -> JobAlertSender:
        """Create alert sender for ctx.alert() in lifecycle hooks.

        Returns a JobAlertSender that routes to job-specific destinations.
        """
        return JobAlertSender(
            telegram_bot=self._telegram_bot,
            telegram_config=self._config.telegram,
            job_alert_to=getattr(job, "_alert_to", None),
            job_id=job.job_id,
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    def _build_tx_info(
        self, intent: TxIntent | None, attempt: TxAttempt | None
    ) -> TxInfo | None:
        """Build TxInfo from intent, enrich with attempt if available."""
        if intent is None:
            return None

        from brawny.jobs.base import TxInfo

        # Safe access for optional gas_params
        gp = getattr(attempt, "gas_params", None) if attempt else None

        return TxInfo(
            hash=normalize_tx_hash(attempt.tx_hash) if attempt else None,
            nonce=attempt.nonce if attempt else None,
            from_address=intent.signer_address,
            to_address=intent.to_address,
            gas_limit=gp.gas_limit if gp else getattr(intent, "gas_limit", 0),
            max_fee_per_gas=gp.max_fee_per_gas if gp else getattr(intent, "max_fee_per_gas", 0),
            max_priority_fee_per_gas=gp.max_priority_fee_per_gas if gp else getattr(intent, "max_priority_fee_per_gas", 0),
        )

    def _build_alert_receipt(self, receipt: dict[str, Any]) -> TxReceipt:
        """Convert raw receipt dict to TxReceipt."""
        from brawny.jobs.base import TxReceipt

        tx_hash = normalize_tx_hash(receipt.get("transactionHash"))
        block_hash = receipt.get("blockHash")
        if hasattr(block_hash, "hex"):
            block_hash = f"0x{block_hash.hex()}"
        return TxReceipt(
            transaction_hash=tx_hash,
            block_number=receipt.get("blockNumber"),
            block_hash=block_hash,
            status=receipt.get("status", 1),
            gas_used=receipt.get("gasUsed", 0),
            logs=receipt.get("logs", []),
        )

    def _get_block_for_failed(
        self,
        attempt: TxAttempt | None,
        receipt: dict[str, Any] | None,
    ) -> AlertBlockInfo | None:
        """Determine block for failed alert. Explicit priority."""
        if receipt and "blockNumber" in receipt:
            return self._fetch_block(receipt["blockNumber"])
        if attempt and attempt.broadcast_block:
            return self._fetch_block(attempt.broadcast_block)
        return None

    def _fetch_block(self, block_number: int | None) -> AlertBlockInfo | None:
        """Fetch block info by number."""
        if block_number is None:
            return None
        try:
            block = self._rpc.get_block(block_number)
        except Exception as e:
            # RECOVERABLE alert block info is optional.
            log_unexpected(
                logger,
                "alerts.block_fetch_failed",
                block_number=block_number,
                error=str(e)[:200],
            )
            return None
        return self._to_alert_block(
            BlockInfo(
                chain_id=self._config.chain_id,
                block_number=block["number"],
                block_hash=f"0x{block['hash'].hex()}"
                if hasattr(block["hash"], "hex")
                else block["hash"],
                timestamp=block["timestamp"],
                base_fee=block.get("baseFeePerGas", 0),
            )
        )

    def _model_block_from_number(self, block_number: int) -> BlockInfo | None:
        """Get BlockInfo model from block number."""
        try:
            block = self._rpc.get_block(block_number)
        except Exception as e:
            # RECOVERABLE alert block info is optional.
            log_unexpected(
                logger,
                "alerts.block_model_failed",
                block_number=block_number,
                error=str(e)[:200],
            )
            return None
        return BlockInfo(
            chain_id=self._config.chain_id,
            block_number=block["number"],
            block_hash=f"0x{block['hash'].hex()}"
            if hasattr(block["hash"], "hex")
            else block["hash"],
            timestamp=block["timestamp"],
            base_fee=block.get("baseFeePerGas", 0),
        )

    def _to_alert_block(self, block: BlockInfo) -> AlertBlockInfo:
        """Convert model BlockInfo to alert BlockInfo."""
        from brawny.jobs.base import BlockInfo as AlertBlockInfo

        return AlertBlockInfo(
            number=block.block_number,
            hash=block.block_hash,
            timestamp=block.timestamp,
        )

    def _to_block_context(self, alert_block: AlertBlockInfo | None) -> BlockContext:
        """Convert alert BlockInfo to BlockContext."""
        if alert_block is None:
            # Default block context when no block available
            return BlockContext(
                number=0,
                timestamp=0,
                hash="0x0",
                base_fee=0,
                chain_id=self._config.chain_id,
            )
        return BlockContext(
            number=alert_block.number,
            timestamp=alert_block.timestamp,
            hash=alert_block.hash,
            base_fee=0,  # Not always available in alert context
            chain_id=self._config.chain_id,
        )

    def _decode_receipt_events(self, receipt: TxReceipt) -> "EventDict":
        """Decode events from receipt using contract system."""
        if self._contract_system is None:
            from brawny.alerts.events import EventDict
            return EventDict([])

        try:
            from brawny.alerts.events import decode_logs

            return decode_logs(
                logs=receipt.logs,
                contract_system=self._contract_system,
            )
        except Exception as e:
            # RECOVERABLE event decoding failures should not block alerts.
            log_unexpected(logger, "events.decode_failed", error=str(e)[:200])
            from brawny.alerts.events import EventDict
            return EventDict([])
