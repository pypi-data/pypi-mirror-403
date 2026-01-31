from __future__ import annotations

import sqlite3
import time
from typing import Any, Literal

from brawny.logging import get_logger
from brawny.model.errors import DatabaseError


FetchMode = Literal["none", "all", "one", "rowcount"]
logger = get_logger("brawny.db.sqlite")


def _run(
    db: Any,
    query: str,
    params: tuple[Any, ...] | dict[str, Any] | None,
    *,
    fetch: FetchMode,
    commit: bool,
) -> Any:
    max_retries = 5
    backoff = 0.05
    attempt = 0

    while True:
        conn = db._ensure_connected()
        db._circuit_breaker.before_call()

        locked_error: sqlite3.OperationalError | None = None
        with db._locked():
            cursor = conn.cursor()
            try:
                if params is None:
                    cursor.execute(query)
                elif isinstance(params, dict):
                    cursor.execute(query, params)
                else:
                    cursor.execute(query, params)

                if fetch == "all":
                    rows = cursor.fetchall()
                    result: Any = [dict(row) for row in rows] if rows else []
                elif fetch == "one":
                    row = cursor.fetchone()
                    result = dict(row) if row else None
                elif fetch == "rowcount":
                    result = cursor.rowcount
                else:
                    result = None

                if commit and db._tx_depth == 0:
                    conn.commit()
                db._circuit_breaker.record_success()
                return result
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower():
                    locked_error = e
                else:
                    db._circuit_breaker.record_failure(e)
                    raise DatabaseError(f"SQLite query failed: {e}") from e
            except sqlite3.Error as e:
                db._circuit_breaker.record_failure(e)
                raise DatabaseError(f"SQLite query failed: {e}") from e
            finally:
                cursor.close()

        if locked_error is not None:
            if db._tx_depth > 0:
                db._circuit_breaker.record_failure(locked_error)
                raise DatabaseError(f"SQLite query failed: {locked_error}") from locked_error
            attempt += 1
            if attempt <= max_retries:
                logger.debug(
                    "sqlite.lock_retry",
                    attempt=attempt,
                    backoff_seconds=backoff,
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 0.2)
                continue
            db._circuit_breaker.record_failure(locked_error)
            raise DatabaseError(f"SQLite query failed: {locked_error}") from locked_error


def execute(
    db: Any,
    query: str,
    params: tuple[Any, ...] | dict[str, Any] | None = None,
) -> None:
    _run(db, query, params, fetch="none", commit=True)


def execute_returning(
    db: Any,
    query: str,
    params: tuple[Any, ...] | dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return _run(db, query, params, fetch="all", commit=False)


def execute_one(
    db: Any,
    query: str,
    params: tuple[Any, ...] | dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    return _run(db, query, params, fetch="one", commit=False)


def execute_returning_rowcount(
    db: Any,
    query: str,
    params: tuple[Any, ...] | dict[str, Any] | None = None,
) -> int:
    return _run(db, query, params, fetch="rowcount", commit=True)
