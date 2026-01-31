"""Job log operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from brawny.db import queries as Q

if TYPE_CHECKING:
    from brawny.db.base import Database

MAX_FIELDS_JSON_BYTES = 16_384  # 16KB cap


def insert_log(
    db: "Database",
    chain_id: int,
    job_id: str,
    block_number: int | None,
    level: str,
    fields: dict[str, Any],
) -> None:
    """Insert a job log entry.

    Payload is capped at 16KB. Oversized payloads are truncated with a marker.
    Timestamp is set by DB (DEFAULT CURRENT_TIMESTAMP).
    """
    fields_json = json.dumps(fields, default=str)

    if len(fields_json) > MAX_FIELDS_JSON_BYTES:
        fields_json = json.dumps({"_truncated": True, "_original_size": len(fields_json)})

    db.execute(Q.INSERT_JOB_LOG, {
        "chain_id": chain_id,
        "job_id": job_id,
        "block_number": block_number,
        "level": level,
        "fields_json": fields_json,
    })


def list_logs(
    db: "Database",
    chain_id: int,
    job_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List recent logs for a job."""
    rows = db.execute_returning(Q.LIST_JOB_LOGS, {
        "chain_id": chain_id,
        "job_id": job_id,
        "limit": limit,
    })
    return [_row_to_log(row) for row in rows]


def list_all_logs(
    db: "Database",
    chain_id: int,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List recent logs across all jobs."""
    rows = db.execute_returning(Q.LIST_ALL_JOB_LOGS, {
        "chain_id": chain_id,
        "limit": limit,
    })
    return [_row_to_log(row) for row in rows]


def list_latest_logs(db: "Database", chain_id: int) -> list[dict[str, Any]]:
    """Get the most recent log entry per job."""
    rows = db.execute_returning(Q.LIST_LATEST_JOB_LOGS, {"chain_id": chain_id})
    return [_row_to_log(row) for row in rows]


def delete_old_logs(db: "Database", chain_id: int, cutoff: datetime) -> int:
    """Delete logs older than cutoff for a chain. Returns count deleted."""
    return db.execute_returning_rowcount(Q.DELETE_OLD_JOB_LOGS, {
        "chain_id": chain_id,
        "cutoff": cutoff,
    })


def _row_to_log(row: dict[str, Any]) -> dict[str, Any]:
    """Convert DB row to log dict."""
    return {
        "id": row["id"],
        "chain_id": row["chain_id"],
        "job_id": row["job_id"],
        "block_number": row["block_number"],
        "ts": row["ts"],
        "level": row["level"],
        "fields": json.loads(row["fields_json"]),
    }
