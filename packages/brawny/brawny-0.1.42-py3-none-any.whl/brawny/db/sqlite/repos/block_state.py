from __future__ import annotations

from typing import Any

from brawny.db.base import BlockState


def get_block_state(db: Any, chain_id: int) -> BlockState | None:
    row = db.execute_one(
        "SELECT * FROM block_state WHERE chain_id = ?",
        (chain_id,),
    )
    if not row:
        return None
    return BlockState(
        chain_id=row["chain_id"],
        last_processed_block_number=row["last_processed_block_number"],
        last_processed_block_hash=row["last_processed_block_hash"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def upsert_block_state(db: Any, chain_id: int, block_number: int, block_hash: str) -> None:
    db.execute(
        """
        INSERT INTO block_state (chain_id, last_processed_block_number, last_processed_block_hash)
        VALUES (?, ?, ?)
        ON CONFLICT(chain_id) DO UPDATE SET
            last_processed_block_number = excluded.last_processed_block_number,
            last_processed_block_hash = excluded.last_processed_block_hash,
            updated_at = CURRENT_TIMESTAMP
        """,
        (chain_id, block_number, block_hash),
    )


def get_block_hash_at_height(db: Any, chain_id: int, block_number: int) -> str | None:
    row = db.execute_one(
        "SELECT block_hash FROM block_hash_history WHERE chain_id = ? AND block_number = ?",
        (chain_id, block_number),
    )
    return row["block_hash"] if row else None


def insert_block_hash(db: Any, chain_id: int, block_number: int, block_hash: str) -> None:
    db.execute(
        """
        INSERT INTO block_hash_history (chain_id, block_number, block_hash)
        VALUES (?, ?, ?)
        ON CONFLICT(chain_id, block_number) DO UPDATE SET
            block_hash = excluded.block_hash,
            inserted_at = CURRENT_TIMESTAMP
        """,
        (chain_id, block_number, block_hash),
    )


def delete_block_hashes_above(db: Any, chain_id: int, block_number: int) -> int:
    return db.execute_returning_rowcount(
        "DELETE FROM block_hash_history WHERE chain_id = ? AND block_number > ?",
        (chain_id, block_number),
    )


def delete_block_hash_at_height(db: Any, chain_id: int, block_number: int) -> bool:
    rowcount = db.execute_returning_rowcount(
        "DELETE FROM block_hash_history WHERE chain_id = ? AND block_number = ?",
        (chain_id, block_number),
    )
    return rowcount > 0


def cleanup_old_block_hashes(db: Any, chain_id: int, keep_count: int) -> int:
    row = db.execute_one(
        "SELECT MAX(block_number) as max_block FROM block_hash_history WHERE chain_id = ?",
        (chain_id,),
    )
    if not row or row["max_block"] is None:
        return 0

    cutoff = row["max_block"] - keep_count + 1
    return db.execute_returning_rowcount(
        "DELETE FROM block_hash_history WHERE chain_id = ? AND block_number < ?",
        (chain_id, cutoff),
    )


def clear_block_hash_history(db: Any, chain_id: int) -> int:
    return db.execute_returning_rowcount(
        "DELETE FROM block_hash_history WHERE chain_id = ?",
        (chain_id,),
    )


def get_oldest_block_in_history(db: Any, chain_id: int) -> int | None:
    row = db.execute_one(
        "SELECT MIN(block_number) as min_block FROM block_hash_history WHERE chain_id = ?",
        (chain_id,),
    )
    return row["min_block"] if row else None


def get_latest_block_in_history(db: Any, chain_id: int) -> int | None:
    row = db.execute_one(
        "SELECT MAX(block_number) as max_block FROM block_hash_history WHERE chain_id = ?",
        (chain_id,),
    )
    return row["max_block"] if row else None
