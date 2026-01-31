"""Worker thread supervision with health tracking and failure handling.

Provides fail-fast supervision for daemon worker threads. When a worker fails
(exception or silent return), the supervisor signals shutdown so the daemon
can exit cleanly with a non-zero exit code.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from brawny.logging import get_logger

logger = get_logger(__name__)


class WorkerStatus(Enum):
    """Status of a supervised worker thread."""

    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"  # Exited without exception (still a failure in daemon)


@dataclass
class WorkerState:
    """State for a supervised worker thread."""

    name: str
    target: Callable[[], None]
    daemon: bool
    status: WorkerStatus = WorkerStatus.STARTING
    thread: threading.Thread | None = None
    started_at: datetime | None = None
    failed_at: datetime | None = None
    failure_count: int = 0
    last_error: str | None = None


class WorkerSupervisor:
    """Supervises worker threads with health tracking and failure handling.

    Responsibilities:
    - Start workers with exception-catching wrapper
    - Record status + last error
    - Signal shutdown on failure (fail-fast mode)
    - Provide snapshot for health checks

    Does NOT:
    - Call sys.exit() (daemon decides exit)
    - Auto-restart workers (V1 - keeps it simple)
    """

    def __init__(
        self,
        *,
        fail_fast: bool = True,
        liveness_check_interval: float = 5.0,
    ) -> None:
        """Initialize the supervisor.

        Args:
            fail_fast: If True, trigger shutdown on any worker failure (default for tx systems)
            liveness_check_interval: How often to check thread liveness (seconds)
        """
        self._workers: dict[str, WorkerState] = {}
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()
        self._fatal_reason: str | None = None
        self._fail_fast = fail_fast
        self._liveness_interval = liveness_check_interval
        self._liveness_thread: threading.Thread | None = None

    def add(
        self,
        name: str,
        target: Callable[[], None],
        *,
        daemon: bool = True,
    ) -> None:
        """Register a worker to be supervised (does not start it).

        Args:
            name: Unique name for the worker
            target: The function to run in the worker thread
            daemon: Whether the thread should be a daemon thread
        """
        with self._lock:
            if name in self._workers:
                raise ValueError(f"Worker {name!r} already registered")
            self._workers[name] = WorkerState(
                name=name,
                target=target,
                daemon=daemon,
            )

    def start_all(self) -> None:
        """Start all registered workers and the liveness monitor."""
        with self._lock:
            for state in self._workers.values():
                self._start_worker(state)

        # Start liveness monitor thread
        self._liveness_thread = threading.Thread(
            target=self._liveness_monitor,
            name="supervisor-liveness",
            daemon=True,
        )
        self._liveness_thread.start()

    def _start_worker(self, state: WorkerState) -> None:
        """Start a single worker thread with supervision wrapper."""
        name = state.name
        target = state.target

        def supervised_target() -> None:
            # Update state to RUNNING
            with self._lock:
                state.status = WorkerStatus.RUNNING
                state.started_at = datetime.now(timezone.utc)

            logger.info("worker.started", worker=name)

            try:
                target()
                # If we get here, worker returned normally - that's a bug in a daemon
                self._handle_worker_exit(name, reason="returned normally (bug)")
            except Exception as e:
                # BUG worker exceptions trigger shutdown.
                failure_count = self._handle_worker_failure(name, e)
                if not getattr(e, "_logged_unexpected", False):
                    logger.error(
                        "worker.failed",
                        worker=name,
                        error=str(e),
                        failure_count=failure_count,
                        exc_info=True,
                    )

        thread = threading.Thread(
            target=supervised_target,
            name=f"worker-{name}",
            daemon=state.daemon,
        )
        state.thread = thread
        thread.start()

    def _handle_worker_failure(self, name: str, error: Exception) -> int:
        """Handle worker thread failure (exception)."""
        # Capture fields under lock, then release before logging
        with self._lock:
            worker = self._workers[name]
            worker.status = WorkerStatus.FAILED
            worker.failed_at = datetime.now(timezone.utc)
            worker.failure_count += 1
            worker.last_error = str(error)
            failure_count = worker.failure_count

        self._trigger_shutdown(f"worker {name!r} failed: {error}")
        return failure_count

    def _handle_worker_exit(self, name: str, reason: str) -> None:
        """Handle worker thread exiting (no exception, but still a failure)."""
        with self._lock:
            worker = self._workers[name]
            worker.status = WorkerStatus.STOPPED
            worker.failed_at = datetime.now(timezone.utc)
            worker.last_error = reason

        logger.error("worker.exited", worker=name, reason=reason)
        self._trigger_shutdown(f"worker {name!r} exited: {reason}")

    def _trigger_shutdown(self, reason: str) -> None:
        """Trigger shutdown with reason.

        When fail_fast=True: Sets shutdown_event, daemon should exit.
        When fail_fast=False: Does NOT set shutdown_event. Daemon keeps running
            but all_healthy() returns False. Health checks should use all_healthy()
            to report degraded status even if process continues.
        """
        # Always record the reason (useful for debugging even if not shutting down)
        with self._lock:
            if self._fatal_reason is None:
                self._fatal_reason = reason

        if self._fail_fast:
            logger.critical("supervisor.shutdown", reason=reason)
            self._shutdown_event.set()
        else:
            # Log but don't trigger shutdown - daemon continues in degraded state
            logger.error("supervisor.worker_failed_no_shutdown", reason=reason)

    def _liveness_monitor(self) -> None:
        """Periodically check that all workers are still alive."""
        while not self._shutdown_event.wait(self._liveness_interval):
            dead_name: str | None = None

            with self._lock:
                for name, state in self._workers.items():
                    if state.status == WorkerStatus.RUNNING:
                        if state.thread is not None and not state.thread.is_alive():
                            # Thread died without us catching it (shouldn't happen, but defensive)
                            state.status = WorkerStatus.STOPPED
                            state.failed_at = datetime.now(timezone.utc)
                            state.last_error = "thread died unexpectedly"
                            dead_name = name  # Capture before releasing lock
                            break

            # Handle dead worker outside lock
            if dead_name is not None:
                logger.error("worker.dead", worker=dead_name)
                self._trigger_shutdown(f"worker {dead_name!r} died unexpectedly")

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Return snapshot of all worker states for health checks."""
        with self._lock:
            return {
                name: {
                    "status": state.status.value,
                    "started_at": state.started_at.isoformat() if state.started_at else None,
                    "failed_at": state.failed_at.isoformat() if state.failed_at else None,
                    "failure_count": state.failure_count,
                    "last_error": state.last_error,
                    "alive": state.thread.is_alive() if state.thread else False,
                }
                for name, state in self._workers.items()
            }

    def all_healthy(self) -> bool:
        """Check if all workers are healthy (running and alive)."""
        with self._lock:
            return all(
                state.status == WorkerStatus.RUNNING
                and state.thread is not None
                and state.thread.is_alive()
                for state in self._workers.values()
            )

    def shutdown_requested(self) -> bool:
        """Check if shutdown has been triggered."""
        return self._shutdown_event.is_set()

    def fatal_reason(self) -> str | None:
        """Return the reason for fatal shutdown, if any."""
        with self._lock:
            return self._fatal_reason

    def wait_for_shutdown(self, timeout: float | None = None) -> bool:
        """Wait for shutdown signal. Returns True if shutdown was signaled."""
        return self._shutdown_event.wait(timeout)

    def request_shutdown(self, reason: str = "requested") -> None:
        """Request supervisor shutdown (e.g., from signal handler)."""
        with self._lock:
            if self._fatal_reason is None:
                self._fatal_reason = reason
        self._shutdown_event.set()
