from __future__ import annotations

from typing import Any


def cleanup_old_intents(
    db: Any,
    older_than_days: int,
    statuses: list[str] | None = None,
) -> int:
    if statuses is None:
        statuses = ["confirmed", "failed", "abandoned"]

    placeholders = ",".join("?" * len(statuses))
    return db.execute_returning_rowcount(
        f"""
        DELETE FROM tx_intents
        WHERE status = 'terminal'
          AND terminal_reason IN ({placeholders})
        AND created_at < datetime('now', ? || ' days')
        """,
        (*statuses, f"-{older_than_days}"),
    )


def get_database_stats(db: Any) -> dict[str, Any]:
    stats: dict[str, Any] = {"type": "sqlite", "path": db._database_path}

    rows = db.execute_returning(
        "SELECT status, COUNT(*) as count FROM tx_intents GROUP BY status"
    )
    stats["intents_by_status"] = {row["status"]: row["count"] for row in rows}

    row = db.execute_one("SELECT COUNT(*) as count FROM jobs")
    stats["total_jobs"] = row["count"] if row else 0

    row = db.execute_one("SELECT COUNT(*) as count FROM jobs WHERE enabled = 1")
    stats["enabled_jobs"] = row["count"] if row else 0

    rows = db.execute_returning("SELECT * FROM block_state")
    stats["block_states"] = [
        {
            "chain_id": row["chain_id"],
            "last_block": row["last_processed_block_number"],
        }
        for row in rows
    ]

    return stats


def clear_orphaned_claims(db: Any, chain_id: int, older_than_minutes: int = 2) -> int:
    return db.execute_returning_rowcount(
        """
        UPDATE tx_intents
        SET claim_token = NULL,
            claimed_at = NULL,
            claimed_by = NULL,
            lease_expires_at = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ?
          AND status != 'claimed'
          AND claim_token IS NOT NULL
          AND claimed_at IS NOT NULL
          AND claimed_at < datetime('now', ? || ' minutes')
        """,
        (chain_id, f"-{older_than_minutes}"),
    )


def release_orphaned_nonces(db: Any, chain_id: int, older_than_minutes: int = 5) -> int:
    return db.execute_returning_rowcount(
        """
        UPDATE nonce_reservations
        SET status = 'released',
            updated_at = CURRENT_TIMESTAMP
        WHERE chain_id = ?
          AND status IN ('reserved', 'in_flight')
          AND updated_at < datetime('now', ? || ' minutes')
          AND intent_id IN (
              SELECT intent_id FROM tx_intents
              WHERE status = 'terminal'
                AND terminal_reason IN ('failed', 'abandoned')
              AND updated_at < datetime('now', ? || ' minutes')
          )
        """,
        (chain_id, f"-{older_than_minutes}", f"-{older_than_minutes}"),
    )


def count_broadcasted_without_attempts(db: Any, chain_id: int) -> int:
    result = db.execute_one(
        """
        SELECT COUNT(*) as count
        FROM tx_intents ti
        LEFT JOIN tx_attempts ta ON ti.intent_id = ta.intent_id
        WHERE ti.chain_id = ?
          AND ti.status = 'broadcasted'
          AND ta.attempt_id IS NULL
        """,
        (chain_id,),
    )
    return result["count"] if result else 0


def count_stale_claims(db: Any, chain_id: int, older_than_minutes: int = 10) -> int:
    result = db.execute_one(
        """
        SELECT COUNT(*) as count
        FROM tx_intents
        WHERE chain_id = ?
          AND status = 'claimed'
          AND claimed_at IS NOT NULL
          AND COALESCE(lease_expires_at, datetime(claimed_at, ? || ' minutes')) < CURRENT_TIMESTAMP
        """,
        (chain_id, f"+{older_than_minutes}"),
    )
    return result["count"] if result else 0


def count_stuck_claimed(db: Any, chain_id: int, older_than_minutes: int = 10) -> int:
    result = db.execute_one(
        """
        SELECT COUNT(*) as count
        FROM tx_intents
        WHERE chain_id = ?
          AND status = 'claimed'
          AND COALESCE(lease_expires_at, datetime(claimed_at, ? || ' minutes')) < CURRENT_TIMESTAMP
        """,
        (chain_id, f"+{older_than_minutes}"),
    )
    return result["count"] if result else 0


def count_orphaned_claims(db: Any, chain_id: int) -> int:
    result = db.execute_one(
        """
        SELECT COUNT(*) as count
        FROM tx_intents
        WHERE chain_id = ?
          AND status != 'claimed'
          AND claim_token IS NOT NULL
        """,
        (chain_id,),
    )
    return result["count"] if result else 0


def count_orphaned_nonces(db: Any, chain_id: int) -> int:
    result = db.execute_one(
        """
        SELECT COUNT(*) as count
        FROM nonce_reservations nr
        JOIN tx_intents ti ON nr.intent_id = ti.intent_id
        WHERE nr.chain_id = ?
          AND nr.status IN ('reserved', 'in_flight')
          AND ti.status = 'terminal'
          AND ti.terminal_reason IN ('failed', 'abandoned')
        """,
        (chain_id,),
    )
    return result["count"] if result else 0


def get_oldest_nonce_gap_age_seconds(db: Any, chain_id: int) -> float:
    result = db.execute_one(
        """
        SELECT COALESCE(
            (julianday('now') - julianday(datetime(MIN(nr.created_at)))) * 86400,
            0
        ) AS oldest_gap_seconds
        FROM signers s
        JOIN nonce_reservations nr
          ON nr.chain_id = s.chain_id
         AND nr.signer_address = s.signer_address
        WHERE s.chain_id = ?
          AND s.last_synced_chain_nonce IS NOT NULL
          AND nr.status IN ('reserved', 'in_flight')
          AND nr.nonce < s.last_synced_chain_nonce
        """,
        (chain_id,),
    )
    if not result:
        return 0.0
    return float(result["oldest_gap_seconds"])
