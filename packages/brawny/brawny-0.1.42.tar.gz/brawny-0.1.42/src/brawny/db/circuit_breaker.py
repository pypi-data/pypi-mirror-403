"""Database circuit breaker for outage protection."""

from __future__ import annotations

import time
from dataclasses import dataclass

from brawny.logging import get_logger
from brawny.metrics import (
    DB_CIRCUIT_BREAKER_OPEN,
    DB_CIRCUIT_BREAKER_STATE,
    get_metrics,
)
from brawny.model.errors import DatabaseCircuitBreakerOpenError

logger = get_logger(__name__)


@dataclass
class CircuitBreakerState:
    consecutive_failures: int = 0
    open_until: float | None = None
    alert_sent: bool = False


class DatabaseCircuitBreaker:
    """Simple circuit breaker for database operations."""

    def __init__(
        self,
        failure_threshold: int,
        open_seconds: int,
        backend: str,
    ) -> None:
        self._failure_threshold = max(1, failure_threshold)
        self._open_seconds = max(1, open_seconds)
        self._backend = backend
        self._state = CircuitBreakerState()

    def before_call(self) -> None:
        """Raise if breaker is open."""
        if self._is_open():
            raise DatabaseCircuitBreakerOpenError(
                "Database circuit breaker is open."
            )

    def record_success(self) -> None:
        """Reset breaker on successful call."""
        if self._state.consecutive_failures or self._state.open_until is not None:
            metrics = get_metrics()
            metrics.gauge(DB_CIRCUIT_BREAKER_STATE).set(
                0,
                db_backend=self._backend,
            )
        self._state.consecutive_failures = 0
        self._state.open_until = None
        self._state.alert_sent = False

    def record_failure(self, error: Exception) -> None:
        """Record a failed DB call and open breaker if threshold is reached."""
        self._state.consecutive_failures += 1
        if self._state.consecutive_failures < self._failure_threshold:
            return

        now = time.time()
        if self._state.open_until and now < self._state.open_until:
            return

        self._state.open_until = now + self._open_seconds
        metrics = get_metrics()
        metrics.counter(DB_CIRCUIT_BREAKER_OPEN).inc(
            db_backend=self._backend,
        )
        metrics.gauge(DB_CIRCUIT_BREAKER_STATE).set(
            1,
            db_backend=self._backend,
        )

        if not self._state.alert_sent:
            logger.error(
                "db.circuit_breaker.open",
                db_backend=self._backend,
                failure_threshold=self._failure_threshold,
                open_seconds=self._open_seconds,
                error=str(error)[:200],
            )
            self._state.alert_sent = True

    def _is_open(self) -> bool:
        if self._state.open_until is None:
            return False
        if time.time() >= self._state.open_until:
            self._state.open_until = None
            self._state.consecutive_failures = 0
            self._state.alert_sent = False
            return False
        return True
