"""Database layer with SQLite-only support."""

from brawny.db.base import (
    ABICacheEntry,
    BlockHashEntry,
    BlockState,
    Database,
    IsolationLevel,
    ProxyCacheEntry,
)
from brawny.db.migrate import Migrator, discover_migrations, get_pending_migrations
from brawny.db.sqlite import SQLiteDatabase
from brawny.db.serialized import SerializedDatabase

__all__ = [
    # Base classes
    "Database",
    "IsolationLevel",
    # Data classes
    "BlockState",
    "BlockHashEntry",
    "ABICacheEntry",
    "ProxyCacheEntry",
    # Implementations
    "SQLiteDatabase",
    "SerializedDatabase",
    # Migration
    "Migrator",
    "discover_migrations",
    "get_pending_migrations",
    # Factory
    "create_database",
]


def create_database(database_url: str, **kwargs: object) -> Database:
    """Factory function to create a database instance based on URL.

    Args:
        database_url: Database connection URL (sqlite:///path/to/db.sqlite)
        **kwargs: Additional arguments passed to the database constructor

    Returns:
        Database instance (SQLiteDatabase)

    Raises:
        ValueError: If database URL scheme is not supported
    """
    circuit_breaker_failures = int(kwargs.pop("circuit_breaker_failures", 5))
    circuit_breaker_seconds = int(kwargs.pop("circuit_breaker_seconds", 30))
    production = kwargs.pop("production", False)
    read_only = kwargs.pop("read_only", False)
    if not isinstance(production, bool):
        raise ValueError("production must be a boolean")
    if not isinstance(read_only, bool):
        raise ValueError("read_only must be a boolean")
    if database_url.startswith("sqlite:///"):
        kwargs.pop("db_op_timeout_seconds", None)
        kwargs.pop("db_busy_retries", None)
        kwargs.pop("db_busy_backoff_seconds", None)
        return SerializedDatabase(
            SQLiteDatabase(
                database_url,
                circuit_breaker_failures=circuit_breaker_failures,
                circuit_breaker_seconds=circuit_breaker_seconds,
                production=production,
                read_only=read_only,
            )
        )
    else:
        raise ValueError(
            f"Unsupported database URL: {database_url}. "
            "Must start with 'sqlite:///'"
        )
