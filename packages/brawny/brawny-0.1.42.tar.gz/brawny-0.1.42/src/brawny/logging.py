"""Structured logging for brawny.

Provides JSON-formatted logs with correlation IDs for request tracing.
"""

from __future__ import annotations

import logging
import re
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Literal

import structlog

from brawny.logging_types import LogFormat

# Module-level state for mode switching
_runtime_log_level: str = "INFO"
_runtime_log_format: LogFormat = LogFormat.JSON
_runtime_chain_id: int | None = None

# Context variable for correlation ID propagation
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """Get the current correlation ID or generate a new one."""
    cid = _correlation_id.get()
    if cid is None:
        cid = generate_correlation_id()
        _correlation_id.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    _correlation_id.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def add_correlation_id(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Processor to add correlation_id to log entries."""
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Processor to add ISO8601 timestamp to log entries."""
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def rename_event_to_event_key(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Rename 'event' to match our log format."""
    # structlog uses 'event' by default, we keep it
    return event_dict


def add_log_level(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add uppercase log level."""
    event_dict["level"] = method_name.upper()
    return event_dict


_URL_CRED_RE = re.compile(r"(https?://)([^/@\s]+):([^/@\s]+)@")


def _redact_url_creds(value: str) -> str:
    return _URL_CRED_RE.sub(r"\1***@", value)


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_url_creds(value)
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_lower = str(key).lower()
            if key_lower in {"authorization", "proxy-authorization"}:
                redacted[key] = "***"
            else:
                redacted[key] = _redact_value(item)
        return redacted
    if isinstance(value, (list, tuple)):
        return type(value)(_redact_value(item) for item in value)
    return value


def redact_sensitive(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Redact credentials or auth tokens from log fields."""
    return {key: _redact_value(value) for key, value in event_dict.items()}


def setup_logging(
    log_level: str = "INFO",
    log_format: LogFormat = LogFormat.JSON,
    chain_id: int | None = None,
    mode: Literal["startup", "runtime"] = "runtime",
) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format (json or text)
        chain_id: Chain ID to include in all log entries
        mode: "startup" uses human-readable ConsoleRenderer with WARNING level,
              "runtime" uses configured format and level
    """
    global _runtime_log_level, _runtime_log_format, _runtime_chain_id

    # Store runtime config for later switch
    _runtime_log_level = log_level
    _runtime_log_format = log_format
    _runtime_chain_id = chain_id

    # Startup mode: only show warnings/errors, human-readable format
    effective_level = "WARNING" if mode == "startup" else log_level

    # Set up stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, effective_level.upper()),
        force=True,  # Allow reconfiguration
    )

    # Suppress noisy HTTP client logs (they can leak tokens in URLs)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("web3").setLevel(logging.WARNING)

    # Common processors
    processors: list[structlog.types.Processor] = [
        structlog.stdlib.filter_by_level,
        add_timestamp,
        add_log_level,
        add_correlation_id,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.format_exc_info,
        redact_sensitive,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Add chain_id to all log entries if provided
    if chain_id is not None:

        def add_chain_id(
            logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
        ) -> dict[str, Any]:
            event_dict.setdefault("chain_id", chain_id)
            return event_dict

        processors.insert(3, add_chain_id)

    # Choose renderer based on mode
    if mode == "startup":
        # Human-friendly with colors for startup warnings/errors
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    elif log_format == LogFormat.JSON:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,  # Allow reconfiguration
    )


def set_runtime_logging() -> None:
    """Switch from startup mode to runtime mode.

    Call after "--- Starting brawny ---" to enable full structured logging.
    """
    setup_logging(_runtime_log_level, _runtime_log_format, _runtime_chain_id, mode="runtime")


def get_logger(name: str | None = None, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually module name)
        **initial_context: Initial context to bind to the logger

    Returns:
        Bound logger instance
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


def log_unexpected(logger: structlog.stdlib.BoundLogger, event: str, **context: Any) -> None:
    """Log an unexpected exception with stack trace."""
    logger.error(event, exc_info=True, **context)


class LogContext:
    """Context manager for scoped logging context."""

    def __init__(self, **context: Any) -> None:
        self._context = context
        self._token: Any = None

    def __enter__(self) -> LogContext:
        # Generate correlation ID if not present
        if "correlation_id" not in self._context:
            cid = generate_correlation_id()
            self._context["correlation_id"] = cid
            set_correlation_id(cid)
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    @property
    def correlation_id(self) -> str:
        """Get the correlation ID for this context."""
        return self._context.get("correlation_id", get_correlation_id())


# Pre-defined log event names per SPEC §11
class LogEvents:
    """Standard log event names."""

    # Block processing
    BLOCK_INGEST_START = "block.ingest.start"
    BLOCK_INGEST_DONE = "block.ingest.done"
    BLOCK_REORG_DETECTED = "block.reorg.detected"
    BLOCK_REORG_REWIND = "block.reorg.rewind"
    BLOCK_REORG_DEEP = "block.reorg.deep"

    # Job execution
    JOB_CHECK_START = "job.check.start"
    JOB_CHECK_SKIP = "job.check.skip"
    JOB_CHECK_TRIGGERED = "job.check.triggered"
    JOB_CHECK_TIMEOUT = "job.check.timeout"

    # Intent lifecycle
    INTENT_CREATE = "intent.create"
    INTENT_DEDUPE = "intent.dedupe"
    INTENT_CLAIM = "intent.claim"
    INTENT_STATUS = "intent.status"
    INTENT_REORG = "intent.reorg"

    # Nonce management
    NONCE_RESERVE = "nonce.reserve"
    NONCE_RECONCILE = "nonce.reconcile"
    NONCE_ORPHANED = "nonce.orphaned"

    # Transaction lifecycle
    TX_SIGN = "tx.sign"
    TX_BROADCAST = "tx.broadcast"
    TX_PENDING = "tx.pending"
    TX_CONFIRMED = "tx.confirmed"
    TX_FAILED = "tx.failed"
    TX_REPLACED = "tx.replaced"
    TX_ABANDONED = "tx.abandoned"

    # Alerts
    ALERT_SEND = "alert.send"
    ALERT_ERROR = "alert.error"

    # RPC
    RPC_REQUEST = "rpc.request"
    RPC_ERROR = "rpc.error"
    RPC_ALL_ENDPOINTS_FAILED = "rpc.all_endpoints_failed"

    # Shutdown
    SHUTDOWN_INITIATED = "shutdown.initiated"
    SHUTDOWN_COMPLETE = "shutdown.complete"
