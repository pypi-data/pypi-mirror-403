"""Transaction confirmation monitoring.

Implements the confirmation monitoring loop from SPEC 9.3:
- Poll for transaction receipt
- Verify receipt is on canonical chain
- Count confirmations
- Detect dropped/stuck transactions
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from web3 import Web3

from brawny.logging import LogEvents, get_logger, log_unexpected
from brawny.metrics import (
    TX_CONFIRMED,
    TX_FAILED,
    TX_CONFIRMATION_SECONDS,
    LAST_TX_CONFIRMED_TIMESTAMP,
    LAST_INTENT_COMPLETED_TIMESTAMP,
    get_metrics,
)
from brawny.model.enums import AttemptStatus, IntentStatus, IntentTerminalReason, NonceStatus
from brawny.model.errors import DatabaseError, FailureType, FailureStage, InvariantViolation
from brawny._rpc.errors import RPCError
from brawny.timeout import Deadline
from brawny.tx.intent import transition_intent

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny.lifecycle import LifecycleDispatcher
    from brawny.model.types import TxAttempt, TxIntent
    from brawny._rpc.clients import ReadClient
    from brawny.tx.nonce import NonceManager

logger = get_logger(__name__)

MONITOR_TICK_TIMEOUT_SECONDS = 10.0


class ConfirmationResult(str, Enum):
    """Result of confirmation monitoring."""

    CONFIRMED = "confirmed"
    REVERTED = "reverted"
    DROPPED = "dropped"
    STUCK = "stuck"
    PENDING = "pending"


@dataclass
class ConfirmationStatus:
    """Status returned from confirmation check."""

    result: ConfirmationResult
    confirmations: int = 0
    block_number: int | None = None
    block_hash: str | None = None
    gas_used: int | None = None
    receipt: dict[str, Any] | None = None


class TxMonitor:
    """Monitor transactions for confirmation.

    Implements SPEC 9.3 confirmation monitoring with:
    - Receipt polling with configurable interval
    - Canonical chain verification
    - Confirmation counting
    - Dropped/stuck transaction detection
    """

    def __init__(
        self,
        db: Database,
        rpc: ReadClient,
        nonce_manager: NonceManager,
        config: Config,
        lifecycle: "LifecycleDispatcher | None" = None,
    ) -> None:
        """Initialize transaction monitor.

        Args:
            db: Database connection
            rpc: RPC manager for chain queries
            nonce_manager: Nonce manager for releasing reservations
            config: Application configuration
        """
        self._db = db
        self._rpc = rpc
        self._nonce_manager = nonce_manager
        self._config = config
        self._lifecycle = lifecycle

    def check_confirmation(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        deadline: Deadline | None = None,
    ) -> ConfirmationStatus:
        """Check confirmation status for a transaction attempt.

        This is a non-blocking check that returns the current status.
        For continuous monitoring, call this repeatedly.

        Args:
            intent: Transaction intent
            attempt: Transaction attempt with tx_hash

        Returns:
            Current confirmation status
        """
        if deadline is not None and deadline.expired():
            return ConfirmationStatus(result=ConfirmationResult.PENDING)
        if not attempt.tx_hash:
            logger.warning(
                "monitor.no_tx_hash",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
            )
            return ConfirmationStatus(result=ConfirmationResult.PENDING)

        # Get receipt
        receipt = self._rpc.get_transaction_receipt(attempt.tx_hash, deadline=deadline)

        if receipt is None:
            # No receipt yet - check if nonce has been consumed by another tx
            if self._is_nonce_consumed(intent, attempt, deadline):
                metrics = get_metrics()
                metrics.counter(TX_FAILED).inc(
                    chain_id=intent.chain_id,
                    job_id=intent.job_id,
                    reason="dropped",
                )
                return ConfirmationStatus(result=ConfirmationResult.DROPPED)

            # Check if stuck
            if self._is_stuck(attempt, deadline):
                metrics = get_metrics()
                metrics.counter(TX_FAILED).inc(
                    chain_id=intent.chain_id,
                    job_id=intent.job_id,
                    reason="stuck",
                )
                return ConfirmationStatus(result=ConfirmationResult.STUCK)

            return ConfirmationStatus(result=ConfirmationResult.PENDING)

        # Have receipt - verify it's on canonical chain
        receipt_block_number = receipt.get("blockNumber")
        receipt_block_hash = receipt.get("blockHash")

        if receipt_block_hash:
            # Convert HexBytes to str if needed
            if hasattr(receipt_block_hash, "hex"):
                receipt_block_hash = receipt_block_hash.hex()
            if not receipt_block_hash.startswith("0x"):
                receipt_block_hash = f"0x{receipt_block_hash}"

        # Verify block hash matches current chain
        try:
            current_block = self._rpc.get_block(receipt_block_number, deadline=deadline)
            current_hash = current_block.get("hash")
            if hasattr(current_hash, "hex"):
                current_hash = current_hash.hex()
            if current_hash and not current_hash.startswith("0x"):
                current_hash = f"0x{current_hash}"

            if current_hash != receipt_block_hash:
                # Receipt is from reorged block
                logger.info(
                    "tx.reorg_pending",
                    tx_hash=attempt.tx_hash,
                    receipt_block=receipt_block_number,
                    receipt_hash=receipt_block_hash[:18] if receipt_block_hash else None,
                    current_hash=current_hash[:18] if current_hash else None,
                )
                return ConfirmationStatus(result=ConfirmationResult.PENDING)
        except Exception as e:
            # RECOVERABLE treat block check failures as pending.
            log_unexpected(
                logger,
                "monitor.block_check_failed",
                block_number=receipt_block_number,
                error=str(e)[:200],
            )
            # On error, treat as pending and retry
            return ConfirmationStatus(result=ConfirmationResult.PENDING)

        # Count confirmations
        current_block_number = self._rpc.get_block_number(deadline=deadline)
        confirmations = current_block_number - receipt_block_number + 1

        # Check if confirmed with enough confirmations
        if confirmations >= intent.min_confirmations:
            status = receipt.get("status", 1)
            if status == 1:
                metrics = get_metrics()
                metrics.counter(TX_CONFIRMED).inc(
                    chain_id=intent.chain_id,
                    job_id=intent.job_id,
                )
                # Only emit confirmation latency metric if we have actual broadcast time
                # Using updated_at as fallback would give meaningless/negative values
                if attempt.broadcast_at:
                    elapsed = time.time() - attempt.broadcast_at.timestamp()
                    if elapsed >= 0:
                        metrics.histogram(TX_CONFIRMATION_SECONDS).observe(
                            elapsed,
                            chain_id=intent.chain_id,
                        )
                return ConfirmationStatus(
                    result=ConfirmationResult.CONFIRMED,
                    confirmations=confirmations,
                    block_number=receipt_block_number,
                    block_hash=receipt_block_hash,
                    gas_used=receipt.get("gasUsed"),
                    receipt=dict(receipt),
                )
            else:
                metrics = get_metrics()
                metrics.counter(TX_FAILED).inc(
                    chain_id=intent.chain_id,
                    job_id=intent.job_id,
                    reason="reverted",
                )
                return ConfirmationStatus(
                    result=ConfirmationResult.REVERTED,
                    confirmations=confirmations,
                    block_number=receipt_block_number,
                    block_hash=receipt_block_hash,
                    gas_used=receipt.get("gasUsed"),
                    receipt=dict(receipt),
                )

        # Not enough confirmations yet
        return ConfirmationStatus(
            result=ConfirmationResult.PENDING,
            confirmations=confirmations,
            block_number=receipt_block_number,
            block_hash=receipt_block_hash,
        )

    def _is_nonce_consumed(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        deadline: Deadline | None,
    ) -> bool:
        """Check if the nonce has been consumed by another transaction.

        Args:
            intent: Transaction intent
            attempt: Transaction attempt

        Returns:
            True if nonce was consumed by another tx
        """
        try:
            # Get confirmed nonce from chain (checksum address for RPC)
            signer_address = Web3.to_checksum_address(intent.signer_address)
            chain_nonce = self._rpc.get_transaction_count(
                signer_address,
                "latest",  # Use "latest" not "pending" to check confirmed
                deadline=deadline,
            )

            # If chain nonce is greater than our nonce, it was consumed
            if chain_nonce > attempt.nonce:
                # Verify our tx isn't the one that consumed it
                receipt = self._rpc.get_transaction_receipt(attempt.tx_hash, deadline=deadline)
                if receipt is None:
                    # Nonce consumed but not by our tx
                    logger.warning(
                        "tx.nonce_consumed_externally",
                        tx_hash=attempt.tx_hash,
                        nonce=attempt.nonce,
                        chain_nonce=chain_nonce,
                    )
                    return True

            return False
        except Exception as e:
            # RECOVERABLE nonce consumption checks are best-effort.
            log_unexpected(
                logger,
                "monitor.nonce_check_failed",
                error=str(e)[:200],
            )
            return False

    def _is_stuck(self, attempt: TxAttempt, deadline: Deadline | None) -> bool:
        """Check if transaction is stuck.

        Stuck is defined as:
        - elapsed_time > stuck_tx_seconds OR
        - blocks_since_broadcast > stuck_tx_blocks

        Args:
            attempt: Transaction attempt

        Returns:
            True if transaction is considered stuck
        """
        if not attempt.broadcast_block or not attempt.broadcast_at:
            return False

        # Check time elapsed using broadcast time (when tx was actually sent)
        elapsed_seconds = time.time() - attempt.broadcast_at.timestamp()
        if elapsed_seconds > self._config.stuck_tx_seconds:
            return True

        # Check blocks elapsed
        try:
            current_block = self._rpc.get_block_number(deadline=deadline)
            blocks_since = current_block - attempt.broadcast_block
            if blocks_since > self._config.stuck_tx_blocks:
                return True
        except Exception as e:
            # RECOVERABLE stuck check failure defers to time-based heuristic.
            log_unexpected(
                logger,
                "tx.stuck_check_error",
                tx_hash=attempt.tx_hash,
                intent_id=str(attempt.intent_id),
                attempt_id=str(attempt.attempt_id),
                error=str(e)[:200],
            )

        return False

    def monitor_until_confirmed(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        poll_interval: float | None = None,
        timeout: float | None = None,
    ) -> ConfirmationStatus:
        """Monitor transaction until confirmed, reverted, dropped, or stuck.

        This is a blocking call that polls until a terminal state is reached.

        Args:
            intent: Transaction intent
            attempt: Transaction attempt
            poll_interval: Polling interval in seconds (default: config.poll_interval_seconds)
            timeout: Maximum time to wait in seconds (default: config.default_deadline_seconds)

        Returns:
            Final confirmation status
        """
        poll_interval = poll_interval or self._config.poll_interval_seconds
        timeout = timeout or self._config.default_deadline_seconds

        start_time = time.time()

        while True:
            status = self.check_confirmation(intent, attempt)

            # Return on terminal states
            if status.result in (
                ConfirmationResult.CONFIRMED,
                ConfirmationResult.REVERTED,
                ConfirmationResult.DROPPED,
                ConfirmationResult.STUCK,
            ):
                return status

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(
                    "monitor.timeout",
                    tx_hash=attempt.tx_hash,
                    elapsed=elapsed,
                    timeout=timeout,
                )
                return ConfirmationStatus(result=ConfirmationResult.STUCK)

            # Wait before next poll
            time.sleep(poll_interval)

    def handle_confirmed(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        status: ConfirmationStatus,
    ) -> None:
        """Handle a confirmed transaction.

        Updates database state for confirmed transaction:
        - Mark attempt as confirmed
        - Mark intent as confirmed
        - Release nonce reservation

        Args:
            intent: Transaction intent
            attempt: Transaction attempt
            status: Confirmation status with receipt
        """
        if status.receipt is None or status.block_number is None:
            raise ValueError("confirmed status missing receipt or block number")
        receipt_tx_hash = status.receipt.get("transactionHash")
        if receipt_tx_hash is None:
            raise ValueError("confirmed receipt missing transaction hash")
        if hasattr(receipt_tx_hash, "hex"):
            receipt_tx_hash = receipt_tx_hash.hex()
        if not str(receipt_tx_hash).startswith("0x"):
            receipt_tx_hash = f"0x{receipt_tx_hash}"
        if attempt.tx_hash is None or str(receipt_tx_hash).lower() != str(attempt.tx_hash).lower():
            raise InvariantViolation("receipt tx_hash does not match attempt")

        # Update attempt status
        try:
            self._db.update_attempt_status(
                attempt.attempt_id,
                AttemptStatus.CONFIRMED.value,
                tx_hash=attempt.tx_hash,
                included_block=status.block_number,
                reason="confirm_receipt",
            )
        except InvariantViolation:
            self._db.update_attempt_status(
                attempt.attempt_id,
                AttemptStatus.CONFIRMED.value,
                tx_hash=receipt_tx_hash,
                included_block=status.block_number,
                reason="receipt_override_local_state",
            )
            logger.warning(
                "monitor.receipt_override",
                intent_id=str(intent.intent_id),
                attempt_id=str(attempt.attempt_id),
                tx_hash=attempt.tx_hash,
                prior_status=attempt.status.value,
            )

        # Update intent status
        transition_intent(
            self._db,
            intent.intent_id,
            IntentStatus.TERMINAL,
            "confirm_receipt",
            chain_id=self._config.chain_id,
            terminal_reason=IntentTerminalReason.CONFIRMED.value,
        )

        # Emit stuckness timestamps after DB transition succeeds (emit-once semantics)
        now = time.time()
        metrics = get_metrics()
        metrics.gauge(LAST_TX_CONFIRMED_TIMESTAMP).set(now, chain_id=intent.chain_id)
        metrics.gauge(LAST_INTENT_COMPLETED_TIMESTAMP).set(now, chain_id=intent.chain_id)

        # Release nonce reservation (checksum address for nonce manager)
        signer_address = Web3.to_checksum_address(intent.signer_address)
        self._nonce_manager.release(signer_address, attempt.nonce)

        if self._lifecycle and status.receipt:
            try:
                self._lifecycle.on_confirmed(intent, attempt, status.receipt)
            except Exception:
                # RECOVERABLE lifecycle hook failures must not block state updates.
                log_unexpected(
                    logger,
                    "lifecycle.hook_failed",
                    hook="on_confirmed",
                    intent_id=str(intent.intent_id),
                    attempt_id=str(attempt.attempt_id),
                    tx_hash=attempt.tx_hash,
                    job_id=intent.job_id,
                    chain_id=intent.chain_id,
                )

        logger.info(
            LogEvents.TX_CONFIRMED,
            intent_id=str(intent.intent_id),
            attempt_id=str(attempt.attempt_id),
            tx_hash=attempt.tx_hash,
            block_number=status.block_number,
            confirmations=status.confirmations,
            gas_used=status.gas_used,
        )

    def handle_reverted(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
        status: ConfirmationStatus,
    ) -> None:
        """Handle a reverted transaction.

        Updates database state for reverted transaction:
        - Mark attempt as failed
        - Mark intent as failed
        - Release nonce reservation

        Args:
            intent: Transaction intent
            attempt: Transaction attempt
            status: Confirmation status with receipt
        """
        # Update attempt status
        self._db.update_attempt_status(
            attempt.attempt_id,
            AttemptStatus.FAILED.value,
            included_block=status.block_number,
            error_code="execution_reverted",
            error_detail="Transaction reverted on-chain",
        )

        # Update intent status
        transition_intent(
            self._db,
            intent.intent_id,
            IntentStatus.TERMINAL,
            "execution_reverted",
            chain_id=self._config.chain_id,
            terminal_reason=IntentTerminalReason.FAILED.value,
        )

        # Release nonce reservation (checksum address for nonce manager)
        signer_address = Web3.to_checksum_address(intent.signer_address)
        self._nonce_manager.release(signer_address, attempt.nonce)

        if self._lifecycle:
            try:
                self._lifecycle.on_failed(
                    intent,
                    attempt,
                    RuntimeError("Transaction reverted on-chain"),
                    failure_type=FailureType.TX_REVERTED,
                    failure_stage=FailureStage.POST_BROADCAST,
                )
            except Exception:
                # RECOVERABLE lifecycle hook failures must not block state updates.
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

        logger.error(
            LogEvents.TX_FAILED,
            intent_id=str(intent.intent_id),
            attempt_id=str(attempt.attempt_id),
            tx_hash=attempt.tx_hash,
            block_number=status.block_number,
            error="execution_reverted",
        )

    def handle_dropped(
        self,
        intent: TxIntent,
        attempt: TxAttempt,
    ) -> None:
        """Handle a dropped transaction (nonce consumed externally).

        The nonce was used by another transaction, so this attempt is dead.
        The intent should be marked as failed.

        Args:
            intent: Transaction intent
            attempt: Transaction attempt
        """
        # Update attempt status
        self._db.update_attempt_status(
            attempt.attempt_id,
            AttemptStatus.FAILED.value,
            error_code="nonce_consumed",
            error_detail="Nonce was consumed by another transaction",
        )

        # Update intent status
        transition_intent(
            self._db,
            intent.intent_id,
            IntentStatus.TERMINAL,
            "nonce_consumed",
            chain_id=self._config.chain_id,
            terminal_reason=IntentTerminalReason.FAILED.value,
        )

        # Mark nonce as orphaned (it was used elsewhere) - checksum address
        signer_address = Web3.to_checksum_address(intent.signer_address)
        self._db.update_nonce_reservation_status(
            self._config.chain_id,
            signer_address,
            attempt.nonce,
            NonceStatus.ORPHANED.value,
        )

        if self._lifecycle:
            try:
                self._lifecycle.on_failed(
                    intent,
                    attempt,
                    RuntimeError("Nonce was consumed by another transaction"),
                    failure_type=FailureType.NONCE_CONSUMED,
                    failure_stage=FailureStage.POST_BROADCAST,
                )
            except Exception:
                # RECOVERABLE lifecycle hook failures must not block state updates.
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
            LogEvents.TX_FAILED,
            intent_id=str(intent.intent_id),
            attempt_id=str(attempt.attempt_id),
            tx_hash=attempt.tx_hash,
            error="nonce_consumed",
        )

    def get_broadcasted_attempts(self) -> list[tuple[TxIntent, TxAttempt]]:
        """Get all broadcasted intents with their latest attempts."""
        broadcasted: list[tuple[TxIntent, TxAttempt]] = []

        intents = self._db.get_intents_by_status(
            IntentStatus.BROADCASTED.value,
            chain_id=self._config.chain_id,
        )

        for intent in intents:
            attempt = self._db.get_latest_attempt_for_intent(intent.intent_id)
            if attempt and attempt.tx_hash:
                broadcasted.append((intent, attempt))

        return broadcasted

    def monitor_all_broadcasted(self) -> dict[str, int]:
        """Monitor all broadcasted transactions and update their status."""
        results = {
            "confirmed": 0,
            "reverted": 0,
            "dropped": 0,
            "stuck": 0,
            "pending": 0,
        }

        pending = self.get_broadcasted_attempts()
        deadline = Deadline.from_seconds(MONITOR_TICK_TIMEOUT_SECONDS)

        for intent, attempt in pending:
            if deadline.expired():
                logger.warning(
                    "monitor.tick_timeout",
                    pending_remaining=len(pending),
                )
                break
            try:
                if (
                    attempt.error_code
                    and attempt.status in (AttemptStatus.FAILED, AttemptStatus.REPLACED)
                ):
                    transitioned = transition_intent(
                        self._db,
                        intent.intent_id,
                        IntentStatus.TERMINAL,
                        "stale_broadcast_attempt",
                        chain_id=self._config.chain_id,
                        terminal_reason=IntentTerminalReason.FAILED.value,
                    )
                    if transitioned:
                        logger.warning(
                            "monitor.stale_broadcast_attempt",
                            intent_id=str(intent.intent_id),
                            attempt_id=str(attempt.attempt_id),
                            attempt_status=attempt.status.value,
                            error_code=attempt.error_code,
                            chain_id=self._config.chain_id,
                        )
                    continue

                status = self.check_confirmation(intent, attempt, deadline=deadline)

                if status.result == ConfirmationResult.CONFIRMED:
                    self.handle_confirmed(intent, attempt, status)
                    results["confirmed"] += 1

                elif status.result == ConfirmationResult.REVERTED:
                    self.handle_reverted(intent, attempt, status)
                    results["reverted"] += 1

                elif status.result == ConfirmationResult.DROPPED:
                    self.handle_dropped(intent, attempt)
                    results["dropped"] += 1

                elif status.result == ConfirmationResult.STUCK:
                    # Don't handle stuck here - let replacement logic handle it
                    results["stuck"] += 1

                else:
                    results["pending"] += 1

            except (RPCError, DatabaseError, OSError, ValueError) as e:
                # Expected monitoring errors - log and retry next cycle
                logger.error(
                    "monitor.check_failed",
                    intent_id=str(intent.intent_id),
                    attempt_id=str(attempt.attempt_id),
                    error=str(e)[:200],
                    error_type=type(e).__name__,
                )
                results["pending"] += 1

        if any(v > 0 for k, v in results.items() if k != "pending"):
            logger.info(
                "monitor.batch_complete",
                **results,
            )

        return results
