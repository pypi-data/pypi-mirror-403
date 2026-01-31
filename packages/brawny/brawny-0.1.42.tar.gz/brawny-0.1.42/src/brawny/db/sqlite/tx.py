from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from enum import Enum
from typing import Any, Iterator

from brawny.db.base import IsolationLevel
from brawny.model.errors import DatabaseError, TransactionFailed


class SQLiteBeginMode(str, Enum):
    DEFERRED = "DEFERRED"
    IMMEDIATE = "IMMEDIATE"
    EXCLUSIVE = "EXCLUSIVE"


def _resolve_begin_cmd(isolation_level: IsolationLevel | SQLiteBeginMode | None) -> str:
    if isolation_level is None:
        return "BEGIN"
    if isinstance(isolation_level, SQLiteBeginMode):
        if isolation_level is SQLiteBeginMode.DEFERRED:
            return "BEGIN"
        return f"BEGIN {isolation_level.value}"
    if isinstance(isolation_level, str):
        mapping = {
            "READ UNCOMMITTED": "BEGIN",
            "READ COMMITTED": "BEGIN",
            "REPEATABLE READ": "BEGIN IMMEDIATE",
            "SERIALIZABLE": "BEGIN EXCLUSIVE",
        }
        if isolation_level not in mapping:
            raise DatabaseError(f"Unsupported isolation level: {isolation_level}")
        begin_cmd = mapping[isolation_level]
        import brawny.db.sqlite as sqlite_mod
        if not getattr(sqlite_mod, "_warned_generic_isolation", False):
            sqlite_mod._warned_generic_isolation = True
            sqlite_mod.logger.warning(
                "sqlite.isolation_level_mapped",
                isolation_level=isolation_level,
                begin_cmd=begin_cmd,
            )
        return begin_cmd
    raise DatabaseError(
        f"Unsupported isolation level type: {type(isolation_level).__name__}"
    )


def begin_transaction(db: Any, conn: sqlite3.Connection, begin_cmd: str) -> None:
    if db._tx_depth == 0:
        conn.execute(begin_cmd)
    db._tx_depth += 1


def commit_transaction(db: Any, conn: sqlite3.Connection) -> None:
    if db._tx_depth <= 0:
        raise DatabaseError("Commit requested with no active transaction")
    db._tx_depth -= 1
    if db._tx_depth != 0:
        return
    if db._tx_failed:
        if conn.in_transaction:
            conn.rollback()
        db._tx_failed = False
        raise TransactionFailed("Transaction rolled back due to earlier error")
    conn.commit()


def rollback_transaction(db: Any, conn: sqlite3.Connection) -> None:
    if db._tx_depth <= 0:
        return
    db._tx_depth -= 1
    if not db._tx_failed:
        db._tx_failed = True
        if conn.in_transaction:
            conn.rollback()
    if db._tx_depth == 0:
        db._tx_failed = False


@contextmanager
def transaction(
    db: Any, isolation_level: IsolationLevel | SQLiteBeginMode | None = None
) -> Iterator[None]:
    """Context manager for database transactions.

    SQLite uses BEGIN modes: DEFERRED, IMMEDIATE, EXCLUSIVE.
    """
    begin_cmd = _resolve_begin_cmd(isolation_level)

    with db._locked():
        conn = db._ensure_connected()
        begin_transaction(db, conn, begin_cmd)
        try:
            yield
        except BaseException:
            rollback_transaction(db, conn)
            raise
        else:
            commit_transaction(db, conn)


@contextmanager
def transaction_conn(
    db: Any, isolation_level: IsolationLevel | SQLiteBeginMode | None = None
) -> Iterator[sqlite3.Connection]:
    """Context manager for transaction with a connection handle."""
    begin_cmd = _resolve_begin_cmd(isolation_level)

    with db._locked():
        conn = db._ensure_connected()
        begin_transaction(db, conn, begin_cmd)
        try:
            yield conn
        except BaseException:
            rollback_transaction(db, conn)
            raise
        else:
            commit_transaction(db, conn)
