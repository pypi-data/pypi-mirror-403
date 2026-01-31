from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from brawny.db.sqlite import mappers, tx
from brawny.model.enums import IntentStatus, IntentTerminalReason
from brawny.model.errors import DatabaseError, InvariantViolation
from brawny.config.validation import (
    InvalidEndpointError,
    canonicalize_endpoint,
    dedupe_preserve_order,
)
from brawny.model.types import TxIntent
from brawny.types import ClaimedIntent

_TERMINAL_REASONS = {
    IntentTerminalReason.CONFIRMED.value,
    IntentTerminalReason.FAILED.value,
    IntentTerminalReason.ABANDONED.value,
}


def _ensure_terminal_reason_compatible(
    existing: str | None,
    new: str | None,
    intent_id: UUID,
) -> None:
    if new is None:
        if existing is not None:
            raise InvariantViolation(
                f"Intent {intent_id} terminal_reason already set to {existing}"
            )
        return
    if existing is not None and existing != new:
        raise InvariantViolation(
            f"Intent {intent_id} terminal_reason already set to {existing}"
        )


def _ensure_halt_reason_compatible(
    existing: str | None,
    new: str | None,
    intent_id: UUID,
) -> None:
    if new is None:
        if existing is not None:
            raise InvariantViolation(
                f"Intent {intent_id} halt_reason already set to {existing}"
            )
        return
    if existing is not None and existing != new:
        raise InvariantViolation(
            f"Intent {intent_id} halt_reason already set to {existing}"
        )


def _validate_terminal_fields(
    status: str,
    terminal_reason: str | None,
    halt_reason: str | None,
    existing_terminal_reason: str | None,
    existing_halt_reason: str | None,
    intent_id: UUID,
) -> None:
    if status != IntentStatus.TERMINAL.value:
        if terminal_reason is not None or halt_reason is not None:
            raise InvariantViolation(
                f"Intent {intent_id} terminal fields set for non-terminal status"
            )
        if existing_terminal_reason is not None or existing_halt_reason is not None:
            raise InvariantViolation(
                f"Intent {intent_id} already terminal; refusing to clear terminal fields"
            )
        return

    if terminal_reason is not None and halt_reason is not None:
        raise InvariantViolation(
            f"Intent {intent_id} cannot set terminal_reason and halt_reason together"
        )
    if terminal_reason is None and halt_reason is None:
        raise InvariantViolation(
            f"Intent {intent_id} terminal status requires terminal_reason or halt_reason"
        )
    if terminal_reason is not None and terminal_reason not in _TERMINAL_REASONS:
        raise InvariantViolation(
            f"Intent {intent_id} invalid terminal_reason: {terminal_reason}"
        )

    _ensure_terminal_reason_compatible(existing_terminal_reason, terminal_reason, intent_id)
    _ensure_halt_reason_compatible(existing_halt_reason, halt_reason, intent_id)


def _require_tx_hash_for_broadcasted(
    status: str,
    has_tx_hash: bool,
    intent_id: UUID,
) -> None:
    if status == IntentStatus.BROADCASTED.value and not has_tx_hash:
        raise InvariantViolation(
            f"Intent {intent_id} cannot be broadcasted without a tx_hash"
        )


def get_inflight_intent_count(db: Any, chain_id: int, job_id: str, signer_address: str) -> int:
    signer_address = db._normalize_address(signer_address)
    row = db.execute_one(
        """
        SELECT COUNT(*) as count
        FROM tx_intents
        WHERE chain_id = ?
          AND job_id = ?
          AND signer_address = ?
          AND status IN ('created', 'claimed', 'broadcasted')
        """,
        (chain_id, job_id, signer_address),
    )
    return int(row["count"]) if row else 0


def get_inflight_intents_for_scope(
    db: Any,
    chain_id: int,
    job_id: str,
    signer_address: str,
    to_address: str,
) -> list[dict[str, Any]]:
    signer_address = db._normalize_address(signer_address)
    to_address = db._normalize_address(to_address)
    rows = db.execute_returning(
        """
        SELECT intent_id, status, claimed_at, created_at
        FROM tx_intents
        WHERE chain_id = ?
          AND job_id = ?
          AND signer_address = ?
          AND to_address = ?
          AND status IN ('created', 'claimed', 'broadcasted')
        ORDER BY created_at ASC
        """,
        (chain_id, job_id, signer_address, to_address),
    )
    return [dict(row) for row in rows]


def create_intent(
    db: Any,
    intent_id: UUID,
    job_id: str,
    chain_id: int,
    signer_address: str,
    idempotency_key: str,
    to_address: str,
    data: str | None,
    value_wei: str,
    gas_limit: int | None,
    max_fee_per_gas: str | None,
    max_priority_fee_per_gas: str | None,
    min_confirmations: int,
    deadline_ts: datetime | None,
    signer_alias: str | None = None,
    broadcast_group: str | None = None,
    broadcast_endpoints: list[str] | None = None,
    metadata: dict | None = None,
) -> TxIntent | None:
    signer_address = db._normalize_address(signer_address)
    to_address = db._normalize_address(to_address)
    try:
        db.execute(
            """
            INSERT INTO tx_intents (
                intent_id, job_id, chain_id, signer_address, signer_alias, idempotency_key,
                to_address, data, value_wei, gas_limit, max_fee_per_gas,
                max_priority_fee_per_gas, min_confirmations, deadline_ts,
                broadcast_group, broadcast_endpoints_json, retry_after, status,
                metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'created', ?)
            """,
            (
                str(intent_id),
                job_id,
                chain_id,
                signer_address,
                signer_alias,
                idempotency_key,
                to_address,
                data,
                value_wei,
                gas_limit,
                max_fee_per_gas,
                max_priority_fee_per_gas,
                min_confirmations,
                deadline_ts,
                broadcast_group,
                json.dumps(broadcast_endpoints) if broadcast_endpoints else None,
                json.dumps(metadata) if metadata else None,
            ),
        )
        return get_intent(db, intent_id)
    except sqlite3.IntegrityError:
        return None
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e):
            return None
        raise


def get_intent(db: Any, intent_id: UUID) -> TxIntent | None:
    row = db.execute_one(
        "SELECT * FROM tx_intents WHERE intent_id = ?",
        (str(intent_id),),
    )
    if not row:
        return None
    return mappers._row_to_intent(row)


def get_intent_by_idempotency_key(
    db: Any,
    chain_id: int,
    signer_address: str,
    idempotency_key: str,
) -> TxIntent | None:
    signer_address = db._normalize_address(signer_address)
    row = db.execute_one(
        "SELECT * FROM tx_intents WHERE chain_id = ? AND signer_address = ? AND idempotency_key = ?",
        (chain_id, signer_address, idempotency_key),
    )
    if not row:
        return None
    return mappers._row_to_intent(row)


def get_intents_by_status(
    db: Any,
    status: str | list[str],
    chain_id: int | None = None,
    job_id: str | None = None,
    limit: int = 100,
) -> list[TxIntent]:
    if isinstance(status, str):
        status = [status]

    placeholders = ",".join("?" * len(status))
    query = f"SELECT * FROM tx_intents WHERE status IN ({placeholders})"
    params: list[Any] = list(status)

    if chain_id is not None:
        query += " AND chain_id = ?"
        params.append(chain_id)
    if job_id is not None:
        query += " AND job_id = ?"
        params.append(job_id)

    query += " ORDER BY created_at ASC LIMIT ?"
    params.append(limit)

    rows = db.execute_returning(query, tuple(params))
    return [mappers._row_to_intent(row) for row in rows]


def list_intents_filtered(
    db: Any,
    status: str | None = None,
    job_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM tx_intents WHERE 1=1"
    params: list[Any] = []

    if status is not None:
        query += " AND status = ?"
        params.append(status)
    if job_id is not None:
        query += " AND job_id = ?"
        params.append(job_id)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    return db.execute_returning(query, tuple(params))


def get_active_intent_count(db: Any, job_id: str, chain_id: int | None = None) -> int:
    statuses = [
        IntentStatus.CREATED.value,
        IntentStatus.CLAIMED.value,
        IntentStatus.BROADCASTED.value,
    ]
    placeholders = ",".join("?" * len(statuses))
    query = (
        f"SELECT COUNT(*) AS count FROM tx_intents WHERE status IN ({placeholders}) AND job_id = ?"
    )
    params: list[Any] = list(statuses)
    params.append(job_id)
    if chain_id is not None:
        query += " AND chain_id = ?"
        params.append(chain_id)
    row = db.execute_one(query, tuple(params))
    return int(row["count"]) if row else 0


def get_pending_intent_count(db: Any, chain_id: int | None = None) -> int:
    statuses = [
        IntentStatus.CREATED.value,
        IntentStatus.CLAIMED.value,
        IntentStatus.BROADCASTED.value,
    ]
    placeholders = ",".join("?" * len(statuses))
    query = f"SELECT COUNT(*) AS count FROM tx_intents WHERE status IN ({placeholders})"
    params: list[Any] = list(statuses)
    if chain_id is not None:
        query += " AND chain_id = ?"
        params.append(chain_id)
    row = db.execute_one(query, tuple(params))
    return int(row["count"]) if row else 0


def get_backing_off_intent_count(db: Any, chain_id: int | None = None) -> int:
    query = "SELECT COUNT(*) AS count FROM tx_intents WHERE retry_after > CURRENT_TIMESTAMP"
    params: list[Any] = []
    if chain_id is not None:
        query += " AND chain_id = ?"
        params.append(chain_id)
    row = db.execute_one(query, tuple(params))
    return int(row["count"]) if row else 0


def get_oldest_pending_intent_age(db: Any, chain_id: int) -> float | None:
    query = """
        SELECT (julianday('now') - julianday(MIN(created_at))) * 86400 AS age_seconds
        FROM tx_intents
        WHERE chain_id = ?
          AND status IN ('created', 'broadcasted', 'claimed')
    """
    result = db.execute_one(query, (chain_id,))
    if result and result.get("age_seconds") is not None:
        return result["age_seconds"]
    return None


def list_intent_inconsistencies(
    db: Any,
    max_age_seconds: int,
    limit: int = 100,
    chain_id: int | None = None,
) -> list[dict[str, Any]]:
    chain_clause = ""
    chain_params: list[Any] = []
    if chain_id is not None:
        chain_clause = " AND chain_id = ?"
        chain_params = [chain_id] * 5

    query = f"""
    SELECT intent_id, status, 'broadcasted_no_tx_hash' AS reason
    FROM tx_intents
    WHERE status = 'broadcasted'
    {chain_clause}
    AND NOT EXISTS (
        SELECT 1 FROM tx_attempts
        WHERE tx_attempts.intent_id = tx_intents.intent_id
          AND tx_attempts.tx_hash IS NOT NULL
    )

    UNION ALL
    SELECT intent_id, status, 'confirmed_no_confirmed_attempt' AS reason
    FROM tx_intents
    WHERE status = 'terminal' AND terminal_reason = 'confirmed'
    {chain_clause}
    AND NOT EXISTS (
        SELECT 1 FROM tx_attempts
        WHERE tx_attempts.intent_id = tx_intents.intent_id
          AND tx_attempts.status = 'confirmed'
    )

    UNION ALL
    SELECT intent_id, status, 'claimed_missing_claim' AS reason
    FROM tx_intents
    WHERE status = 'claimed'
    {chain_clause}
    AND (claim_token IS NULL OR claimed_at IS NULL OR lease_expires_at IS NULL)

    UNION ALL
    SELECT intent_id, status, 'nonclaimed_with_claim' AS reason
    FROM tx_intents
    WHERE status != 'claimed'
    {chain_clause}
    AND (claim_token IS NOT NULL OR claimed_at IS NOT NULL OR lease_expires_at IS NOT NULL)

    UNION ALL
    SELECT intent_id, status, 'broadcasted_stuck' AS reason
    FROM tx_intents
    WHERE status = 'broadcasted'
    {chain_clause}
    AND updated_at < datetime('now', ? || ' seconds')

    LIMIT ?
    """
    params_with_age = chain_params + [f"-{max_age_seconds}", limit]
    rows = db.execute_returning(query, tuple(params_with_age))
    return [dict(row) for row in rows]


def list_broadcasted_intents_older_than(
    db: Any,
    max_age_seconds: int,
    limit: int = 100,
    chain_id: int | None = None,
) -> list[TxIntent]:
    query = """
    SELECT * FROM tx_intents
    WHERE status = 'broadcasted'
    AND updated_at < datetime('now', ? || ' seconds')
    """
    params: list[Any] = [f"-{max_age_seconds}"]
    if chain_id is not None:
        query += " AND chain_id = ?"
        params.append(chain_id)
    query += " ORDER BY updated_at ASC LIMIT ?"
    params.append(limit)
    rows = db.execute_returning(query, tuple(params))
    return [mappers._row_to_intent(row) for row in rows]


def list_claimed_intents_older_than(
    db: Any,
    max_age_seconds: int,
    limit: int = 100,
    chain_id: int | None = None,
) -> list[TxIntent]:
    query = """
    SELECT * FROM tx_intents
    WHERE status = 'claimed'
    AND COALESCE(lease_expires_at, datetime(claimed_at, ? || ' seconds')) < CURRENT_TIMESTAMP
    AND EXISTS (
        SELECT 1 FROM tx_attempts WHERE tx_attempts.intent_id = tx_intents.intent_id
    )
    """
    params: list[Any] = [f"+{max_age_seconds}"]
    if chain_id is not None:
        query += " AND chain_id = ?"
        params.append(chain_id)
    query += " ORDER BY updated_at ASC LIMIT ?"
    params.append(limit)
    rows = db.execute_returning(query, tuple(params))
    return [mappers._row_to_intent(row) for row in rows]


def claim_next_intent(
    db: Any,
    claim_token: str,
    claimed_by: str | None = None,
    lease_seconds: int | None = None,
) -> ClaimedIntent | None:
    if lease_seconds is None:
        raise DatabaseError("lease_seconds is required for claim_next_intent")
    if lease_seconds <= 0:
        raise DatabaseError("lease_seconds must be positive for claim_next_intent")
    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tx_intents
                SET status = 'claimed', claim_token = ?, claimed_at = CURRENT_TIMESTAMP,
                    claimed_by = ?,
                    lease_expires_at = datetime('now', ? || ' seconds'),
                    retry_after = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE intent_id = (
                    SELECT intent_id FROM tx_intents
                    WHERE status = 'created'
                    AND (deadline_ts IS NULL OR deadline_ts > CURRENT_TIMESTAMP)
                    AND (retry_after IS NULL OR retry_after <= CURRENT_TIMESTAMP)
                    ORDER BY created_at ASC, intent_id ASC
                    LIMIT 1
                )
                AND status = 'created'
                """,
                (claim_token, claimed_by, f"{int(lease_seconds)}"),
            )

            if cursor.rowcount == 0:
                return None

            cursor.execute(
                "SELECT * FROM tx_intents WHERE claim_token = ? AND status = 'claimed'",
                (claim_token,),
            )
            row = cursor.fetchone()
            if row:
                return mappers._row_to_claimed_intent(dict(row))
            return None
        finally:
            cursor.close()


def update_intent_status(
    db: Any,
    intent_id: UUID,
    status: str,
    claim_token: str | None = None,
    terminal_reason: str | None = None,
    halt_reason: str | None = None,
) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    terminal_reason,
                    halt_reason,
                    EXISTS (
                        SELECT 1 FROM tx_attempts
                        WHERE tx_attempts.intent_id = tx_intents.intent_id
                          AND tx_attempts.tx_hash IS NOT NULL
                    ) as has_tx_hash
                FROM tx_intents
                WHERE intent_id = ?
                """,
                (str(intent_id),),
            )
            row = cursor.fetchone()
            if not row:
                return False
            _require_tx_hash_for_broadcasted(status, row["has_tx_hash"], intent_id)
            _validate_terminal_fields(
                status,
                terminal_reason,
                halt_reason,
                row["terminal_reason"],
                row["halt_reason"],
                intent_id,
            )

            terminal_value = (
                terminal_reason if status == IntentStatus.TERMINAL.value else None
            )
            halt_value = halt_reason if status == IntentStatus.TERMINAL.value else None

            if claim_token:
                cursor.execute(
                    """
                    UPDATE tx_intents SET status = ?, claim_token = ?,
                        claimed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP,
                        terminal_reason = ?, halt_reason = ?
                    WHERE intent_id = ?
                    """,
                    (
                        status,
                        claim_token,
                        terminal_value,
                        halt_value,
                        str(intent_id),
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE tx_intents SET status = ?, updated_at = CURRENT_TIMESTAMP,
                        terminal_reason = ?, halt_reason = ?
                    WHERE intent_id = ?
                    """,
                    (
                        status,
                        terminal_value,
                        halt_value,
                        str(intent_id),
                    ),
                )
            return cursor.rowcount > 0
        finally:
            cursor.close()


def update_intent_status_if(
    db: Any,
    intent_id: UUID,
    status: str,
    expected_status: str | list[str],
    terminal_reason: str | None = None,
    halt_reason: str | None = None,
) -> bool:
    if isinstance(expected_status, str):
        expected_status = [expected_status]
    placeholders = ",".join("?" * len(expected_status))
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    terminal_reason,
                    halt_reason,
                    EXISTS (
                        SELECT 1 FROM tx_attempts
                        WHERE tx_attempts.intent_id = tx_intents.intent_id
                          AND tx_attempts.tx_hash IS NOT NULL
                    ) as has_tx_hash
                FROM tx_intents
                WHERE intent_id = ?
                """,
                (str(intent_id),),
            )
            row = cursor.fetchone()
            if not row:
                return False
            _require_tx_hash_for_broadcasted(status, row["has_tx_hash"], intent_id)
            _validate_terminal_fields(
                status,
                terminal_reason,
                halt_reason,
                row["terminal_reason"],
                row["halt_reason"],
                intent_id,
            )

            terminal_value = (
                terminal_reason if status == IntentStatus.TERMINAL.value else None
            )
            halt_value = halt_reason if status == IntentStatus.TERMINAL.value else None
            cursor.execute(
                f"""
                UPDATE tx_intents SET status = ?, updated_at = CURRENT_TIMESTAMP,
                    terminal_reason = ?, halt_reason = ?
                WHERE intent_id = ? AND status IN ({placeholders})
                """,
                (status, terminal_value, halt_value, str(intent_id), *expected_status),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()


def transition_intent_status_immediate(
    db: Any,
    intent_id: UUID,
    from_statuses: list[str],
    to_status: str,
    terminal_reason: str | None = None,
    halt_reason: str | None = None,
) -> tuple[bool, str | None]:
    placeholders = ",".join("?" * len(from_statuses))
    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    status,
                    terminal_reason,
                    halt_reason,
                    EXISTS (
                        SELECT 1 FROM tx_attempts
                        WHERE tx_attempts.intent_id = tx_intents.intent_id
                          AND tx_attempts.tx_hash IS NOT NULL
                    ) as has_tx_hash
                FROM tx_intents
                WHERE intent_id = ?
                """,
                (str(intent_id),),
            )
            row = cursor.fetchone()
            if not row:
                return (False, None)

            old_status = row["status"]

            if to_status == IntentStatus.BROADCASTED.value and not row["has_tx_hash"]:
                return (False, None)

            _validate_terminal_fields(
                to_status,
                terminal_reason,
                halt_reason,
                row["terminal_reason"],
                row["halt_reason"],
                intent_id,
            )

            terminal_value = (
                terminal_reason if to_status == IntentStatus.TERMINAL.value else None
            )
            halt_value = halt_reason if to_status == IntentStatus.TERMINAL.value else None

            if old_status not in from_statuses:
                return (False, None)

            should_clear_claim = old_status == "claimed" and to_status != "claimed"

            if should_clear_claim:
                cursor.execute(
                    f"""
                    UPDATE tx_intents
                    SET status = ?,
                        updated_at = CURRENT_TIMESTAMP,
                        claim_token = NULL,
                        claimed_at = NULL,
                        claimed_by = NULL,
                        lease_expires_at = NULL,
                        terminal_reason = ?,
                        halt_reason = ?
                    WHERE intent_id = ? AND status IN ({placeholders})
                    """,
                    (to_status, terminal_value, halt_value, str(intent_id), *from_statuses),
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE tx_intents
                    SET status = ?, updated_at = CURRENT_TIMESTAMP,
                        terminal_reason = ?, halt_reason = ?
                    WHERE intent_id = ? AND status IN ({placeholders})
                    """,
                    (to_status, terminal_value, halt_value, str(intent_id), *from_statuses),
                )

            if cursor.rowcount == 0:
                return (False, None)

            return (True, old_status)
        finally:
            cursor.close()


def update_intent_signer(db: Any, intent_id: UUID, signer_address: str) -> bool:
    signer_address = db._normalize_address(signer_address)
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tx_intents SET signer_address = ?, updated_at = CURRENT_TIMESTAMP
                WHERE intent_id = ?
                """,
                (signer_address, str(intent_id)),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()


def release_intent_claim(db: Any, intent_id: UUID) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tx_intents SET status = 'created', claim_token = NULL,
                    claimed_at = NULL, lease_expires_at = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE intent_id = ? AND status = 'claimed'
                """,
                (str(intent_id),),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()


def release_intent_claim_if_token(db: Any, intent_id: UUID, claim_token: str) -> bool:
    rowcount = db.execute_returning_rowcount(
        """
        UPDATE tx_intents
        SET status = 'created',
            claim_token = NULL,
            claimed_at = NULL,
            claimed_by = NULL,
            lease_expires_at = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE intent_id = ? AND claim_token = ? AND status = 'claimed'
        """,
        (str(intent_id), claim_token),
    )
    return rowcount == 1


def release_claim_if_token_and_no_attempts(db: Any, intent_id: UUID, claim_token: str) -> bool:
    rowcount = db.execute_returning_rowcount(
        """
        UPDATE tx_intents
        SET status = 'created',
            claim_token = NULL,
            claimed_at = NULL,
            claimed_by = NULL,
            lease_expires_at = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE intent_id = ?
          AND claim_token = ?
          AND status = 'claimed'
          AND NOT EXISTS (
              SELECT 1 FROM tx_attempts
              WHERE tx_attempts.intent_id = tx_intents.intent_id
          )
        """,
        (str(intent_id), claim_token),
    )
    return rowcount == 1


def clear_intent_claim(db: Any, intent_id: UUID) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tx_intents
                SET claim_token = NULL, claimed_at = NULL, lease_expires_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE intent_id = ?
                """,
                (str(intent_id),),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()


def set_intent_retry_after(db: Any, intent_id: UUID, retry_after: datetime | None) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tx_intents
                SET retry_after = ?, updated_at = CURRENT_TIMESTAMP
                WHERE intent_id = ?
                """,
                (retry_after, str(intent_id)),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()


def increment_intent_retry_count(db: Any, intent_id: UUID) -> int:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tx_intents
                SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE intent_id = ?
                """,
                (str(intent_id),),
            )
            if cursor.rowcount == 0:
                return 0
            cursor.execute(
                "SELECT retry_count FROM tx_intents WHERE intent_id = ?",
                (str(intent_id),),
            )
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()


def should_create_intent(
    db: Any,
    cooldown_key: str,
    now: int,
    cooldown_seconds: int,
) -> tuple[bool, int | None]:
    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT last_intent_at FROM job_cooldowns WHERE cooldown_key = ?",
                (cooldown_key,),
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO job_cooldowns (cooldown_key, last_intent_at) VALUES (?, ?)",
                    (cooldown_key, now),
                )
                return True, None

            last_intent_at = int(row[0])
            if now - last_intent_at >= cooldown_seconds:
                cursor.execute(
                    "UPDATE job_cooldowns SET last_intent_at = ? WHERE cooldown_key = ?",
                    (now, cooldown_key),
                )
                return True, last_intent_at

            return False, last_intent_at
        finally:
            cursor.close()


def prune_job_cooldowns(db: Any, older_than_days: int) -> int:
    if older_than_days <= 0:
        return 0
    cutoff = int(time.time()) - (older_than_days * 86400)
    rowcount = db.execute_returning_rowcount(
        "DELETE FROM job_cooldowns WHERE last_intent_at < ?",
        (cutoff,),
    )
    return rowcount


def requeue_expired_claims_no_attempts(
    db: Any,
    limit: int,
    grace_seconds: int,
    chain_id: int | None = None,
) -> int:
    if limit <= 0:
        return 0
    offset = f"-{grace_seconds} seconds"
    params: list[Any] = [offset]
    chain_clause = ""
    if chain_id is not None:
        chain_clause = "AND chain_id = ?"
        params.append(chain_id)
    params.append(limit)

    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                WITH expired AS (
                    SELECT intent_id
                    FROM tx_intents
                    WHERE status = 'claimed'
                      AND lease_expires_at IS NOT NULL
                      AND lease_expires_at < datetime('now', ?)
                      {chain_clause}
                      AND NOT EXISTS (
                          SELECT 1 FROM tx_attempts
                          WHERE tx_attempts.intent_id = tx_intents.intent_id
                      )
                    ORDER BY lease_expires_at ASC, intent_id ASC
                    LIMIT ?
                )
                UPDATE tx_intents
                SET status = 'created',
                    claim_token = NULL,
                    claimed_at = NULL,
                    claimed_by = NULL,
                    lease_expires_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE intent_id IN (SELECT intent_id FROM expired)
                  AND status = 'claimed'
                  AND NOT EXISTS (
                      SELECT 1 FROM tx_attempts
                      WHERE tx_attempts.intent_id = tx_intents.intent_id
                  )
                """,
                tuple(params),
            )
            cursor.execute("SELECT changes()")
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()


def count_expired_claims_with_attempts(
    db: Any,
    limit: int,
    grace_seconds: int,
    chain_id: int | None = None,
) -> int:
    if limit <= 0:
        return 0
    offset = f"-{grace_seconds} seconds"
    params: list[Any] = [offset]
    chain_clause = ""
    if chain_id is not None:
        chain_clause = "AND chain_id = ?"
        params.append(chain_id)
    params.append(limit)
    row = db.execute_one(
        f"""
        SELECT COUNT(*) AS count FROM (
            SELECT intent_id
            FROM tx_intents
            WHERE status = 'claimed'
              AND lease_expires_at IS NOT NULL
              AND lease_expires_at < datetime('now', ?)
              {chain_clause}
              AND EXISTS (
                  SELECT 1 FROM tx_attempts
                  WHERE tx_attempts.intent_id = tx_intents.intent_id
              )
            ORDER BY lease_expires_at ASC, intent_id ASC
            LIMIT ?
        )
        """,
        tuple(params),
    )
    return int(row["count"]) if row else 0


def requeue_missing_lease_claims_no_attempts(
    db: Any,
    limit: int,
    cutoff_seconds: int,
    chain_id: int | None = None,
) -> int:
    if limit <= 0:
        return 0
    offset = f"-{cutoff_seconds} seconds"
    params: list[Any] = [offset]
    chain_clause = ""
    if chain_id is not None:
        chain_clause = "AND chain_id = ?"
        params.append(chain_id)
    params.append(limit)

    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                WITH stale AS (
                    SELECT intent_id
                    FROM tx_intents
                    WHERE status = 'claimed'
                      AND lease_expires_at IS NULL
                      AND claimed_at IS NOT NULL
                      AND claimed_at < datetime('now', ?)
                      {chain_clause}
                      AND NOT EXISTS (
                          SELECT 1 FROM tx_attempts
                          WHERE tx_attempts.intent_id = tx_intents.intent_id
                      )
                    ORDER BY claimed_at ASC, intent_id ASC
                    LIMIT ?
                )
                UPDATE tx_intents
                SET status = 'created',
                    claim_token = NULL,
                    claimed_at = NULL,
                    claimed_by = NULL,
                    lease_expires_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE intent_id IN (SELECT intent_id FROM stale)
                  AND status = 'claimed'
                  AND lease_expires_at IS NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM tx_attempts
                      WHERE tx_attempts.intent_id = tx_intents.intent_id
                  )
                """,
                tuple(params),
            )
            cursor.execute("SELECT changes()")
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()


def count_missing_lease_claims_with_attempts(
    db: Any,
    limit: int,
    cutoff_seconds: int,
    chain_id: int | None = None,
) -> int:
    if limit <= 0:
        return 0
    offset = f"-{cutoff_seconds} seconds"
    params: list[Any] = [offset]
    chain_clause = ""
    if chain_id is not None:
        chain_clause = "AND chain_id = ?"
        params.append(chain_id)
    params.append(limit)
    row = db.execute_one(
        f"""
        SELECT COUNT(*) AS count FROM (
            SELECT intent_id
            FROM tx_intents
            WHERE status = 'claimed'
              AND lease_expires_at IS NULL
              AND claimed_at IS NOT NULL
              AND claimed_at < datetime('now', ?)
              {chain_clause}
              AND EXISTS (
                  SELECT 1 FROM tx_attempts
                  WHERE tx_attempts.intent_id = tx_intents.intent_id
              )
            ORDER BY claimed_at ASC, intent_id ASC
            LIMIT ?
        )
        """,
        tuple(params),
    )
    return int(row["count"]) if row else 0


def abandon_intent(db: Any, intent_id: UUID) -> bool:
    return update_intent_status(
        db,
        intent_id,
        IntentStatus.TERMINAL.value,
        terminal_reason=IntentTerminalReason.ABANDONED.value,
    )


def get_broadcasted_intents_for_signer(
    db: Any, chain_id: int, address: str
) -> list[TxIntent]:
    address = db._normalize_address(address)
    rows = db.execute_returning(
        """
        SELECT * FROM tx_intents
        WHERE chain_id = ? AND signer_address = ?
        AND status IN ('broadcasted')
        ORDER BY created_at
        """,
        (chain_id, address),
    )
    return [mappers._row_to_intent(row) for row in rows]


def bind_broadcast_endpoints(
    db: Any,
    intent_id: UUID,
    group_name: str | None,
    endpoints: list[str],
) -> tuple[str | None, list[str]]:
    ordered: list[str] = []
    for i, ep in enumerate(endpoints):
        try:
            ordered.append(canonicalize_endpoint(ep))
        except InvalidEndpointError as exc:
            raise DatabaseError(f"Invalid endpoint[{i}]: {exc}") from exc
    ordered = dedupe_preserve_order(ordered)
    canonical = db._canonicalize_endpoints(ordered)
    if not canonical:
        raise DatabaseError("Broadcast endpoints list is empty after canonicalization")
    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT broadcast_group, broadcast_endpoints_json
                FROM tx_intents
                WHERE intent_id = ?
                """,
                (str(intent_id),),
            )
            row = cursor.fetchone()
            if not row:
                raise DatabaseError(f"Intent {intent_id} not found")

            if row["broadcast_endpoints_json"] is not None:
                stored = json.loads(row["broadcast_endpoints_json"])
                stored_canonical = db._canonicalize_endpoints(stored)
                if stored_canonical == canonical and (
                    group_name is None or row["broadcast_group"] == group_name
                ):
                    return row["broadcast_group"], stored
                raise InvariantViolation(
                    f"Intent {intent_id} already bound with different endpoints"
                )

            binding_id = str(uuid4())
            cursor.execute(
                """
                UPDATE tx_intents
                SET broadcast_group = ?,
                    broadcast_endpoints_json = ?,
                    broadcast_binding_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE intent_id = ?
                  AND broadcast_endpoints_json IS NULL
                """,
                (group_name, json.dumps(ordered), binding_id, str(intent_id)),
            )

            if cursor.rowcount != 1:
                cursor.execute(
                    """
                    SELECT broadcast_group, broadcast_endpoints_json
                    FROM tx_intents
                    WHERE intent_id = ?
                    """,
                    (str(intent_id),),
                )
                row = cursor.fetchone()
                if not row or row["broadcast_endpoints_json"] is None:
                    raise InvariantViolation(
                        f"Binding race for intent {intent_id}: no binding persisted"
                    )
                stored = json.loads(row["broadcast_endpoints_json"])
                stored_canonical = db._canonicalize_endpoints(stored)
                if stored_canonical == canonical and (
                    group_name is None or row["broadcast_group"] == group_name
                ):
                    return row["broadcast_group"], stored
                raise InvariantViolation(
                    f"Intent {intent_id} already bound with different endpoints"
                )

            return group_name, ordered
        finally:
            cursor.close()


def get_broadcast_binding(db: Any, intent_id: UUID) -> tuple[str | None, list[str]] | None:
    row = db.execute_one(
        """
        SELECT broadcast_group, broadcast_endpoints_json
        FROM tx_intents
        WHERE intent_id = ?
        """,
        (str(intent_id),),
    )

    if not row:
        return None

    has_endpoints = row["broadcast_endpoints_json"] is not None
    if not has_endpoints:
        return None

    endpoints = json.loads(row["broadcast_endpoints_json"])
    if not isinstance(endpoints, list):
        raise ValueError(
            f"Corrupt binding for intent {intent_id}: "
            f"endpoints_json is {type(endpoints).__name__}, expected list"
        )

    canonical = db._canonicalize_endpoints(endpoints)
    if not canonical:
        raise ValueError(
            f"Corrupt binding for intent {intent_id}: endpoints list is empty"
        )

    return row["broadcast_group"], endpoints
