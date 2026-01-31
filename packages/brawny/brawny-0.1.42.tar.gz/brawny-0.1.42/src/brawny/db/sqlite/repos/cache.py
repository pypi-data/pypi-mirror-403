from __future__ import annotations

from typing import Any

from brawny.db.base import ABICacheEntry, ProxyCacheEntry


def get_cached_abi(db: Any, chain_id: int, address: str) -> ABICacheEntry | None:
    address = db._normalize_address(address)
    row = db.execute_one(
        "SELECT * FROM abi_cache WHERE chain_id = ? AND address = ?",
        (chain_id, address),
    )
    if not row:
        return None
    return ABICacheEntry(
        chain_id=row["chain_id"],
        address=row["address"],
        abi_json=row["abi_json"],
        source=row["source"],
        resolved_at=row["resolved_at"],
    )


def set_cached_abi(
    db: Any,
    chain_id: int,
    address: str,
    abi_json: str,
    source: str,
) -> None:
    address = db._normalize_address(address)
    db.execute(
        """
        INSERT INTO abi_cache (chain_id, address, abi_json, source)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chain_id, address) DO UPDATE SET
            abi_json = excluded.abi_json,
            source = excluded.source,
            resolved_at = CURRENT_TIMESTAMP
        """,
        (chain_id, address, abi_json, source),
    )


def clear_cached_abi(db: Any, chain_id: int, address: str) -> bool:
    address = db._normalize_address(address)
    rowcount = db.execute_returning_rowcount(
        "DELETE FROM abi_cache WHERE chain_id = ? AND address = ?",
        (chain_id, address),
    )
    return rowcount > 0


def cleanup_expired_abis(db: Any, max_age_seconds: int) -> int:
    return db.execute_returning_rowcount(
        "DELETE FROM abi_cache WHERE resolved_at < datetime('now', ? || ' seconds')",
        (f"-{max_age_seconds}",),
    )


def get_cached_proxy(db: Any, chain_id: int, proxy_address: str) -> ProxyCacheEntry | None:
    proxy_address = db._normalize_address(proxy_address)
    row = db.execute_one(
        "SELECT * FROM proxy_cache WHERE chain_id = ? AND proxy_address = ?",
        (chain_id, proxy_address),
    )
    if not row:
        return None
    return ProxyCacheEntry(
        chain_id=row["chain_id"],
        proxy_address=row["proxy_address"],
        implementation_address=row["implementation_address"],
        resolved_at=row["resolved_at"],
    )


def set_cached_proxy(
    db: Any,
    chain_id: int,
    proxy_address: str,
    implementation_address: str,
) -> None:
    proxy_address = db._normalize_address(proxy_address)
    implementation_address = db._normalize_address(implementation_address)
    db.execute(
        """
        INSERT INTO proxy_cache (chain_id, proxy_address, implementation_address)
        VALUES (?, ?, ?)
        ON CONFLICT(chain_id, proxy_address) DO UPDATE SET
            implementation_address = excluded.implementation_address,
            resolved_at = CURRENT_TIMESTAMP
        """,
        (chain_id, proxy_address, implementation_address),
    )


def clear_cached_proxy(db: Any, chain_id: int, proxy_address: str) -> bool:
    proxy_address = db._normalize_address(proxy_address)
    rowcount = db.execute_returning_rowcount(
        "DELETE FROM proxy_cache WHERE chain_id = ? AND proxy_address = ?",
        (chain_id, proxy_address),
    )
    return rowcount > 0
