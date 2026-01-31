"""Stuck transaction detection and replacement.

Implements transaction replacement logic from SPEC 9.4:
- Detect stuck transactions based on time and blocks
- Calculate replacement fees with proper bumping
- Create replacement attempts with linked history
- Enforce max replacement attempts and backoff
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from web3 import Web3

from brawny.logging import LogEvents, get_logger, log_unexpected
from brawny.metrics import TX_REPLACED, get_metrics
from brawny.model.enums import AttemptStatus, IntentStatus, IntentTerminalReason
from brawny.model.errors import FailureStage, FailureType, SimulationNetworkError, SimulationReverted
from brawny.recovery.ops import (
    RecoveryContext,
    release_nonce_if_safe,
    transition_intent_if_current_status,
)
from brawny.timeout import Deadline
from brawny.tx.utils import normalize_tx_dict
from brawny.model.types import GasParams

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny.keystore import Keystore
    from brawny.lifecycle import LifecycleDispatcher
    from brawny.model.types import TxAttempt, TxIntent
    from brawny._rpc.clients import BroadcastClient
    from brawny.tx.nonce import NonceManager
    from brawny.runtime_controls import RuntimeControls

logger = get_logger(__name__)

REPLACER_TICK_TIMEOUT_SECONDS = 10.0


def _safe_endpoint_label(endpoint: str) -> str:
    parts = endpoint.split("://", 1)
    if len(parts) == 2:
        scheme, rest = parts
    else:
        scheme, rest = "http", parts[0]
    host = rest.split("/", 1)[0]
    host = host.split("@", 1)[-1]
    return f"{scheme}://{host}"


@dataclass
class ReplacementResult:
    """Result of a replacement attempt."""

    success: bool
    new_attempt: TxAttempt | None = None
    new_tx_hash: str | None = None
    error: str | None = None


class TxReplacer:
    """Handle stuck transaction replacement.

    Implements SPEC 9.4 replacement policy:
    - Same nonce as original attempt
    - Bump both max_fee_per_gas and max_priority_fee_per_gas by fee_bump_percent
    - Link via replaces_attempt_id
    - Mark old attempt as replaced
    - Max max_replacement_attempts before abandoning
    - Double wait time between each replacement attempt
    """

    def __init__(
        self,
        db: Database,
        rpc: BroadcastClient,
        keystore: Keystore,
        nonce_manager: NonceManager,
        config: Config,
        lifecycle: "LifecycleDispatcher | None" = None,
        controls: "RuntimeControls | None" = None,
    ) -> None:
        """Initialize transaction replacer.

        Args:
            db: Database connection
            rpc: RPC manager for chain queries
            keystore: Keystore for transaction signing
            nonce_manager: Nonce manager
            config: Application configuration
        """
        self._db = db
        self._rpc = rpc
        self._keystore = keystore
        self._nonce_manager = nonce_manager
        self._config = config
        self._lifecycle = lifecycle
        self._controls = controls

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

    def get_replacement_count(self, intent_id) -> int:
        """Get number of replacement attempts for an intent.

        Args:
            intent_id: Intent ID

        Returns:
            Number of attempts that are replacements
        """
        attempts = self._db.get_attempts_for_intent(intent_id)
        return sum(1 for a in attempts if a.replaces_attempt_id is not None)

    def should_replace(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        deadline: Deadline | None,
    ) -> bool:
        """Check if a transaction should be replaced.

        Args:
            intent: Transaction intent
            attempt: Current transaction attempt

        Returns:
            True if transaction should be replaced
        """
        if not attempt.broadcast_block or not attempt.tx_hash:
            return False

        # Check max replacements
        replacement_count = self.get_replacement_count(intent.intent_id)
        if replacement_count >= self._config.max_replacement_attempts:
            logger.info(
                "replacement.max_reached",
                intent_id=str(intent.intent_id),
                count=replacement_count,
                max=self._config.max_replacement_attempts,
            )
            return False

        # Check time elapsed using Unix timestamps (no timezone issues)
        import time

        elapsed_seconds: float | None = None
        if attempt.broadcast_at:
            elapsed_seconds = time.time() - attempt.broadcast_at.timestamp()

        # Double wait time for each replacement attempt
        wait_multiplier = 2 ** replacement_count
        required_wait = self._config.stuck_tx_seconds * wait_multiplier
        time_ready = elapsed_seconds is not None and elapsed_seconds >= required_wait

        # Check if still pending (no receipt)
        if deadline is not None and deadline.expired():
            return False
        receipt = self._rpc.get_transaction_receipt(attempt.tx_hash, deadline=deadline)
        if receipt is not None:
            # Has receipt - don't replace
            return False

        if time_ready:
            return True

        # Check blocks elapsed (only if time threshold not reached)
        try:
            current_block = self._rpc.get_block_number(deadline=deadline)
            blocks_since = current_block - attempt.broadcast_block

            required_blocks = self._config.stuck_tx_blocks * wait_multiplier
            if blocks_since >= required_blocks:
                return True
        except Exception as e:
            # RECOVERABLE block lookup failure defers replacement decision.
            log_unexpected(
                logger,
                "replacement.block_number_failed",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                tx_hash=attempt.tx_hash,
                error=str(e)[:200],
            )

        return False

    def replace_transaction(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        deadline: Deadline | None,
    ) -> ReplacementResult:
        """Create a replacement transaction with bumped fees.

        Uses the same nonce as the original attempt but with higher fees.

        Args:
            intent: Transaction intent
            attempt: Current stuck attempt

        Returns:
            ReplacementResult with new attempt if successful
        """
        if attempt.tx_hash:
            try:
                receipt = self._rpc.get_transaction_receipt(attempt.tx_hash, deadline=deadline)
            except Exception as e:
                # RECOVERABLE receipt check failures fall back to replacement path.
                log_unexpected(
                    logger,
                    "replacement.receipt_check_failed",
                    intent_id=str(intent.intent_id),
                    attempt_id=str(attempt.attempt_id),
                    tx_hash=attempt.tx_hash,
                    error=str(e)[:200],
                )
                receipt = None
            if receipt:
                logger.info(
                    "replacement.skip_confirmed",
                    intent_id=str(intent.intent_id),
                    attempt_id=str(attempt.attempt_id),
                    tx_hash=attempt.tx_hash,
                )
                return ReplacementResult(success=False, error="already_confirmed")

        current_intent = self._db.get_intent(intent.intent_id)
        if current_intent is None or current_intent.status != IntentStatus.BROADCASTED:
            return ReplacementResult(success=False, error="intent_not_broadcasted")

        logger.info(
            "replacement.starting",
            intent_id=str(intent.intent_id),
            attempt_id=str(attempt.attempt_id),
            old_tx_hash=attempt.tx_hash,
            nonce=attempt.nonce,
        )

        binding = self._db.get_broadcast_binding(intent.intent_id)
        if not binding:
            logger.error(
                "replacement.missing_binding",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                chain_id=intent.chain_id,
            )
            return ReplacementResult(success=False, error="missing_broadcast_binding")

        group_name, endpoints = binding
        try:
            self._db.require_bound_and_attempt(intent.intent_id, attempt.nonce, endpoints)
        except Exception as e:
            # RECOVERABLE binding mismatches block replacement to avoid wrong endpoints.
            log_unexpected(
                logger,
                "replacement.binding_invalid",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                chain_id=intent.chain_id,
                error=str(e)[:200],
            )
            return ReplacementResult(success=False, error="binding_invalid")

        # Calculate new gas parameters
        new_gas_params = self.calculate_replacement_fees(attempt.gas_params)

        # Checksum addresses for RPC/signing
        signer_address = Web3.to_checksum_address(intent.signer_address)
        to_address = Web3.to_checksum_address(intent.to_address)

        # Build replacement transaction (same nonce!)
        tx_dict = {
            "nonce": attempt.nonce,  # SAME nonce as original
            "to": to_address,
            "value": intent.value_wei,
            "gas": new_gas_params.gas_limit,
            "maxFeePerGas": new_gas_params.max_fee_per_gas,
            "maxPriorityFeePerGas": new_gas_params.max_priority_fee_per_gas,
            "chainId": intent.chain_id,
            "type": 2,  # EIP-1559
        }

        if intent.data:
            tx_dict["data"] = intent.data

        tx_dict = normalize_tx_dict(tx_dict)
        tx_dict["from"] = signer_address

        endpoint_labels = [_safe_endpoint_label(endpoint) for endpoint in endpoints]

        try:
            self._rpc.simulate_transaction(tx_dict, deadline=deadline)
            logger.info(
                "replacement.attempt_decision",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                nonce=attempt.nonce,
                reason="stuck",
                simulated_ok=True,
                simulation_rpc_group="read",
                broadcast_group=group_name,
                broadcast_endpoints=endpoint_labels,
            )
        except SimulationReverted as exc:
            summary = exc.reason
            logger.error(
                "replacement.simulation_blocked",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                tx_hash=attempt.tx_hash,
                nonce=attempt.nonce,
                error_type=type(exc).__name__,
                revert_reason=summary[:200],
                broadcast_group=group_name,
                broadcast_endpoints=endpoint_labels,
                simulation_rpc_group="read",
            )
            logger.info(
                "replacement.attempt_decision",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                nonce=attempt.nonce,
                reason="stuck",
                simulated_ok=False,
                simulation_error_type=type(exc).__name__,
                simulation_error=summary[:200],
                simulation_rpc_group="read",
                broadcast_group=group_name,
                broadcast_endpoints=endpoint_labels,
            )

            self._db.update_attempt_status(
                attempt.attempt_id,
                AttemptStatus.FAILED.value,
                error_code="replacement_simulation_reverted",
                error_detail=summary[:500],
            )

            ctx = RecoveryContext(
                db=self._db,
                chain_id=self._config.chain_id,
                actor=intent.job_id,
                source="replacer",
            )
            transition_intent_if_current_status(
                intent.intent_id,
                IntentStatus.BROADCASTED,
                IntentStatus.TERMINAL,
                "stale_pre_broadcast",
                ctx,
                terminal_reason=IntentTerminalReason.FAILED.value,
            )
            release_nonce_if_safe(
                signer_address,
                attempt.nonce,
                intent.intent_id,
                "stale_pre_broadcast",
                ctx,
            )

            if self._lifecycle:
                try:
                    self._lifecycle.on_failed(
                        intent,
                        attempt,
                        exc,
                        failure_type=FailureType.SIMULATION_REVERTED,
                        failure_stage=FailureStage.PRE_BROADCAST,
                        cleanup_trigger=False,
                    )
                except Exception:
                    # RECOVERABLE lifecycle hook failures must not block replacement.
                    log_unexpected(
                        logger,
                        "lifecycle.hook_failed",
                        hook="on_failed",
                        intent_id=str(intent.intent_id),
                        attempt_id=str(attempt.attempt_id),
                        tx_hash=attempt.tx_hash,
                        job_id=intent.job_id,
                        chain_id=intent.chain_id,
                    )

            return ReplacementResult(success=False, error="simulation_reverted")
        except SimulationNetworkError as exc:
            error_str = str(exc)
            logger.error(
                "replacement.simulation_failed",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                tx_hash=attempt.tx_hash,
                nonce=attempt.nonce,
                error_type=type(exc).__name__,
                error=error_str[:200],
                broadcast_group=group_name,
                broadcast_endpoints=endpoint_labels,
                simulation_rpc_group="read",
            )
            logger.info(
                "replacement.attempt_decision",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                nonce=attempt.nonce,
                reason="stuck",
                simulated_ok=False,
                simulation_error_type=type(exc).__name__,
                simulation_error=error_str[:200],
                simulation_rpc_group="read",
                broadcast_group=group_name,
                broadcast_endpoints=endpoint_labels,
            )
            return ReplacementResult(success=False, error="simulation_network_error")

        try:
            # Sign transaction
            signed_tx = self._keystore.sign_transaction(
                tx_dict,
                signer_address,
            )
        except Exception as e:
            # RECOVERABLE replacement signing failures return a failed result.
            log_unexpected(
                logger,
                "replacement.sign_failed",
                intent_id=str(intent.intent_id),
                error=str(e)[:200],
            )
            return ReplacementResult(success=False, error=f"Sign failed: {e}")

        # Create new attempt record
        new_attempt_id = uuid4()
        new_attempt = self._db.create_attempt(
            attempt_id=new_attempt_id,
            intent_id=intent.intent_id,
            nonce=attempt.nonce,  # Same nonce
            gas_params_json=new_gas_params.to_json(),
            status=AttemptStatus.PENDING_SEND.value,
            replaces_attempt_id=attempt.attempt_id,
            broadcast_group=group_name,
            actor=intent.job_id,
            reason="replacement_attempt",
            source="replacer",
        )

        try:
            # Broadcast replacement
            from brawny._rpc.broadcast import broadcast_transaction

            tx_hash, endpoint_url = broadcast_transaction(
                raw_tx=signed_tx.raw_transaction,
                endpoints=endpoints,
                group_name=group_name,
                config=self._config,
                job_id=intent.job_id,
                deadline=deadline,
            )

            # Update new attempt with tx_hash
            current_block = self._rpc.get_block_number(deadline=deadline)
            self._db.update_attempt_status(
                new_attempt_id,
                AttemptStatus.BROADCAST.value,
                tx_hash=tx_hash,
                broadcast_block=current_block,
                endpoint_url=endpoint_url,
            )

            # Mark old attempt as replaced
            self._db.update_attempt_status(
                attempt.attempt_id,
                AttemptStatus.REPLACED.value,
            )

            logger.info(
                LogEvents.TX_REPLACED,
                intent_id=str(intent.intent_id),
                old_attempt_id=str(attempt.attempt_id),
                new_attempt_id=str(new_attempt_id),
                old_tx_hash=attempt.tx_hash,
                new_tx_hash=tx_hash,
                nonce=attempt.nonce,
                old_max_fee=attempt.gas_params.max_fee_per_gas,
                new_max_fee=new_gas_params.max_fee_per_gas,
            )
            metrics = get_metrics()
            metrics.counter(TX_REPLACED).inc(
                chain_id=intent.chain_id,
                job_id=intent.job_id,
            )

            # Refresh attempt from DB
            new_attempt = self._db.get_attempt(new_attempt_id)
            if self._lifecycle and new_attempt is not None:
                try:
                    self._lifecycle.on_replaced(intent, new_attempt)
                except Exception:
                    # RECOVERABLE lifecycle hook failures must not block replacement.
                    log_unexpected(
                        logger,
                        "lifecycle.hook_failed",
                        hook="on_replaced",
                        intent_id=str(intent.intent_id),
                        attempt_id=str(new_attempt.attempt_id),
                        old_attempt_id=str(attempt.attempt_id),
                        old_tx_hash=attempt.tx_hash,
                        new_tx_hash=new_attempt.tx_hash,
                        job_id=intent.job_id,
                        chain_id=intent.chain_id,
                    )

            return ReplacementResult(
                success=True,
                new_attempt=new_attempt,
                new_tx_hash=tx_hash,
            )

        except Exception as e:
            error_str = str(e)

            # Check for specific errors
            if "replacement transaction underpriced" in error_str.lower():
                # RECOVERABLE underpriced replacements should retry with higher fees.
                log_unexpected(
                    logger,
                    "replacement.underpriced",
                    intent_id=str(intent.intent_id),
                    error=error_str[:200],
                )
                # Mark as failed, will retry with higher fees
                self._db.update_attempt_status(
                    new_attempt_id,
                    AttemptStatus.FAILED.value,
                    error_code="replacement_underpriced",
                    error_detail=error_str[:500],
                )
                return ReplacementResult(
                    success=False,
                    error="replacement_underpriced",
                )

            # RECOVERABLE replacement broadcast failures are reported and retried later.
            log_unexpected(
                logger,
                "replacement.broadcast_failed",
                intent_id=str(intent.intent_id),
                error=error_str[:200],
            )

            self._db.update_attempt_status(
                new_attempt_id,
                AttemptStatus.FAILED.value,
                error_code="broadcast_failed",
                error_detail=error_str[:500],
            )

            return ReplacementResult(success=False, error=error_str[:200])

    def abandon_intent(self, intent: TxIntent, attempt: TxAttempt, reason: str) -> None:
        """Abandon an intent after max replacement attempts.

        Args:
            intent: Transaction intent
            attempt: Last attempt
            reason: Reason for abandonment
        """
        ctx = RecoveryContext(
            db=self._db,
            chain_id=self._config.chain_id,
            actor=intent.job_id,
            source="replacer",
        )

        transition_intent_if_current_status(
            intent.intent_id,
            IntentStatus.BROADCASTED,
            IntentStatus.TERMINAL,
            "max_replacements_exceeded",
            ctx,
            terminal_reason=IntentTerminalReason.ABANDONED.value,
        )

        signer_address = Web3.to_checksum_address(intent.signer_address)
        release_nonce_if_safe(
            signer_address,
            attempt.nonce,
            intent.intent_id,
            "max_replacements_exceeded",
            ctx,
        )

        if self._lifecycle:
            try:
                self._lifecycle.on_failed(
                    intent,
                    attempt,
                    RuntimeError(reason),
                )
            except Exception:
                # RECOVERABLE lifecycle hook failures must not block replacement.
                log_unexpected(
                    logger,
                    "lifecycle.hook_failed",
                    hook="on_failed",
                    intent_id=str(intent.intent_id),
                    attempt_id=str(attempt.attempt_id),
                    tx_hash=attempt.tx_hash,
                    job_id=intent.job_id,
                    chain_id=intent.chain_id,
                )

        logger.warning(
            LogEvents.TX_ABANDONED,
            intent_id=str(intent.intent_id),
            attempt_id=str(attempt.attempt_id),
            nonce=attempt.nonce,
            reason=reason,
        )

    def process_stuck_transactions(self) -> dict[str, int]:
        """Process all stuck transactions and attempt replacement.

        Single pass through broadcasted intents, checking for stuck transactions
        and attempting replacement where appropriate.

        Returns:
            Dict with counts of actions taken
        """
        results = {
            "checked": 0,
            "replaced": 0,
            "abandoned": 0,
            "paused": 0,
            "errors": 0,
        }

        if self._controls and self._controls.is_active("pause_replacements"):
            logger.warning("replacement.paused_globally")
            return results

        # Get broadcasted intents
        broadcasted_intents = self._db.get_intents_by_status(
            IntentStatus.BROADCASTED.value,
            chain_id=self._config.chain_id,
        )

        deadline = Deadline.from_seconds(REPLACER_TICK_TIMEOUT_SECONDS)

        for intent in broadcasted_intents:
            if deadline.expired():
                logger.warning(
                    "replacement.tick_timeout",
                    pending_remaining=len(broadcasted_intents),
                )
                break
            signer_state = self._db.get_signer_state(
                self._config.chain_id,
                intent.signer_address,
            )
            if signer_state and signer_state.replacements_paused:
                continue
            attempt = self._db.get_latest_attempt_for_intent(intent.intent_id)
            if not attempt or not attempt.tx_hash:
                continue

            results["checked"] += 1

            try:
                if self.should_replace(intent, attempt, deadline):
                    # Check if we've exceeded max replacements
                    replacement_count = self.get_replacement_count(intent.intent_id)
                    if replacement_count >= self._config.max_replacement_attempts:
                        self._db.set_replacements_paused(
                            self._config.chain_id,
                            intent.signer_address,
                            True,
                            reason="replacement_budget_exceeded",
                            source="replacer",
                        )
                        logger.warning(
                            "replacement.paused_signer",
                            intent_id=str(intent.intent_id),
                            signer=intent.signer_address,
                            count=replacement_count,
                        )
                        results["paused"] += 1
                        continue

                    # Attempt replacement
                    result = self.replace_transaction(intent, attempt, deadline)
                    if result.success:
                        results["replaced"] += 1
                    else:
                        results["errors"] += 1

            except Exception as e:
                # RECOVERABLE replacement processing failures are isolated per intent.
                log_unexpected(
                    logger,
                    "replacement.process_failed",
                    intent_id=str(intent.intent_id),
                    error=str(e)[:200],
                )
                results["errors"] += 1

        if results["replaced"] > 0 or results["abandoned"] > 0:
            logger.info(
                "replacement.batch_complete",
                **results,
            )

        return results
