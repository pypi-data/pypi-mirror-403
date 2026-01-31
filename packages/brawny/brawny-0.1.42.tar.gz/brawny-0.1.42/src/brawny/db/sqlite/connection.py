from __future__ import annotations

import os
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - non-Unix platforms
    fcntl = None  # type: ignore

import threading

from brawny.logging import get_logger
from brawny.model.errors import DatabaseError

logger = get_logger("brawny.db.sqlite")


def connect(db: Any) -> None:
    if db._closed:
        raise DatabaseError("Database is closed")
    if db._connected:
        return

    lock_acquired = False
    conn = None
    try:
        if db._database_path != ":memory:":
            path = Path(db._database_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            _assert_local_filesystem(path, production=db._production)
            if not getattr(db, "_read_only", False):
                _acquire_db_lock(db, path)
                lock_acquired = True

        db._closed = False
        conn = _open_connection(db)
        db._connected = True
        journal_mode_row = conn.execute("PRAGMA journal_mode").fetchone()
        journal_mode = journal_mode_row[0] if journal_mode_row else "unknown"
        logger.info("sqlite.journal_mode", mode=str(journal_mode).lower())
    except BaseException:
        if conn is not None:
            close_current_thread_conn(db)
        db._connected = False
        if lock_acquired and db._lock_handle is not None:
            try:
                if fcntl is not None:
                    fcntl.flock(db._lock_handle.fileno(), fcntl.LOCK_UN)
            finally:
                db._lock_handle.close()
                db._lock_handle = None
                if db._lock_path is not None:
                    try:
                        db._lock_path.unlink(missing_ok=True)
                    except OSError:
                        logger.error(
                            "sqlite.lock_cleanup_failed",
                            path=str(db._lock_path),
                            exc_info=True,
                        )
                    db._lock_path = None
        raise


def close(db: Any) -> None:
    if db._closed:
        return
    db._closed = True
    db._connected = False
    close_current_thread_conn(db)
    _warn_other_thread_conns(db)
    with db._conns_lock:
        db._conn_generation += 1
        db._memory_owner_thread_id = None
        db._warned_other_thread_conns = False
    _clear_thread_local_conn(db)

    if db._lock_handle is not None:
        try:
            if fcntl is not None:
                fcntl.flock(db._lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            db._lock_handle.close()
            db._lock_handle = None
            if db._lock_path is not None:
                try:
                    db._lock_path.unlink(missing_ok=True)
                except OSError:
                    pass
                db._lock_path = None


def is_connected(db: Any) -> bool:
    return db._connected and not db._closed


def ensure_connected(db: Any) -> sqlite3.Connection:
    if db._closed:
        raise DatabaseError("Database is closed")
    if not db._connected:
        raise DatabaseError("Database not connected. Call connect() first.")
    conn = getattr(db._thread_local, "conn", None)
    generation = getattr(db._thread_local, "generation", None)
    if conn is not None and generation == db._conn_generation:
        return conn
    return _open_connection(db)


def _open_connection(db: Any) -> sqlite3.Connection:
    if db._database_path == ":memory:":
        current_thread_id = threading.get_ident()
        owner_thread_id = db._memory_owner_thread_id
        if owner_thread_id is None:
            db._memory_owner_thread_id = current_thread_id
        elif owner_thread_id != current_thread_id:
            raise DatabaseError(
                "SQLite in-memory databases cannot be shared across threads. "
                f"path={db._database_path} owner_thread_id={owner_thread_id} "
                f"current_thread_id={current_thread_id}"
            )
    database_path = db._database_path
    read_only = getattr(db, "_read_only", False)
    if read_only and database_path != ":memory:":
        database_path = f"file:{database_path}?mode=ro"
    conn = sqlite3.connect(
        database_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        check_same_thread=True,
        timeout=30.0,
        uri=read_only,
    )
    conn.row_factory = sqlite3.Row
    _assert_minimum_sqlite_version(db)
    conn.execute("PRAGMA foreign_keys = ON")
    if not read_only:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    if not read_only:
        conn.execute("PRAGMA temp_store = MEMORY")
    current_thread_id = threading.get_ident()
    db._thread_local.conn = conn
    db._thread_local.generation = db._conn_generation
    db._thread_local.owner_thread_id = current_thread_id
    _record_conn_open(db, current_thread_id)
    return conn


def close_current_thread_conn(db: Any) -> None:
    conn = getattr(db._thread_local, "conn", None)
    if conn is None:
        return
    owner_thread_id = getattr(db._thread_local, "owner_thread_id", None)
    current_thread_id = threading.get_ident()
    if owner_thread_id is not None and owner_thread_id != current_thread_id:
        logger.warning(
            "sqlite.close_wrong_thread",
            owner_thread_id=owner_thread_id,
            current_thread_id=current_thread_id,
        )
        return
    try:
        conn.close()
    except Exception:
        # RECOVERABLE close failures should not crash shutdown.
        logger.error(
            "sqlite.close_failed",
            thread_id=current_thread_id,
            exc_info=True,
        )
    _record_conn_closed(db, current_thread_id)
    _clear_thread_local_conn(db)


def _clear_thread_local_conn(db: Any) -> None:
    if isinstance(db._thread_local, threading.local):
        if hasattr(db._thread_local, "conn"):
            try:
                del db._thread_local.conn
            except Exception:
                # RECOVERABLE cleanup failures are logged for investigation.
                logger.error("sqlite.thread_local_cleanup_failed", field="conn", exc_info=True)
        if hasattr(db._thread_local, "generation"):
            try:
                del db._thread_local.generation
            except Exception:
                # RECOVERABLE cleanup failures are logged for investigation.
                logger.error("sqlite.thread_local_cleanup_failed", field="generation", exc_info=True)
        if hasattr(db._thread_local, "owner_thread_id"):
            try:
                del db._thread_local.owner_thread_id
            except Exception:
                # RECOVERABLE cleanup failures are logged for investigation.
                logger.error("sqlite.thread_local_cleanup_failed", field="owner_thread_id", exc_info=True)


def _record_conn_open(db: Any, thread_id: int) -> None:
    with db._conns_lock:
        meta = db._conns.get(thread_id)
        if meta and meta.get("is_closed"):
            db._conns.pop(thread_id, None)
        db._conns[thread_id] = {
            "thread_id": thread_id,
            "created_at": time.time(),
            "is_closed": False,
        }


def _record_conn_closed(db: Any, thread_id: int) -> None:
    with db._conns_lock:
        meta = db._conns.get(thread_id)
        if meta:
            meta["is_closed"] = True
            meta["closed_at"] = time.time()


def _warn_other_thread_conns(db: Any) -> None:
    with db._conns_lock:
        remaining = sum(1 for meta in db._conns.values() if not meta.get("is_closed"))
    if remaining > 0 and not db._warned_other_thread_conns:
        logger.warning(
            "sqlite.other_thread_conns_open",
            count=remaining,
        )
        db._warned_other_thread_conns = True


def _assert_minimum_sqlite_version(db: Any) -> None:
    if db._version_checked:
        return
    minimum = (3, 35, 0)
    current = sqlite3.sqlite_version_info
    if current < minimum:
        raise DatabaseError(
            "SQLite >= 3.35 is required (for RETURNING support); "
            f"found {sqlite3.sqlite_version}"
        )
    db._version_checked = True


def _acquire_db_lock(db: Any, db_path: Path) -> None:
    if fcntl is None:
        raise DatabaseError("SQLite runner lock requires fcntl (Unix-only).")

    lock_path = db_path.with_suffix(db_path.suffix + ".lock")
    lock_handle = lock_path.open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        lock_handle.seek(0)
        existing = lock_handle.read().strip()
        lock_handle.close()
        detail = f" Existing lock: {existing}" if existing else ""
        raise DatabaseError(
            f"Database lock already held for {db_path}.{detail}"
        ) from exc

    lock_handle.seek(0)
    lock_handle.truncate()
    lock_handle.write(f"{socket.gethostname()}:{os.getpid()}\n")
    lock_handle.flush()
    db._lock_handle = lock_handle
    db._lock_path = lock_path


def _assert_local_filesystem(db_path: Path, *, production: bool) -> None:
    expanded_path = db_path.expanduser()
    absolute_path = expanded_path.absolute()
    resolved_path = expanded_path.resolve(strict=False)
    check_path = resolved_path if resolved_path.exists() else resolved_path.parent
    mode = "prod" if production else "non-prod"

    if production and absolute_path != resolved_path:
        logger.error(
            "sqlite.db_path_symlinked",
            path=str(check_path),
            fs_type="symlink",
            original_path=str(absolute_path),
            resolved_path=str(resolved_path),
            mode=mode,
        )
        raise DatabaseError(
            "SQLite database path must not be a symlink in production. "
            f"path={absolute_path} resolved={resolved_path}"
        )

    fs_type = _detect_fs_type(check_path)
    fs_label = fs_type or "unknown"

    if fs_type is None:
        if production:
            logger.error(
                "sqlite.fs_type_unknown",
                path=str(check_path),
                fs_type=fs_label,
                mode=mode,
                decision="deny",
            )
            raise DatabaseError(
                f"SQLite database filesystem type unknown at {check_path} (mode={mode})"
            )
        logger.warning(
            "sqlite.fs_type_unknown",
            path=str(check_path),
            fs_type=fs_label,
            mode=mode,
            decision="allow",
            hint="Ensure the database is on a local filesystem (no NFS/SMB).",
        )
        return

    fs_type_lower = fs_type.lower()
    network_fs = {"nfs", "nfs4", "smbfs", "cifs", "afpfs", "fuse.sshfs", "sshfs"}
    if fs_type_lower in network_fs:
        if production:
            logger.error(
                "sqlite.fs_network_filesystem",
                path=str(check_path),
                fs_type=fs_type,
                mode=mode,
                decision="deny",
            )
            raise DatabaseError(
                f"SQLite database must be on a local filesystem; detected {fs_type} at {check_path}"
            )
        logger.warning(
            "sqlite.fs_network_filesystem",
            path=str(check_path),
            fs_type=fs_type,
            mode=mode,
            decision="allow",
        )
        return

    logger.info(
        "sqlite.fs_check_ok",
        path=str(check_path),
        fs_type=fs_type,
        mode=mode,
        decision="allow",
    )


def _detect_fs_type(db_path: Path) -> str | None:
    try:
        if sys.platform == "darwin":
            output = subprocess.check_output(["stat", "-f", "%T", str(db_path)])
            return output.decode().strip()
        if sys.platform.startswith("linux"):
            output = subprocess.check_output(
                ["stat", "-f", "-c", "%T", str(db_path)]
            )
            return output.decode().strip()
    except Exception:
        # RECOVERABLE filesystem type detection is best-effort.
        logger.error("sqlite.fs_type_detect_failed", path=str(db_path), exc_info=True)
        return None
    return None
