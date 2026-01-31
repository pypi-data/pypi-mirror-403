"""Runtime network guard for job execution contexts."""

from __future__ import annotations

import inspect
import socket
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from brawny.logging import get_logger
from brawny.metrics import get_metrics, NETWORK_GUARD_ALLOW, NETWORK_GUARD_VIOLATION


_guard_depth = 0
_guard_context_counts: dict[str, int] = {}
_guard_lock = threading.RLock()
_allow_network: ContextVar[bool] = ContextVar("brawny_allow_network", default=False)
_allow_reason: ContextVar[str | None] = ContextVar("brawny_allow_reason", default=None)
_patched = False

_ALLOWED_REASONS = frozenset({"rpc", "alerts", "approved_http_client"})

logger = get_logger(__name__)


def install_network_guard() -> None:
    """Install socket-level guard (idempotent)."""
    global _patched
    if _patched:
        return

    original_connect = socket.socket.connect
    original_create_connection = socket.create_connection

    def guarded_connect(sock: socket.socket, address: object) -> object:
        if _guard_is_active() and not _allow_network.get():
            _record_violation()
            raise RuntimeError(
                "Direct network call blocked. Use ctx.rpc or ctx.http (approved clients)."
            )
        return original_connect(sock, address)

    def guarded_create_connection(*args: object, **kwargs: object) -> socket.socket:
        if _guard_is_active() and not _allow_network.get():
            _record_violation()
            raise RuntimeError(
                "Direct network call blocked. Use ctx.rpc or ctx.http (approved clients)."
            )
        return original_create_connection(*args, **kwargs)

    socket.socket.connect = guarded_connect  # type: ignore[assignment]
    socket.create_connection = guarded_create_connection  # type: ignore[assignment]
    _patched = True


def _guard_is_active() -> bool:
    with _guard_lock:
        return _guard_depth > 0


def _current_context() -> str:
    with _guard_lock:
        if "job" in _guard_context_counts:
            return "job"
        if _guard_context_counts:
            return next(iter(_guard_context_counts.keys()))
    return "unknown"


def _caller_module() -> str:
    for frame_info in inspect.stack()[2:]:
        module = inspect.getmodule(frame_info.frame)
        if module is None:
            continue
        name = module.__name__
        if name.startswith(("socket", "httpx", "requests", "urllib", "ssl", "asyncio")):
            continue
        if name.startswith("brawny"):
            continue
        return name
    return "unknown"


def _record_violation() -> None:
    metrics = get_metrics()
    metrics.counter(NETWORK_GUARD_VIOLATION).inc(
        context=_current_context(),
        caller_module=_caller_module(),
    )
    logger.warning(
        "network_guard.violation",
        context=_current_context(),
        caller_module=_caller_module(),
    )


@contextmanager
def job_network_guard(context: str = "job") -> Iterator[None]:
    """Enable network guard within a job execution context."""
    install_network_guard()
    with _guard_lock:
        global _guard_depth
        _guard_depth += 1
        _guard_context_counts[context] = _guard_context_counts.get(context, 0) + 1
    try:
        yield
    finally:
        with _guard_lock:
            current = _guard_context_counts.get(context, 0)
            if current <= 1:
                _guard_context_counts.pop(context, None)
            else:
                _guard_context_counts[context] = current - 1
            _guard_depth -= 1


@contextmanager
def allow_network_calls(reason: str) -> Iterator[None]:
    """Temporarily allow network calls within a guarded context."""
    if reason not in _ALLOWED_REASONS:
        raise ValueError(f"Invalid allow_network reason: {reason}")
    metrics = get_metrics()
    metrics.counter(NETWORK_GUARD_ALLOW).inc(reason=reason)
    logger.debug("network_guard.allow", reason=reason)
    token = _allow_network.set(True)
    reason_token = _allow_reason.set(reason)
    try:
        yield
    finally:
        _allow_reason.reset(reason_token)
        _allow_network.reset(token)
