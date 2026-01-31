"""Centralized nonce manager for transaction execution.

Implements the nonce management strategy from SPEC 8:
- Reserve nonce with SQLite BEGIN EXCLUSIVE locking
- Nonce status transitions (reserved → in_flight → released/orphaned)
- Reconciliation loop for startup and periodic sync
- SQLite-specific locking for development

Jobs NEVER allocate or set nonces - the nonce manager owns all nonce operations.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator
from uuid import UUID

from cachetools import TTLCache
from web3 import Web3

from brawny.logging import LogEvents, get_logger
from brawny.model.enums import IntentStatus, NonceStatus
from brawny.model.errors import NonceUnavailable
from brawny._rpc.errors import RPCError
from brawny.timeout import Deadline

# Rate limit gap detection logs to once per 60 seconds per signer
GAP_LOG_RATE_LIMIT_SECONDS = 60

if TYPE_CHECKING:
    from brawny.db.base import Database
    from brawny.model.types import NonceReservation
    from brawny._rpc.clients import ReadClient

logger = get_logger(__name__)


class NonceManager:
    """Centralized nonce manager for transaction execution.

    Provides atomic nonce reservation with database-backed persistence.
    Handles multiple in-flight nonces per signer to prevent global blocking.

    Thread-safe: Uses database transactions for concurrency control.
    """

    def __init__(
        self,
        db: Database,
        rpc: ReadClient,
        chain_id: int,
    ) -> None:
        """Initialize nonce manager.

        Args:
            db: Database connection
            rpc: RPC manager for chain state queries
            chain_id: Chain ID for nonce tracking
        """
        self._db = db
        self._rpc = rpc
        self._chain_id = chain_id
        # Rate limiting for gap detection logs: signer_address -> last_log_time
        # Single-threaded access (from executor) - no lock needed
        # Low cardinality keys (signer addresses): maxsize=1000, ttl=1h
        self._gap_log_times: TTLCache[str, float] = TTLCache(maxsize=1000, ttl=3600)

    def reserve_nonce(
        self,
        signer_address: str,
        intent_id: UUID | None = None,
        deadline: Deadline | None = None,
    ) -> int:
        """Reserve the next available nonce for a signer.

        Algorithm:
        1. Lock signer row (or create if not exists)
        2. Fetch chain pending nonce
        3. Calculate base nonce as max(chain_nonce, db_next_nonce)
        4. Find next available nonce (skip existing reservations)
        5. Create reservation and update signer's next_nonce

        Args:
            signer_address: Ethereum address of the signer
            intent_id: Optional intent ID to associate with reservation

        Returns:
            The reserved nonce value

        Raises:
            Exception: If reservation fails
        """
        signer_address = signer_address.lower()

        try:
            chain_nonce = self._rpc.get_transaction_count(
                Web3.to_checksum_address(signer_address),
                block_identifier="pending",
                deadline=deadline,
            )
        except (RPCError, OSError, TimeoutError, ValueError, RuntimeError) as exc:
            endpoint = getattr(exc, "endpoint", None)
            raise NonceUnavailable("Chain nonce unavailable", endpoint=endpoint) from exc

        signer_state = self._db.get_signer_state(self._chain_id, signer_address)
        if (
            signer_state
            and chain_nonce is not None
            and signer_state.last_synced_chain_nonce is not None
            and chain_nonce < signer_state.last_synced_chain_nonce
        ):
            self._db.set_signer_quarantined(
                self._chain_id,
                signer_address,
                reason="stale_chain_nonce",
                source="nonce_reserve",
            )
            logger.warning(
                "nonce.stale_chain_nonce",
                signer=signer_address,
                chain_nonce=chain_nonce,
                last_synced_chain_nonce=signer_state.last_synced_chain_nonce,
            )
            raise RuntimeError("Stale chain nonce detected; signer quarantined")
        if signer_state and signer_state.quarantined_at:
            logger.warning(
                "nonce.signer_quarantined",
                signer=signer_address,
                reason=signer_state.quarantine_reason,
            )
            raise RuntimeError("Signer is quarantined; nonce reservation blocked")

        nonce = self._db.reserve_nonce_atomic(
            chain_id=self._chain_id,
            address=signer_address,
            chain_nonce=chain_nonce,
            intent_id=intent_id,
        )

        logger.debug(
            LogEvents.NONCE_RESERVE,
            signer=signer_address,
            nonce=nonce,
            chain_nonce=chain_nonce,
            intent_id=str(intent_id) if intent_id else None,
        )

        return nonce

    def mark_in_flight(
        self,
        signer_address: str,
        nonce: int,
        intent_id: UUID,
    ) -> bool:
        """Mark a nonce reservation as in-flight (after broadcast).

        Args:
            signer_address: Ethereum address of the signer
            nonce: The nonce value
            intent_id: Intent ID to associate

        Returns:
            True if updated successfully
        """
        signer_address = signer_address.lower()
        return self._db.update_nonce_reservation_status(
            chain_id=self._chain_id,
            address=signer_address,
            nonce=nonce,
            status=NonceStatus.IN_FLIGHT.value,
            intent_id=intent_id,
        )

    def release(
        self,
        signer_address: str,
        nonce: int,
        reason: str | None = None,
        source: str | None = None,
    ) -> bool:
        """Release a nonce reservation (after confirm/fail/abandon).

        Args:
            signer_address: Ethereum address of the signer
            nonce: The nonce value

        Returns:
            True if released successfully
        """
        signer_address = signer_address.lower()
        return self._db.release_nonce_reservation(
            self._chain_id,
            signer_address,
            nonce,
            reason=reason,
            source=source,
        )

    @contextmanager
    def reserved(
        self,
        signer_address: str,
        intent_id: UUID | None = None,
    ) -> Generator[int, None, None]:
        """Context manager for nonce reservation with automatic release on failure.

        Automatically releases the nonce if an exception occurs within the context.
        On success path, caller is responsible for calling mark_in_flight() to
        transition the nonce to in-flight status.

        Usage:
            with nonce_manager.reserved(signer) as nonce:
                # Build and sign transaction with nonce
                # If exception raised, nonce is automatically released

            # After context, caller should call mark_in_flight() on success

        Args:
            signer_address: Ethereum address of the signer
            intent_id: Optional intent ID to associate with reservation

        Yields:
            Reserved nonce value

        Raises:
            Exception: Re-raises any exception after releasing the nonce
        """
        signer_address = signer_address.lower()
        nonce = self.reserve_nonce(signer_address, intent_id)

        try:
            yield nonce
        except BaseException:
            # Release nonce on any exception
            self.release(signer_address, nonce)
            logger.debug(
                "nonce.released_on_error",
                signer=signer_address,
                nonce=nonce,
            )
            raise

    def mark_orphaned(
        self,
        signer_address: str,
        nonce: int,
    ) -> bool:
        """Mark a nonce as orphaned (nonce used but no tx found).

        Args:
            signer_address: Ethereum address of the signer
            nonce: The nonce value

        Returns:
            True if updated successfully
        """
        signer_address = signer_address.lower()
        updated = self._db.update_nonce_reservation_status(
            chain_id=self._chain_id,
            address=signer_address,
            nonce=nonce,
            status=NonceStatus.ORPHANED.value,
        )
        if updated:
            logger.warning(
                LogEvents.NONCE_ORPHANED,
                signer=signer_address,
                nonce=nonce,
            )
        return updated

    def get_reservation(
        self,
        signer_address: str,
        nonce: int,
    ) -> NonceReservation | None:
        """Get a specific nonce reservation.

        Args:
            signer_address: Ethereum address of the signer
            nonce: The nonce value

        Returns:
            Reservation if found, None otherwise
        """
        return self._db.get_nonce_reservation(
            self._chain_id, signer_address.lower(), nonce
        )

    def get_active_reservations(
        self,
        signer_address: str,
    ) -> list[NonceReservation]:
        """Get all active (non-released) reservations for a signer.

        Args:
            signer_address: Ethereum address of the signer

        Returns:
            List of active reservations
        """
        all_reservations = self._db.get_reservations_for_signer(
            self._chain_id, signer_address.lower()
        )
        return [
            r for r in all_reservations
            if r.status not in (NonceStatus.RELEASED,)
        ]

    def reconcile(self, signer_address: str | None = None) -> dict[str, int]:
        """Reconcile nonce reservations using SAFE operations only.

        SAFETY INVARIANTS:
        - NEVER mutates signers.next_nonce (use force_reset() for that)
        - Only releases reservations provable from DB state (confirmed intents)
        - Gap detection is observability-only (log + metric, no action)

        Run at startup and periodically to:
        - Update signer's synced chain nonce (observability)
        - Detect nonce gaps and emit alerts (no auto-reset)
        - Release reservations for DB-confirmed intents
        - Clean up old orphaned reservations (time-based)

        Args:
            signer_address: Optional specific signer to reconcile.
                           If None, reconciles all signers.

        Returns:
            Dictionary with reconciliation stats
        """
        from brawny.metrics import NONCE_GAP_DETECTED, get_metrics

        stats = {
            "signers_checked": 0,
            "nonces_released": 0,
            "orphans_cleaned": 0,
            "gaps_detected": 0,
            "orphans_marked": 0,
            "stale_released": 0,
        }

        if signer_address:
            signers = [self._db.get_signer_state(self._chain_id, signer_address.lower())]
            signers = [s for s in signers if s is not None]
        else:
            signers = self._db.get_all_signers(self._chain_id)

        metrics = get_metrics()

        for signer in signers:
            stats["signers_checked"] += 1

            try:
                # Get current chain nonce (for observability only)
                chain_nonce = self._rpc.get_transaction_count(
                    Web3.to_checksum_address(signer.signer_address), block_identifier="pending"
                )

                # Update signer's synced chain nonce (observability only)
                self._db.update_signer_chain_nonce(
                    self._chain_id, signer.signer_address, chain_nonce
                )

                # Gap detection: log + metric only, NO auto-reset
                # Reason: single-endpoint "pending nonce" is not a truth source.
                # Auto-reset based on RPC can brick the system during RPC incidents.
                # Recovery requires explicit operator action via force_reset().
                if chain_nonce < signer.next_nonce:
                    gap_size = signer.next_nonce - chain_nonce
                    stats["gaps_detected"] += 1

                    # Emit metric for alerting (always - metrics are cheap)
                    metrics.counter(NONCE_GAP_DETECTED).inc(
                        chain_id=self._chain_id,
                        signer=signer.signer_address[:10],  # Truncate for cardinality
                    )

                    # Rate-limited log warning (per signer)
                    now = time.monotonic()
                    last_log = self._gap_log_times.get(signer.signer_address, 0)
                    if now - last_log >= GAP_LOG_RATE_LIMIT_SECONDS:
                        self._gap_log_times[signer.signer_address] = now
                        logger.warning(
                            "nonce.gap_detected",
                            signer=signer.signer_address,
                            chain_id=self._chain_id,
                            db_next_nonce=signer.next_nonce,
                            chain_pending_nonce=chain_nonce,
                            gap_size=gap_size,
                            action="none",
                            recovery=f"Run 'brawny signer force-reset {signer.signer_address[:10]}...'",
                        )

                # SAFE CLEANUP: Only release reservations provable from DB state
                # We iterate all non-released reservations and check DB for confirmation
                released_count = self._release_confirmed_reservations(signer.signer_address)
                stats["nonces_released"] += released_count

                # Mark reservations below chain nonce with no intent as orphaned.
                # This handles external transactions consuming a nonce.
                orphans_marked = self._mark_orphaned_below_chain_nonce(
                    signer.signer_address, chain_nonce
                )
                stats["orphans_marked"] += orphans_marked

                stale_released = self._release_stale_below_chain_nonce(
                    signer.signer_address, chain_nonce
                )
                stats["stale_released"] += stale_released

                log_fn = logger.info
                if released_count == 0 and orphans_marked == 0 and stale_released == 0:
                    log_fn = logger.debug
                log_fn(
                    LogEvents.NONCE_RECONCILE,
                    signer=signer.signer_address,
                    chain_nonce=chain_nonce,
                    released_count=released_count,
                    orphans_marked=orphans_marked,
                    stale_released=stale_released,
                )

            except Exception as e:
                # RECOVERABLE reconcile failures are isolated per signer.
                logger.error(
                    "nonce.reconcile.error",
                    signer=signer.signer_address,
                    error=str(e),
                    exc_info=True,
                )

        # Cleanup old orphaned reservations (24+ hours old, time-based)
        stats["orphans_cleaned"] = self.cleanup_orphaned()

        return stats

    def _mark_orphaned_below_chain_nonce(self, signer_address: str, chain_nonce: int) -> int:
        """Mark reservations below chain nonce with no intent as orphaned.

        Uses chain nonce as a lower bound to prevent reusing externally consumed nonces.
        """
        signer_address = signer_address.lower()
        reservations = self._db.get_reservations_below_nonce(
            self._chain_id, signer_address, chain_nonce
        )
        marked = 0
        for reservation in reservations:
            if reservation.status in (NonceStatus.RELEASED, NonceStatus.ORPHANED):
                continue
            if reservation.intent_id is not None:
                continue
            if self.mark_orphaned(signer_address, reservation.nonce):
                marked += 1
        return marked

    def _release_confirmed_reservations(self, signer_address: str) -> int:
        """Release reservations for intents that are DB-confirmed.

        SAFE: Only uses DB state, never RPC.
        """
        signer_address = signer_address.lower()
        reservations = self._db.get_reservations_for_signer(
            self._chain_id, signer_address
        )

        released = 0
        for reservation in reservations:
            if reservation.status == NonceStatus.RELEASED:
                continue

            if not reservation.intent_id:
                # No intent attached - skip (could be pre-broadcast)
                continue

            # Check if intent is confirmed IN THE DATABASE
            attempt = self._db.get_latest_attempt_for_intent(reservation.intent_id)
            if attempt and attempt.status.value == "confirmed":
                self.release(signer_address, reservation.nonce)
                released += 1

        return released

    def _release_stale_below_chain_nonce(self, signer_address: str, chain_nonce: int) -> int:
        """Release reservations below chain nonce when intent is terminal or missing.

        SAFE: Uses DB state only. Does not mutate next_nonce.
        """
        signer_address = signer_address.lower()
        reservations = self._db.get_reservations_below_nonce(
            self._chain_id, signer_address, chain_nonce
        )

        released = 0
        for reservation in reservations:
            if reservation.status in (NonceStatus.RELEASED, NonceStatus.ORPHANED):
                continue
            if reservation.intent_id is None:
                continue
            intent = self._db.get_intent(reservation.intent_id)
            if intent is None or intent.status == IntentStatus.TERMINAL:
                if self.release(signer_address, reservation.nonce):
                    released += 1
        return released

    def cleanup_orphaned(self, older_than_hours: int = 24) -> int:
        """Delete orphaned nonce reservations older than specified hours.

        Orphaned reservations occur when a nonce was used but no transaction
        was found on-chain. These are safe to delete after some time.

        Args:
            older_than_hours: Delete orphans older than this (default: 24h)

        Returns:
            Number of deleted reservations
        """
        deleted = self._db.cleanup_orphaned_nonces(self._chain_id, older_than_hours)
        if deleted > 0:
            logger.info(
                "nonce.orphans_cleaned",
                chain_id=self._chain_id,
                deleted=deleted,
                older_than_hours=older_than_hours,
            )
        return deleted

    def sync_from_chain(self, signer_address: str) -> int:
        """Sync signer state from chain and return current pending nonce.

        Use this during startup or after external transactions.

        Args:
            signer_address: Ethereum address of the signer

        Returns:
            Current pending nonce from chain
        """
        signer_address = signer_address.lower()
        chain_nonce = self._rpc.get_transaction_count(
            Web3.to_checksum_address(signer_address), block_identifier="pending"
        )

        # Upsert signer with chain nonce
        self._db.upsert_signer(
            chain_id=self._chain_id,
            address=signer_address,
            next_nonce=chain_nonce,
            last_synced_chain_nonce=chain_nonce,
        )

        logger.info(
            "nonce.synced_from_chain",
            signer=signer_address,
            chain_nonce=chain_nonce,
        )

        return chain_nonce

    def force_reset(
        self,
        signer_address: str,
        source: str = "unknown",
        reason: str | None = None,
        target_nonce: int | None = None,
    ) -> int:
        """Force reset nonce state. Returns new next_nonce.

        USE WITH CAUTION: Destructive operation that may cause issues if
        dropped txs later mine. This requires explicit operator action.

        This will:
        - Query current chain pending nonce (or use target_nonce if provided)
        - Reset local next_nonce to match
        - Release all reservations with nonce >= target
        - Clear gap tracking
        - Emit audit log and metric

        Args:
            signer_address: Ethereum address of the signer
            source: Where this reset originated ("cli", "executor", "api")
            reason: Human-readable reason for the reset
            target_nonce: Optional explicit target. If None, uses chain pending nonce.

        Returns:
            The new next_nonce
        """
        from brawny.metrics import NONCE_FORCE_RESET, get_metrics

        signer_address = signer_address.lower()

        # Get target nonce
        if target_nonce is None:
            target_nonce = self._rpc.get_transaction_count(
                Web3.to_checksum_address(signer_address), block_identifier="pending"
            )

        # Get current state for audit logging
        current_state = self._db.get_signer_state(self._chain_id, signer_address)
        old_next_nonce = current_state.next_nonce if current_state else None

        # Release all reservations at or above target nonce
        reservations = self._db.get_reservations_for_signer(
            self._chain_id, signer_address
        )
        released_count = 0
        for r in reservations:
            if r.nonce >= target_nonce and r.status in (
                NonceStatus.RESERVED,
                NonceStatus.IN_FLIGHT,
            ):
                self.release(signer_address, r.nonce)
                released_count += 1

        # Reset next_nonce
        self._db.update_signer_next_nonce(self._chain_id, signer_address, target_nonce)

        # Clear gap tracking
        self._db.clear_gap_started_at(self._chain_id, signer_address)

        # Emit metric for observability
        metrics = get_metrics()
        metrics.counter(NONCE_FORCE_RESET).inc(
            chain_id=self._chain_id,
            signer=signer_address[:10],  # Truncate for cardinality
            source=source,
        )

        # Explicit audit log - this is a destructive operation
        logger.warning(
            "nonce.force_reset",
            signer=signer_address,
            old_next_nonce=old_next_nonce,
            new_next_nonce=target_nonce,
            released_reservations=released_count,
            source=source,
            reason=reason or "not provided",
        )

        # Durable audit record in DB (survives log rotation)
        self._db.record_nonce_reset_audit(
            chain_id=self._chain_id,
            signer_address=signer_address,
            old_next_nonce=old_next_nonce,
            new_next_nonce=target_nonce,
            released_reservations=released_count,
            source=source,
            reason=reason,
        )

        return target_nonce
