"""Structured logging gateway for brawny.

The emit() function is the single enforcement choke point for all logging.
It validates event/result pairs, normalizes error fields, and controls trace inclusion.

See LOGGING_METRICS_PLAN.md for design rationale.
"""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from typing import Any

# Run ID for correlating logs across restarts
RUN_ID = os.environ.get("BRAWNY_RUN_ID") or f"run_{uuid.uuid4().hex[:12]}"

# Allowed event families and their valid results
# Any (event, result) pair not in this dict will raise ValueError
ALLOWED: dict[str, set[str]] = {
    "job.check": {"triggered", "skipped", "timeout", "error"},
    "intent": {"created", "claimed", "executed", "failed", "status"},
    "tx": {"signed", "broadcast", "confirmed", "failed", "replaced"},
    "rpc": {"ok", "error", "timeout"},
    "nonce": {"reserved", "released", "reconciled"},
    "block": {"processed", "reorg"},
    "system": {"started", "draining", "shutdown"},
}

# Error message truncation limit
ERROR_MESSAGE_MAX_LENGTH = 500


def emit(
    log: structlog.stdlib.BoundLogger,
    *,
    level: str,
    event: str,
    result: str,
    err: Exception | None = None,
    is_terminal: bool = False,
    **fields: Any,
) -> None:
    """Emit a structured log event.

    This is the single enforcement choke point for all logging in brawny.
    It validates event/result pairs, normalizes error fields, and controls
    stack trace inclusion.

    Args:
        log: Bound logger instance
        level: Log level ("debug", "info", "warning", "error")
        event: Event family (e.g., "tx", "intent", "job.check")
        result: Event result (e.g., "confirmed", "failed", "triggered")
        err: Optional exception for error events
        is_terminal: If True and err is provided, include stack trace
        **fields: Additional context fields

    Raises:
        ValueError: If (event, result) pair is not in ALLOWED

    Example:
        emit(log, level="info", event="tx", result="broadcast", tx_hash=hash)
        emit(log, level="error", event="tx", result="failed", err=e, is_terminal=True)
    """
    # Validate event/result pair
    if event not in ALLOWED:
        raise ValueError(f"Invalid event family: {event!r}. Must be one of: {sorted(ALLOWED.keys())}")
    if result not in ALLOWED[event]:
        raise ValueError(
            f"Invalid result {result!r} for event {event!r}. Must be one of: {sorted(ALLOWED[event])}"
        )

    # Normalize error fields
    if err is not None:
        msg = str(err)
        fields["error_type"] = type(err).__name__
        # Truncate long error messages
        if len(msg) > ERROR_MESSAGE_MAX_LENGTH:
            fields["error"] = msg[:ERROR_MESSAGE_MAX_LENGTH] + "..."
        else:
            fields["error"] = msg

    # Get the logging function for this level
    log_fn = getattr(log, level.lower())

    # Dispatch - exc_info must be a kwarg to logger, not a field
    if err is not None and is_terminal:
        log_fn(event, result=result, exc_info=True, **fields)
    else:
        log_fn(event, result=result, **fields)


def get_logger(**bind: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger with run_id bound.

    Use this at component boundaries to get a base logger.

    Args:
        **bind: Additional fields to bind (e.g., worker_id, chain_id)

    Returns:
        Bound logger with run_id and any additional fields

    Example:
        log = get_logger(worker_id=1, chain_id=1)
    """
    return structlog.get_logger("brawny").bind(run_id=RUN_ID, **bind)


def bind_intent(
    log: structlog.stdlib.BoundLogger,
    *,
    intent_id: str,
    job_id: str,
) -> structlog.stdlib.BoundLogger:
    """Bind intent context to a logger.

    Use when processing a specific intent.

    Args:
        log: Base logger
        intent_id: Intent UUID as string
        job_id: Job identifier

    Returns:
        Logger with intent context bound
    """
    return log.bind(intent_id=intent_id, job_id=job_id)


def bind_attempt(
    log: structlog.stdlib.BoundLogger,
    *,
    attempt_id: str,
    nonce: int | None = None,
) -> structlog.stdlib.BoundLogger:
    """Bind attempt context to a logger.

    Use when processing a specific transaction attempt.

    Args:
        log: Base logger (typically with intent context already bound)
        attempt_id: Attempt UUID as string
        nonce: Transaction nonce (optional, but include when known)

    Returns:
        Logger with attempt context bound
    """
    # Use 'is not None' to correctly handle nonce=0
    if nonce is not None:
        return log.bind(attempt_id=attempt_id, nonce=nonce)
    return log.bind(attempt_id=attempt_id)
