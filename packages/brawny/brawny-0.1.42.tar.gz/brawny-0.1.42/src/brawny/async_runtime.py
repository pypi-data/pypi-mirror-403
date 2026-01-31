"""Async runtime boundary helpers.

Provides a single owned event loop and safe sync/async adapters.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Coroutine, TypeVar

T = TypeVar("T")

_loop: asyncio.AbstractEventLoop | None = None
_loop_thread_id: int | None = None
_lock = threading.Lock()


def register_loop(loop: asyncio.AbstractEventLoop, loop_thread_id: int) -> None:
    """Register the owned event loop and its thread id."""
    global _loop, _loop_thread_id
    with _lock:
        _loop = loop
        _loop_thread_id = loop_thread_id


def clear_loop() -> None:
    """Clear the owned event loop (shutdown)."""
    global _loop, _loop_thread_id
    with _lock:
        _loop = None
        _loop_thread_id = None


def run_sync(coro: Coroutine[object, object, T]) -> T:
    """Run a coroutine on the owned loop from sync code."""
    loop = _loop
    if loop is None:
        raise RuntimeError("run_sync called before the async loop is registered")
    if _loop_thread_id is not None and threading.get_ident() == _loop_thread_id:
        raise RuntimeError("Called run_sync from the loop thread — await the coroutine instead.")
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


async def to_thread(func, /, *args, **kwargs):
    """Run sync work in a worker thread from async code."""
    return await asyncio.to_thread(func, *args, **kwargs)
