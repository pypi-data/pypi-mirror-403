from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from brawny.db.sqlite import mappers, tx
from brawny.model.types import JobConfig


def get_job(db: Any, job_id: str) -> JobConfig | None:
    row = db.execute_one("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    if not row:
        return None
    return mappers._row_to_job_config(row)


def get_enabled_jobs(db: Any) -> list[JobConfig]:
    rows = db.execute_returning(
        """
        SELECT * FROM jobs
        WHERE enabled = 1
          AND (drain_until IS NULL OR drain_until <= CURRENT_TIMESTAMP)
        ORDER BY job_id
        """
    )
    return [mappers._row_to_job_config(row) for row in rows]


def list_all_jobs(db: Any) -> list[JobConfig]:
    rows = db.execute_returning("SELECT * FROM jobs ORDER BY job_id")
    return [mappers._row_to_job_config(row) for row in rows]


def upsert_job(
    db: Any,
    job_id: str,
    job_name: str,
    check_interval_blocks: int,
    enabled: bool = True,
) -> None:
    db.execute(
        """
        INSERT INTO jobs (job_id, job_name, check_interval_blocks, enabled)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            job_name = excluded.job_name,
            check_interval_blocks = excluded.check_interval_blocks,
            updated_at = CURRENT_TIMESTAMP
        """,
        (job_id, job_name, check_interval_blocks, enabled),
    )


def update_job_checked(db: Any, job_id: str, block_number: int, triggered: bool = False) -> None:
    if triggered:
        db.execute(
            """
            UPDATE jobs SET
                last_checked_block_number = ?,
                last_triggered_block_number = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
            """,
            (block_number, block_number, job_id),
        )
        return

    db.execute(
        """
        UPDATE jobs SET
            last_checked_block_number = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE job_id = ?
        """,
        (block_number, job_id),
    )


def set_job_enabled(db: Any, job_id: str, enabled: bool) -> bool:
    rowcount = db.execute_returning_rowcount(
        "UPDATE jobs SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
        (enabled, job_id),
    )
    return rowcount > 0


def set_job_drain(
    db: Any,
    job_id: str,
    drain_until: datetime,
    reason: str | None = None,
    actor: str | None = None,
    source: str | None = None,
) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE jobs
                SET drain_until = ?,
                    drain_reason = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                """,
                (drain_until.isoformat(), reason, job_id),
            )
            updated = cursor.rowcount > 0
        finally:
            cursor.close()
    if updated:
        db.record_mutation_audit(
            entity_type="job",
            entity_id=job_id,
            action="drain",
            actor=actor,
            reason=reason,
            source=source,
            metadata={"drain_until": drain_until.isoformat()},
        )
    return updated


def clear_job_drain(
    db: Any,
    job_id: str,
    actor: str | None = None,
    source: str | None = None,
) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE jobs
                SET drain_until = NULL,
                    drain_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                """,
                (job_id,),
            )
            updated = cursor.rowcount > 0
        finally:
            cursor.close()
    if updated:
        db.record_mutation_audit(
            entity_type="job",
            entity_id=job_id,
            action="undrain",
            actor=actor,
            reason=None,
            source=source,
        )
    return updated


def delete_job(db: Any, job_id: str) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM job_kv WHERE job_id = ?", (job_id,))
            cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            deleted = cursor.rowcount > 0
        finally:
            cursor.close()
        return deleted


def get_job_kv(db: Any, job_id: str, key: str) -> Any | None:
    row = db.execute_one(
        "SELECT value_json FROM job_kv WHERE job_id = ? AND key = ?",
        (job_id, key),
    )
    if not row:
        return None
    return mappers.parse_json(row["value_json"])


def set_job_kv(db: Any, job_id: str, key: str, value: Any) -> None:
    value_json = json.dumps(value)
    db.execute(
        """
        INSERT INTO job_kv (job_id, key, value_json)
        VALUES (?, ?, ?)
        ON CONFLICT(job_id, key) DO UPDATE SET
            value_json = excluded.value_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (job_id, key, value_json),
    )


def delete_job_kv(db: Any, job_id: str, key: str) -> bool:
    rowcount = db.execute_returning_rowcount(
        "DELETE FROM job_kv WHERE job_id = ? AND key = ?",
        (job_id, key),
    )
    return rowcount > 0
