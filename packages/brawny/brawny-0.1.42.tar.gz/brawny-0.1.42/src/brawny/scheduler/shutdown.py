"""Graceful shutdown handling for brawny.

Implements SPEC 9.5 Graceful Shutdown:
- Signal handling (SIGTERM, SIGINT)
- Graceful shutdown sequence
- In-progress intent handling
- Connection cleanup
"""

from __future__ import annotations

import signal
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable

from brawny.logging import LogEvents, get_logger
from brawny.model.enums import IntentStatus, NonceStatus

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny._rpc.clients import ReadClient
    from brawny.tx.nonce import NonceManager

logger = get_logger(__name__)


class ShutdownState(str, Enum):
    """Shutdown state machine."""

    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN_COMPLETE = "shutdown_complete"


@dataclass
class ShutdownStats:
    """Statistics from shutdown process."""

    claimed_released: int = 0
    pending_orphaned: int = 0
    errors: int = 0


class ShutdownHandler:
    """Manages graceful shutdown of brawny.

    Handles SIGTERM and SIGINT signals to trigger graceful shutdown.
    Coordinates shutdown of all components in proper order.
    """

    def __init__(
        self,
        config: Config,
        db: Database | None = None,
        rpc: ReadClient | None = None,
        nonce_manager: NonceManager | None = None,
    ) -> None:
        """Initialize shutdown handler.

        Args:
            config: Application configuration
            db: Database connection (optional, set later)
            rpc: RPC manager (optional, set later)
            nonce_manager: Nonce manager (optional, set later)
        """
        self._config = config
        self._db = db
        self._rpc = rpc
        self._nonce_manager = nonce_manager

        self._state = ShutdownState.RUNNING
        self._shutdown_flag = threading.Event()
        self._shutdown_lock = threading.Lock()

        # Callbacks to notify on shutdown
        self._shutdown_callbacks: list[Callable[[], None]] = []
        self._callbacks_notified = False

        # Force exit counter
        self._signal_count = 0

        # Stats
        self._stats = ShutdownStats()

    def set_db(self, db: Database) -> None:
        """Set database connection."""
        self._db = db

    def set_rpc(self, rpc: ReadClient) -> None:
        """Set RPC manager."""
        self._rpc = rpc

    def set_nonce_manager(self, nonce_manager: NonceManager) -> None:
        """Set nonce manager."""
        self._nonce_manager = nonce_manager

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called on shutdown.

        Args:
            callback: Function to call during shutdown
        """
        self._shutdown_callbacks.append(callback)

    def install_signal_handlers(self) -> None:
        """Install signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        logger.debug("shutdown.handlers_installed")

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signal.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        import os
        import sys

        self._signal_count += 1
        signal_name = signal.Signals(signum).name

        if self._signal_count >= 3:
            logger.warning("shutdown.force_exit", signal_count=self._signal_count)
            print("\nForce exit.", file=sys.stderr)
            os._exit(1)

        logger.info(
            "shutdown.signal_received",
            signal=signal_name,
            count=self._signal_count,
        )
        self.initiate_shutdown()

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown has been initiated."""
        return self._state != ShutdownState.RUNNING

    @property
    def shutdown_flag(self) -> threading.Event:
        """Get shutdown flag for waiting."""
        return self._shutdown_flag

    def initiate_shutdown(self) -> None:
        """Initiate graceful shutdown.

        Can be called from signal handler or programmatically.
        Immediately notifies callbacks to stop blocking loops.
        """
        with self._shutdown_lock:
            if self._state != ShutdownState.RUNNING:
                return

            self._state = ShutdownState.SHUTTING_DOWN
            self._shutdown_flag.set()

            logger.info(LogEvents.SHUTDOWN_INITIATED)

        # Notify callbacks immediately (outside lock to avoid deadlock)
        # This stops blocking loops like the poller
        self._notify_callbacks()

    def wait_for_shutdown(self, timeout: float | None = None) -> bool:
        """Wait for shutdown signal.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if shutdown was signaled, False if timeout
        """
        return self._shutdown_flag.wait(timeout)

    def execute_shutdown(self, timeout: float | None = None) -> ShutdownStats:
        """Execute the full shutdown sequence.

        Per SPEC 9.5:
        1. Stop accepting new block processing
        2. Wait for current block to finish
        3. Handle in-progress intents
        4. Flush logs and metrics
        5. Close connections

        Args:
            timeout: Maximum time for shutdown (default from config)

        Returns:
            Shutdown statistics
        """
        timeout = timeout or self._config.shutdown_timeout_seconds

        logger.info(
            "shutdown.executing",
            timeout_seconds=timeout,
        )

        start_time = time.time()
        self._stats = ShutdownStats()

        # 1. Notify registered callbacks (stops pollers, workers, etc.)
        self._notify_callbacks()

        # 2. Wait for graceful completion (callbacks should signal)
        remaining = timeout - (time.time() - start_time)
        if remaining > 0:
            time.sleep(min(remaining, 2.0))  # Brief wait for work to finish

        # 3. Handle in-progress intents
        self._handle_in_progress_intents()

        # 4. Close RPC connections
        if self._rpc:
            try:
                self._rpc.close()
            except Exception as e:
                # RECOVERABLE shutdown continues even if RPC close fails.
                logger.error("shutdown.rpc_close_failed", error=str(e)[:200], exc_info=True)

        # 5. Close database
        if self._db:
            try:
                self._db.close()
            except Exception as e:
                # RECOVERABLE shutdown continues even if DB close fails.
                logger.error("shutdown.db_close_failed", error=str(e)[:200], exc_info=True)

        # Mark shutdown complete
        self._state = ShutdownState.SHUTDOWN_COMPLETE

        elapsed = time.time() - start_time
        logger.info(
            LogEvents.SHUTDOWN_COMPLETE,
            elapsed_seconds=round(elapsed, 2),
            claimed_released=self._stats.claimed_released,
            pending_orphaned=self._stats.pending_orphaned,
        )

        return self._stats

    def _notify_callbacks(self) -> None:
        """Notify all registered shutdown callbacks.

        Only runs once, even if called multiple times.
        """
        if self._callbacks_notified:
            return
        self._callbacks_notified = True

        logger.info("shutdown.notifying_callbacks", count=len(self._shutdown_callbacks))

        for i, callback in enumerate(self._shutdown_callbacks):
            try:
                logger.debug("shutdown.callback_start", index=i)
                callback()
                logger.debug("shutdown.callback_done", index=i)
            except Exception as e:
                # RECOVERABLE shutdown callbacks are best-effort.
                logger.error(
                    "shutdown.callback_failed",
                    index=i,
                    error=str(e)[:200],
                    exc_info=True,
                )
                self._stats.errors += 1

        logger.info("shutdown.callbacks_complete")

    def _handle_in_progress_intents(self) -> None:
        """Handle intents that are in progress during shutdown.

        Per SPEC 9.5:
        - Claimed but not broadcast: release back to queue
        - Broadcasted: leave for reconciliation on restart
        """
        if not self._db:
            return

        try:
            # Handle claimed intents (not yet broadcast)
            claimed = self._db.get_intents_by_status(
                IntentStatus.CLAIMED.value,
                chain_id=self._config.chain_id,
            )

            for intent in claimed:
                try:
                    # Release claim (revert to created)
                    self._db.release_intent_claim(intent.intent_id)

                    # Get the attempt to find nonce
                    attempt = self._db.get_latest_attempt_for_intent(intent.intent_id)
                    if attempt and self._nonce_manager:
                        # Release nonce reservation
                        self._nonce_manager.release(
                            intent.signer_address,
                            attempt.nonce,
                        )

                    logger.debug(
                        "shutdown.intent_released",
                        intent_id=str(intent.intent_id),
                    )
                    self._stats.claimed_released += 1

                except Exception as e:
                    # RECOVERABLE individual intent release failures do not stop shutdown.
                    logger.error(
                        "shutdown.intent_release_failed",
                        intent_id=str(intent.intent_id),
                        error=str(e)[:200],
                        exc_info=True,
                    )
                    self._stats.errors += 1

            # Log broadcasted intents (left for reconciliation)
            in_flight_statuses = [IntentStatus.BROADCASTED.value]

            for status in in_flight_statuses:
                intents = self._db.get_intents_by_status(
                    status,
                    chain_id=self._config.chain_id,
                )

                for intent in intents:
                    logger.info(
                        "shutdown.orphan_pending",
                        intent_id=str(intent.intent_id),
                        status=status,
                    )
                    self._stats.pending_orphaned += 1

        except Exception as e:
            # RECOVERABLE shutdown continues even if cleanup fails.
            logger.error(
                "shutdown.handle_intents_failed",
                error=str(e)[:200],
                exc_info=True,
            )
            self._stats.errors += 1


class ShutdownContext:
    """Context manager for graceful shutdown handling.

    Usage:
        handler = ShutdownHandler(config)
        with ShutdownContext(handler):
            # Main application loop
            while not handler.is_shutting_down:
                process_block()
    """

    def __init__(self, handler: ShutdownHandler) -> None:
        """Initialize context.

        Args:
            handler: Shutdown handler to use
        """
        self._handler = handler

    def __enter__(self) -> ShutdownHandler:
        """Enter context and install signal handlers."""
        self._handler.install_signal_handlers()
        return self._handler

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context and execute shutdown."""
        if self._handler.is_shutting_down:
            self._handler.execute_shutdown()
        return False  # Don't suppress exceptions
