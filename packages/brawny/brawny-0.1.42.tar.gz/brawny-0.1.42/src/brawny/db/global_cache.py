"""Global ABI cache stored in ~/.brawny/abi_cache.db

This module provides a standalone SQLite database for caching contract ABIs
and proxy resolutions. Unlike the project database, this cache is shared
across all projects and persists in the user's home directory.

Mirrors eth-brownie's ~/.brownie/ pattern for global data storage.
"""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from brawny.utils import db_address

if TYPE_CHECKING:
    pass

# Global paths (following brownie's ~/.brownie/ pattern)
BRAWNY_DIR = Path.home() / ".brawny"
ABI_CACHE_DB = BRAWNY_DIR / "abi_cache.db"


@dataclass
class ABICacheEntry:
    """Cached ABI entry."""

    chain_id: int
    address: str
    abi_json: str
    source: str
    resolved_at: datetime


@dataclass
class ProxyCacheEntry:
    """Cached proxy resolution."""

    chain_id: int
    proxy_address: str
    implementation_address: str
    resolved_at: datetime


class GlobalABICache:
    """SQLite-backed global ABI cache.

    Provides persistent storage for contract ABIs and proxy resolutions
    in ~/.brawny/abi_cache.db. Auto-creates the database and schema
    on first use.

    Thread-safe for concurrent access within a single process.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the cache.

        Args:
            db_path: Override path for testing. Defaults to ~/.brawny/abi_cache.db
        """
        self._db_path = db_path or ABI_CACHE_DB
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()

    def _ensure_connected(self) -> sqlite3.Connection:
        """Ensure database connection exists, creating if needed."""
        if self._conn is None:
            # Create directory if needed
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            # Connect with check_same_thread=False for multi-threaded use
            self._conn = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
                timeout=30.0,
            )
            self._conn.row_factory = sqlite3.Row
            self._init_schema()

        return self._conn

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        if self._conn is None:
            raise RuntimeError("Global cache connection not initialized")

        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS abi_cache (
                chain_id INTEGER NOT NULL,
                address TEXT NOT NULL,
                abi_json TEXT NOT NULL,
                source TEXT NOT NULL,
                resolved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chain_id, address)
            );

            CREATE INDEX IF NOT EXISTS idx_abi_cache_resolved
                ON abi_cache(resolved_at);

            CREATE TABLE IF NOT EXISTS proxy_cache (
                chain_id INTEGER NOT NULL,
                proxy_address TEXT NOT NULL,
                implementation_address TEXT NOT NULL,
                resolved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chain_id, proxy_address)
            );
        """)
        self._conn.commit()

    def get_cached_abi(self, chain_id: int, address: str) -> ABICacheEntry | None:
        """Get cached ABI for a contract.

        Args:
            chain_id: Chain ID
            address: Contract address (checksummed)

        Returns:
            ABICacheEntry if found, None otherwise
        """
        address = db_address(address)
        with self._lock:
            conn = self._ensure_connected()
            cursor = conn.execute(
                "SELECT * FROM abi_cache WHERE chain_id = ? AND address = ?",
                (chain_id, address),
            )
            row = cursor.fetchone()
            if not row:
                return None

            resolved_at = row["resolved_at"]
            if isinstance(resolved_at, str):
                resolved_at = datetime.fromisoformat(resolved_at)

            return ABICacheEntry(
                chain_id=row["chain_id"],
                address=row["address"],
                abi_json=row["abi_json"],
                source=row["source"],
                resolved_at=resolved_at,
            )

    def set_cached_abi(
        self,
        chain_id: int,
        address: str,
        abi_json: str,
        source: str,
    ) -> None:
        """Cache an ABI for a contract.

        Args:
            chain_id: Chain ID
            address: Contract address (checksummed)
            abi_json: JSON-encoded ABI
            source: Source of ABI ('etherscan', 'sourcify', 'manual', 'proxy_implementation')
        """
        address = db_address(address)
        with self._lock:
            conn = self._ensure_connected()
            conn.execute(
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
            conn.commit()

    def clear_cached_abi(self, chain_id: int, address: str) -> bool:
        """Clear cached ABI for a contract.

        Args:
            chain_id: Chain ID
            address: Contract address

        Returns:
            True if entry was deleted, False if not found
        """
        address = db_address(address)
        with self._lock:
            conn = self._ensure_connected()
            cursor = conn.execute(
                "DELETE FROM abi_cache WHERE chain_id = ? AND address = ?",
                (chain_id, address),
            )
            conn.commit()
            return cursor.rowcount > 0

    def cleanup_expired_abis(self, max_age_seconds: int) -> int:
        """Delete ABIs older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of entries deleted
        """
        with self._lock:
            conn = self._ensure_connected()
            cursor = conn.execute(
                """
                DELETE FROM abi_cache
                WHERE resolved_at < datetime('now', ? || ' seconds')
                """,
                (f"-{max_age_seconds}",),
            )
            conn.commit()
            return cursor.rowcount

    def get_cached_proxy(
        self, chain_id: int, proxy_address: str
    ) -> ProxyCacheEntry | None:
        """Get cached proxy implementation address.

        Args:
            chain_id: Chain ID
            proxy_address: Proxy contract address

        Returns:
            ProxyCacheEntry if found, None otherwise
        """
        proxy_address = db_address(proxy_address)
        with self._lock:
            conn = self._ensure_connected()
            cursor = conn.execute(
                "SELECT * FROM proxy_cache WHERE chain_id = ? AND proxy_address = ?",
                (chain_id, proxy_address),
            )
            row = cursor.fetchone()
            if not row:
                return None

            resolved_at = row["resolved_at"]
            if isinstance(resolved_at, str):
                resolved_at = datetime.fromisoformat(resolved_at)

            return ProxyCacheEntry(
                chain_id=row["chain_id"],
                proxy_address=row["proxy_address"],
                implementation_address=row["implementation_address"],
                resolved_at=resolved_at,
            )

    def set_cached_proxy(
        self,
        chain_id: int,
        proxy_address: str,
        implementation_address: str,
    ) -> None:
        """Cache a proxy-to-implementation mapping.

        Args:
            chain_id: Chain ID
            proxy_address: Proxy contract address
            implementation_address: Implementation contract address
        """
        proxy_address = db_address(proxy_address)
        implementation_address = db_address(implementation_address)
        with self._lock:
            conn = self._ensure_connected()
            conn.execute(
                """
                INSERT INTO proxy_cache (chain_id, proxy_address, implementation_address)
                VALUES (?, ?, ?)
                ON CONFLICT(chain_id, proxy_address) DO UPDATE SET
                    implementation_address = excluded.implementation_address,
                    resolved_at = CURRENT_TIMESTAMP
                """,
                (chain_id, proxy_address, implementation_address),
            )
            conn.commit()

    def clear_cached_proxy(self, chain_id: int, proxy_address: str) -> bool:
        """Clear cached proxy resolution.

        Args:
            chain_id: Chain ID
            proxy_address: Proxy contract address

        Returns:
            True if entry was deleted, False if not found
        """
        proxy_address = db_address(proxy_address)
        with self._lock:
            conn = self._ensure_connected()
            cursor = conn.execute(
                "DELETE FROM proxy_cache WHERE chain_id = ? AND proxy_address = ?",
                (chain_id, proxy_address),
            )
            conn.commit()
            return cursor.rowcount > 0

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
