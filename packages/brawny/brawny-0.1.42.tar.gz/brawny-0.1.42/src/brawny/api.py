"""Public API helpers for implicit context.

These functions provide a Flask-like implicit context pattern for job hooks.
Import and use them directly - they read from contextvars set by the framework.

Usage:
    from brawny import Contract, trigger, intent, block

    @job(signer="harvester")
    class VaultHarvester(Job):
        def check(self):
            vault = Contract("vault")
            if vault.totalAssets() > 10e18:
                return trigger(reason="Harvest time", tx_required=True)

        def build_intent(self, trig):
            vault = Contract("vault")
            return intent(
                to_address=vault.address,
                data=vault.harvest.encode_input(),
            )  # signer inherited from @job decorator
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from brawny._context import get_current_job, get_job_context

if TYPE_CHECKING:
    from brawny.alerts.contracts import ContractHandle
    from brawny.model.types import Trigger, TxIntentSpec
    from brawny._rpc.gas import GasQuote


def trigger(
    reason: str,
    tx_required: bool = True,
    idempotency_parts: list[str | int | bytes] | None = None,
) -> Trigger:
    """Create a Trigger to signal that action is needed.

    Only valid inside check().

    Args:
        reason: Human-readable description of why we're triggering
            (auto-included in intent.metadata["reason"])
        tx_required: Whether this trigger needs a transaction (default True)
        idempotency_parts: Optional list for deduplication

    Returns:
        Trigger instance

    Raises:
        LookupError: If called outside check()

    Example:
        if profit > threshold:
            return trigger(reason=f"Harvesting {profit} profit")
    """
    from brawny.model.types import Trigger as TriggerType

    # Verify we're in a job context (check() or build_tx())
    get_job_context()

    return TriggerType(
        reason=reason,
        tx_required=tx_required,
        idempotency_parts=idempotency_parts or [],
    )


def intent(
    to_address: str,
    data: str | None = None,
    value_wei: str | int | float = 0,
    gas_limit: int | float | None = None,
    max_fee_per_gas: int | float | None = None,
    max_priority_fee_per_gas: int | float | None = None,
    min_confirmations: int = 1,
    deadline_seconds: int | None = None,
    *,
    signer_address: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> TxIntentSpec:
    """Create a transaction intent specification.

    Only valid inside build_intent().

    Args:
        to_address: Target contract address
        data: Calldata (hex string)
        value_wei: ETH value in wei (int or string)
        gas_limit: Optional gas limit override
        max_fee_per_gas: Optional EIP-1559 max fee
        max_priority_fee_per_gas: Optional EIP-1559 priority fee
        min_confirmations: Confirmations required (default 1)
        deadline_seconds: Optional deadline for transaction
        signer_address: Signer alias or hex address. If not provided, uses
            the signer from @job(signer="...") decorator.
        metadata: Per-intent context for alerts. Merged with trigger.reason
            (job metadata wins on key collision).

    Returns:
        TxIntentSpec instance

    Raises:
        LookupError: If called outside build_intent()
        RuntimeError: If no signer specified and job has no default signer

    Example:
        vault = Contract("vault")
        return intent(
            to_address=vault.address,
            data=vault.harvest.encode_input(),
            metadata={"profit": str(profit)},
        )
    """
    from brawny.model.types import TxIntentSpec

    # Verify we're in a job context
    get_job_context()

    # Resolve signer: explicit param > job decorator > error
    resolved_signer = signer_address
    if resolved_signer is None:
        job = get_current_job()
        if job._signer_name is None:
            raise RuntimeError(
                f"No signer specified. Either pass signer_address= to intent() "
                f"or set @job(signer='...') on {job.job_id}"
            )
        resolved_signer = job._signer_name

    return TxIntentSpec(
        signer_address=resolved_signer,
        to_address=to_address,
        data=data,
        value_wei=str(int(value_wei)) if isinstance(value_wei, (int, float)) else value_wei,
        gas_limit=int(gas_limit) if gas_limit is not None else None,
        max_fee_per_gas=int(max_fee_per_gas) if max_fee_per_gas is not None else None,
        max_priority_fee_per_gas=int(max_priority_fee_per_gas) if max_priority_fee_per_gas is not None else None,
        min_confirmations=min_confirmations,
        deadline_seconds=deadline_seconds,
        metadata=metadata,
    )


class _BlockProxy:
    """Proxy object for accessing current block info.

    Provides clean attribute access to block properties without needing
    to pass context explicitly.

    Usage:
        from brawny import block

        if block.number % 100 == 0:
            return trigger(reason="Periodic check")
    """

    @property
    def number(self) -> int:
        """Current block number."""
        return get_job_context().block.number

    @property
    def timestamp(self) -> int:
        """Current block timestamp (Unix seconds)."""
        return get_job_context().block.timestamp

    @property
    def hash(self) -> str:
        """Current block hash (hex string with 0x prefix)."""
        return get_job_context().block.hash


# Singleton instance for import
block = _BlockProxy()


async def gas_ok() -> bool:
    """Check if current gas is acceptable.

    Gate condition: 2 * base_fee + effective_priority_fee <= effective_max_fee

    This matches what will actually be submitted, not RPC suggestions.

    Returns:
        True if gas acceptable or no gating configured (max_fee=None)

    Example:
        async def check(self):
            if not await gas_ok():
                return None
    """
    from brawny._context import _current_job
    from brawny.logging import get_logger

    ctx = get_job_context()
    job = _current_job.get()

    # Get gas settings from job (no config fallback in OE7 contexts)
    effective_max_fee = job.max_fee if job and job.max_fee is not None else None
    effective_priority_fee = job.priority_fee if job and job.priority_fee is not None else 0

    # No gating if max_fee is None
    if effective_max_fee is None:
        return True

    # Get quote (async)
    quote = await ctx.rpc.gas_quote()

    # Compute what we would actually submit
    computed_max_fee = (2 * quote.base_fee) + effective_priority_fee

    ok = computed_max_fee <= effective_max_fee

    if not ok:
        logger = get_logger(__name__)
        logger.info(
            "job.skipped_high_gas",
            job_id=job.job_id if job else None,
            base_fee=quote.base_fee,
            effective_priority_fee=effective_priority_fee,
            computed_max_fee=computed_max_fee,
            effective_max_fee=effective_max_fee,
        )

    return ok


async def gas_quote() -> "GasQuote":
    """Get current gas quote.

    Example:
        quote = await gas_quote()
        print(f"Base fee: {quote.base_fee / 1e9:.1f} gwei")
    """
    from brawny._rpc.gas import GasQuote

    return await get_job_context().rpc.gas_quote()


def ctx():
    """Get current phase context.

    Use when you need the full context object in a job that uses
    the implicit (no-parameter) signature.

    Example:
        from brawny import ctx, trigger

        def check(self):
            c = ctx()
            c.logger.info("checking", block=c.block.number)
            return trigger(reason="...")

    Returns:
        CheckContext (in check()) or BuildContext (in build_tx())

    Raises:
        LookupError: If called outside of job execution context.
    """
    return get_job_context()


class _KVProxy:
    """Proxy object for accessing job's persistent KV store.

    Works in job hooks (check/build_intent). Provides get/set/delete for
    persistent key-value storage that survives restarts.

    Usage:
        from brawny import kv

        def check(self):
            last_price = kv.get("last_price")
            kv.set("last_price", current_price)
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from KV store.

        Args:
            key: Storage key
            default: Default if not found

        Returns:
            Stored value or default
        """
        return get_job_context().kv.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in KV store.

        Args:
            key: Storage key
            value: JSON-serializable value
        """
        get_job_context().kv.set(key, value)

    def delete(self, key: str) -> bool:
        """Delete key from KV store.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if not found
        """
        return get_job_context().kv.delete(key)


# Singleton instance for import
kv = _KVProxy()


def _get_rpc_from_context():
    """Get RPC client from job context or alert context."""
    from brawny._context import _job_ctx, get_alert_context

    # Try job context first
    job_ctx = _job_ctx.get()
    if job_ctx is not None:
        return job_ctx.rpc

    # Try alert context (OE7 AlertContext has contracts: ContractFactory)
    alert_ctx = get_alert_context()
    if alert_ctx is not None and alert_ctx.contracts is not None:
        return alert_ctx.contracts._system.rpc

    raise LookupError(
        "No active context. Must be called from within a job hook "
        "(check/build_intent) or alert hook (alert_*)."
    )


class _RPCProxy:
    """Proxy object for accessing the RPC client.

    Works in both job hooks (check/build_intent) and alert hooks.
    Provides access to ReadClient/BroadcastClient methods with retries.

    Usage:
        from brawny import rpc

        def check(self):
            bal = rpc.get_balance(self.operator_address)
            gas = rpc.get_gas_price()

        def on_failure(self, ctx):
            bal = rpc.get_balance(self.operator_address) / 1e18
    """

    def __getattr__(self, name: str):
        """Delegate attribute access to the underlying RPC client."""
        return getattr(_get_rpc_from_context(), name)


# Singleton instance for import
rpc = _RPCProxy()


def _get_http_from_context():
    """Get approved HTTP client from job or alert context."""
    from brawny._context import _job_ctx, get_alert_context

    job_ctx = _job_ctx.get()
    if job_ctx is not None:
        return job_ctx.http

    alert_ctx = get_alert_context()
    if alert_ctx is not None and getattr(alert_ctx, "http", None) is not None:
        return alert_ctx.http

    raise LookupError(
        "No active context. Must be called from within a job hook "
        "(check/build_intent) or alert hook (alert_*)."
    )


class _HTTPProxy:
    """Proxy object for accessing approved HTTP client."""

    def __getattr__(self, name: str):
        return getattr(_get_http_from_context(), name)


http = _HTTPProxy()


# Thread-safe keystore address resolver - set once at startup
import threading

_keystore = None
_keystore_lock = threading.Lock()
_keystore_initialized = threading.Event()


def _set_keystore(ks) -> None:
    """Called by framework at startup to make keystore available.

    Thread-safe: uses lock and event to ensure visibility across threads.
    Must be called before worker threads are started.
    """
    global _keystore
    with _keystore_lock:
        _keystore = ks
        _keystore_initialized.set()


def _get_keystore():
    """Get keystore with thread-safe access.

    Returns:
        The keystore instance

    Raises:
        RuntimeError: If keystore not initialized within timeout
    """
    # Fast path - already initialized
    if _keystore is not None:
        return _keystore

    # Wait for initialization (with timeout)
    if not _keystore_initialized.wait(timeout=5.0):
        raise RuntimeError(
            "Keystore not initialized within timeout. This is only available "
            "when running with a keystore configured (not in dry-run mode)."
        )

    with _keystore_lock:
        if _keystore is None:
            raise RuntimeError(
                "Keystore initialization signaled but keystore is None. "
                "This should not happen - please report as a bug."
            )
        return _keystore


def get_address_from_alias(alias: str) -> str:
    """Resolve a signer alias to its address.

    Thread-safe: properly synchronized access to keystore.

    Usage:
        from brawny import get_address_from_alias

        def on_failure(self, ctx):
            addr = get_address_from_alias("yearn-worker")
            bal = rpc.get_balance(addr) / 1e18
    """
    return _get_keystore().get_address(alias)


def shorten(hex_string: str, prefix: int = 6, suffix: int = 4) -> str:
    """Shorten a hex string (address or hash) for display.

    Works in any context - no active hook required.

    Args:
        hex_string: Full hex string (e.g., 0x1234...abcd)
        prefix: Characters to keep at start (including 0x)
        suffix: Characters to keep at end

    Returns:
        Shortened string like "0x1234...abcd"

    Example:
        from brawny import shorten

        def on_success(self, ctx):
            ctx.alert(f"Tx: {shorten(ctx.receipt.transaction_hash)}")
    """
    from brawny.alerts.base import shorten as _shorten

    return _shorten(hex_string, prefix, suffix)


def explorer_link(
    hash_or_address: str,
    chain_id: int | None = None,
    label: str | None = None,
) -> str:
    """Create a Markdown explorer link with emoji.

    Automatically detects chain_id from alert context if not provided.
    Detects if input is a tx hash (66 chars) or address (42 chars).

    Args:
        hash_or_address: Transaction hash or address
        chain_id: Chain ID (auto-detected from context if not provided)
        label: Custom label (default: "🔗 View on Explorer")

    Returns:
        Markdown formatted link like "[🔗 View on Explorer](url)"

    Example:
        from brawny import explorer_link

        def on_success(self, ctx):
            ctx.alert(f"Done!\\n{explorer_link(ctx.receipt.transaction_hash)}")
    """
    from brawny._context import get_alert_context
    from brawny.alerts.base import explorer_link as _explorer_link

    if chain_id is None:
        alert_ctx = get_alert_context()
        if alert_ctx is not None:
            chain_id = alert_ctx.chain_id
        else:
            chain_id = 1  # Default to mainnet

    return _explorer_link(hash_or_address, chain_id, label)


def Contract(address: str, abi: list[dict[str, Any]] | None = None) -> ContractHandle:
    """Get a contract handle (Brownie-style).

    Works in job hooks (check/build_intent) and alert hooks.

    Args:
        address: Ethereum address (0x...)
        abi: Optional ABI override

    Returns:
        ContractHandle bound to current context's RPC

    Raises:
        LookupError: If called outside a job or alert hook

    Example:
        vault = Contract(self.vault_address)
        decimals = vault.decimals()
    """
    from brawny._context import _job_ctx, get_alert_context, get_console_context

    # Try job context first (CheckContext or BuildContext)
    job_ctx = _job_ctx.get()
    if job_ctx is not None:
        if job_ctx.contracts is None:
            raise RuntimeError(
                "Contract system not configured. Ensure the contract system is initialized."
            )
        # Access the underlying ContractSystem via SimpleContractFactory._system
        return job_ctx.contracts._system.handle(
            address=address,
            job_id=job_ctx.job_id,
            abi=abi,
        )

    # Try alert context (new OE7 AlertContext from model/contexts.py)
    alert_ctx = get_alert_context()
    if alert_ctx is not None:
        if alert_ctx.contracts is None:
            raise RuntimeError(
                "Contract system not configured. Ensure the contract system is initialized."
            )
        # Access the underlying ContractSystem via SimpleContractFactory._system
        return alert_ctx.contracts._system.handle(
            address=address,
            abi=abi,
        )

    # Try console context
    console_ctx = get_console_context()
    if console_ctx is not None:
        return console_ctx.contract_system.handle(address=address, abi=abi)

    raise LookupError(
        "No active context. Contract() must be called from within a job hook "
        "(check/build_intent), alert hook (alert_*), or console."
    )


def Wei(value: str | int) -> int:
    """Convert to wei. Brownie-compatible.

    Works anywhere - no active context required.

    Args:
        value: Integer wei amount, or string like "1 ether", "100 gwei"

    Returns:
        Amount in wei (int)

    Example:
        Wei("1 ether")   → 1000000000000000000
        Wei("100 gwei")  → 100000000000
        Wei("500 wei")   → 500
        Wei(123)         → 123
    """
    if isinstance(value, int):
        return value
    value_str = str(value).strip().lower()
    if value_str.endswith(" ether"):
        return int(float(value_str[:-6]) * 10**18)
    elif value_str.endswith(" gwei"):
        return int(float(value_str[:-5]) * 10**9)
    elif value_str.endswith(" wei"):
        return int(value_str[:-4])
    return int(value_str)


class _Web3Proxy:
    """Proxy for context-aware web3 access.

    Provides full web3-py API while using the current RPC client's endpoints.
    Works in job hooks (check/build_intent) and alert hooks.

    Usage:
        from brawny import web3

        balance = web3.eth.get_balance("0x...")
        block = web3.eth.get_block("latest")
        chain_id = web3.eth.chain_id
    """

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying Web3 instance."""
        return getattr(self._get_web3(), name)

    def _get_web3(self):
        """Get Web3 instance from active context."""
        from brawny._context import _job_ctx, get_alert_context, get_console_context

        # Try job context first
        job_ctx = _job_ctx.get()
        if job_ctx is not None and job_ctx.rpc is not None:
            return job_ctx.rpc.web3

        # Try alert context (OE7 AlertContext has contracts: ContractFactory)
        alert_ctx = get_alert_context()
        if alert_ctx is not None and alert_ctx.contracts is not None:
            return alert_ctx.contracts._system.rpc.web3

        # Try console context
        console_ctx = get_console_context()
        if console_ctx is not None:
            return console_ctx.rpc.web3

        raise LookupError(
            "No active context. web3 must be used from within a job hook "
            "(check/build_intent), alert hook (alert_*), or console."
        )

    def __repr__(self) -> str:
        try:
            w3 = self._get_web3()
            return f"<Web3Proxy connected to chain {w3.eth.chain_id}>"
        except LookupError:
            return "<Web3Proxy (no active context)>"


# Singleton instance for import
web3 = _Web3Proxy()


# Re-export Brownie-style singletons for convenience
from brawny.accounts import accounts, Account
from brawny.history import history
from brawny.chain import chain
from brawny.multicall import multicall

# Re-export alert function for use in hooks
from brawny.alerts.send import alert

__all__ = [
    "trigger",
    "intent",
    "alert",
    "block",
    "ctx",
    "gas_ok",
    "gas_quote",
    "kv",
    "rpc",
    "Contract",
    "Wei",
    "web3",
    "multicall",
    "shorten",
    "explorer_link",
    "get_address_from_alias",
    "accounts",
    "Account",
    "history",
    "chain",
]
