"""Persistent job key-value storage helpers.

KV protocols are type-enforced by phase:
- KVReader (read-only): BuildContext and AlertContext
- KVStore (read+write): CheckContext only
"""

from __future__ import annotations

from typing import Any, Protocol

from brawny.db.base import Database


class KVReader(Protocol):
    """Read-only KV access for build/alert phases."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from storage."""
        ...


class KVStore(KVReader, Protocol):
    """Read+write KV access for check phase only."""

    def set(self, key: str, value: Any) -> None:
        """Set a value in storage."""
        ...

    def delete(self, key: str) -> bool:
        """Delete a value from storage. Returns True if deleted."""
        ...


class InMemoryJobKVStore:
    """In-memory KV store for tests or fallback usage.

    Implements both KVStore and KVReader protocols.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the in-memory store."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the in-memory store."""
        self._data[key] = value

    def delete(self, key: str) -> bool:
        """Delete a value from the in-memory store."""
        return self._data.pop(key, None) is not None


class DatabaseJobKVReader:
    """Read-only job KV access backed by the database.

    Used for SuccessContext and FailureContext where writes are not allowed.
    """

    _MISSING = object()

    def __init__(self, db: Database, job_id: str) -> None:
        self._db = db
        self._job_id = job_id
        self._cache: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from persistent storage."""
        if key in self._cache:
            cached = self._cache[key]
            if cached is self._MISSING:
                return default
            return cached

        value = self._db.get_job_kv(self._job_id, key)
        if value is None:
            self._cache[key] = self._MISSING
            return default

        self._cache[key] = value
        return value


class DatabaseJobKVStore:
    """Job KV store backed by the database with a small read cache."""

    _MISSING = object()

    def __init__(self, db: Database, job_id: str) -> None:
        self._db = db
        self._job_id = job_id
        self._cache: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from persistent storage."""
        if key in self._cache:
            cached = self._cache[key]
            if cached is self._MISSING:
                return default
            return cached

        value = self._db.get_job_kv(self._job_id, key)
        if value is None:
            self._cache[key] = self._MISSING
            return default

        self._cache[key] = value
        return value

    def set(self, key: str, value: Any) -> None:
        """Persist a value and update the cache."""
        self._db.set_job_kv(self._job_id, key, value)
        self._cache[key] = value

    def delete(self, key: str) -> bool:
        """Delete a value from persistent storage."""
        deleted = self._db.delete_job_kv(self._job_id, key)
        if deleted:
            self._cache.pop(key, None)
        else:
            self._cache[key] = self._MISSING
        return deleted
