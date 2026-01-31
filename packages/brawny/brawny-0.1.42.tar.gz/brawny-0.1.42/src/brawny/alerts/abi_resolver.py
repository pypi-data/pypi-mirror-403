"""ABI resolution with Etherscan, Sourcify fallback, and proxy detection.

This module handles:
1. ABI fetching from Etherscan API
2. Sourcify fallback when Etherscan fails
3. EIP-1967 proxy detection and implementation resolution
4. Persistent caching in global ~/.brawny/abi_cache.db
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import httpx
from cachetools import TTLCache
from eth_utils import to_checksum_address

from brawny.alerts.errors import (
    ABINotFoundError,
    InvalidAddressError,
    ProxyResolutionError,
)
from brawny.db.global_cache import GlobalABICache
from brawny.logging import get_logger, log_unexpected
from brawny.network_guard import allow_network_calls

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny._rpc.clients import ReadClient


logger = get_logger(__name__)

# Short timeout to avoid blocking workers (Plan 08)
_FETCH_TIMEOUT = 2.0

# Address validation: 40 hex chars, optional 0x prefix
_ADDR_RE = re.compile(r"^(0x)?[0-9a-fA-F]{40}$")

# In-memory caches with different TTLs (fast-path before database):
# - Success cache: ABIs are immutable, cache for 24h
# - Failure cache: Cache misses for 30min (allows recovery if API fixed)
# Multi-threaded access (from worker threads) - protected by _mem_cache_lock
_mem_abi_cache: TTLCache[str, list[dict[str, Any]]] = TTLCache(maxsize=5_000, ttl=24 * 3600)
_mem_abi_not_found: TTLCache[str, bool] = TTLCache(maxsize=1_000, ttl=30 * 60)
_mem_cache_lock = threading.Lock()

# Module-level HTTP client for connection pooling
_http_client: httpx.Client | None = httpx.Client(timeout=_FETCH_TIMEOUT)


def close_http_client() -> None:
    """Close HTTP client on shutdown. Idempotent + safe in partial init."""
    global _http_client
    client, _http_client = _http_client, None
    if client is not None:
        client.close()
    # Also clear in-memory caches
    with _mem_cache_lock:
        _mem_abi_cache.clear()
        _mem_abi_not_found.clear()


def clear_memory_cache() -> None:
    """Clear in-memory ABI caches. Useful for testing."""
    with _mem_cache_lock:
        _mem_abi_cache.clear()
        _mem_abi_not_found.clear()


def _client() -> httpx.Client:
    """Get HTTP client, fail fast if closed."""
    if _http_client is None:
        raise RuntimeError("HTTP client is closed")
    return _http_client


def _is_valid_address(address: str) -> bool:
    """Check if string looks like a valid Ethereum address."""
    return bool(_ADDR_RE.match(address))


def _normalize_address(address: str) -> str:
    """Normalize address for cache key: lowercase with 0x prefix.

    Caller should validate with _is_valid_address() first.
    """
    addr = address.lower()
    if not addr.startswith("0x"):
        addr = "0x" + addr
    return addr


def _mem_cache_key(chain_id: int, address: str) -> str:
    """Build cache key for in-memory cache: chain_id:normalized_address."""
    return f"{chain_id}:{_normalize_address(address)}"


# EIP-1967 storage slots for proxy detection
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"

# Empty slot value (32 zero bytes)
EMPTY_SLOT = "0x" + "00" * 32

# Etherscan v2 API unified endpoint
ETHERSCAN_V2_API_URL = "https://api.etherscan.io/v2/api"

# Supported chain IDs for Etherscan v2 API
ETHERSCAN_SUPPORTED_CHAINS = {
    1,        # Ethereum Mainnet
    5,        # Goerli (deprecated)
    11155111, # Sepolia
    137,      # Polygon
    42161,    # Arbitrum One
    10,       # Optimism
    8453,     # Base
    56,       # BSC
    43114,    # Avalanche C-Chain
    250,      # Fantom
    42170,    # Arbitrum Nova
    59144,    # Linea
    534352,   # Scroll
    324,      # zkSync Era
}

# Chain ID to Sourcify chain name
SOURCIFY_CHAIN_IDS = {
    1: "1",
    5: "5",
    11155111: "11155111",
    137: "137",
    42161: "42161",
    10: "10",
    8453: "8453",
    56: "56",
    43114: "43114",
    250: "250",
}


@dataclass
class ResolvedABI:
    """Result of ABI resolution."""

    address: str
    abi: list[dict[str, Any]]
    source: str  # 'etherscan', 'sourcify', 'manual', 'proxy_implementation'
    implementation_address: str | None = None  # Set if resolved through proxy


class ABIResolver:
    """Resolves contract ABIs with caching and proxy support.

    Resolution order:
    1. Check in-memory TTLCache (fast-path, avoids blocking)
    2. Check database cache (with TTL validation)
    3. Detect if address is a proxy and resolve implementation
    4. Try Etherscan API (short timeout to avoid blocking workers)
    5. Try Sourcify as fallback
    6. Raise ABINotFoundError if all fail (or return None for resolve_safe)

    Policy (Plan 08):
    - Critical path (check/build): Use local ABIs via interfaces or with_abi()
    - Non-critical path (alerts/hooks): Runtime fetch is best-effort

    Proxy detection:
    - Checks EIP-1967 implementation slot
    - Checks EIP-1967 beacon slot (and reads implementation from beacon)
    - Recursively resolves up to 3 levels deep
    """

    def __init__(
        self,
        rpc: ReadClient,
        config: Config,
        abi_cache: GlobalABICache | None = None,
    ) -> None:
        self.abi_cache = abi_cache or GlobalABICache()
        self.rpc = rpc
        self.config = config
        self._etherscan_api_url = ETHERSCAN_V2_API_URL
        self._etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")
        self._sourcify_enabled = True
        self._request_timeout = _FETCH_TIMEOUT

    def resolve(
        self,
        address: str,
        chain_id: int | None = None,
        force_refresh: bool = False,
    ) -> ResolvedABI:
        """Resolve ABI for a contract address.

        Args:
            address: Contract address to resolve ABI for
            chain_id: Chain ID (defaults to config.chain_id)
            force_refresh: Bypass cache and fetch fresh ABI

        Returns:
            ResolvedABI with the contract ABI and metadata

        Raises:
            ABINotFoundError: If ABI cannot be resolved from any source
            InvalidAddressError: If address is invalid
        """
        # Validate address format (don't poison cache with garbage)
        if not _is_valid_address(address):
            raise InvalidAddressError(address)

        # Normalize for caching/lookup
        try:
            address = to_checksum_address(address)
        except ValueError:
            raise InvalidAddressError(address)

        chain_id = chain_id or self.config.chain_id
        cache_key = _mem_cache_key(chain_id, address)
        checked_sources: list[str] = []

        # Step 0/1: Check database cache first (authoritative), then memory cache.
        if not force_refresh:
            cached = self.abi_cache.get_cached_abi(chain_id, address)
            if cached and not self._is_cache_expired(cached.resolved_at):
                # Populate in-memory cache for next time
                abi = json.loads(cached.abi_json)
                with _mem_cache_lock:
                    _mem_abi_cache[cache_key] = abi
                return ResolvedABI(
                    address=address,
                    abi=abi,
                    source=cached.source,
                )
            with _mem_cache_lock:
                if cache_key in _mem_abi_cache:
                    return ResolvedABI(
                        address=address,
                        abi=_mem_abi_cache[cache_key],
                        source="memory_cache",
                    )
                if cache_key in _mem_abi_not_found:
                    raise ABINotFoundError(address, ["memory_cache"])

        # Step 2: Check if proxy and resolve implementation
        impl_address = self._resolve_proxy_implementation(chain_id, address)
        if impl_address and impl_address != address:
            logger.debug(
                "abi.proxy_detected",
                proxy=address,
                implementation=impl_address,
            )
            # Resolve ABI for implementation
            try:
                impl_abi = self._fetch_abi(chain_id, impl_address, checked_sources)
                if impl_abi:
                    # Cache both the proxy resolution and the ABI
                    self.abi_cache.set_cached_proxy(chain_id, address, impl_address)
                    self.abi_cache.set_cached_abi(
                        chain_id,
                        address,
                        json.dumps(impl_abi),
                        "proxy_implementation",
                    )
                    # Populate in-memory cache
                    with _mem_cache_lock:
                        _mem_abi_cache[cache_key] = impl_abi
                    return ResolvedABI(
                        address=address,
                        abi=impl_abi,
                        source="proxy_implementation",
                        implementation_address=impl_address,
                    )
            except Exception as e:
                # RECOVERABLE proxy implementation resolution failures fall back to next source.
                log_unexpected(
                    logger,
                    "abi.impl_resolution_failed",
                    proxy=address,
                    implementation=impl_address,
                    error=str(e),
                )

        # Step 3: Try to fetch ABI directly
        abi = self._fetch_abi(chain_id, address, checked_sources)
        if abi:
            source = checked_sources[-1] if checked_sources else "unknown"
            self.abi_cache.set_cached_abi(chain_id, address, json.dumps(abi), source)
            # Populate in-memory cache
            with _mem_cache_lock:
                _mem_abi_cache[cache_key] = abi
            return ResolvedABI(address=address, abi=abi, source=source)

        # Cache failure in memory (shorter TTL allows recovery)
        with _mem_cache_lock:
            _mem_abi_not_found[cache_key] = True

        raise ABINotFoundError(address, checked_sources)

    def resolve_safe(
        self,
        address: str,
        chain_id: int | None = None,
    ) -> ResolvedABI | None:
        """Resolve ABI with fail-open behavior (returns None instead of raising).

        Use this for non-critical paths where missing ABI should be handled
        gracefully (e.g., event decoding in alerts, lifecycle hooks).

        Args:
            address: Contract address to resolve ABI for
            chain_id: Chain ID (defaults to config.chain_id)

        Returns:
            ResolvedABI if found, None if resolution fails for any reason
        """
        try:
            return self.resolve(address, chain_id=chain_id)
        except (ABINotFoundError, InvalidAddressError):
            return None
        except Exception as e:
            # RECOVERABLE resolve_safe is explicitly fail-open.
            log_unexpected(
                logger,
                "abi_resolver.resolve_safe_error",
                address=address[:50] if address else "None",
                error=type(e).__name__,
            )
            return None

    def _is_cache_expired(self, resolved_at: datetime) -> bool:
        """Check if cached entry is expired based on TTL."""
        if self.config.abi_cache_ttl_seconds <= 0:
            return True

        now = datetime.now(timezone.utc)
        if resolved_at.tzinfo is None:
            resolved_at = resolved_at.replace(tzinfo=timezone.utc)

        age_seconds = (now - resolved_at).total_seconds()
        return age_seconds > self.config.abi_cache_ttl_seconds

    def _resolve_proxy_implementation(
        self,
        chain_id: int,
        address: str,
        depth: int = 0,
    ) -> str | None:
        """Resolve proxy to implementation address using EIP-1967.

        Args:
            chain_id: Chain ID
            address: Proxy address
            depth: Current recursion depth (max 3)

        Returns:
            Implementation address or None if not a proxy
        """
        if depth > 3:
            logger.warning("proxy.max_depth_exceeded", address=address)
            return None

        # Check cache first
        cached = self.abi_cache.get_cached_proxy(chain_id, address)
        if cached:
            # Recursively check if cached implementation is also a proxy
            nested = self._resolve_proxy_implementation(
                chain_id, cached.implementation_address, depth + 1
            )
            return nested or cached.implementation_address

        # Try EIP-1967 implementation slot
        try:
            impl = self._read_storage_slot(address, IMPLEMENTATION_SLOT)
            if impl and impl != EMPTY_SLOT:
                impl_address = self._slot_to_address(impl)
                if impl_address:
                    # Recursively check if implementation is also a proxy
                    nested = self._resolve_proxy_implementation(
                        chain_id, impl_address, depth + 1
                    )
                    final_impl = nested or impl_address
                    self.abi_cache.set_cached_proxy(chain_id, address, final_impl)
                    return final_impl
        except Exception as e:
            # RECOVERABLE proxy slot read failures fall back to other resolution paths.
            log_unexpected(logger, "proxy.impl_slot_error", address=address, error=str(e))

        # Try EIP-1967 beacon slot
        try:
            beacon = self._read_storage_slot(address, BEACON_SLOT)
            if beacon and beacon != EMPTY_SLOT:
                beacon_address = self._slot_to_address(beacon)
                if beacon_address:
                    # Read implementation from beacon
                    impl_address = self._read_beacon_implementation(beacon_address)
                    if impl_address:
                        nested = self._resolve_proxy_implementation(
                            chain_id, impl_address, depth + 1
                        )
                        final_impl = nested or impl_address
                        self.abi_cache.set_cached_proxy(chain_id, address, final_impl)
                        return final_impl
        except (ValueError, TypeError) as e:
            logger.debug("proxy.beacon_slot_error", address=address, error=str(e))

        return None

    def _read_storage_slot(self, address: str, slot: str) -> str | None:
        """Read a storage slot from a contract."""
        from brawny._rpc.errors import RPCError

        try:
            result = self.rpc.get_storage_at(address, slot)
            if result is None:
                return None
            # Convert bytes to hex string if needed
            if isinstance(result, bytes):
                return "0x" + result.hex()
            return result
        except (RPCError, ValueError, TypeError):
            return None

    def _slot_to_address(self, slot_value: str) -> str | None:
        """Extract address from storage slot value."""
        if not slot_value or slot_value == EMPTY_SLOT:
            return None

        # Remove 0x prefix and take last 40 chars (20 bytes = address)
        if slot_value.startswith("0x"):
            slot_value = slot_value[2:]

        if len(slot_value) < 40:
            return None

        # Address is in the last 40 characters
        addr_hex = slot_value[-40:]

        # Check if it's a valid non-zero address
        if addr_hex == "0" * 40:
            return None

        try:
            return to_checksum_address("0x" + addr_hex)
        except ValueError:
            return None

    def _read_beacon_implementation(self, beacon_address: str) -> str | None:
        """Read implementation address from a beacon contract.

        Beacons typically have an implementation() function.
        """
        from brawny._rpc.errors import RPCError

        # implementation() function selector: 0x5c60da1b
        try:
            tx_params = {"to": beacon_address, "data": "0x5c60da1b"}
            result = self.rpc.eth_call(tx_params)
            if result:
                # Convert bytes to hex string if needed
                if isinstance(result, bytes):
                    result = "0x" + result.hex()
                if result != "0x":
                    return self._slot_to_address(result)
        except (RPCError, ValueError, TypeError) as e:
            logger.debug(
                "proxy.beacon_call_error",
                beacon=beacon_address,
                error=str(e),
            )
        return None

    def _fetch_abi(
        self,
        chain_id: int,
        address: str,
        checked_sources: list[str],
    ) -> list[dict[str, Any]] | None:
        """Fetch ABI from external sources.

        Tries Etherscan v2 API first, then Sourcify as fallback.
        """
        # Try Etherscan first (works without API key, but rate-limited)
        if chain_id in ETHERSCAN_SUPPORTED_CHAINS:
            checked_sources.append("etherscan")
            abi = self._fetch_from_etherscan(chain_id, address)
            if abi:
                return abi

        # Try Sourcify as fallback if enabled
        if self._sourcify_enabled:
            checked_sources.append("sourcify")
            abi = self._fetch_from_sourcify(chain_id, address)
            if abi:
                return abi

        return None

    def _fetch_from_etherscan(
        self,
        chain_id: int,
        address: str,
    ) -> list[dict[str, Any]] | None:
        """Fetch ABI from Etherscan v2 API.

        Uses the unified v2 endpoint with chainid parameter.
        Works without API key but with stricter rate limits.
        """
        api_url = self._etherscan_api_url

        params: dict[str, Any] = {
            "chainid": chain_id,
            "module": "contract",
            "action": "getabi",
            "address": address,
        }

        # Add API key if configured (higher rate limits)
        if self._etherscan_api_key:
            params["apikey"] = self._etherscan_api_key

        try:
            with allow_network_calls(reason="alerts"):
                response = _client().get(api_url, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "1" and data.get("result"):
                abi = json.loads(data["result"])
                logger.debug(
                    "etherscan.abi_fetched",
                    address=address,
                    chain_id=chain_id,
                )
                return abi
            else:
                logger.warning(
                    "etherscan.abi_fetch_failed",
                    address=address,
                    chain_id=chain_id,
                    etherscan_status=data.get("status"),
                    etherscan_message=data.get("message"),
                )
        except httpx.TimeoutException:
            logger.warning(
                "etherscan.timeout",
                address=address,
                chain_id=chain_id,
            )
        except httpx.HTTPStatusError as e:
            logger.warning(
                "etherscan.http_error",
                address=address,
                chain_id=chain_id,
                status=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.warning(
                "etherscan.request_error",
                address=address,
                chain_id=chain_id,
                error=str(e),
            )
        except json.JSONDecodeError as e:
            logger.warning(
                "etherscan.json_error",
                address=address,
                chain_id=chain_id,
                error=str(e),
            )

        return None

    def _fetch_from_sourcify(
        self,
        chain_id: int,
        address: str,
    ) -> list[dict[str, Any]] | None:
        """Fetch ABI from Sourcify."""
        # Try full match first
        abi = self._fetch_sourcify_match(chain_id, address, full_match=True)
        if abi:
            return abi

        # Try partial match
        return self._fetch_sourcify_match(chain_id, address, full_match=False)

    def _fetch_sourcify_match(
        self,
        chain_id: int,
        address: str,
        full_match: bool,
    ) -> list[dict[str, Any]] | None:
        """Fetch from Sourcify with specific match type."""
        match_type = "full_match" if full_match else "partial_match"
        url = f"https://sourcify.dev/server/repository/contracts/{match_type}/{chain_id}/{address}/metadata.json"

        try:
            with allow_network_calls(reason="alerts"):
                response = _client().get(url)
            response.raise_for_status()
            metadata = response.json()
            if "output" in metadata and "abi" in metadata["output"]:
                logger.debug(
                    "sourcify.abi_fetched",
                    address=address,
                    match_type=match_type,
                )
                return metadata["output"]["abi"]
        except httpx.TimeoutException:
            logger.debug("sourcify.timeout", address=address)
        except httpx.HTTPStatusError as e:
            # 404 is expected when contract not found
            if e.response.status_code != 404:
                logger.debug(
                    "sourcify.http_error",
                    address=address,
                    status=e.response.status_code,
                )
        except httpx.RequestError as e:
            logger.debug("sourcify.request_error", address=address, error=str(e))
        except json.JSONDecodeError as e:
            logger.debug("sourcify.json_error", address=address, error=str(e))

        return None

    def clear_cache(self, address: str, chain_id: int | None = None) -> bool:
        """Clear cached ABI and proxy resolution for an address.

        Clears both in-memory and database caches.

        Args:
            address: Contract address
            chain_id: Chain ID (defaults to config.chain_id)

        Returns:
            True if cache entry was cleared
        """
        chain_id = chain_id or self.config.chain_id
        try:
            address = to_checksum_address(address)
        except ValueError:
            raise InvalidAddressError(address)

        # Clear in-memory cache
        cache_key = _mem_cache_key(chain_id, address)
        with _mem_cache_lock:
            _mem_abi_cache.pop(cache_key, None)
            _mem_abi_not_found.pop(cache_key, None)

        # Clear database cache
        abi_cleared = self.abi_cache.clear_cached_abi(chain_id, address)
        proxy_cleared = self.abi_cache.clear_cached_proxy(chain_id, address)

        return abi_cleared or proxy_cleared

    def set_manual_abi(
        self,
        address: str,
        abi: list[dict[str, Any]],
        chain_id: int | None = None,
    ) -> None:
        """Manually set ABI for a contract.

        Populates both in-memory and database caches.

        Args:
            address: Contract address
            abi: ABI to cache
            chain_id: Chain ID (defaults to config.chain_id)
        """
        chain_id = chain_id or self.config.chain_id
        try:
            address = to_checksum_address(address)
        except ValueError:
            raise InvalidAddressError(address)

        # Populate in-memory cache
        cache_key = _mem_cache_key(chain_id, address)
        with _mem_cache_lock:
            _mem_abi_cache[cache_key] = abi
            _mem_abi_not_found.pop(cache_key, None)  # Clear any failure marker

        # Populate database cache
        self.abi_cache.set_cached_abi(chain_id, address, json.dumps(abi), "manual")
        logger.info("abi.manual_set", address=address, chain_id=chain_id)


def get_function_signature(name: str, inputs: list[dict[str, Any]]) -> str:
    """Build function signature string from name and inputs.

    Example: "transfer(address,uint256)"
    """
    types = [inp["type"] for inp in inputs]
    return f"{name}({','.join(types)})"


def get_event_signature(name: str, inputs: list[dict[str, Any]]) -> str:
    """Build event signature string from name and inputs.

    Example: "Transfer(address,address,uint256)"
    """
    types = [inp["type"] for inp in inputs]
    return f"{name}({','.join(types)})"
