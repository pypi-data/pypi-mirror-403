from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from brawny.db.sqlite import mappers, tx
from brawny.model.enums import NonceStatus
from brawny.model.errors import DatabaseError, InvariantViolation
from brawny.model.types import NonceReservation, RuntimeControl, SignerState


def get_signer_state(db: Any, chain_id: int, address: str) -> SignerState | None:
    address = db._normalize_address(address)
    row = db.execute_one(
        "SELECT * FROM signers WHERE chain_id = ? AND signer_address = ?",
        (chain_id, address),
    )
    if not row:
        return None
    return mappers._row_to_signer_state(row)


def get_all_signers(db: Any, chain_id: int) -> list[SignerState]:
    rows = db.execute_returning(
        "SELECT * FROM signers WHERE chain_id = ?", (chain_id,)
    )
    return [mappers._row_to_signer_state(row) for row in rows]


def upsert_signer(
    db: Any,
    chain_id: int,
    address: str,
    next_nonce: int,
    last_synced_chain_nonce: int | None = None,
) -> None:
    address = db._normalize_address(address)
    db.execute(
        """
        INSERT INTO signers (chain_id, signer_address, next_nonce, last_synced_chain_nonce)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chain_id, signer_address) DO UPDATE SET
            next_nonce = excluded.next_nonce,
            last_synced_chain_nonce = excluded.last_synced_chain_nonce,
            updated_at = CURRENT_TIMESTAMP
        """,
        (chain_id, address, next_nonce, last_synced_chain_nonce),
    )


def update_signer_next_nonce(db: Any, chain_id: int, address: str, next_nonce: int) -> None:
    address = db._normalize_address(address)
    db.execute(
        """
        UPDATE signers SET next_nonce = ?, updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ? AND signer_address = ?
        """,
        (next_nonce, chain_id, address),
    )


def update_signer_chain_nonce(db: Any, chain_id: int, address: str, chain_nonce: int) -> None:
    address = db._normalize_address(address)
    db.execute(
        """
        UPDATE signers SET last_synced_chain_nonce = ?, updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ? AND signer_address = ?
        """,
        (chain_nonce, chain_id, address),
    )


def set_gap_started_at(db: Any, chain_id: int, address: str, started_at: datetime) -> None:
    address = db._normalize_address(address)
    db.execute(
        """
        UPDATE signers SET gap_started_at = ?, updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ? AND signer_address = ?
        """,
        (started_at.isoformat() if started_at else None, chain_id, address),
    )


def clear_gap_started_at(db: Any, chain_id: int, address: str) -> None:
    address = db._normalize_address(address)
    db.execute(
        """
        UPDATE signers SET gap_started_at = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ? AND signer_address = ?
        """,
        (chain_id, address),
    )


def set_signer_quarantined(
    db: Any,
    chain_id: int,
    address: str,
    reason: str,
    actor: str | None = None,
    source: str | None = None,
) -> bool:
    address = db._normalize_address(address)
    updated = db.execute_returning_rowcount(
        """
        UPDATE signers
        SET quarantined_at = CURRENT_TIMESTAMP,
            quarantine_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ? AND signer_address = ?
        """,
        (reason, chain_id, address),
    )
    if updated:
        db.record_mutation_audit(
            entity_type="signer",
            entity_id=f"{chain_id}:{address}",
            action="quarantine",
            actor=actor,
            reason=reason,
            source=source,
        )
    return updated == 1


def clear_signer_quarantined(
    db: Any,
    chain_id: int,
    address: str,
    actor: str | None = None,
    source: str | None = None,
) -> bool:
    address = db._normalize_address(address)
    updated = db.execute_returning_rowcount(
        """
        UPDATE signers
        SET quarantined_at = NULL,
            quarantine_reason = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ? AND signer_address = ?
        """,
        (chain_id, address),
    )
    if updated:
        db.record_mutation_audit(
            entity_type="signer",
            entity_id=f"{chain_id}:{address}",
            action="unquarantine",
            actor=actor,
            source=source,
        )
    return updated == 1


def set_replacements_paused(
    db: Any,
    chain_id: int,
    address: str,
    paused: bool,
    reason: str | None = None,
    actor: str | None = None,
    source: str | None = None,
) -> bool:
    address = db._normalize_address(address)
    updated = db.execute_returning_rowcount(
        """
        UPDATE signers
        SET replacements_paused = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ? AND signer_address = ?
        """,
        (1 if paused else 0, chain_id, address),
    )
    if updated:
        db.record_mutation_audit(
            entity_type="signer",
            entity_id=f"{chain_id}:{address}",
            action="pause_replacements" if paused else "resume_replacements",
            actor=actor,
            reason=reason,
            source=source,
        )
    return updated == 1


def set_runtime_control(
    db: Any,
    control: str,
    active: bool,
    expires_at: datetime | None,
    reason: str | None,
    actor: str | None,
    mode: str,
) -> RuntimeControl:
    db.execute(
        """
        INSERT INTO runtime_controls (
            control, active, expires_at, reason, actor, mode, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(control) DO UPDATE SET
            active = excluded.active,
            expires_at = excluded.expires_at,
            reason = excluded.reason,
            actor = excluded.actor,
            mode = excluded.mode,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            control,
            1 if active else 0,
            expires_at.isoformat() if expires_at else None,
            reason,
            actor,
            mode,
        ),
    )
    db.record_mutation_audit(
        entity_type="runtime_control",
        entity_id=control,
        action="activate" if active else "deactivate",
        actor=actor,
        reason=reason,
        source="runtime_control",
        metadata={"mode": mode, "expires_at": expires_at.isoformat() if expires_at else None},
    )
    row = db.execute_one(
        "SELECT * FROM runtime_controls WHERE control = ?",
        (control,),
    )
    if not row:
        raise DatabaseError("Failed to set runtime control")
    return mappers._row_to_runtime_control(row)


def get_runtime_control(db: Any, control: str) -> RuntimeControl | None:
    row = db.execute_one(
        "SELECT * FROM runtime_controls WHERE control = ?",
        (control,),
    )
    if not row:
        return None
    return mappers._row_to_runtime_control(row)


def list_runtime_controls(db: Any) -> list[RuntimeControl]:
    rows = db.execute_returning(
        "SELECT * FROM runtime_controls ORDER BY control",
    )
    return [mappers._row_to_runtime_control(row) for row in rows]


def record_nonce_reset_audit(
    db: Any,
    chain_id: int,
    signer_address: str,
    old_next_nonce: int | None,
    new_next_nonce: int,
    released_reservations: int,
    source: str,
    reason: str | None,
) -> None:
    signer_address = db._normalize_address(signer_address)
    db.execute(
        """
        INSERT INTO nonce_reset_audit (
            chain_id, signer_address, old_next_nonce, new_next_nonce,
            released_reservations, source, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            chain_id,
            signer_address,
            old_next_nonce,
            new_next_nonce,
            released_reservations,
            source,
            reason,
        ),
    )


def record_mutation_audit(
    db: Any,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str | None = None,
    reason: str | None = None,
    source: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    metadata_json = json.dumps(metadata) if metadata else None
    db.execute(
        """
        INSERT INTO mutation_audit (
            entity_type, entity_id, action, actor, reason, source, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (entity_type, entity_id, action, actor, reason, source, metadata_json),
    )


def get_signer_by_alias(db: Any, chain_id: int, alias: str) -> SignerState | None:
    row = db.execute_one(
        """
        SELECT * FROM signers
        WHERE chain_id = ? AND alias = ?
        """,
        (chain_id, alias),
    )
    if not row:
        return None
    return mappers._row_to_signer_state(row)


def reserve_nonce_atomic(
    db: Any,
    chain_id: int,
    address: str,
    chain_nonce: int,
    intent_id: UUID | None = None,
) -> int:
    if chain_nonce is None:
        raise InvariantViolation("chain_nonce is required for nonce reservation")
    address = db._normalize_address(address)
    intent_id_str = str(intent_id) if intent_id else None
    with tx.transaction_conn(db, tx.SQLiteBeginMode.IMMEDIATE) as conn:
        conn.execute(
            """
            INSERT INTO signers (chain_id, signer_address, next_nonce, last_synced_chain_nonce)
            VALUES (?, ?, 0, NULL)
            ON CONFLICT(chain_id, signer_address) DO NOTHING
            """,
            (chain_id, address),
        )

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT next_nonce FROM signers
                WHERE chain_id = ? AND signer_address = ?
                """,
                (chain_id, address),
            )
            row = cursor.fetchone()
            if row is None:
                raise DatabaseError("Failed to lock signer row")

            db_next_nonce = row["next_nonce"]
            base_nonce = max(chain_nonce, db_next_nonce) if chain_nonce is not None else db_next_nonce

            cursor.execute(
                """
                SELECT nonce FROM nonce_reservations
                WHERE chain_id = ? AND signer_address = ?
                AND status != ?
                AND nonce >= ?
                ORDER BY nonce
                """,
                (chain_id, address, NonceStatus.RELEASED.value, base_nonce),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

        candidate = base_nonce
        for res in rows:
            if res["nonce"] == candidate:
                candidate += 1
            elif res["nonce"] > candidate:
                break

        if candidate - base_nonce > 100:
            raise DatabaseError(
                f"Could not find available nonce within 100 slots for signer {address}"
            )

        conn.execute(
            """
            INSERT INTO nonce_reservations (chain_id, signer_address, nonce, status, intent_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chain_id, signer_address, nonce) DO UPDATE SET
                status = excluded.status,
                intent_id = excluded.intent_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (chain_id, address, candidate, NonceStatus.RESERVED.value, intent_id_str),
        )

        new_next_nonce = max(db_next_nonce, candidate + 1)
        conn.execute(
            """
            UPDATE signers SET next_nonce = ?, updated_at = CURRENT_TIMESTAMP
            WHERE chain_id = ? AND signer_address = ?
            """,
            (new_next_nonce, chain_id, address),
        )
        return candidate


def get_nonce_reservation(
    db: Any, chain_id: int, address: str, nonce: int
) -> NonceReservation | None:
    address = db._normalize_address(address)
    row = db.execute_one(
        """
        SELECT * FROM nonce_reservations
        WHERE chain_id = ? AND signer_address = ? AND nonce = ?
        """,
        (chain_id, address, nonce),
    )
    if not row:
        return None
    return mappers._row_to_nonce_reservation(row)


def get_reservations_for_signer(
    db: Any, chain_id: int, address: str, status: str | None = None
) -> list[NonceReservation]:
    address = db._normalize_address(address)
    if status:
        rows = db.execute_returning(
            """
            SELECT * FROM nonce_reservations
            WHERE chain_id = ? AND signer_address = ? AND status = ?
            ORDER BY nonce
            """,
            (chain_id, address, status),
        )
    else:
        rows = db.execute_returning(
            """
            SELECT * FROM nonce_reservations
            WHERE chain_id = ? AND signer_address = ?
            ORDER BY nonce
            """,
            (chain_id, address),
        )
    return [mappers._row_to_nonce_reservation(row) for row in rows]


def get_reservations_below_nonce(
    db: Any, chain_id: int, address: str, nonce: int
) -> list[NonceReservation]:
    address = db._normalize_address(address)
    rows = db.execute_returning(
        """
        SELECT * FROM nonce_reservations
        WHERE chain_id = ? AND signer_address = ? AND nonce < ?
        ORDER BY nonce
        """,
        (chain_id, address, nonce),
    )
    return [mappers._row_to_nonce_reservation(row) for row in rows]


def create_nonce_reservation(
    db: Any,
    chain_id: int,
    address: str,
    nonce: int,
    status: str = "reserved",
    intent_id: UUID | None = None,
) -> NonceReservation:
    address = db._normalize_address(address)
    intent_id_str = str(intent_id) if intent_id else None
    db.execute(
        """
        INSERT INTO nonce_reservations (chain_id, signer_address, nonce, status, intent_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chain_id, signer_address, nonce) DO UPDATE SET
            status = excluded.status,
            intent_id = excluded.intent_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        (chain_id, address, nonce, status, intent_id_str),
    )
    reservation = get_nonce_reservation(db, chain_id, address, nonce)
    if not reservation:
        raise DatabaseError("Failed to create nonce reservation")
    return reservation


def update_nonce_reservation_status(
    db: Any,
    chain_id: int,
    address: str,
    nonce: int,
    status: str,
    intent_id: UUID | None = None,
) -> bool:
    address = db._normalize_address(address)
    intent_id_str = str(intent_id) if intent_id else None
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            if intent_id_str:
                cursor.execute(
                    """
                    UPDATE nonce_reservations SET status = ?, intent_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chain_id = ? AND signer_address = ? AND nonce = ?
                    """,
                    (status, intent_id_str, chain_id, address, nonce),
                )
            else:
                cursor.execute(
                    """
                    UPDATE nonce_reservations SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chain_id = ? AND signer_address = ? AND nonce = ?
                    """,
                    (status, chain_id, address, nonce),
                )
            updated = cursor.rowcount > 0
        finally:
            cursor.close()
        return updated


def release_nonce_reservation(
    db: Any,
    chain_id: int,
    address: str,
    nonce: int,
    actor: str | None = None,
    reason: str | None = None,
    source: str | None = None,
) -> bool:
    address = db._normalize_address(address)
    updated = update_nonce_reservation_status(db, chain_id, address, nonce, "released")
    if updated:
        db.execute(
            """
            UPDATE signers
            SET next_nonce = ?, updated_at = CURRENT_TIMESTAMP
            WHERE chain_id = ? AND signer_address = ? AND next_nonce = ?
            """,
            (nonce, chain_id, address, nonce + 1),
        )
        db.record_mutation_audit(
            entity_type="nonce_reservation",
            entity_id=f"{chain_id}:{address}:{nonce}",
            action="release",
            actor=actor,
            reason=reason,
            source=source,
        )
    return updated


def cleanup_orphaned_nonces(db: Any, chain_id: int, older_than_hours: int = 24) -> int:
    with tx.transaction_conn(db) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM nonce_reservations
                WHERE chain_id = ?
                  AND status = 'orphaned'
                  AND updated_at < datetime('now', ? || ' hours')
                """,
                (chain_id, f"-{older_than_hours}"),
            )
            return cursor.rowcount
        finally:
            cursor.close()
