"""Gas quote system with block-aware caching.

Cache semantics (OE6):
- Cache is keyed by (block_number, block_hash) to handle same-height reorgs
- Cache hit: if block (number, hash) is identical, return cached base_fee
- One RPC call per invocation (get_block returns number, hash, baseFee)

Why no TTL? We fetch the latest block on every call to get current (number, hash).
If they match our cache, the base_fee hasn't changed. TTL would only add complexity
without reducing RPC calls.

Reorg handling: If a reorg replaces block N with different content, the block hash
changes. Our cache key includes hash, so we'll miss and refetch.
"""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING

from brawny.timeout import Deadline
if TYPE_CHECKING:
    from brawny._rpc.clients import ReadClient

# Bounded executor for async wrappers (prevents thread starvation)
_GAS_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gas_rpc")


@dataclass(frozen=True)
class GasQuote:
    """EIP-1559 gas quote with block context for cache validation."""

    base_fee: int
    block_number: int
    block_hash: str
    timestamp: float

    def matches_block(self, block_number: int, block_hash: str) -> bool:
        """Check if this quote matches the given block (number AND hash)."""
        return self.block_number == block_number and self.block_hash == block_hash


class GasQuoteCache:
    """Gas quote cache keyed by (block_number, block_hash).

    Cache hit requires: same block (number AND hash).
    No TTL needed since we fetch latest block each call.
    """

    def __init__(self, rpc: "ReadClient", ttl_seconds: int = 15) -> None:
        """Initialize gas cache.

        Args:
            rpc: RPC manager for fetching blocks
            ttl_seconds: Ignored (kept for backwards compatibility).
                         Cache is now keyed by block, not TTL.
        """
        self._rpc = rpc
        self._cache: GasQuote | None = None
        self._lock = asyncio.Lock()

    async def get_quote(self) -> GasQuote:
        """Get gas quote (async).

        Cache hit: same block (number AND hash) -> return cached.
        One RPC call per invocation regardless of cache hit/miss.
        """
        async with self._lock:
            return await self._fetch_quote()

    async def _fetch_quote(self) -> GasQuote:
        """Fetch quote from RPC, using cache if block matches."""
        loop = asyncio.get_running_loop()

        # Run sync RPC call in bounded executor with timeout
        block = await asyncio.wait_for(
            loop.run_in_executor(_GAS_EXECUTOR, lambda: self._rpc.get_block("latest")),
            timeout=10.0,
        )

        # Extract block identifiers
        block_number = block.get("number", 0)
        if isinstance(block_number, str):
            block_number = int(block_number, 16)
        block_hash = block.get("hash", "")
        if hasattr(block_hash, "hex"):
            block_hash = block_hash.hex()
        elif not isinstance(block_hash, str):
            block_hash = str(block_hash)

        # Cache hit: same block (number AND hash)
        if self._cache is not None and self._cache.matches_block(block_number, block_hash):
            return self._cache

        # Cache miss: extract base_fee from already-fetched block
        base_fee = block.get("baseFeePerGas", 0)
        if isinstance(base_fee, str):
            base_fee = int(base_fee, 16)
        else:
            base_fee = int(base_fee) if base_fee else 0

        # Validate base_fee (0 = missing/pre-EIP-1559 chain = invalid)
        if base_fee == 0:
            raise ValueError("baseFeePerGas is 0 or missing (non-EIP-1559 chain?)")

        quote = GasQuote(
            base_fee=base_fee,
            block_number=block_number,
            block_hash=block_hash,
            timestamp=time.time(),
        )
        self._cache = quote
        return quote

    def get_quote_sync(self, deadline: "Deadline | None" = None) -> GasQuote | None:
        """Get cached quote if available (non-blocking, for executor).

        Returns cached quote without checking block freshness.
        Caller should be aware this may be from a previous block.
        """
        if self._cache is None:
            self._cache = self._fetch_quote_sync(deadline)
        return self._cache

    def _fetch_quote_sync(self, deadline: "Deadline | None") -> GasQuote:
        """Fetch quote synchronously from RPC."""
        block = self._rpc.get_block("latest", deadline=deadline)

        block_number = block.get("number", 0)
        if isinstance(block_number, str):
            block_number = int(block_number, 16)
        block_hash = block.get("hash", "")
        if hasattr(block_hash, "hex"):
            block_hash = block_hash.hex()
        elif not isinstance(block_hash, str):
            block_hash = str(block_hash)

        base_fee = block.get("baseFeePerGas", 0)
        if isinstance(base_fee, str):
            base_fee = int(base_fee, 16)
        else:
            base_fee = int(base_fee) if base_fee else 0

        if base_fee == 0:
            raise ValueError("baseFeePerGas is 0 or missing (non-EIP-1559 chain?)")

        return GasQuote(
            base_fee=base_fee,
            block_number=block_number,
            block_hash=block_hash,
            timestamp=time.time(),
        )

    def invalidate(self) -> None:
        """Force refresh on next call."""
        self._cache = None
