"""Transaction executor for signing, broadcasting, and monitoring transactions.

Implements the tx execution flow from SPEC 9:
1. Validate deadline
2. Reserve nonce
3. Build tx dict with gas estimation
4. Sign transaction
5. Broadcast transaction
6. Monitor for confirmation
7. Handle replacement for stuck txs

Golden Rule: Intents are persisted BEFORE signing - the executor only
works with already-persisted intents.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Callable
from uuid import UUID, uuid4

from web3 import Web3

from brawny.logging import LogEvents, get_logger, log_unexpected
from brawny.tx.utils import normalize_tx_dict
from brawny.tx.stages.types import (
    Fail,
    Ok,
    Retry,
    RetryDecision,
    RunContext,
    StageName,
    StageResult,
    StageOutcome,
)
from brawny.tx import retry_policy
from brawny.metrics import (
    EXECUTOR_ATTEMPT_DURATION_SECONDS,
    EXECUTOR_STAGE_OUTCOME,
    EXECUTOR_STAGE_STARTED,
    EXECUTOR_STAGE_TIMEOUTS,
    CLAIM_RELEASED_PRE_ATTEMPT,
    CLAIM_RELEASE_SKIPPED,
    SIMULATION_NETWORK_ERRORS,
    SIMULATION_REVERTED,
    TX_BROADCAST,
    TX_FAILED,
    INTENT_RETRY_ATTEMPTS,
    get_metrics,
)
from brawny.model.enums import AttemptStatus, IntentStatus, IntentTerminalReason
from brawny.model.errors import (
    DatabaseError,
    FailureStage,
    FailureType,
    InvariantViolation,
    SimulationNetworkError,
    SimulationReverted,
)
from brawny.model.types import GasParams, TxAttempt, TxIntent
from brawny.types import ClaimedIntent
from brawny._rpc.context import (
    set_job_context as set_rpc_job_context,
    reset_job_context as reset_rpc_job_context,
    set_intent_budget_context as set_rpc_intent_budget_context,
    reset_intent_budget_context as reset_rpc_intent_budget_context,
)
from brawny._rpc.errors import RPCError, RPCRetryableError, RpcErrorKind
from brawny.tx.nonce import NonceManager
from brawny.tx.intent import release_claim, transition_intent
from brawny.timeout import Deadline
from brawny.utils import ensure_utc, utc_now, serialize_error

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny.jobs.base import Job
    from brawny.keystore import Keystore
    from brawny.lifecycle import LifecycleDispatcher
    from brawny._rpc.clients import ReadClient

logger = get_logger(__name__)

STAGE_BUILD_TX = "build_tx"
STAGE_SIGN = "sign"
STAGE_CREATE_ATTEMPT = "create_attempt"
STAGE_BROADCAST = "broadcast"

STAGE_TIMEOUT_SECONDS: dict[StageName, float] = {
    StageName.GAP_CHECK: 5.0,
    StageName.RESERVE_NONCE: 5.0,
    StageName.BUILD_TX: 10.0,
    StageName.SIGN: 2.0,
    StageName.BROADCAST: 20.0,
    StageName.MONITOR_TICK: 10.0,
    StageName.FINALIZE: 5.0,
}


def _safe_endpoint_label(endpoint: str | None) -> str | None:
    if not endpoint:
        return None
    parts = endpoint.split("://", 1)
    if len(parts) == 2:
        scheme, rest = parts
    else:
        scheme, rest = "http", parts[0]
    host = rest.split("/", 1)[0]
    host = host.split("@", 1)[-1]
    return f"{scheme}://{host}"


def maybe_release_pre_attempt_claim(
    db: Database,
    claimed: ClaimedIntent,
    exc: Exception,
    stage: str,
) -> bool:
    """Release claim if no attempt exists and token matches.

    Returns True if claim was released, False otherwise.
    Never raises - swallows DB errors to avoid masking original exception.
    """
    try:
        released = db.release_claim_if_token_and_no_attempts(
            intent_id=claimed.intent_id,
            claim_token=claimed.claim_token,
        )

        # If monotonic is already captured at claim time, prefer it for elapsed_ms.
        claimed_at = ensure_utc(claimed.claimed_at)
        elapsed_ms = (utc_now() - claimed_at).total_seconds() * 1000
        metrics = get_metrics()

        if released:
            logger.exception(
                "claim.released_pre_attempt",
                intent_id=str(claimed.intent_id),
                stage=stage,
                exc_type=type(exc).__name__,
                elapsed_ms=elapsed_ms,
            )
            metrics.counter(CLAIM_RELEASED_PRE_ATTEMPT).inc(stage=stage)
        else:
            logger.debug(
                "claim.release_skipped",
                intent_id=str(claimed.intent_id),
                stage=stage,
            )
            metrics.counter(CLAIM_RELEASE_SKIPPED).inc(stage=stage)

        return released

    except Exception as db_error:
        # RECOVERABLE claim release failure should not mask original error.
        logger.error(
            "claim.release_db_error",
            intent_id=str(claimed.intent_id),
            error=str(db_error),
            exc_info=True,
        )
        return False


class ExecutionResult(str, Enum):
    """Result of transaction execution."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REVERTED = "reverted"
    DROPPED = "dropped"
    STUCK = "stuck"
    DEADLINE_EXPIRED = "deadline_expired"
    FAILED = "failed"
    BLOCKED = "blocked"  # Signer blocked by nonce gap


@dataclass
class ExecutionOutcome:
    """Outcome of executing an intent."""

    result: ExecutionResult
    intent: TxIntent
    attempt: TxAttempt | None
    tx_hash: str | None = None
    error: Exception | None = None
    block_number: int | None = None
    confirmations: int = 0


class TxExecutor:
    """Transaction executor with full lifecycle management.

    Handles:
    - Gas estimation (EIP-1559)
    - Nonce reservation via NonceManager
    - Transaction signing via Keystore
    - Broadcasting with retry
    - Confirmation monitoring
    - Stuck tx detection and replacement
    """

    def __init__(
        self,
        db: Database,
        rpc: ReadClient,
        keystore: Keystore,
        config: Config,
        lifecycle: "LifecycleDispatcher | None" = None,
        jobs: dict[str, "Job"] | None = None,
    ) -> None:
        """Initialize transaction executor.

        Args:
            db: Database connection
            rpc: RPC manager for chain operations
            keystore: Keystore for transaction signing
            config: Application configuration
            lifecycle: Optional lifecycle dispatcher for events
            jobs: Optional jobs registry for job metadata
        """
        self._db = db
        self._rpc = rpc
        self._keystore = keystore
        self._config = config
        self._nonce_manager = NonceManager(db, rpc, config.chain_id)
        self._lifecycle = lifecycle
        self._jobs = jobs
        self._chain_id = config.chain_id

    def _error_from_data(self, data: dict[str, object]) -> Exception | None:
        error_obj = data.get("exception")
        if isinstance(error_obj, Exception):
            return error_obj
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("error") or str(error)
            return RuntimeError(message)
        if error is None:
            return None
        return RuntimeError(str(error))

    @property
    def nonce_manager(self) -> NonceManager:
        """Get the nonce manager."""
        return self._nonce_manager

    def process_claimed_intent(
        self,
        claimed: ClaimedIntent,
        *,
        intent: TxIntent | None = None,
    ) -> ExecutionOutcome:
        """Process a claimed intent with safe pre-attempt claim release."""
        stage = "unknown"
        try:
            if intent is None:
                intent = self._db.get_intent(claimed.intent_id)
            if intent is None:
                raise RuntimeError(f"Claimed intent not found: {claimed.intent_id}")
            stage = STAGE_BUILD_TX
            return self.execute(intent)
        except BaseException as exc:
            maybe_release_pre_attempt_claim(
                db=self._db,
                claimed=claimed,
                exc=exc,
                stage=stage,
            )
            raise

    # =========================================================================
    # Nonce Gap Detection (Pre-flight check)
    # =========================================================================

    def _check_nonce_gap(
        self,
        signer_address: str,
        deadline: Deadline | None = None,
    ) -> tuple[bool, int | None, float | None]:
        """Check if signer is blocked by a nonce gap.

        Returns (is_blocked, oldest_in_flight_nonce, oldest_age_seconds).

        Checks both RESERVED and IN_FLIGHT records - a gap can exist with either.
        """
        from brawny.model.enums import NonceStatus

        chain_pending = self._rpc.get_transaction_count(
            signer_address,
            "pending",
            deadline=deadline,
        )

        # Get all active reservations (RESERVED or IN_FLIGHT)
        active = self._nonce_manager.get_active_reservations(signer_address)

        if not active:
            # No reservations = no gap possible
            self._clear_gap_tracking(signer_address)
            return False, None, None

        # Find the lowest nonce we're tracking
        expected_next = min(r.nonce for r in active)

        if chain_pending >= expected_next:
            # No gap - chain has caught up or is ahead
            self._clear_gap_tracking(signer_address)
            return False, None, None

        # Gap exists: chain_pending < expected_next
        # Find oldest IN_FLIGHT for TxReplacer visibility
        from brawny.model.enums import NonceStatus
        in_flight = [r for r in active if r.status == NonceStatus.IN_FLIGHT]
        oldest_nonce = None
        oldest_age = None

        if in_flight:
            oldest = min(in_flight, key=lambda r: r.nonce)
            oldest_nonce = oldest.nonce
            oldest_age = (utc_now() - ensure_utc(oldest.created_at)).total_seconds()

        return True, oldest_nonce, oldest_age

    def _get_gap_duration(self, signer_address: str) -> float:
        """Get how long this signer has been blocked by a nonce gap (persisted in DB)."""
        signer_state = self._db.get_signer_state(self._chain_id, signer_address.lower())

        if signer_state is None:
            return 0.0

        if signer_state.gap_started_at is None:
            # First time seeing gap - record it
            self._db.set_gap_started_at(self._chain_id, signer_address.lower(), utc_now())
            return 0.0

        return (utc_now() - ensure_utc(signer_state.gap_started_at)).total_seconds()

    def _clear_gap_tracking(self, signer_address: str) -> None:
        """Clear gap tracking when gap is resolved or force_reset runs."""
        self._db.clear_gap_started_at(self._chain_id, signer_address.lower())

    def _alert_nonce_gap(
        self,
        signer_address: str,
        duration: float,
        oldest_nonce: int | None,
        oldest_age: float | None,
    ) -> None:
        """Alert on prolonged nonce gap (rate-limited per signer)."""
        if not self._lifecycle:
            return

        context = f"Signer {signer_address} blocked for {duration:.0f}s."
        if oldest_nonce is not None and oldest_age is not None:
            context += f" Oldest IN_FLIGHT: nonce {oldest_nonce} ({oldest_age:.0f}s old)."
        context += f" TxReplacer should recover, or run: brawny signer force-reset {signer_address}"

        self._lifecycle.alert(
            level="warning",
            title=f"Nonce gap blocking signer {signer_address[:10]}...",
            message=context,
        )

    def estimate_gas(
        self,
        intent: TxIntent,
        signer_address: str | None = None,
        to_address: str | None = None,
        job: "Job | None" = None,
        deadline: Deadline | None = None,
    ) -> GasParams:
        """Estimate gas for a transaction intent.

        Uses EIP-1559 gas pricing with cached gas quotes.

        Args:
            intent: Transaction intent
            signer_address: Resolved signer address (optional, uses intent if not provided)
            to_address: Resolved to address (optional, uses intent if not provided)
            job: Job instance for gas overrides (optional)

        Returns:
            Estimated gas parameters

        Raises:
            RetriableExecutionError: If no cached gas quote available
        """
        from brawny.model.errors import RetriableExecutionError

        # Use resolved addresses if provided, otherwise fall back to intent
        from_addr = signer_address or intent.signer_address
        to_addr = to_address or intent.to_address

        # Gas limit
        if intent.gas_limit:
            gas_limit = intent.gas_limit
        else:
            try:
                tx_params = {
                    "from": from_addr,
                    "to": to_addr,
                    "value": int(intent.value_wei),
                }
                if intent.data:
                    tx_params["data"] = intent.data

                estimated = self._rpc.estimate_gas(tx_params, deadline=deadline)
                gas_limit = int(estimated * self._config.gas_limit_multiplier)
            except Exception as e:
                if isinstance(e, RPCError) and e.code == RpcErrorKind.EXECUTION_REVERTED.value:
                    # BUG re-raise execution reverted on gas estimation.
                    logger.error(
                        "gas.estimate_reverted",
                        intent_id=str(intent.intent_id),
                        error=str(e),
                        exc_info=True,
                    )
                    setattr(e, "_logged_unexpected", True)
                    raise
                # RECOVERABLE fall back to configured gas limit on estimation failure.
                logger.error(
                    "gas.estimate_failed",
                    intent_id=str(intent.intent_id),
                    error=str(e),
                    exc_info=True,
                )
                gas_limit = self._config.fallback_gas_limit

        # Resolve effective priority_fee (priority: intent > job > config)
        if intent.max_priority_fee_per_gas:
            priority_fee = int(intent.max_priority_fee_per_gas)
        elif job is not None and job.priority_fee is not None:
            priority_fee = int(job.priority_fee)
        else:
            priority_fee = int(self._config.priority_fee)

        # Gas price (EIP-1559)
        if intent.max_fee_per_gas:
            # Explicit in intent - use directly
            max_fee = int(intent.max_fee_per_gas)
        else:
            # Compute from quote (sync cache only)
            quote = self._rpc.gas_quote_sync(deadline=deadline)

            if quote is None:
                # No cached quote - raise retriable error (don't guess)
                # This should rarely happen (gas_ok warms cache)
                # NOTE: Executor must handle RetriableExecutionError with backoff,
                # not tight-loop retry. See intent_retry_backoff_seconds config.
                raise RetriableExecutionError("No gas quote available, will retry")

            computed_max_fee = int((2 * quote.base_fee) + priority_fee)

            # Apply cap if configured
            effective_max_fee = job.max_fee if job and job.max_fee is not None else self._config.max_fee

            if effective_max_fee is not None:
                max_fee = min(int(effective_max_fee), computed_max_fee)
            else:
                max_fee = computed_max_fee

        return GasParams(
            gas_limit=gas_limit,
            max_fee_per_gas=max_fee,
            max_priority_fee_per_gas=priority_fee,
        )

    def calculate_replacement_fees(self, old_params: GasParams) -> GasParams:
        """Calculate bumped fees for replacement transaction.

        Per Ethereum protocol, replacement must have at least 10% higher fees.
        Uses configured fee_bump_percent (default 15%).

        Args:
            old_params: Previous gas parameters

        Returns:
            New gas parameters with bumped fees
        """
        from brawny.tx.fees import bump_fees

        return bump_fees(
            old_params,
            bump_percent=self._config.fee_bump_percent,
            max_fee_cap=self._config.max_fee,
        )

    def execute(self, intent: TxIntent) -> ExecutionOutcome:
        """Execute a transaction intent.

        Full execution flow:
        1. Validate deadline
        2. Reserve nonce
        3. Estimate gas
        4. Build tx dict
        5. Simulate (unless job opts out)
        6. Sign transaction
        7. Broadcast

        Args:
            intent: Transaction intent to execute

        Returns:
            Execution outcome with result and details
        """
        def _retry_intent(reason: str) -> None:
            """Reset intent to created with exponential backoff, or abandon if max retries exceeded."""
            metrics = get_metrics()
            metrics.counter(INTENT_RETRY_ATTEMPTS).inc(
                chain_id=self._chain_id,
                reason=reason,
            )

            # Atomically increment retry count on intent row
            retry_count = self._db.increment_intent_retry_count(intent.intent_id)

            # Check if max retries exceeded
            if retry_count > self._config.max_executor_retries:
                logger.warning(
                    "intent.max_retries_exceeded",
                    intent_id=str(intent.intent_id),
                    retry_count=retry_count,
                    max_retries=self._config.max_executor_retries,
                    reason=reason,
                )
                transition_intent(
                    self._db,
                    intent.intent_id,
                    IntentStatus.TERMINAL,
                    "max_retries_exceeded",
                    chain_id=self._chain_id,
                    terminal_reason=IntentTerminalReason.ABANDONED.value,
                )
                if self._lifecycle:
                    try:
                        self._lifecycle.on_failed(
                            intent, None,
                            RuntimeError(f"Max executor retries ({self._config.max_executor_retries}) exceeded"),
                            failure_type=FailureType.UNKNOWN,
                            failure_stage=FailureStage.PRE_BROADCAST,
                        )
                    except Exception:
                        # RECOVERABLE lifecycle hook failures must not block retries.
                        log_unexpected(
                            logger,
                            "lifecycle.hook_failed",
                            hook="on_failed",
                            intent_id=str(intent.intent_id),
                            job_id=intent.job_id,
                            chain_id=self._chain_id,
                        )
                return

            # Calculate exponential backoff with jitter
            if self._config.intent_retry_backoff_seconds > 0:
                base_backoff = self._config.intent_retry_backoff_seconds * (2 ** (retry_count - 1))
                jitter = random.uniform(0, min(base_backoff * 0.1, 10))  # 10% jitter, max 10s
                backoff_seconds = min(base_backoff + jitter, 300)  # Cap at 5 minutes
                retry_after = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
                self._db.set_intent_retry_after(intent.intent_id, retry_after)
                logger.info(
                    "intent.retry_scheduled",
                    intent_id=str(intent.intent_id),
                    job_id=intent.job_id,
                    retry_count=retry_count,
                    backoff_seconds=round(backoff_seconds, 1),
                    retry_after=retry_after.isoformat(),
                    reason=reason,
                )
            else:
                logger.info(
                    "intent.retry_scheduled",
                    intent_id=str(intent.intent_id),
                    job_id=intent.job_id,
                    retry_count=retry_count,
                    retry_after=None,
                    reason=reason,
                )

            # Release claim to return to CREATED
            if not release_claim(self._db, intent.intent_id):
                logger.warning(
                    "intent.retry_reset_failed",
                    intent_id=str(intent.intent_id),
                    reason=reason,
                )

        # Set RPC job context for metrics attribution
        rpc_ctx_token = set_rpc_job_context(intent.job_id)
        try:
            return self._execute_with_context(intent, _retry_intent)
        finally:
            reset_rpc_job_context(rpc_ctx_token)

    def _resolve_deadline(self, intent: TxIntent) -> Deadline:
        """Resolve overall deadline for an intent."""
        if intent.deadline_ts:
            remaining = (intent.deadline_ts - datetime.now(timezone.utc)).total_seconds()
            return Deadline.from_seconds(remaining)
        return Deadline.from_seconds(self._config.default_deadline_seconds)

    def _execute_with_context(
        self,
        intent: TxIntent,
        _retry_intent: Callable[[str], None],
    ) -> ExecutionOutcome:
        """Execute intent with RPC context already set (internal)."""
        # 0. Resolve signer alias to actual checksum address
        try:
            signer_address = self._keystore.get_address(intent.signer_address)
        except Exception as e:
            # RECOVERABLE signer resolution failures are retried with backoff.
            logger.error(
                "signer.resolution_failed",
                intent_id=str(intent.intent_id),
                signer=intent.signer_address,
                error=str(e),
                exc_info=True,
            )
            if self._lifecycle:
                try:
                    self._lifecycle.on_failed(
                        intent, None, e,
                        failure_type=FailureType.SIGNER_FAILED,
                        failure_stage=FailureStage.PRE_BROADCAST,
                        cleanup_trigger=False,
                    )
                except Exception:
                    # RECOVERABLE lifecycle hook failures must not block execution.
                    log_unexpected(
                        logger,
                        "lifecycle.hook_failed",
                        hook="on_failed",
                        intent_id=str(intent.intent_id),
                        job_id=intent.job_id,
                        chain_id=self._chain_id,
                    )
            _retry_intent("signer_resolution_failed")
            return ExecutionOutcome(
                result=ExecutionResult.FAILED,
                intent=intent,
                attempt=None,
                error=e,
            )

        # Update intent with resolved signer address (so monitor can use it)
        if signer_address.lower() != intent.signer_address.lower():
            self._db.update_intent_signer(intent.intent_id, signer_address)
            logger.debug(
                "signer.resolved",
                intent_id=str(intent.intent_id),
                alias=intent.signer_address,
                address=signer_address,
            )

        # Set RPC budget key after signer resolution (uses canonical signer)
        budget_key = f"{self._chain_id}:{signer_address.lower()}:{intent.intent_id}"
        budget_token = set_rpc_intent_budget_context(budget_key)
        try:
            # Ensure to_address is checksummed
            to_address = Web3.to_checksum_address(intent.to_address)
            job = self._jobs.get(intent.job_id) if self._jobs else None

            deadline = self._resolve_deadline(intent)
            ctx = RunContext(
                intent=intent,
                chain_id=self._chain_id,
                signer_address=signer_address,
                to_address=to_address,
                job=job,
                logger=logger,
                config=self._config,
                rpc=self._rpc,
                db=self._db,
                nonce_manager=self._nonce_manager,
                keystore=self._keystore,
                lifecycle=self._lifecycle,
                deadline=deadline,
            )

            stage = StageName.GAP_CHECK
            data: dict[str, object] = {}

            while True:
                result = self._run_stage(stage, ctx, data)
                outcome = self._apply_result(stage, result, ctx, _retry_intent)
                if outcome.done:
                    return outcome.final
                stage = outcome.next_stage
                data = outcome.data or {}
        finally:
            reset_rpc_intent_budget_context(budget_token)

    def _run_stage(self, stage: StageName, ctx: RunContext, data: dict[str, object]) -> StageResult:
        metrics = get_metrics()
        stage_start = time.monotonic()
        metrics.counter(EXECUTOR_STAGE_STARTED).inc(stage=stage.value)

        if ctx.deadline.expired():
            err = TimeoutError("Intent deadline expired")
            ctx.logger.warning(
                "executor.deadline_expired",
                intent_id=str(ctx.intent.intent_id),
                job_id=ctx.intent.job_id,
                stage=stage.value,
                deadline_remaining_seconds=ctx.deadline.remaining(),
            )
            return Fail(
                "deadline_expired",
                True,
                {
                    "execution_result": ExecutionResult.DEADLINE_EXPIRED,
                    "error": serialize_error(err),
                    "exception": err,
                },
            )

        stage_budget = STAGE_TIMEOUT_SECONDS.get(stage, 10.0)
        stage_deadline = ctx.deadline.child(stage_budget)
        if stage_deadline.expired():
            metrics.counter(EXECUTOR_STAGE_TIMEOUTS).inc(stage=stage.value)
            err = TimeoutError(f"Stage timeout: {stage.value}")
            ctx.logger.warning(
                "executor.stage_timeout",
                intent_id=str(ctx.intent.intent_id),
                job_id=ctx.intent.job_id,
                stage=stage.value,
                deadline_remaining_seconds=ctx.deadline.remaining(),
            )
            return Retry(
                stage,
                RetryDecision(None, reason="stage_timeout"),
                {"error": serialize_error(err), "exception": err},
            )

        if stage == StageName.GAP_CHECK:
            result = self._stage_gap_check(ctx, stage_deadline)
        elif stage == StageName.RESERVE_NONCE:
            result = self._stage_reserve_nonce(ctx, stage_deadline)
        elif stage == StageName.BUILD_TX:
            result = self._stage_build_tx(ctx, data, stage_deadline)
        elif stage == StageName.SIGN:
            result = self._stage_sign(ctx, data, stage_deadline)
        elif stage == StageName.BROADCAST:
            result = self._stage_broadcast(ctx, data, stage_deadline)
        elif stage == StageName.MONITOR_TICK:
            result = self._stage_monitor_tick(ctx, data, stage_deadline)
        elif stage == StageName.FINALIZE:
            result = Ok(StageName.FINALIZE, data)
        else:
            err = RuntimeError(f"Unknown stage {stage}")
            result = Fail("unknown_stage", True, {"error": serialize_error(err), "exception": err})

        outcome_label = "ok"
        if isinstance(result, Retry):
            outcome_label = "retry"
        elif isinstance(result, Fail):
            outcome_label = "fail"
        metrics.counter(EXECUTOR_STAGE_OUTCOME).inc(
            stage=stage.value,
            outcome=outcome_label,
        )
        metrics.histogram(EXECUTOR_ATTEMPT_DURATION_SECONDS).observe(
            time.monotonic() - stage_start,
            stage=stage.value,
        )
        return result

    def _apply_result(
        self,
        stage: StageName,
        result: StageResult,
        ctx: RunContext,
        _retry_intent: Callable[[str], None],
    ) -> StageOutcome:
        intent = ctx.intent

        if isinstance(result, Ok):
            if stage == StageName.SIGN:
                return self._apply_sign_result(ctx, result.data, _retry_intent)
            if stage == StageName.BROADCAST:
                if result.data.get("execution_outcome") is not None:
                    return StageOutcome(
                        done=True,
                        final=result.data.get("execution_outcome"),
                    )
                return self._apply_broadcast_result(ctx, result.data, _retry_intent)
            if stage == StageName.MONITOR_TICK:
                return StageOutcome(done=True, final=result.data.get("execution_outcome"))
            if stage == StageName.FINALIZE:
                return StageOutcome(done=True, final=result.data.get("execution_outcome"))
            return StageOutcome(done=False, next_stage=result.next_stage, data=result.data)

        if isinstance(result, Retry):
            error = result.data.get("error")
            error_obj = self._error_from_data(result.data)
            nonce = result.data.get("nonce")
            if nonce is not None and result.data.get("release_nonce"):
                ctx.nonce_manager.release(ctx.signer_address, int(nonce))

            failure_type = result.data.get("failure_type")
            failure_stage = result.data.get("failure_stage")
            if error_obj is not None and failure_type and ctx.lifecycle:
                try:
                    ctx.lifecycle.on_failed(
                        intent, None, error_obj,
                        failure_type=failure_type,
                        failure_stage=failure_stage or FailureStage.PRE_BROADCAST,
                        cleanup_trigger=False,
                    )
                except Exception:
                    # RECOVERABLE lifecycle hook failures must not block retries.
                    log_unexpected(
                        logger,
                        "lifecycle.hook_failed",
                        hook="on_failed",
                        intent_id=str(intent.intent_id),
                        job_id=intent.job_id,
                        chain_id=ctx.chain_id,
                    )

            _retry_intent(result.retry.reason or "retry")
            return StageOutcome(
                done=True,
                final=ExecutionOutcome(
                    result=ExecutionResult.FAILED,
                    intent=intent,
                    attempt=None,
                    error=error_obj,
                ),
            )

        if isinstance(result, Fail):
            error = result.data.get("error")
            error_obj = self._error_from_data(result.data)
            execution_result = result.data.get("execution_result")

            nonce = result.data.get("nonce")
            if nonce is not None and result.data.get("release_nonce"):
                ctx.nonce_manager.release(ctx.signer_address, int(nonce))

            if execution_result == ExecutionResult.DEADLINE_EXPIRED:
                transition_intent(
                    ctx.db,
                    intent.intent_id,
                    IntentStatus.TERMINAL,
                    "deadline_expired",
                    chain_id=ctx.chain_id,
                    terminal_reason=IntentTerminalReason.ABANDONED.value,
                )
                if ctx.lifecycle:
                    try:
                        ctx.lifecycle.on_failed(
                            intent,
                            None,
                            error_obj or TimeoutError("Intent deadline expired"),
                            failure_type=FailureType.DEADLINE_EXPIRED,
                            failure_stage=FailureStage.PRE_BROADCAST,
                        )
                    except Exception:
                        # RECOVERABLE lifecycle hook failures must not block execution.
                        log_unexpected(
                            logger,
                            "lifecycle.hook_failed",
                            hook="on_failed",
                            intent_id=str(intent.intent_id),
                            job_id=intent.job_id,
                            chain_id=ctx.chain_id,
                        )
                return StageOutcome(
                    done=True,
                    final=ExecutionOutcome(
                        result=ExecutionResult.DEADLINE_EXPIRED,
                        intent=intent,
                        attempt=None,
                        error=error_obj or TimeoutError("Intent deadline expired"),
                    ),
                )

            if execution_result == ExecutionResult.BLOCKED:
                return StageOutcome(
                    done=True,
                    final=ExecutionOutcome(
                        result=ExecutionResult.BLOCKED,
                        intent=intent,
                        attempt=None,
                        error=error_obj,
                    ),
                )

            failure_type = result.data.get("failure_type")
            failure_stage = result.data.get("failure_stage")
            if error_obj is not None and failure_type and ctx.lifecycle:
                try:
                    ctx.lifecycle.on_failed(
                        intent, None, error_obj,
                        failure_type=failure_type,
                        failure_stage=failure_stage or FailureStage.PRE_BROADCAST,
                        cleanup_trigger=False,
                    )
                except Exception:
                    # RECOVERABLE lifecycle hook failures must not block execution.
                    log_unexpected(
                        logger,
                        "lifecycle.hook_failed",
                        hook="on_failed",
                        intent_id=str(intent.intent_id),
                        job_id=intent.job_id,
                        chain_id=ctx.chain_id,
                    )

            if not result.fatal:
                _retry_intent(result.reason)

            return StageOutcome(
                done=True,
                final=ExecutionOutcome(
                    result=ExecutionResult.FAILED,
                    intent=intent,
                    attempt=None,
                    error=error_obj,
                ),
            )

        return StageOutcome(
            done=True,
            final=ExecutionOutcome(
                result=ExecutionResult.FAILED,
                intent=intent,
                attempt=None,
                error=RuntimeError("Unknown stage result"),
            ),
        )

    def _stage_gap_check(self, ctx: RunContext, deadline: Deadline) -> StageResult:
        intent = ctx.intent
        if intent.deadline_ts and datetime.now(timezone.utc) > intent.deadline_ts:
            err = TimeoutError("Intent deadline expired")
            return Fail(
                "deadline_expired",
                True,
                {
                    "execution_result": ExecutionResult.DEADLINE_EXPIRED,
                    "error": serialize_error(err),
                    "exception": err,
                },
            )

        try:
            is_blocked, oldest_nonce, oldest_age = self._check_nonce_gap(
                ctx.signer_address,
                deadline=deadline,
            )
        except Exception as e:
            # RECOVERABLE nonce gap check failures trigger retry.
            ctx.logger.error(
                "nonce.gap_check_failed",
                intent_id=str(intent.intent_id),
                signer=ctx.signer_address,
                error=str(e)[:100],
                exc_info=True,
            )
            decision = retry_policy.decide(StageName.GAP_CHECK.value, e)
            return Retry(
                StageName.GAP_CHECK,
                decision or RetryDecision(None, reason="nonce_gap_check_failed"),
                {"error": serialize_error(e), "exception": e},
            )

        if is_blocked:
            err = RuntimeError(
                f"Nonce gap detected for {ctx.signer_address}, waiting for TxReplacer"
            )
            gap_duration = self._get_gap_duration(ctx.signer_address)
            ctx.logger.warning(
                "nonce.gap_blocked",
                intent_id=str(intent.intent_id),
                job_id=intent.job_id,
                signer=ctx.signer_address,
                blocked_duration_seconds=gap_duration,
                oldest_in_flight_nonce=oldest_nonce,
                oldest_in_flight_age_seconds=oldest_age,
            )

            if ctx.config.allow_unsafe_nonce_reset:
                ctx.logger.warning("nonce.unsafe_reset_triggered", signer=ctx.signer_address)
                ctx.nonce_manager.force_reset(
                    ctx.signer_address,
                    source="executor",
                    reason=f"allow_unsafe_nonce_reset=True, gap_duration={gap_duration}s",
                )
            else:
                if gap_duration > ctx.config.nonce_gap_alert_seconds:
                    self._alert_nonce_gap(ctx.signer_address, gap_duration, oldest_nonce, oldest_age)
                return Fail(
                    "nonce_gap_blocked",
                    True,
                    {
                        "execution_result": ExecutionResult.BLOCKED,
                        "error": serialize_error(err),
                        "exception": err,
                    },
                )

        return Ok(StageName.RESERVE_NONCE, {})

    def _stage_reserve_nonce(self, ctx: RunContext, deadline: Deadline) -> StageResult:
        try:
            nonce = ctx.nonce_manager.reserve_nonce(
                ctx.signer_address,
                intent_id=ctx.intent.intent_id,
                deadline=deadline,
            )
        except Exception as e:
            # RECOVERABLE nonce reservation failures trigger retry.
            endpoint = getattr(e, "endpoint", None)
            if endpoint is None and getattr(e, "__cause__", None) is not None:
                endpoint = getattr(e.__cause__, "endpoint", None)
            ctx.logger.error(
                "nonce.reservation_failed",
                exc_info=True,
                intent_id=str(ctx.intent.intent_id),
                job_id=ctx.intent.job_id,
                signer=ctx.signer_address,
                endpoint=_safe_endpoint_label(endpoint),
                error=str(e),
            )
            decision = retry_policy.decide(StageName.RESERVE_NONCE.value, e)
            return Retry(
                StageName.RESERVE_NONCE,
                decision or RetryDecision(None, reason="nonce_reservation_failed"),
                {
                    "error": serialize_error(e),
                    "exception": e,
                    "failure_type": FailureType.NONCE_FAILED,
                    "failure_stage": FailureStage.PRE_BROADCAST,
                },
            )

        return Ok(StageName.BUILD_TX, {"nonce": nonce})

    def _stage_build_tx(self, ctx: RunContext, data: dict[str, object], deadline: Deadline) -> StageResult:
        nonce = int(data["nonce"])
        try:
            gas_params = self.estimate_gas(
                ctx.intent,
                ctx.signer_address,
                ctx.to_address,
                job=ctx.job,
                deadline=deadline,
            )
        except Exception as e:
            # RECOVERABLE build failures return explicit retry/fail results.
            already_logged = getattr(e, "_logged_unexpected", False)
            if isinstance(e, RPCRetryableError):
                if not already_logged:
                    ctx.logger.error(
                        "build_tx.rpc_retry",
                        exc_info=True,
                        intent_id=str(ctx.intent.intent_id),
                        job_id=ctx.intent.job_id,
                        error=str(e),
                    )
                decision = retry_policy.decide(StageName.BUILD_TX.value, e)
                return Retry(
                    StageName.BUILD_TX,
                    decision or RetryDecision(None, reason="rpc_timeout"),
                    {
                        "error": serialize_error(e),
                        "exception": e,
                        "nonce": nonce,
                        "release_nonce": True,
                    },
                )
            if "RetriableExecutionError" in type(e).__name__ or "No gas quote" in str(e):
                if not already_logged:
                    ctx.logger.error(
                        "gas.no_quote_available",
                        intent_id=str(ctx.intent.intent_id),
                        job_id=ctx.intent.job_id,
                        error=str(e),
                        exc_info=True,
                    )
                decision = retry_policy.decide(StageName.BUILD_TX.value, e)
                return Retry(
                    StageName.BUILD_TX,
                    decision or RetryDecision(None, reason="no_gas_quote"),
                    {
                        "error": serialize_error(e),
                        "exception": e,
                        "nonce": nonce,
                        "release_nonce": True,
                    },
                )
            if not already_logged:
                ctx.logger.error(
                    "estimate_gas_failed",
                    intent_id=str(ctx.intent.intent_id),
                    job_id=ctx.intent.job_id,
                    error=str(e),
                    exc_info=True,
                )
            return Fail(
                "estimate_gas_failed",
                True,
                {
                    "error": serialize_error(e),
                    "exception": e,
                    "nonce": nonce,
                    "release_nonce": True,
                },
            )

        tx_dict = self._build_tx_dict(ctx.intent, nonce, gas_params, ctx.to_address)
        tx_dict["from"] = ctx.signer_address
        return Ok(StageName.SIGN, {"nonce": nonce, "gas_params": gas_params, "tx_dict": tx_dict})

    def _stage_sign(self, ctx: RunContext, data: dict[str, object], deadline: Deadline) -> StageResult:
        nonce = int(data["nonce"])
        gas_params = data["gas_params"]
        tx_dict = data["tx_dict"]
        try:
            signed_tx = ctx.keystore.sign_transaction(tx_dict, ctx.signer_address)
        except Exception as e:
            # RECOVERABLE signing failures trigger retry.
            ctx.logger.error(
                "tx.sign_failed",
                intent_id=str(ctx.intent.intent_id),
                job_id=ctx.intent.job_id,
                error=str(e),
                exc_info=True,
            )
            decision = retry_policy.decide(StageName.SIGN.value, e)
            return Retry(
                StageName.SIGN,
                decision or RetryDecision(None, reason="sign_failed"),
                {
                    "error": serialize_error(e),
                    "exception": e,
                    "nonce": nonce,
                    "release_nonce": True,
                    "failure_type": FailureType.SIGN_FAILED,
                    "failure_stage": FailureStage.PRE_BROADCAST,
                },
            )

        tx_hash = self._compute_signed_tx_hash(signed_tx)
        if gas_params.max_priority_fee_per_gas < 100_000_000:
            ctx.logger.warning(
                "gas.priority_fee_very_low",
                intent_id=str(ctx.intent.intent_id),
                job_id=ctx.intent.job_id,
                priority_fee_wei=gas_params.max_priority_fee_per_gas,
                priority_fee_gwei=gas_params.max_priority_fee_per_gas / 1e9,
                hint="Transaction may not be included - validators receive almost no tip",
            )

        ctx.logger.info(
            LogEvents.TX_SIGN,
            intent_id=str(ctx.intent.intent_id),
            job_id=ctx.intent.job_id,
            signer=ctx.signer_address,
            nonce=nonce,
            gas_limit=gas_params.gas_limit,
            max_fee=gas_params.max_fee_per_gas,
            priority_fee=gas_params.max_priority_fee_per_gas,
        )

        data.update({"signed_tx": signed_tx, "tx_hash": tx_hash, "nonce": nonce, "gas_params": gas_params})
        return Ok(StageName.BROADCAST, data)

    def _stage_broadcast(self, ctx: RunContext, data: dict[str, object], deadline: Deadline) -> StageResult:
        signed_tx = data["signed_tx"]
        endpoints = data["endpoints"]
        group_name = data["broadcast_group"]
        job_id = ctx.job.job_id if ctx.job else None

        resume_pending_send = bool(data.get("resume_pending_send"))
        if resume_pending_send and data.get("tx_hash"):
            try:
                exists = self._probe_pending_send(str(data["tx_hash"]), deadline)
            except Exception as e:
                # RECOVERABLE probe failures trigger retry.
                ctx.logger.error(
                    "broadcast.probe_failed",
                    intent_id=str(ctx.intent.intent_id),
                    job_id=job_id,
                    error=str(e)[:200],
                    exc_info=True,
                )
                return Retry(
                    StageName.BROADCAST,
                    RetryDecision(None, reason="probe_unknown"),
                    {
                        "error": serialize_error(e),
                        "exception": e,
                        "nonce": data.get("nonce"),
                        "attempt_id": data.get("attempt_id"),
                    },
                )
            if exists:
                return Ok(StageName.FINALIZE, {**data, "already_known": True, "endpoint_url": None})

        nonce = int(data["nonce"])
        try:
            ctx.db.require_bound_and_attempt(ctx.intent.intent_id, nonce, endpoints)
        except InvariantViolation as exc:
            ctx.logger.error(
                "broadcast.invariant_violation",
                intent_id=str(ctx.intent.intent_id),
                job_id=job_id,
                error=str(exc)[:200],
            )
            transition_intent(
                ctx.db,
                ctx.intent.intent_id,
                IntentStatus.TERMINAL,
                "missing_binding_or_attempt",
                chain_id=ctx.chain_id,
                terminal_reason=IntentTerminalReason.FAILED.value,
            )
            return Fail(
                "missing_binding_or_attempt",
                True,
                {
                    "error": serialize_error(exc),
                    "exception": exc,
                    "failure_type": FailureType.UNKNOWN,
                    "failure_stage": FailureStage.PRE_BROADCAST,
                },
            )

        from brawny._rpc.broadcast import broadcast_transaction
        from brawny._rpc.errors import RPCGroupUnavailableError

        tx_dict = data.get("tx_dict")
        if not isinstance(tx_dict, dict):
            err = RuntimeError("Missing tx_dict for broadcast simulation")
            ctx.logger.error(
                "broadcast.missing_tx_dict",
                intent_id=str(ctx.intent.intent_id),
                job_id=job_id,
                error=str(err),
            )
            return Fail(
                "missing_tx_dict",
                True,
                {
                    "error": serialize_error(err),
                    "exception": err,
                    "nonce": data.get("nonce"),
                    "attempt_id": data.get("attempt_id"),
                },
            )

        tx_dict["from"] = ctx.signer_address
        tx_dict["nonce"] = nonce

        simulation_endpoint: str | None = None

        def _pre_send_simulation(endpoint: str) -> None:
            nonlocal simulation_endpoint
            # Use read-group RPC for simulation (broadcast endpoints may not support eth_call).
            simulation_endpoint = None
            ctx.logger.debug(
                "simulation.pre_send",
                intent_id=str(ctx.intent.intent_id),
                job_id=job_id,
                broadcast_group=group_name,
                simulation_rpc_group="read",
            )
            self._rpc.simulate_transaction(tx_dict, deadline=deadline)

        try:
            tx_hash, endpoint_url = broadcast_transaction(
                raw_tx=signed_tx.raw_transaction,
                endpoints=endpoints,
                group_name=group_name,
                config=ctx.config,
                job_id=job_id,
                deadline=deadline,
                pre_call=_pre_send_simulation,
            )
        except (SimulationReverted, SimulationNetworkError) as e:
            head_block = None
            try:
                head_block = ctx.rpc.get_block_number(deadline=deadline.child(2.0))
            except Exception as e:
                # RECOVERABLE head block fetch failures should not block recovery.
                log_unexpected(
                    ctx.logger,
                    "broadcast.head_block_fetch_failed",
                    intent_id=str(ctx.intent.intent_id),
                    job_id=job_id,
                    chain_id=ctx.chain_id,
                    error=str(e)[:200],
                )
                head_block = None
            outcome = self._handle_send_simulation_failure(
                ctx,
                data,
                e,
                simulation_endpoint,
                head_block,
            )
            return Ok(StageName.FINALIZE, {"execution_outcome": outcome})
        except RPCGroupUnavailableError as e:
            ctx.logger.error(
                "broadcast_unavailable",
                intent_id=str(ctx.intent.intent_id),
                job_id=job_id,
                broadcast_group=group_name,
                endpoints=endpoints,
                error=str(e.last_error) if e.last_error else None,
            )
            return Fail(
                "broadcast_failed",
                False,
                {
                    "error": serialize_error(e),
                    "exception": e,
                    "nonce": data.get("nonce"),
                    "attempt_id": data.get("attempt_id"),
                },
            )
        except (RPCError, DatabaseError, OSError, ValueError, RuntimeError) as e:
            ctx.logger.error(
                "tx.broadcast_failed",
                intent_id=str(ctx.intent.intent_id),
                job_id=job_id,
                attempt_id=str(data.get("attempt_id")) if data.get("attempt_id") else None,
                error=str(e),
            )
            return Fail(
                "broadcast_failed",
                False,
                {
                    "error": serialize_error(e),
                    "exception": e,
                    "nonce": data.get("nonce"),
                    "attempt_id": data.get("attempt_id"),
                },
            )

        return Ok(StageName.FINALIZE, {**data, "endpoint_url": endpoint_url, "tx_hash_rpc": tx_hash})

    def _stage_monitor_tick(self, ctx: RunContext, data: dict[str, object], deadline: Deadline) -> StageResult:
        return Ok(StageName.FINALIZE, data)

    def _apply_sign_result(
        self,
        ctx: RunContext,
        data: dict[str, object],
        _retry_intent: Callable[[str], None],
    ) -> StageOutcome:
        intent = ctx.intent
        nonce = int(data["nonce"])
        gas_params = data["gas_params"]
        tx_hash = data["tx_hash"]

        attempt = self._find_attempt_by_hash(intent.intent_id, tx_hash)
        attempt_preexisting = attempt is not None
        if attempt and attempt.status in (
            AttemptStatus.BROADCAST.value,
            AttemptStatus.PENDING.value,
            AttemptStatus.CONFIRMED.value,
        ):
            ctx.nonce_manager.mark_in_flight(ctx.signer_address, nonce, intent.intent_id)
            transition_intent(
                ctx.db,
                intent.intent_id,
                IntentStatus.BROADCASTED,
                "broadcast_complete",
                chain_id=ctx.chain_id,
            )
            return StageOutcome(
                done=True,
                final=ExecutionOutcome(
                    result=ExecutionResult.PENDING,
                    intent=intent,
                    attempt=attempt,
                    tx_hash=attempt.tx_hash,
                ),
            )

        group_name, endpoints = self._resolve_broadcast_binding(ctx)

        attempt_id = attempt.attempt_id if attempt else uuid4()
        if attempt is None:
            try:
                attempt = ctx.db.create_attempt_once(
                    attempt_id=attempt_id,
                    intent_id=intent.intent_id,
                    nonce=nonce,
                    gas_params_json=gas_params.to_json(),
                    status=AttemptStatus.PENDING_SEND.value,
                    tx_hash=tx_hash,
                    broadcast_group=group_name,
                    endpoint_url=None,
                    binding=(group_name, endpoints),
                    actor=intent.job_id,
                    reason="initial_attempt",
                    source="executor",
                )
            except InvariantViolation as e:
                ctx.logger.error(
                    "broadcast.binding_failed",
                    intent_id=str(intent.intent_id),
                    job_id=intent.job_id,
                    error=str(e)[:200],
                )
                transition_intent(
                    ctx.db,
                    intent.intent_id,
                    IntentStatus.TERMINAL,
                    "binding_failed",
                    chain_id=ctx.chain_id,
                    terminal_reason=IntentTerminalReason.FAILED.value,
                )
                return StageOutcome(
                    done=True,
                    final=ExecutionOutcome(
                        result=ExecutionResult.FAILED,
                        intent=intent,
                        attempt=None,
                        error=e,
                    ),
                )
            except Exception as e:
                # RECOVERABLE attempt creation failures trigger retry.
                ctx.logger.error(
                    "attempt.create_failed",
                    intent_id=str(intent.intent_id),
                    job_id=intent.job_id,
                    error=str(e)[:200],
                    exc_info=True,
                )
                _retry_intent("attempt_create_failed")
                return StageOutcome(
                    done=True,
                    final=ExecutionOutcome(
                        result=ExecutionResult.FAILED,
                        intent=intent,
                        attempt=None,
                        error=e,
                    ),
                )

        data.update(
            {
                "attempt_id": attempt_id,
                "broadcast_group": group_name,
                "endpoints": endpoints,
                "resume_pending_send": attempt_preexisting and attempt.status in (
                    AttemptStatus.PENDING_SEND.value,
                    AttemptStatus.SIGNED.value,
                ),
            }
        )
        return StageOutcome(done=False, next_stage=StageName.BROADCAST, data=data)

    def _apply_broadcast_result(
        self,
        ctx: RunContext,
        data: dict[str, object],
        _retry_intent: Callable[[str], None],
    ) -> StageOutcome:
        intent = ctx.intent
        attempt_id = data.get("attempt_id")
        nonce = int(data["nonce"])

        if data.get("error") is not None:
            error = data["error"]
            error_obj = self._error_from_data(data)
            metrics = get_metrics()
            metrics.counter(TX_FAILED).inc(
                chain_id=ctx.chain_id,
                job_id=intent.job_id,
                reason="broadcast_failed",
            )
            if attempt_id is not None:
                ctx.db.update_attempt_status(
                    attempt_id,
                    AttemptStatus.FAILED.value,
                    error_code="broadcast_failed",
                    error_detail=str(error_obj or error)[:500],
                )
            ctx.nonce_manager.release(ctx.signer_address, nonce)
            if ctx.lifecycle:
                try:
                    ctx.lifecycle.on_failed(
                        intent, None, error_obj or RuntimeError(str(error)),
                        failure_type=FailureType.BROADCAST_FAILED,
                        failure_stage=FailureStage.BROADCAST,
                        cleanup_trigger=False,
                    )
                except Exception:
                    # RECOVERABLE lifecycle hook failures must not block retries.
                    log_unexpected(
                        logger,
                        "lifecycle.hook_failed",
                        hook="on_failed",
                        intent_id=str(intent.intent_id),
                        job_id=intent.job_id,
                        chain_id=ctx.chain_id,
                    )
            _retry_intent("broadcast_failed")
            return StageOutcome(
                done=True,
                final=ExecutionOutcome(
                    result=ExecutionResult.FAILED,
                    intent=intent,
                    attempt=None,
                    error=error_obj or RuntimeError(str(error)),
                ),
            )

        from brawny.tx_hash import normalize_tx_hash

        tx_hash = normalize_tx_hash(data.get("tx_hash_rpc") or data.get("tx_hash"))
        endpoint_url = data.get("endpoint_url")
        gas_params = data.get("gas_params")
        current_block = None

        if attempt_id is not None:
            broadcast_deadline = ctx.deadline.child(STAGE_TIMEOUT_SECONDS[StageName.BROADCAST])
            current_block = ctx.rpc.get_block_number(deadline=broadcast_deadline)
            ctx.db.update_attempt_status(
                attempt_id,
                AttemptStatus.BROADCAST.value,
                tx_hash=tx_hash,
                broadcast_block=current_block,
                broadcast_at=datetime.now(timezone.utc),
                endpoint_url=endpoint_url,
            )

        ctx.nonce_manager.mark_in_flight(ctx.signer_address, nonce, intent.intent_id)

        if not transition_intent(
            ctx.db,
            intent.intent_id,
            IntentStatus.BROADCASTED,
            "broadcast_complete",
            chain_id=ctx.chain_id,
        ):
            return StageOutcome(
                done=True,
                final=ExecutionOutcome(
                    result=ExecutionResult.FAILED,
                    intent=intent,
                    attempt=None,
                    error=RuntimeError("Intent status not in claimed state"),
                ),
            )

        ctx.logger.info(
            LogEvents.TX_BROADCAST,
            intent_id=str(intent.intent_id),
            job_id=intent.job_id,
            attempt_id=str(attempt_id) if attempt_id else None,
            tx_hash=tx_hash,
            signer=ctx.signer_address,
            nonce=nonce,
            broadcast_group=data.get("broadcast_group"),
            endpoint_url=_safe_endpoint_label(endpoint_url),
            head_block=current_block,
            max_fee=gas_params.max_fee_per_gas if gas_params else None,
            priority_fee=gas_params.max_priority_fee_per_gas if gas_params else None,
        )
        metrics = get_metrics()
        metrics.counter(TX_BROADCAST).inc(
            chain_id=ctx.chain_id,
            job_id=intent.job_id,
        )

        attempt = ctx.db.get_attempt(attempt_id) if attempt_id else None
        if ctx.lifecycle and attempt is not None:
            try:
                ctx.lifecycle.on_submitted(intent, attempt)
            except Exception:
                # RECOVERABLE lifecycle hook failures must not block execution.
                log_unexpected(
                    logger,
                    "lifecycle.hook_failed",
                    hook="on_submitted",
                    intent_id=str(intent.intent_id),
                    attempt_id=str(attempt.attempt_id),
                    tx_hash=attempt.tx_hash,
                    job_id=intent.job_id,
                    chain_id=ctx.chain_id,
                )

        return StageOutcome(
            done=True,
            final=ExecutionOutcome(
                result=ExecutionResult.PENDING,
                intent=intent,
                attempt=attempt,
                tx_hash=tx_hash,
            ),
        )

    def _resolve_broadcast_binding(
        self,
        ctx: RunContext,
    ) -> tuple[str, list[str]]:
        binding = ctx.db.get_broadcast_binding(ctx.intent.intent_id)
        job_id = ctx.job.job_id if ctx.job else None

        if binding is not None:
            group_name, endpoints = binding
            if ctx.job:
                from brawny.config.routing import resolve_job_groups

                _, job_broadcast_group = resolve_job_groups(ctx.config, ctx.job)
                if job_broadcast_group != group_name:
                    ctx.logger.warning(
                        "broadcast_group_mismatch",
                        intent_id=str(ctx.intent.intent_id),
                        job_id=job_id,
                        persisted_group=group_name,
                        current_job_group=job_broadcast_group,
                    )
        else:
            if ctx.job is None:
                from brawny.config.routing import resolve_default_broadcast_group

                group_name = resolve_default_broadcast_group(ctx.config)
            else:
                from brawny.config.routing import resolve_job_groups

                _, group_name = resolve_job_groups(ctx.config, ctx.job)
            endpoints = ctx.config.rpc_groups[group_name].endpoints

        return group_name, list(endpoints)

    def _find_attempt_by_hash(self, intent_id: UUID, tx_hash: str) -> TxAttempt | None:
        attempts = self._db.get_attempts_for_intent(intent_id)
        for attempt in attempts:
            if attempt.tx_hash and attempt.tx_hash.lower() == tx_hash.lower():
                return attempt
        return None

    def _compute_signed_tx_hash(self, signed_tx: object) -> str:
        if hasattr(signed_tx, "hash"):
            tx_hash = signed_tx.hash
            if hasattr(tx_hash, "hex"):
                return f"0x{tx_hash.hex()}"
            return str(tx_hash)
        return f"0x{Web3.keccak(signed_tx.raw_transaction).hex()}"

    def _probe_pending_send(self, tx_hash: str, deadline: Deadline) -> bool:
        receipt = self._rpc.get_transaction_receipt(tx_hash, deadline=deadline)
        if receipt:
            return True
        tx = self._rpc.get_transaction_by_hash(tx_hash, deadline=deadline)
        return tx is not None

    def _build_tx_dict(
        self,
        intent: TxIntent,
        nonce: int,
        gas_params: GasParams,
        to_address: str | None = None,
    ) -> dict:
        """Build transaction dictionary for signing.

        Args:
            intent: Transaction intent
            nonce: Nonce to use
            gas_params: Gas parameters
            to_address: Resolved to address (optional, uses intent if not provided)

        Returns:
            Transaction dictionary ready for signing
        """
        tx = {
            "nonce": nonce,
            "to": to_address or intent.to_address,
            "value": intent.value_wei,
            "gas": gas_params.gas_limit,
            "maxFeePerGas": gas_params.max_fee_per_gas,
            "maxPriorityFeePerGas": gas_params.max_priority_fee_per_gas,
            "chainId": intent.chain_id,
            "type": 2,  # EIP-1559
        }

        if intent.data:
            tx["data"] = intent.data

        return normalize_tx_dict(tx)

    # =========================================================================
    # Send-boundary simulation handling
    # =========================================================================

    def _simulation_error_summary(
        self,
        error: SimulationReverted | SimulationNetworkError,
        max_len: int = 200,
    ) -> str:
        if isinstance(error, SimulationReverted):
            summary = error.reason
        else:
            summary = str(error)
        summary = summary.strip() or type(error).__name__
        if len(summary) > max_len:
            summary = f"{summary[: max_len - 3]}..."
        return summary

    def _send_simulation_blocked_alert(
        self,
        intent: TxIntent,
        job_name: str,
        endpoint_url: str | None,
        head_block: int | None,
        reason_code: str,
        summary: str,
    ) -> None:
        tg = self._config.telegram
        if not tg.bot_token:
            return
        from brawny.alerts.routing import resolve_targets
        from brawny.alerts.send import AlertConfig, AlertPayload, AlertEvent
        from brawny.alerts import send as alerts_send

        admin_chat_ids = resolve_targets(tg.admin, tg.chats, [])
        if not admin_chat_ids:
            return

        endpoint_label = _safe_endpoint_label(endpoint_url)
        lines = [
            "Simulation failed at send time; tx NOT broadcast.",
            f"job_id={intent.job_id}",
            f"intent_id={intent.intent_id}",
        ]
        if endpoint_label:
            lines.append(f"endpoint={endpoint_label}")
        if head_block is not None:
            lines.append(f"block={head_block}")
        lines.append(f"reason_code={reason_code}")
        lines.append(f"revert={summary}")

        payload = AlertPayload(
            job_id=intent.job_id,
            job_name=job_name,
            event_type=AlertEvent.FAILED,
            message="\n".join(lines),
            parse_mode=tg.parse_mode or "Markdown",
            chain_id=self._config.chain_id,
        )
        config = AlertConfig(
            telegram_token=tg.bot_token,
            telegram_chat_ids=admin_chat_ids,
        )
        alerts_send.enqueue_alert(payload, config)

    def _handle_send_simulation_failure(
        self,
        ctx: RunContext,
        data: dict[str, object],
        error: SimulationReverted | SimulationNetworkError,
        endpoint_url: str | None,
        head_block: int | None,
    ) -> ExecutionOutcome:
        intent = ctx.intent
        attempt_id = data.get("attempt_id")
        nonce = int(data["nonce"]) if data.get("nonce") is not None else None
        gas_params = data.get("gas_params")
        summary = self._simulation_error_summary(error)
        reason_code = "stale_pre_broadcast"

        metrics = get_metrics()
        if isinstance(error, SimulationReverted):
            metrics.counter(SIMULATION_REVERTED).inc(
                chain_id=intent.chain_id,
                job_id=intent.job_id,
            )
        else:
            metrics.counter(SIMULATION_NETWORK_ERRORS).inc(
                chain_id=intent.chain_id,
                job_id=intent.job_id,
            )

        ctx.logger.error(
            "tx.simulation_blocked_send",
            intent_id=str(intent.intent_id),
            job_id=intent.job_id,
            attempt_id=str(attempt_id) if attempt_id else None,
            endpoint_url=_safe_endpoint_label(endpoint_url),
            head_block=head_block,
            nonce=nonce,
            max_fee=gas_params.max_fee_per_gas if gas_params else None,
            priority_fee=gas_params.max_priority_fee_per_gas if gas_params else None,
            reason_code=reason_code,
            error_type=type(error).__name__,
            revert_reason=summary,
        )

        if attempt_id is not None:
            ctx.db.update_attempt_status(
                attempt_id,
                AttemptStatus.FAILED.value,
                endpoint_url=endpoint_url,
                error_code="simulation_blocked_send",
                error_detail=summary[:500],
            )

        if nonce is not None:
            ctx.nonce_manager.release(ctx.signer_address, nonce)

        transitioned = transition_intent(
            ctx.db,
            intent.intent_id,
            IntentStatus.TERMINAL,
            reason_code,
            chain_id=ctx.chain_id,
            halt_reason=reason_code,
        )

        if transitioned:
            job_name = ctx.job.name if ctx.job else intent.job_id
            self._send_simulation_blocked_alert(
                intent=intent,
                job_name=job_name,
                endpoint_url=endpoint_url,
                head_block=head_block,
                reason_code=reason_code,
                summary=summary,
            )
            if ctx.lifecycle:
                failure_type = FailureType.SIMULATION_REVERTED
                if isinstance(error, SimulationNetworkError):
                    failure_type = FailureType.SIMULATION_NETWORK_ERROR
                try:
                    ctx.lifecycle.on_failed(
                        intent,
                        None,
                        error,
                        failure_type=failure_type,
                        failure_stage=FailureStage.PRE_BROADCAST,
                        cleanup_trigger=False,
                    )
                except Exception:
                    # RECOVERABLE lifecycle hook failures must not block execution.
                    log_unexpected(
                        logger,
                        "lifecycle.hook_failed",
                        hook="on_failed",
                        intent_id=str(intent.intent_id),
                        job_id=intent.job_id,
                        chain_id=ctx.chain_id,
                    )

        return ExecutionOutcome(
            result=ExecutionResult.FAILED,
            intent=intent,
            attempt=None,
            error=error,
        )

    # NOTE: _abandon_stranded_intents() has been removed as part of the
    # nonce policy simplification. Stranded intents are now recovered by
    # TxReplacer via fee bumping, rather than being auto-abandoned.
    # See NONCE.md for the new policy.
