"""Runtime controls with TTL caching."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from brawny.model.types import RuntimeControl
from brawny.metrics import RUNTIME_CONTROL_ACTIVE, RUNTIME_CONTROL_TTL_SECONDS, get_metrics

if TYPE_CHECKING:
    from brawny.db.base import Database


@dataclass
class _CachedControl:
    control: RuntimeControl | None
    expires_at: float


class RuntimeControls:
    """Cached runtime controls accessor."""

    def __init__(self, db: "Database", ttl_seconds: float = 2.0) -> None:
        self._db = db
        self._ttl_seconds = ttl_seconds
        self._lock = threading.RLock()
        self._cache: dict[str, _CachedControl] = {}

    def get(self, control: str) -> RuntimeControl | None:
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(control)
            if cached and cached.expires_at > now:
                return cached.control

        value = self._db.get_runtime_control(control)
        self._emit_metrics(control, value)
        with self._lock:
            self._cache[control] = _CachedControl(
                control=value,
                expires_at=now + self._ttl_seconds,
            )
        return value

    def is_active(self, control: str) -> bool:
        rc = self.get(control)
        if rc is None or not rc.active:
            return False
        if rc.expires_at is None:
            return True
        now = datetime.utcnow()
        if rc.expires_at.tzinfo is not None:
            now = datetime.now(rc.expires_at.tzinfo)
        return rc.expires_at > now

    def refresh(self, control: str) -> None:
        with self._lock:
            if control in self._cache:
                del self._cache[control]

    def _emit_metrics(self, control: str, rc: RuntimeControl | None) -> None:
        metrics = get_metrics()
        if rc is None:
            metrics.gauge(RUNTIME_CONTROL_ACTIVE).set(0, control=control)
            return
        metrics.gauge(RUNTIME_CONTROL_ACTIVE).set(1 if rc.active else 0, control=control)
        if rc.expires_at:
            now = datetime.utcnow()
            ttl = (rc.expires_at - now).total_seconds()
            metrics.gauge(RUNTIME_CONTROL_TTL_SECONDS).set(max(ttl, 0), control=control)
