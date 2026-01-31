"""Timeout budget helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Deadline:
    """Monotonic deadline with child budgets.

    Child deadlines may only consume remaining time; they never extend parents.
    """

    _deadline: float

    @classmethod
    def from_seconds(cls, seconds: float) -> "Deadline":
        """Create a deadline seconds from now."""
        now = time.monotonic()
        return cls(now + max(0.0, seconds))

    def remaining(self) -> float:
        """Return seconds remaining (clamped at 0)."""
        return max(0.0, self._deadline - time.monotonic())

    def expired(self) -> bool:
        """Return True if the deadline is exhausted."""
        return self.remaining() <= 0.0

    def child(self, seconds: float | None = None) -> "Deadline":
        """Create a child deadline bounded by this deadline."""
        now = time.monotonic()
        parent_deadline = self._deadline
        if seconds is None:
            return Deadline(parent_deadline)
        return Deadline(min(parent_deadline, now + max(0.0, seconds)))
