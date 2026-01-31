from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Iterator

from brawny.model.errors import DatabaseError


class SerializedDatabase:
    """Serialize all DB access with a single process-wide lock."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._lock = threading.RLock()
        self._closed = False

    @property
    def dialect(self) -> str:
        return self._inner.dialect

    def _ensure_open(self) -> None:
        if self._closed:
            raise DatabaseError("Database is closed")

    def connect(self) -> None:
        self._ensure_open()
        with self._lock:
            self._ensure_open()
            self._inner.connect()

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._inner.close()
                self._closed = True

    def is_connected(self) -> bool:
        if self._closed:
            return False
        with self._lock:
            return self._inner.is_connected()

    @contextmanager
    def transaction(self, isolation_level: str | None = None) -> Iterator[None]:
        self._ensure_open()
        with self._lock:
            self._ensure_open()
            with self._inner.transaction(isolation_level):
                yield

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr

        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            self._ensure_open()
            with self._lock:
                self._ensure_open()
                return attr(*args, **kwargs)

        return _wrapped
