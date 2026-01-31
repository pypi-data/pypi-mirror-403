"""Heartbeat-based liveness for brawny.

Liveness is NOT "can we respond to HTTP?" - it's "is the core loop making progress?"

The Heartbeat class tracks when critical loops last made progress.
/livez returns 503 when the heartbeat is stale (no progress in 30s).

See LOGGING_METRICS_PLAN.md Section 4.1.2 for design rationale.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Heartbeat:
    """Track liveness of a critical loop.

    A heartbeat is considered stale if beat() hasn't been called within
    max_age_seconds. This indicates the loop is stuck or deadlocked.

    Thread-safe: beat() and is_stale() can be called from different threads.

    Usage:
        heartbeat = Heartbeat()

        # In the critical loop
        while not stop_event.is_set():
            heartbeat.beat()
            # ... do work ...

        # In /livez endpoint
        if heartbeat.is_stale():
            return Response(status_code=503)
        return Response(status_code=200)
    """

    last_beat_ts: float = field(default=0.0)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def beat(self) -> None:
        """Record that the loop is making progress.

        Call this at the start of each loop iteration.
        """
        with self._lock:
            self.last_beat_ts = time.time()

    def is_stale(self, max_age_seconds: float = 30.0) -> bool:
        """Check if the heartbeat is stale.

        Args:
            max_age_seconds: Maximum allowed time since last beat.
                Default 30s is a reasonable choice for most loops.

        Returns:
            True if:
            - beat() was never called (last_beat_ts == 0.0), OR
            - More than max_age_seconds have passed since last beat
        """
        with self._lock:
            if self.last_beat_ts == 0.0:
                # Never started
                return True
            return (time.time() - self.last_beat_ts) > max_age_seconds

    def age_seconds(self) -> float:
        """Get the age of the last heartbeat in seconds.

        Returns:
            Seconds since last beat, or float('inf') if never beat.
        """
        with self._lock:
            if self.last_beat_ts == 0.0:
                return float("inf")
            return time.time() - self.last_beat_ts


# Global heartbeats for critical loops
_heartbeats: dict[str, Heartbeat] = {}
_heartbeats_lock = Lock()


def get_heartbeat(name: str) -> Heartbeat:
    """Get or create a named heartbeat.

    Use this to track different critical loops:
    - "block_poller" for the block processing loop
    - "monitor" for the transaction monitor loop

    Args:
        name: Identifier for the heartbeat

    Returns:
        The Heartbeat instance for this name
    """
    with _heartbeats_lock:
        if name not in _heartbeats:
            _heartbeats[name] = Heartbeat()
        return _heartbeats[name]


def any_stale(max_age_seconds: float = 30.0) -> bool:
    """Check if any registered heartbeat is stale.

    Use this in /livez to check overall system liveness.

    Args:
        max_age_seconds: Maximum allowed time since last beat

    Returns:
        True if any heartbeat is stale
    """
    with _heartbeats_lock:
        if not _heartbeats:
            # No heartbeats registered yet - system is starting up
            return False
        return any(hb.is_stale(max_age_seconds) for hb in _heartbeats.values())


def all_heartbeat_ages() -> dict[str, float]:
    """Get the age of all registered heartbeats.

    Useful for /healthz diagnostics endpoint.

    Returns:
        Dict mapping heartbeat name to age in seconds
    """
    with _heartbeats_lock:
        return {name: hb.age_seconds() for name, hb in _heartbeats.items()}
