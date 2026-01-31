from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any
from uuid import UUID

from brawny.db.sqlite import mappers, tx
from brawny.model.errors import DatabaseError, InvariantViolation
from brawny.model.enums import AttemptStatus
from brawny.model.types import TxAttempt


def create_attempt(
    db: Any,
    attempt_id: UUID,
    intent_id: UUID,
    nonce: int,
    gas_params_json: str,
    status: str = "pending_send",
    tx_hash: str | None = None,
    replaces_attempt_id: UUID | None = None,
    broadcast_group: str | None = None,
    endpoint_url: str | None = None,
    binding: tuple[str | None, list[str]] | None = None,
    actor: str | None = None,
    reason: str | None = None,
    source: str | None = None,
) -> TxAttempt:
    """Create attempt, optionally setting binding atomically.

    Args:
        binding: If provided (first broadcast), persist binding atomically.
                 Tuple of (group_name or None, endpoints)

    CRITICAL: Uses WHERE broadcast_endpoints_json IS NULL to prevent overwrites.
    """
    replaces_str = str(replaces_attempt_id) if replaces_attempt_id else None
    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        binding_id: str | None = None

        if binding is not None:
            group_name, endpoints = binding
            db.bind_broadcast_endpoints(intent_id, group_name, endpoints)

        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT broadcast_binding_id FROM tx_intents WHERE intent_id = ?",
                (str(intent_id),),
            )
            row = cursor.fetchone()
            if row is not None:
                binding_id = row["broadcast_binding_id"]
        finally:
            cursor.close()

        conn.execute(
            """
            INSERT INTO tx_attempts (
                attempt_id, intent_id, nonce, gas_params_json, status,
                tx_hash, replaces_attempt_id, broadcast_group, endpoint_url,
                endpoint_binding_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(attempt_id),
                str(intent_id),
                nonce,
                gas_params_json,
                status,
                tx_hash,
                replaces_str,
                broadcast_group,
                endpoint_url,
                binding_id,
            ),
        )

    attempt = db.get_attempt(attempt_id)
    if not attempt:
        raise DatabaseError("Failed to create attempt")
    db.record_mutation_audit(
        entity_type="attempt",
        entity_id=str(attempt_id),
        action="create_attempt",
        actor=actor,
        reason=reason,
        source=source,
        metadata={"intent_id": str(intent_id), "nonce": nonce, "status": status},
    )
    return attempt


def create_attempt_once(
    db: Any,
    attempt_id: UUID,
    intent_id: UUID,
    nonce: int,
    gas_params_json: str,
    status: str = "pending_send",
    tx_hash: str | None = None,
    replaces_attempt_id: UUID | None = None,
    broadcast_group: str | None = None,
    endpoint_url: str | None = None,
    binding: tuple[str | None, list[str]] | None = None,
    actor: str | None = None,
    reason: str | None = None,
    source: str | None = None,
) -> TxAttempt:
    if replaces_attempt_id is not None:
        return create_attempt(
            db,
            attempt_id=attempt_id,
            intent_id=intent_id,
            nonce=nonce,
            gas_params_json=gas_params_json,
            status=status,
            tx_hash=tx_hash,
            replaces_attempt_id=replaces_attempt_id,
            broadcast_group=broadcast_group,
            endpoint_url=endpoint_url,
            binding=binding,
            actor=actor,
            reason=reason,
            source=source,
        )

    try:
        with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
            cursor = conn.cursor()
            try:
                if binding is not None:
                    group_name, endpoints = binding
                    try:
                        db.bind_broadcast_endpoints(intent_id, group_name, endpoints)
                    except (DatabaseError, InvariantViolation) as exc:
                        raise InvariantViolation(
                            f"Intent {intent_id} binding failed: {exc}"
                        ) from exc

                cursor.execute(
                    """
                    SELECT * FROM tx_attempts
                    WHERE intent_id = ? AND nonce = ? AND replaces_attempt_id IS NULL
                    ORDER BY created_at ASC LIMIT 1
                    """,
                    (str(intent_id), nonce),
                )
                row = cursor.fetchone()
                if row:
                    attempt = mappers._row_to_attempt(dict(row))
                    if tx_hash and attempt.tx_hash and attempt.tx_hash.lower() != tx_hash.lower():
                        raise InvariantViolation(
                            f"Attempt already exists for intent {intent_id} nonce {nonce}"
                        )
                    return attempt

                cursor.execute(
                    "SELECT broadcast_binding_id FROM tx_intents WHERE intent_id = ?",
                    (str(intent_id),),
                )
                binding_row = cursor.fetchone()
                binding_id = binding_row["broadcast_binding_id"] if binding_row else None

                conn.execute(
                    """
                    INSERT INTO tx_attempts (
                        attempt_id, intent_id, nonce, gas_params_json, status,
                        tx_hash, replaces_attempt_id, broadcast_group, endpoint_url,
                        endpoint_binding_id
                    ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
                    """,
                    (
                        str(attempt_id),
                        str(intent_id),
                        nonce,
                        gas_params_json,
                        status,
                        tx_hash,
                        broadcast_group,
                        endpoint_url,
                        binding_id,
                    ),
                )
            finally:
                cursor.close()
    except sqlite3.IntegrityError:
        row = db.execute_one(
            """
            SELECT * FROM tx_attempts
            WHERE intent_id = ? AND nonce = ? AND replaces_attempt_id IS NULL
            ORDER BY created_at ASC LIMIT 1
            """,
            (str(intent_id), nonce),
        )
        if row:
            attempt = mappers._row_to_attempt(row)
            if tx_hash and attempt.tx_hash and attempt.tx_hash.lower() != tx_hash.lower():
                raise InvariantViolation(
                    f"Attempt already exists for intent {intent_id} nonce {nonce}"
                )
            return attempt
        raise

    attempt = db.get_attempt(attempt_id)
    if not attempt:
        raise DatabaseError("Failed to create attempt")
    db.record_mutation_audit(
        entity_type="attempt",
        entity_id=str(attempt_id),
        action="create_attempt",
        actor=actor,
        reason=reason,
        source=source,
        metadata={"intent_id": str(intent_id), "nonce": nonce, "status": status},
    )
    return attempt


def require_bound_and_attempt(
    db: Any,
    intent_id: UUID,
    nonce: int,
    endpoints: list[str],
) -> None:
    canonical = db._canonicalize_endpoints(endpoints)
    row = db.execute_one(
        """
        SELECT broadcast_binding_id, broadcast_endpoints_json
        FROM tx_intents WHERE intent_id = ?
        """,
        (str(intent_id),),
    )
    if not row or row["broadcast_endpoints_json"] is None:
        raise InvariantViolation(f"Intent {intent_id} has no broadcast binding")

    stored = json.loads(row["broadcast_endpoints_json"])
    stored_canonical = db._canonicalize_endpoints(stored)
    if stored_canonical != canonical:
        raise InvariantViolation(
            f"Intent {intent_id} binding does not match endpoints"
        )

    binding_id = row["broadcast_binding_id"]
    attempt_row = db.execute_one(
        """
        SELECT attempt_id, endpoint_binding_id
        FROM tx_attempts
        WHERE intent_id = ? AND nonce = ?
        ORDER BY created_at ASC LIMIT 1
        """,
        (str(intent_id), nonce),
    )
    if not attempt_row:
        raise InvariantViolation(f"Intent {intent_id} missing attempt for nonce {nonce}")

    if binding_id is not None:
        attempt_binding = attempt_row.get("endpoint_binding_id")
        if attempt_binding is None or str(attempt_binding) != str(binding_id):
            raise InvariantViolation(
                f"Intent {intent_id} attempt binding mismatch for nonce {nonce}"
            )


def get_attempt(db: Any, attempt_id: UUID) -> TxAttempt | None:
    row = db.execute_one(
        "SELECT * FROM tx_attempts WHERE attempt_id = ?",
        (str(attempt_id),),
    )
    if not row:
        return None
    return mappers._row_to_attempt(row)


def get_attempts_for_intent(db: Any, intent_id: UUID) -> list[TxAttempt]:
    rows = db.execute_returning(
        "SELECT * FROM tx_attempts WHERE intent_id = ? ORDER BY created_at",
        (str(intent_id),),
    )
    return [mappers._row_to_attempt(row) for row in rows]


def get_latest_attempt_for_intent(db: Any, intent_id: UUID) -> TxAttempt | None:
    row = db.execute_one(
        """
        SELECT * FROM tx_attempts WHERE intent_id = ?
        ORDER BY created_at DESC LIMIT 1
        """,
        (str(intent_id),),
    )
    if not row:
        return None
    return mappers._row_to_attempt(row)


def get_attempt_by_tx_hash(db: Any, tx_hash: str) -> TxAttempt | None:
    row = db.execute_one(
        "SELECT * FROM tx_attempts WHERE tx_hash = ?",
        (tx_hash,),
    )
    if not row:
        return None
    return mappers._row_to_attempt(row)


def update_attempt_status(
    db: Any,
    attempt_id: UUID,
    status: str,
    tx_hash: str | None = None,
    broadcast_block: int | None = None,
    broadcast_at: datetime | None = None,
    included_block: int | None = None,
    endpoint_url: str | None = None,
    error_code: str | None = None,
    error_detail: str | None = None,
    actor: str | None = None,
    reason: str | None = None,
    source: str | None = None,
) -> bool:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT status, tx_hash, broadcast_block, broadcast_at,
                       included_block, endpoint_url, error_code, error_detail
                FROM tx_attempts WHERE attempt_id = ?
                """,
                (str(attempt_id),),
            )
            row = cursor.fetchone()
            if not row:
                return False

            if error_code is not None and row["error_code"] is not None:
                # Idempotent error_code writes: already set, no-op.
                return False

            current_status = row["status"]
            if reason == "receipt_override_local_state":
                if status != AttemptStatus.CONFIRMED.value:
                    raise InvariantViolation(
                        "receipt_override_local_state only supports confirmed status"
                    )
                if included_block is None:
                    raise InvariantViolation(
                        "receipt_override_local_state requires included_block"
                    )
                if tx_hash is None:
                    raise InvariantViolation(
                        "receipt_override_local_state requires tx_hash"
                    )
                existing_hash = row["tx_hash"]
                if existing_hash is None or str(existing_hash).lower() != str(tx_hash).lower():
                    raise InvariantViolation(
                        "receipt_override_local_state requires matching tx_hash"
                    )
            if not _is_allowed_attempt_transition(current_status, status, reason):
                raise InvariantViolation(
                    f"Attempt {attempt_id} status transition {current_status} -> {status} not allowed"
                )

            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params: list[Any] = [status]

            if tx_hash is not None:
                existing = row["tx_hash"]
                if existing is not None:
                    if str(existing).lower() != str(tx_hash).lower():
                        raise InvariantViolation(
                            f"Attempt {attempt_id} tx_hash already set"
                        )
                else:
                    updates.append("tx_hash = ?")
                    params.append(tx_hash)
            if broadcast_block is not None:
                existing = row["broadcast_block"]
                if existing is not None and int(existing) != int(broadcast_block):
                    raise InvariantViolation(
                        f"Attempt {attempt_id} broadcast_block already set"
                    )
                if existing is None:
                    updates.append("broadcast_block = ?")
                    params.append(broadcast_block)
            if broadcast_at is not None:
                existing = row["broadcast_at"]
                if existing is not None and not _same_value(existing, broadcast_at):
                    raise InvariantViolation(
                        f"Attempt {attempt_id} broadcast_at already set"
                    )
                if existing is None:
                    updates.append("broadcast_at = ?")
                    params.append(broadcast_at)
            if included_block is not None:
                existing = row["included_block"]
                if existing is not None and int(existing) != int(included_block):
                    raise InvariantViolation(
                        f"Attempt {attempt_id} included_block already set"
                    )
                if existing is None:
                    updates.append("included_block = ?")
                    params.append(included_block)
            if endpoint_url is not None:
                existing = row["endpoint_url"]
                if existing is not None and str(existing) != str(endpoint_url):
                    raise InvariantViolation(
                        f"Attempt {attempt_id} endpoint_url already set"
                    )
                if existing is None:
                    updates.append("endpoint_url = ?")
                    params.append(endpoint_url)
            if error_code is not None:
                existing = row["error_code"]
                if existing is not None and str(existing) != str(error_code):
                    raise InvariantViolation(
                        f"Attempt {attempt_id} error_code already set"
                    )
                if existing is None:
                    updates.append("error_code = ?")
                    params.append(error_code)
            if error_detail is not None:
                existing = row["error_detail"]
                if existing is not None and str(existing) != str(error_detail):
                    raise InvariantViolation(
                        f"Attempt {attempt_id} error_detail already set"
                    )
                if existing is None:
                    updates.append("error_detail = ?")
                    params.append(error_detail)

            params.append(str(attempt_id))
            query = f"UPDATE tx_attempts SET {', '.join(updates)} WHERE attempt_id = ?"
            cursor.execute(query, params)
            updated = cursor.rowcount > 0
        finally:
            cursor.close()

    if updated:
        db.record_mutation_audit(
            entity_type="attempt",
            entity_id=str(attempt_id),
            action=f"status:{status}",
            actor=actor,
            reason=reason,
            source=source,
            metadata={
                "tx_hash": tx_hash,
                "broadcast_block": broadcast_block,
                "included_block": included_block,
                "error_code": error_code,
            },
        )
    return updated


def _is_allowed_attempt_transition(
    current_status: str,
    new_status: str,
    reason: str | None,
) -> bool:
    if current_status == new_status:
        return True
    if reason == "receipt_override_local_state":
        return new_status == AttemptStatus.CONFIRMED.value
    if reason == "reorg_revert":
        return (
            current_status == AttemptStatus.CONFIRMED.value
            and new_status == AttemptStatus.PENDING.value
        )
    allowed = {
        AttemptStatus.SIGNED.value: {
            AttemptStatus.PENDING_SEND.value,
            AttemptStatus.BROADCAST.value,
            AttemptStatus.PENDING.value,
            AttemptStatus.FAILED.value,
            AttemptStatus.REPLACED.value,
        },
        AttemptStatus.PENDING_SEND.value: {
            AttemptStatus.BROADCAST.value,
            AttemptStatus.PENDING.value,
            AttemptStatus.FAILED.value,
            AttemptStatus.REPLACED.value,
        },
        AttemptStatus.BROADCAST.value: {
            AttemptStatus.PENDING.value,
            AttemptStatus.CONFIRMED.value,
            AttemptStatus.FAILED.value,
            AttemptStatus.REPLACED.value,
        },
        AttemptStatus.PENDING.value: {
            AttemptStatus.CONFIRMED.value,
            AttemptStatus.FAILED.value,
            AttemptStatus.REPLACED.value,
        },
        AttemptStatus.CONFIRMED.value: set(),
        AttemptStatus.FAILED.value: set(),
        AttemptStatus.REPLACED.value: set(),
    }
    return new_status in allowed.get(current_status, set())


def _same_value(existing: object, new: object) -> bool:
    if hasattr(existing, "isoformat"):
        existing_val = existing.isoformat()  # type: ignore[union-attr]
    else:
        existing_val = str(existing)
    if hasattr(new, "isoformat"):
        new_val = new.isoformat()  # type: ignore[union-attr]
    else:
        new_val = str(new)
    return existing_val == new_val
