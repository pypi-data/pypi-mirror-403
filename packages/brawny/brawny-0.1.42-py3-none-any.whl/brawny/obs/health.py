"""Cached health state for readiness probes.

Readiness probes (/readyz) must be fast and never block on slow checks.
This module provides cached health state that's updated by background loops.

See LOGGING_METRICS_PLAN.md Section 4.1.3 for design rationale.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from threading import Thread


@dataclass
class HealthState:
    """Cached health state for readiness checks.

    Updated by background loops, read by /readyz endpoint.
    All fields are protected by a lock for thread safety.

    NOT READY when:
    - shutdown_requested is True (draining)
    - db_ok is False
    - rpc_ok is False
    - workers_ok is False

    Usage:
        # Background loop updates state
        health_state.update_db(db.ping())
        health_state.update_rpc(rpc.any_healthy())
        health_state.update_workers(worker_threads)

        # /readyz reads cached state (fast, never blocks)
        if not health_state.is_ready():
            return Response(status_code=503)
        return Response(status_code=200)
    """

    # Cached component health
    db_ok: bool = field(default=True)
    rpc_ok: bool = field(default=True)
    workers_ok: bool = field(default=True)

    # Draining state
    shutdown_requested: bool = field(default=False)

    # Last update timestamps (for staleness detection)
    last_db_check: float = field(default=0.0)
    last_rpc_check: float = field(default=0.0)
    last_workers_check: float = field(default=0.0)

    # Thread safety
    _lock: Lock = field(default_factory=Lock, repr=False)

    def update_db(self, ok: bool) -> None:
        """Update database health state."""
        with self._lock:
            self.db_ok = ok
            self.last_db_check = time.time()

    def update_rpc(self, ok: bool) -> None:
        """Update RPC health state."""
        with self._lock:
            self.rpc_ok = ok
            self.last_rpc_check = time.time()

    def update_workers(self, threads: list["Thread"]) -> None:
        """Update worker health state.

        Args:
            threads: List of worker threads
        """
        with self._lock:
            self.workers_ok = any(t.is_alive() for t in threads) if threads else False
            self.last_workers_check = time.time()

    def request_shutdown(self) -> None:
        """Mark the system as draining.

        Call this at the start of graceful shutdown.
        /readyz will return 503 immediately.
        """
        with self._lock:
            self.shutdown_requested = True

    def is_ready(self) -> bool:
        """Check if the system is ready to accept work.

        Returns:
            True if ready, False if not ready (should return 503)
        """
        with self._lock:
            if self.shutdown_requested:
                return False
            if not self.db_ok:
                return False
            if not self.rpc_ok:
                return False
            if not self.workers_ok:
                return False
            return True

    def readiness_reasons(self) -> list[str]:
        """Get human-readable reasons for not being ready.

        Useful for /healthz diagnostics.

        Returns:
            List of reasons why the system is not ready, empty if ready
        """
        reasons = []
        with self._lock:
            if self.shutdown_requested:
                reasons.append("shutdown_requested")
            if not self.db_ok:
                reasons.append("db_unhealthy")
            if not self.rpc_ok:
                reasons.append("rpc_unhealthy")
            if not self.workers_ok:
                reasons.append("no_workers_alive")
        return reasons

    def to_dict(self) -> dict[str, object]:
        """Get full health state as a dictionary.

        Useful for /healthz JSON response.
        """
        with self._lock:
            # Compute ready inline to avoid deadlock (is_ready also acquires lock)
            ready = (
                not self.shutdown_requested
                and self.db_ok
                and self.rpc_ok
                and self.workers_ok
            )
            return {
                "ready": ready,
                "shutdown_requested": self.shutdown_requested,
                "db_ok": self.db_ok,
                "rpc_ok": self.rpc_ok,
                "workers_ok": self.workers_ok,
                "last_db_check": self.last_db_check,
                "last_rpc_check": self.last_rpc_check,
                "last_workers_check": self.last_workers_check,
            }


# Global health state singleton
_health_state: HealthState | None = None
_health_state_lock = Lock()


def get_health_state() -> HealthState:
    """Get the global health state singleton.

    Creates the singleton on first access.
    """
    global _health_state
    with _health_state_lock:
        if _health_state is None:
            _health_state = HealthState()
        return _health_state


def reset_health_state() -> None:
    """Reset the global health state (for testing)."""
    global _health_state
    with _health_state_lock:
        _health_state = None
