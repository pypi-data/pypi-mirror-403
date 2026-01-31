from __future__ import annotations

from typing import Any

from brawny.tx.stages.types import RetryDecision


def decide(stage: str, error: Exception | None, attempt_state: dict[str, Any] | None = None) -> RetryDecision | None:
    """Return a retry decision for a stage+error.

    This is intentionally conservative; a None return means fail.
    """
    if error is None:
        return None

    # Default: retry with backoff handled by executor scheduling.
    return RetryDecision(
        retry_in_seconds=None,
        same_endpoint=True,
        rotate_endpoint=False,
        increase_fees=False,
        max_attempts_key=stage,
        reason=type(error).__name__,
    )
