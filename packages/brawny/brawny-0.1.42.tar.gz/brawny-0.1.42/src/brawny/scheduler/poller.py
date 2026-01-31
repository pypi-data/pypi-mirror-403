"""Block poller for continuous block processing.

Implements the polling loop from SPEC 5:
- HTTP poll head block (eth_blockNumber)
- Process sequentially from last_processed+1 up to head
- Limit catchup blocks per iteration
- Sleep poll_interval_seconds between iterations
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Event, Thread
from typing import TYPE_CHECKING, Callable

from brawny.alerts.health import health_alert
from brawny.error_taxonomy import classify_error
from brawny.invariants import collect_invariants
from brawny.logging import get_logger
from brawny.metrics import (
    BLOCK_PROCESSING_SECONDS,
    BLOCKS_PROCESSED,
    BLOCK_PROCESSING_LAG_SECONDS,
    ERRORS_TOTAL,
    LAST_BLOCK_TIMESTAMP,
    LAST_BLOCK_PROCESSED_TIMESTAMP,
    LAST_PROCESSED_BLOCK,
    OLDEST_PENDING_INTENT_AGE_SECONDS,
    PENDING_INTENTS,
    get_metrics,
)

# Collect invariants every N blocks to avoid overhead
INVARIANT_COLLECTION_INTERVAL_BLOCKS = 6

if TYPE_CHECKING:
    from brawny.automation import AutomationState
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny.model.types import BlockInfo
    from brawny._rpc.clients import ReadClient
    from brawny.scheduler.reorg import ReorgDetector

logger = get_logger(__name__)


@dataclass
class PollResult:
    """Result of a poll iteration."""

    blocks_processed: int
    head_block: int
    last_processed: int
    reorg_detected: bool = False
    reorg_depth: int = 0


class BlockPoller:
    """Block poller with configurable interval.

    Always starts at chain head (live-head mode). No historical catchup.
    Downtime means missed block evaluations by design.

    Provides the main polling loop that:
    1. Gets head block from RPC
    2. Processes blocks sequentially from last processed (or head on startup)
    3. Calls block handler for each block
    4. Sleeps between iterations
    """

    def __init__(
        self,
        db: Database,
        rpc: ReadClient,
        config: Config,
        block_handler: Callable[[BlockInfo], None],
        reorg_detector: "ReorgDetector | None" = None,
        health_send_fn: Callable[..., None] | None = None,
        admin_chat_ids: list[str] | None = None,
        health_cooldown: int = 1800,
        automation: "AutomationState | None" = None,
    ) -> None:
        """Initialize block poller.

        Args:
            db: Database connection
            rpc: RPC manager
            config: Application configuration
            block_handler: Callback for processing each block
            reorg_detector: Optional reorg detector
            health_send_fn: Optional health alert send function
            admin_chat_ids: Optional admin alert chat IDs
            health_cooldown: Health alert cooldown in seconds
            automation: Optional automation gate for hard-stop controls
        """
        self._db = db
        self._rpc = rpc
        self._config = config
        self._block_handler = block_handler
        self._reorg_detector = reorg_detector
        self._chain_id = config.chain_id

        # Health alerting
        self._health_send_fn = health_send_fn
        self._admin_chat_ids = admin_chat_ids
        self._health_cooldown = health_cooldown
        self._automation = automation

        # Polling state
        self._running = False
        self._stop_event = Event()
        self._poll_thread: Thread | None = None

        # Session state - will be initialized on first poll
        self._session_last_processed: int | None = None

        # Invariant collection tick counter
        self._invariant_tick_count = 0

    @property
    def is_running(self) -> bool:
        """Check if poller is running."""
        return self._running

    def start(self, blocking: bool = True) -> None:
        """Start the polling loop.

        Args:
            blocking: If True, run in current thread. Otherwise spawn thread.
        """
        self._running = True
        self._stop_event.clear()

        if blocking:
            self._poll_loop()
        else:
            self._poll_thread = Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()

    def stop(self, timeout: float | None = None) -> bool:
        """Stop the polling loop.

        Args:
            timeout: Max seconds to wait for clean stop

        Returns:
            True if stopped cleanly, False if timed out
        """
        self._stop_event.set()
        self._running = False

        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=timeout)
            return not self._poll_thread.is_alive()

        return True

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for current block processing to complete.

        Args:
            timeout: Max seconds to wait

        Returns:
            True if completed within timeout
        """
        if self._poll_thread:
            self._poll_thread.join(timeout=timeout)
            return not self._poll_thread.is_alive()
        return True

    def _poll_loop(self) -> None:
        """Main polling loop."""
        logger.info(
            "poller.started",
            chain_id=self._chain_id,
            poll_interval=self._config.poll_interval_seconds,
        )

        while not self._stop_event.is_set():
            try:
                result = self._poll_once()

                if result.blocks_processed > 0:
                    logger.debug(
                        "poller.iteration",
                        blocks_processed=result.blocks_processed,
                        head=result.head_block,
                        last_processed=result.last_processed,
                    )

            except Exception as e:
                # RECOVERABLE poller loop failures are logged and retried.
                if not getattr(e, "_logged_unexpected", False):
                    classification = classify_error(e)
                    logger.error(
                        "poller.error",
                        error=str(e),
                        error_class=classification.error_class.value,
                        reason_code=classification.reason_code,
                        exc_info=True,
                    )
                    metrics = get_metrics()
                    metrics.counter(ERRORS_TOTAL).inc(
                        error_class=classification.error_class.value,
                        reason_code=classification.reason_code,
                        subsystem="poller",
                    )
                    if self._automation and classification.reason_code in {
                        "rpc_unhealthy",
                        "db_locked",
                        "db_circuit_breaker_open",
                    }:
                        self._automation.disable(
                            classification.reason_code,
                            source="poller",
                            detail=str(e)[:200],
                        )
                health_alert(
                    component="brawny.scheduler.poller",
                    chain_id=self._chain_id,
                    error=e,
                    action="Check RPC connectivity",
                    db_dialect=self._db.dialect,
                    send_fn=self._health_send_fn,
                    admin_chat_ids=self._admin_chat_ids,
                    cooldown_seconds=self._health_cooldown,
                )

            # Sleep between iterations
            if not self._stop_event.wait(timeout=self._config.poll_interval_seconds):
                continue
            else:
                break  # Stop event was set

        logger.info("poller.stopped")

    def _poll_once(self) -> PollResult:
        """Execute one poll iteration.

        Returns:
            Poll result with blocks processed
        """
        # Get head block (bounded by RPC timeout)
        timeout = min(5.0, float(self._config.rpc_timeout_seconds))
        head_block = self._rpc.get_block_number(timeout=timeout)

        # Determine starting point
        if self._session_last_processed is None:
            # First poll of session - always start at chain head (no catchup)
            last_processed = head_block - 1
            logger.info(
                "poller.starting_at_head",
                chain_id=self._chain_id,
                head_block=head_block,
            )
        else:
            last_processed = self._session_last_processed

        # Calculate how many blocks to process
        blocks_to_process = head_block - last_processed

        if blocks_to_process <= 0:
            return PollResult(
                blocks_processed=0,
                head_block=head_block,
                last_processed=last_processed,
            )

        # Process blocks sequentially
        blocks_processed = 0
        for block_number in range(last_processed + 1, last_processed + blocks_to_process + 1):
            if self._stop_event.is_set():
                break

            try:
                if self._reorg_detector:
                    reorg_result = self._reorg_detector.check(block_number)
                    if reorg_result is None:
                        return PollResult(
                            blocks_processed=0,
                            head_block=head_block,
                            last_processed=last_processed,
                        )
                    if reorg_result.reorg_detected:
                        if reorg_result.pause:
                            logger.error(
                                "poller.reorg_pause",
                                chain_id=self._chain_id,
                                reason=reorg_result.rewind_reason,
                            )
                            self._stop_event.set()
                            self._running = False
                            return PollResult(
                                blocks_processed=0,
                                head_block=head_block,
                                last_processed=last_processed,
                                reorg_detected=True,
                                reorg_depth=reorg_result.reorg_depth,
                            )
                        if reorg_result.last_good_height is None or reorg_result.last_good_height < 0:
                            self._reorg_detector.handle_deep_reorg()
                            if self._config.deep_reorg_pause:
                                logger.error(
                                    "poller.deep_reorg_pause",
                                    chain_id=self._chain_id,
                                )
                                self._stop_event.set()
                                self._running = False
                            # Deep reorg - reset to start fresh at head on next poll
                            self._session_last_processed = None
                            return PollResult(
                                blocks_processed=0,
                                head_block=head_block,
                                last_processed=last_processed,
                                reorg_detected=True,
                                reorg_depth=reorg_result.reorg_depth,
                            )

                        rewind_result = self._reorg_detector.rewind(reorg_result)
                        new_last = (
                            rewind_result.last_good_height
                            if rewind_result.last_good_height is not None
                            else last_processed
                        )
                        self._session_last_processed = new_last
                        return PollResult(
                            blocks_processed=0,
                            head_block=head_block,
                            last_processed=new_last,
                            reorg_detected=True,
                            reorg_depth=reorg_result.reorg_depth,
                        )

                # Fetch block with retries for transient RPC issues
                block_info = None
                for retry in range(3):
                    block_info = self._fetch_block_info(block_number)
                    if block_info is not None:
                        break
                    logger.debug(
                        "poller.block_fetch_retry",
                        block_number=block_number,
                        retry=retry + 1,
                    )

                if block_info is None:
                    logger.warning(
                        "poller.block_not_found_after_retries",
                        block_number=block_number,
                        retries=3,
                    )
                    break

                # Call the block handler (this is where job evaluation happens)
                metrics = get_metrics()
                start_time = time.perf_counter()
                self._block_handler(block_info)
                duration = time.perf_counter() - start_time
                metrics.histogram(BLOCK_PROCESSING_SECONDS).observe(
                    duration,
                    chain_id=self._chain_id,
                )
                metrics.counter(BLOCKS_PROCESSED).inc(chain_id=self._chain_id)
                metrics.gauge(LAST_PROCESSED_BLOCK).set(
                    block_info.block_number,
                    chain_id=self._chain_id,
                )
                pending_count = self._db.get_pending_intent_count(chain_id=self._chain_id)
                metrics.gauge(PENDING_INTENTS).set(
                    pending_count,
                    chain_id=self._chain_id,
                )
                oldest_age = self._db.get_oldest_pending_intent_age(chain_id=self._chain_id)
                if oldest_age is not None:
                    metrics.gauge(OLDEST_PENDING_INTENT_AGE_SECONDS).set(
                        oldest_age,
                        chain_id=self._chain_id,
                    )
                else:
                    metrics.gauge(OLDEST_PENDING_INTENT_AGE_SECONDS).set(
                        0,
                        chain_id=self._chain_id,
                    )

                # Update block state and hash history
                self._db.upsert_block_state(
                    self._chain_id,
                    block_number,
                    block_info.block_hash,
                )
                self._db.insert_block_hash(
                    self._chain_id,
                    block_number,
                    block_info.block_hash,
                )

                # Cleanup old block hashes
                self._db.cleanup_old_block_hashes(
                    self._chain_id,
                    self._config.block_hash_history_size,
                )

                # Emit timestamp after all DB commits are complete
                metrics.gauge(LAST_BLOCK_PROCESSED_TIMESTAMP).set(
                    time.time(),
                    chain_id=self._chain_id,
                )
                metrics.gauge(LAST_BLOCK_TIMESTAMP).set(
                    block_info.timestamp,
                    chain_id=self._chain_id,
                )
                metrics.gauge(BLOCK_PROCESSING_LAG_SECONDS).set(
                    time.time() - float(block_info.timestamp),
                    chain_id=self._chain_id,
                )

                # Collect invariants every N blocks
                self._invariant_tick_count += 1
                if self._invariant_tick_count >= INVARIANT_COLLECTION_INTERVAL_BLOCKS:
                    self._invariant_tick_count = 0
                    try:
                        collect_invariants(
                            self._db,
                            self._chain_id,
                            health_send_fn=self._health_send_fn,
                            admin_chat_ids=self._admin_chat_ids,
                            health_cooldown=self._health_cooldown,
                            log_violations=False,
                        )
                    except Exception as e:
                        # RECOVERABLE invariant collection failures should not stop polling.
                        logger.error(
                            "invariants.collection_failed",
                            error=str(e),
                            exc_info=True,
                        )

                blocks_processed += 1

            except Exception as e:
                # RECOVERABLE stop current batch on block processing errors.
                if not getattr(e, "_logged_unexpected", False):
                    logger.error(
                        "poller.block_error",
                        block_number=block_number,
                        error=str(e),
                        exc_info=True,
                    )
                break

        # Update session state
        self._session_last_processed = last_processed + blocks_processed

        return PollResult(
            blocks_processed=blocks_processed,
            head_block=head_block,
            last_processed=last_processed + blocks_processed,
        )

    def _fetch_block_info(self, block_number: int) -> BlockInfo | None:
        """Fetch block info from RPC.

        Args:
            block_number: Block number to fetch

        Returns:
            BlockInfo or None if not found
        """
        from brawny.model.types import BlockInfo
        from brawny._rpc.errors import RPCError

        try:
            block = self._rpc.get_block(block_number)
            if block is None:
                return None

            return BlockInfo(
                chain_id=self._chain_id,
                block_number=block["number"],
                block_hash=f"0x{block['hash'].hex()}" if isinstance(block["hash"], bytes) else block["hash"],
                timestamp=block["timestamp"],
                base_fee=block.get("baseFeePerGas", 0),
            )
        except (RPCError, KeyError, TypeError, ValueError):
            return None

    def poll_once(self) -> PollResult:
        """Public method to run a single poll iteration.

        Useful for testing and one-shot processing.

        Returns:
            Poll result
        """
        return self._poll_once()
