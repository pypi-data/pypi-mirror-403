"""Reorg detection and handling.

Implements reorg detection from SPEC 5.2:
- Maintain block_hash_history window
- Compare stored hash at anchor height with chain
- Binary search to find last matching height
- Rewind and reprocess on reorg detection
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Callable

from brawny.alerts.health import health_alert
from brawny.logging import LogEvents, get_logger
from brawny.metrics import REORGS_DETECTED, get_metrics
from brawny.model.enums import AttemptStatus, IntentStatus, IntentTerminalReason
from brawny.model.errors import DatabaseError
from brawny._rpc.errors import RPCError

if TYPE_CHECKING:
    from brawny.db.base import Database
    from brawny.lifecycle import LifecycleDispatcher
    from brawny._rpc.clients import ReadClient

logger = get_logger(__name__)


@dataclass
class ReorgResult:
    """Result of reorg detection."""

    reorg_detected: bool
    reorg_depth: int = 0
    last_good_height: int | None = None
    intents_reverted: int = 0
    attempts_reverted: int = 0
    rewind_reason: str | None = None
    anchor_height: int | None = None
    anchor_hash_db: str | None = None
    anchor_hash_chain: str | None = None
    history_min_height: int | None = None
    history_max_height: int | None = None
    finality_confirmations: int | None = None
    pause: bool = False
    last_processed: int | None = None


class ReorgDetector:
    """Reorg detector using block hash history comparison.

    Algorithm:
    1. Select anchor height (last_processed - reorg_depth)
    2. Compare stored hash at anchor to current chain hash
    3. If mismatch, binary search for last matching height
    4. Rewind state and handle affected intents
    """

    def __init__(
        self,
        db: Database,
        rpc: ReadClient,
        chain_id: int,
        reorg_depth: int = 32,
        block_hash_history_size: int = 256,
        finality_confirmations: int = 0,
        lifecycle: "LifecycleDispatcher | None" = None,
        deep_reorg_alert_enabled: bool = True,
        health_send_fn: Callable[..., None] | None = None,
        admin_chat_ids: list[str] | None = None,
        health_cooldown: int = 1800,
    ) -> None:
        """Initialize reorg detector.

        Args:
            db: Database connection
            rpc: RPC manager
            chain_id: Chain ID
            reorg_depth: Blocks back to check for reorg
            block_hash_history_size: Size of hash history window
        """
        self._db = db
        self._rpc = rpc
        self._chain_id = chain_id
        self._reorg_depth = reorg_depth
        self._history_size = block_hash_history_size
        self._finality_confirmations = max(0, finality_confirmations)
        self._lifecycle = lifecycle
        self._deep_reorg_alert_enabled = deep_reorg_alert_enabled
        self._health_send_fn = health_send_fn
        self._admin_chat_ids = admin_chat_ids
        self._health_cooldown = health_cooldown

    def check(self, current_block: int) -> ReorgResult | None:
        """Check for reorg at the current block height.

        Args:
            current_block: Current block being processed

        Returns:
            ReorgResult with detection status, or None if probing fails
        """
        # Get block state
        block_state = self._db.get_block_state(self._chain_id)
        if block_state is None:
            return ReorgResult(reorg_detected=False)

        last_processed = block_state.last_processed_block_number
        history_min = self._db.get_oldest_block_in_history(self._chain_id)
        history_max = self._db.get_latest_block_in_history(self._chain_id)

        # Calculate anchor height
        anchor_height = max(0, last_processed - self._reorg_depth)

        # Get stored hash at anchor
        stored_hash = self._db.get_block_hash_at_height(self._chain_id, anchor_height)
        anchor_missing = False
        if stored_hash is None:
            # No history at anchor - check if we have any history
            if history_min is None:
                return ReorgResult(reorg_detected=False)
            if history_max is None or anchor_height > history_max:
                anchor_height = history_min
                stored_hash = self._db.get_block_hash_at_height(self._chain_id, anchor_height)
                if stored_hash is None:
                    return ReorgResult(reorg_detected=False)
                anchor_missing = True
            elif anchor_height >= history_min:
                if history_max is not None and history_max - history_min < self._reorg_depth:
                    logger.warning(
                        "reorg.history_insufficient",
                        anchor_height=anchor_height,
                        history_min=history_min,
                        history_max=history_max,
                        reorg_depth=self._reorg_depth,
                    )
                    return ReorgResult(reorg_detected=False)
                # Expected history missing -> possible corruption
                logger.error(
                    "reorg.history_missing",
                    anchor_height=anchor_height,
                    history_min=history_min,
                    history_max=history_max,
                )
                cleared = self._db.clear_block_hash_history(self._chain_id)
                logger.warning(
                    "reorg.history_reset",
                    chain_id=self._chain_id,
                    cleared=cleared,
                )
                return ReorgResult(reorg_detected=False)
            else:
                anchor_height = history_min
                stored_hash = self._db.get_block_hash_at_height(self._chain_id, anchor_height)
                if stored_hash is None:
                    return ReorgResult(reorg_detected=False)
                anchor_missing = True
        if not stored_hash.startswith("0x"):
            stored_hash = f"0x{stored_hash}"

        # Get current chain hash at anchor
        try:
            block = self._rpc.get_block(anchor_height)
            if block is None:
                return ReorgResult(reorg_detected=False)

            chain_hash = block.get("hash")
            if chain_hash is None:
                logger.warning(
                    "reorg.missing_block_hash",
                    block_number=anchor_height,
                )
                return ReorgResult(reorg_detected=False)
            if isinstance(chain_hash, bytes):
                chain_hash = chain_hash.hex()
            if not chain_hash.startswith("0x"):
                chain_hash = f"0x{chain_hash}"
        except asyncio.CancelledError:
            raise
        except RPCError as e:
            logger.warning(
                "reorg.check_failed",
                anchor_height=anchor_height,
                chain_id=self._chain_id,
                error=str(e),
            )
            return ReorgResult(reorg_detected=False)

        # Compare hashes
        stored_normalized = stored_hash.lower()
        chain_normalized = chain_hash.lower()

        if stored_normalized == chain_normalized:
            # No reorg
            return ReorgResult(reorg_detected=False)

        # Reorg detected!
        rewind_reason = "missing_history" if anchor_missing else "anchor_mismatch"
        # Find last good height via binary search
        last_good_height = self._find_last_good_height(anchor_height, last_processed)
        if last_good_height is None:
            return None

        logger.warning(
            LogEvents.BLOCK_REORG_DETECTED,
            anchor_height=anchor_height,
            stored_hash=stored_hash[:18],
            chain_hash=chain_hash[:18],
        )
        metrics = get_metrics()
        metrics.counter(REORGS_DETECTED).inc(
            chain_id=self._chain_id,
        )
        oldest = history_min
        if oldest is not None and last_good_height < oldest:
            finality_floor = max(0, last_processed - self._finality_confirmations)
            if anchor_missing and last_good_height < finality_floor:
                logger.error(
                    LogEvents.BLOCK_REORG_DEEP,
                    oldest_known=oldest,
                    history_size=self._history_size,
                )
                if self._lifecycle and self._deep_reorg_alert_enabled:
                    self._lifecycle.on_deep_reorg(oldest, self._history_size, last_processed)
                return ReorgResult(
                    reorg_detected=True,
                    reorg_depth=last_processed - (oldest - 1),
                    last_good_height=None,
                    rewind_reason="deep_reorg",
                    anchor_height=anchor_height,
                    anchor_hash_db=stored_hash,
                    anchor_hash_chain=chain_hash,
                    history_min_height=oldest,
                    history_max_height=history_max,
                    finality_confirmations=self._finality_confirmations,
                    pause=True,
                    last_processed=last_processed,
                )

            logger.warning(
                "reorg.insufficient_history",
                oldest_known=oldest,
                last_good_height=last_good_height,
                history_size=self._history_size,
            )
            last_good_height = oldest

        # Handle impossible state: mismatch at anchor but last_good >= anchor
        # This happens with sparse hash history - delete stale anchor hash
        if rewind_reason == "anchor_mismatch" and last_good_height >= anchor_height:
            logger.warning(
                "reorg.stale_hash_detected",
                anchor_height=anchor_height,
                last_good_height=last_good_height,
                stored_hash=stored_hash[:18],
                chain_hash=chain_hash[:18],
            )
            # Delete the stale hash at anchor and set last_good to anchor - 1
            self._db.delete_block_hash_at_height(self._chain_id, anchor_height)
            last_good_height = anchor_height - 1

        reorg_depth = last_processed - last_good_height

        logger.warning(
            LogEvents.BLOCK_REORG_REWIND,
            last_good_height=last_good_height,
            reorg_depth=reorg_depth,
        )

        return ReorgResult(
            reorg_detected=True,
            reorg_depth=reorg_depth,
            last_good_height=last_good_height,
            rewind_reason=rewind_reason,
            anchor_height=anchor_height,
            anchor_hash_db=stored_hash,
            anchor_hash_chain=chain_hash,
            history_min_height=history_min,
            history_max_height=history_max,
            finality_confirmations=self._finality_confirmations,
            last_processed=last_processed,
        )

    def _find_last_good_height(self, low: int, high: int) -> int | None:
        """Binary search to find last matching block height.

        Args:
            low: Lower bound (known bad)
            high: Upper bound (known bad)

        Returns:
            Last good block height, or None if probing fails
        """
        mid = None
        left = None
        right = None

        try:
            oldest = self._db.get_oldest_block_in_history(self._chain_id)
            if oldest is None:
                return low

            # Start from the known bad anchor and search forward
            # We need to find where the chain diverged
            left = max(oldest, low)
            right = high

            last_good = left - 1  # Assume nothing matches if search fails

            while left <= right:
                mid = (left + right) // 2

                stored = self._db.get_block_hash_at_height(self._chain_id, mid)
                if stored is None:
                    # No history here, move right
                    left = mid + 1
                    continue

                block = self._rpc.get_block(mid)
                if block is None:
                    left = mid + 1
                    continue

                chain_hash = block["hash"]
                if isinstance(chain_hash, bytes):
                    chain_hash = chain_hash.hex()
                if not chain_hash.startswith("0x"):
                    chain_hash = f"0x{chain_hash}"

                if stored.lower() == chain_hash.lower():
                    # Match - reorg is after this point
                    last_good = mid
                    left = mid + 1
                else:
                    # Mismatch - reorg is at or before this point
                    right = mid - 1

            return last_good
        except asyncio.CancelledError:
            raise
        except (DatabaseError, RPCError):
            endpoint = getattr(self._rpc, "endpoint", None)
            if endpoint is None:
                endpoint = getattr(self._rpc, "url", None)

            log_fields = {
                "chain_id": self._chain_id,
                "low": low,
                "high": high,
                "endpoint": endpoint,
            }
            if mid is None:
                log_fields["left"] = left
                log_fields["right"] = right
            else:
                log_fields["mid"] = mid

            logger.warning(
                "reorg.probe_failed",
                exc_info=True,
                **log_fields,
            )
            return None
    def rewind(self, reorg_result: ReorgResult) -> ReorgResult:
        """Rewind state using the centralized recovery contract."""
        recovery = ReorgRecovery(
            db=self._db,
            rpc=self._rpc,
            chain_id=self._chain_id,
            lifecycle=self._lifecycle,
            finality_confirmations=self._finality_confirmations,
            health_send_fn=self._health_send_fn,
            admin_chat_ids=self._admin_chat_ids,
            health_cooldown=self._health_cooldown,
        )
        return recovery.rewind(reorg_result)

    def handle_deep_reorg(self) -> None:
        """Handle a reorg deeper than our history window.

        This is a critical situation - emit error and rewind to oldest known block.
        """
        oldest = self._db.get_oldest_block_in_history(self._chain_id)

        logger.error(
            LogEvents.BLOCK_REORG_DEEP,
            oldest_known=oldest,
            history_size=self._history_size,
        )

        if oldest is not None:
            recovery = ReorgRecovery(
                db=self._db,
                rpc=self._rpc,
                chain_id=self._chain_id,
                lifecycle=self._lifecycle,
                finality_confirmations=self._finality_confirmations,
                health_send_fn=self._health_send_fn,
                admin_chat_ids=self._admin_chat_ids,
                health_cooldown=self._health_cooldown,
            )
            recovery.rewind(
                ReorgResult(
                    reorg_detected=True,
                    reorg_depth=0,
                    last_good_height=oldest,
                    rewind_reason="deep_reorg",
                    history_min_height=oldest,
                    history_max_height=self._db.get_latest_block_in_history(self._chain_id),
                    finality_confirmations=self._finality_confirmations,
                )
            )


class ReorgRecovery:
    """Centralized reorg recovery contract.

    Preconditions:
      - caller holds poller lock
      - no concurrent monitor execution

    Postconditions:
      - last_processed_block <= to_height
      - no confirmed attempt exists above last_processed_block
      - nonce state consistent with attempts
    """

    def __init__(
        self,
        db: Database,
        rpc: ReadClient,
        chain_id: int,
        lifecycle: "LifecycleDispatcher | None" = None,
        finality_confirmations: int = 0,
        health_send_fn: Callable[..., None] | None = None,
        admin_chat_ids: list[str] | None = None,
        health_cooldown: int = 1800,
    ) -> None:
        self._db = db
        self._rpc = rpc
        self._chain_id = chain_id
        self._lifecycle = lifecycle
        self._finality_confirmations = max(0, finality_confirmations)
        self._health_send_fn = health_send_fn
        self._admin_chat_ids = admin_chat_ids
        self._health_cooldown = health_cooldown

    def rewind(self, reorg_result: ReorgResult) -> ReorgResult:
        """Rewind state to the last good height."""
        to_height = reorg_result.last_good_height
        if to_height is None:
            return reorg_result

        block_state = self._db.get_block_state(self._chain_id)
        if block_state is None:
            raise RuntimeError("reorg.rewind_missing_block_state")
        last_processed = block_state.last_processed_block_number

        deleted_hashes = 0
        intents_reverted = 0
        attempts_reverted = 0
        rewind_hash = None

        if to_height == last_processed:
            reorg_result = replace(reorg_result, last_good_height=to_height)
            self._log_summary(
                reorg_result,
                last_processed_before=last_processed,
                last_processed_after=last_processed,
                deleted_hashes=0,
                intents_reverted=0,
                attempts_reverted=0,
            )
            return replace(
                reorg_result,
                intents_reverted=0,
                attempts_reverted=0,
            )

        try:
            with self._db.transaction():
                deleted_hashes = self._db.delete_block_hashes_above(self._chain_id, to_height)

                rewind_hash = self._db.get_block_hash_at_height(self._chain_id, to_height)
                if rewind_hash is None:
                    try:
                        block = self._rpc.get_block(to_height)
                        if block:
                            rewind_hash = block["hash"]
                            if isinstance(rewind_hash, bytes):
                                rewind_hash = rewind_hash.hex()
                    except asyncio.CancelledError:
                        raise
                    except RPCError as e:
                        logger.warning(
                            "reorg.rewind_hash_fetch_failed",
                            chain_id=self._chain_id,
                            to_height=to_height,
                            error=str(e),
                        )
                        rewind_hash = None

                if rewind_hash is None:
                    logger.warning(
                        "reorg.rewind_hash_missing",
                        to_height=to_height,
                    )
                    rewind_hash = "0x0"

                self._db.upsert_block_state(self._chain_id, to_height, rewind_hash or "0x0")

                intents_reverted, attempts_reverted = self._revert_reorged_intents(to_height)
                self._assert_no_confirmed_above(to_height)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # BUG re-raise unexpected reorg rewind failures.
            logger.error(
                "reorg.rewind_failed",
                chain_id=self._chain_id,
                to_height=to_height,
                error=str(e)[:200],
                exc_info=True,
            )
            health_alert(
                component="brawny.scheduler.reorg",
                chain_id=self._chain_id,
                error=e,
                action="Reorg rewind failed; inspect DB state",
                db_dialect=self._db.dialect,
                send_fn=self._health_send_fn,
                admin_chat_ids=self._admin_chat_ids,
                cooldown_seconds=self._health_cooldown,
            )
            raise

        self._log_summary(
            reorg_result,
            last_processed_before=last_processed,
            last_processed_after=to_height,
            deleted_hashes=deleted_hashes,
            intents_reverted=intents_reverted,
            attempts_reverted=attempts_reverted,
        )

        return replace(
            reorg_result,
            reorg_detected=True,
            reorg_depth=max(0, last_processed - to_height),
            last_good_height=to_height,
            intents_reverted=intents_reverted,
            attempts_reverted=attempts_reverted,
            last_processed=last_processed,
        )

    def _revert_reorged_intents(self, to_height: int) -> tuple[int, int]:
        """Stop on reorged confirmed intents; do not attempt to revert."""
        confirmed_intents = self._db.get_intents_by_status(
            IntentStatus.TERMINAL.value,
            chain_id=self._chain_id,
        )

        for intent in confirmed_intents:
            if intent.terminal_reason != IntentTerminalReason.CONFIRMED.value:
                continue
            attempts = self._db.get_attempts_for_intent(intent.intent_id)
            if not attempts:
                continue

            confirmed_attempts = [
                a for a in attempts
                if a.status == AttemptStatus.CONFIRMED and a.included_block
                and a.included_block > to_height
            ]
            if not confirmed_attempts:
                continue

            attempt = max(confirmed_attempts, key=lambda a: a.included_block or 0)
            if attempt.included_block and attempt.included_block > to_height:
                logger.error(
                    "reorg.intent_revert_blocked",
                    intent_id=str(intent.intent_id),
                    attempt_id=str(attempt.attempt_id),
                    old_block=attempt.included_block,
                    reorg_height=to_height,
                    chain_id=self._chain_id,
                )
                raise RuntimeError(
                    f"reorg.intent_revert_blocked intent={intent.intent_id} block={attempt.included_block} to_height={to_height}"
                )

        return (0, 0)

    def _assert_no_confirmed_above(self, to_height: int) -> None:
        confirmed_intents = self._db.get_intents_by_status(
            IntentStatus.TERMINAL.value,
            chain_id=self._chain_id,
        )
        for intent in confirmed_intents:
            if intent.terminal_reason != IntentTerminalReason.CONFIRMED.value:
                continue
            attempts = self._db.get_attempts_for_intent(intent.intent_id)
            for attempt in attempts:
                if (
                    attempt.status == AttemptStatus.CONFIRMED
                    and attempt.included_block
                    and attempt.included_block > to_height
                ):
                    raise RuntimeError(
                        f"reorg.invariant_failed intent={intent.intent_id} included_block={attempt.included_block} to_height={to_height}"
                    )

    def _log_summary(
        self,
        reorg_result: ReorgResult,
        *,
        last_processed_before: int,
        last_processed_after: int,
        deleted_hashes: int,
        intents_reverted: int,
        attempts_reverted: int,
    ) -> None:
        logger.warning(
            "reorg.summary",
            last_processed_before=last_processed_before,
            last_processed_after=last_processed_after,
            anchor_height=reorg_result.anchor_height,
            last_good_height=reorg_result.last_good_height,
            anchor_hash_db=reorg_result.anchor_hash_db,
            anchor_hash_chain=reorg_result.anchor_hash_chain,
            history_min_height=reorg_result.history_min_height,
            history_max_height=reorg_result.history_max_height,
            intents_reverted=intents_reverted,
            attempts_reverted=attempts_reverted,
            deleted_hash_count=deleted_hashes,
            finality_confirmations=self._finality_confirmations,
            rewind_reason=reorg_result.rewind_reason,
        )
