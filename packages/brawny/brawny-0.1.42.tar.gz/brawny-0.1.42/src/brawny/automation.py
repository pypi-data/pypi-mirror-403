"""Automation gate for stopping scheduling when invariants break."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import TYPE_CHECKING

from brawny.metrics import AUTOMATION_ENABLED, get_metrics

if TYPE_CHECKING:
    from logging import Logger


@dataclass
class AutomationState:
    """In-memory automation gate with a single disable reason."""

    chain_id: int
    log: "Logger"

    def __post_init__(self) -> None:
        self._lock = Lock()
        self._enabled = True
        self._disabled_reason: str | None = None
        self._disabled_at: datetime | None = None
        get_metrics().gauge(AUTOMATION_ENABLED).set(1, chain_id=self.chain_id)

    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def status(self) -> tuple[bool, str | None, datetime | None]:
        with self._lock:
            return self._enabled, self._disabled_reason, self._disabled_at

    def disable(self, reason: str, *, source: str | None = None, detail: str | None = None) -> bool:
        """Disable automation. Returns True if state changed."""
        with self._lock:
            if not self._enabled:
                return False
            self._enabled = False
            self._disabled_reason = reason
            self._disabled_at = datetime.now(timezone.utc)
            disabled_at = self._disabled_at

        get_metrics().gauge(AUTOMATION_ENABLED).set(0, chain_id=self.chain_id)
        self.log.error(
            "automation.disabled",
            chain_id=self.chain_id,
            reason=reason,
            source=source,
            detail=detail,
            disabled_at=disabled_at.isoformat() if disabled_at else None,
        )
        return True
