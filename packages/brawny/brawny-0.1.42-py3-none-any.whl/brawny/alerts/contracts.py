"""Contract handle for the Alerts extension.

Provides an ergonomic interface for interacting with contracts:
- Attribute-based function access: token.decimals()
- State mutability checks to prevent accidental state changes
- Explicit function access for overloads: token.fn("balanceOf(address)").call(owner)

Brownie-style interface:
- token.balanceOf(owner) - view functions return value directly
- token.transfer(to, amount, {"from": accounts[0]}) - broadcasts, returns receipt
- vault.harvest() - returns EncodedCall (calldata) if no tx_params
- vault.harvest.call() - forces eth_call (static simulation)
- vault.harvest.transact({"from": "signer"}) - deferred broadcast
- vault.harvest.encode_input() - returns calldata only

For events, use ctx.events (brownie-compatible):
    ctx.events["Deposit"][0]           # First Deposit event
    ctx.events["Deposit"]["amount"]    # Field access
"""

from __future__ import annotations

import re
import threading
import time
from typing import TYPE_CHECKING, Any

from cachetools import TTLCache
from eth_abi import decode as abi_decode
from eth_utils import function_signature_to_4byte_selector, to_checksum_address

from brawny._context import resolve_block_identifier
from brawny.alerts.encoded_call import EncodedCall, FunctionABI, ReturnValue
from brawny.alerts.errors import (
    AmbiguousOverloadError,
    ContractCallError,
    FunctionNotFoundError,
)
from brawny.alerts.function_caller import (
    ExplicitFunctionCaller,
    FunctionCaller,
    OverloadedFunction,
)
from brawny._rpc.errors import RPCError
from brawny.model.errors import KeystoreError
from brawny.db.global_cache import GlobalABICache
from brawny.logging import get_logger

logger = get_logger(__name__)

# Warn-once cache: don't spam logs for same missing ABI
# Multi-threaded access - protected by lock
_warned_addresses: TTLCache[str, bool] = TTLCache(maxsize=1_000, ttl=3600)
_warned_lock = threading.Lock()


def _normalize_for_warn(address: str) -> str:
    """Normalize address for warn-once cache (matches ABIResolver normalization)."""
    addr = address.lower()
    if not addr.startswith("0x"):
        addr = "0x" + addr
    return addr


def _warn_once(address: str) -> bool:
    """Return True if we should warn (first time for this address)."""
    addr = _normalize_for_warn(address)
    with _warned_lock:
        if addr in _warned_addresses:
            return False
        _warned_addresses[addr] = True
        return True

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.jobs.base import TxReceipt
    from brawny._rpc.clients import BroadcastClient


class ContractSystem:
    """Injected contract system for ABI resolution and eth_call execution.

    Uses global ABI cache at ~/.brawny/abi_cache.db for persistent storage.
    """

    def __init__(self, rpc: "BroadcastClient", config: "Config") -> None:
        self._rpc = rpc
        self._config = config
        self._abi_cache = GlobalABICache()
        self._resolver = None

    @property
    def rpc(self) -> "BroadcastClient":
        return self._rpc

    @property
    def config(self) -> "Config":
        return self._config

    def resolver(self):
        if self._resolver is None:
            from brawny.alerts.abi_resolver import ABIResolver

            self._resolver = ABIResolver(self._rpc, self._config, self._abi_cache)
        return self._resolver

    def handle(
        self,
        address: str,
        receipt: "TxReceipt | None" = None,
        block_identifier: int | None = None,
        job_id: str | None = None,
        hook: str | None = None,
        abi: list[dict[str, Any]] | None = None,
    ) -> "ContractHandle":
        return ContractHandle(
            address=address,
            receipt=receipt,
            block_identifier=block_identifier,
            system=self,
            job_id=job_id,
            hook=hook,
            abi=abi,
        )


class ContractHandle:
    """Handle for interacting with a contract.

    Provides:
    - Attribute access for function calls: token.decimals()
    - Explicit function access: token.fn("balanceOf(address)").call(owner)

    For events, use ctx.events (brownie-style):
        ctx.events["Deposit"][0]    # First Deposit event
        ctx.events["Deposit"]["amount"]  # Field access
    """

    def __init__(
        self,
        address: str,
        receipt: "TxReceipt | None" = None,
        block_identifier: int | None = None,
        system: ContractSystem | None = None,
        job_id: str | None = None,
        hook: str | None = None,
        abi: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize contract handle.

        Args:
            address: Contract address
            receipt: Transaction receipt (for event access)
            block_identifier: Block number for eth_calls
            abi: Optional pre-resolved ABI (if None, will be resolved)
        """
        if system is None:
            raise RuntimeError(
                "Contract system not configured. Initialize ContractSystem and "
                "pass it into contexts before using ContractHandle."
            )
        self._address = to_checksum_address(address)
        self._receipt = receipt
        self._block_identifier = block_identifier
        self._system = system
        self._job_id = job_id
        self._hook = hook
        self._abi_list = abi
        self._abi_source: str | None = "manual" if abi is not None else None
        self._functions: dict[str, list[FunctionABI]] | None = None

    @property
    def address(self) -> str:
        """Contract address (checksummed)."""
        return self._address

    @property
    def abi(self) -> list[dict[str, Any]]:
        """Contract ABI."""
        self._ensure_abi()
        return self._abi_list  # type: ignore

    def _ensure_abi(self) -> None:
        """Ensure ABI is loaded, fetching if needed.

        Uses resolve_safe() which returns None instead of raising on failure.
        If ABI cannot be resolved, logs warning once but doesn't raise.
        Callers should check self._abi_list before using it.
        """
        if self._abi_list is not None:
            return

        resolver = self._system.resolver()
        resolved = resolver.resolve_safe(self._address)

        if resolved is not None:
            self._abi_list = resolved.abi
            self._abi_source = resolved.source
        else:
            # Always log at INFO level so resolution failures are visible
            logger.info(
                "contract.abi_resolution_failed",
                address=self._address,
            )
            if _warn_once(self._address):
                logger.warning(
                    "contract.abi_not_found",
                    address=self._address,
                    hint="Use ctx.contracts.with_abi() or add to interfaces/",
                )

    def _ensure_functions_parsed(self) -> None:
        """Ensure function ABIs are parsed."""
        if self._functions is not None:
            return

        self._ensure_abi()
        self._functions = {}

        # Handle case where ABI resolution failed
        if self._abi_list is None:
            return

        for item in self._abi_list:
            if item.get("type") != "function":
                continue

            name = item.get("name", "")
            if not name:
                continue

            inputs = item.get("inputs", [])
            outputs = item.get("outputs", [])
            state_mutability = item.get("stateMutability", "nonpayable")

            # Build signature
            input_types = [inp["type"] for inp in inputs]
            signature = f"{name}({','.join(input_types)})"

            # Calculate selector
            selector = function_signature_to_4byte_selector(signature)

            func_abi = FunctionABI(
                name=name,
                inputs=inputs,
                outputs=outputs,
                state_mutability=state_mutability,
                signature=signature,
                selector=selector,
            )

            if name not in self._functions:
                self._functions[name] = []
            self._functions[name].append(func_abi)

    def __getattr__(self, name: str) -> FunctionCaller:
        """Get function caller by attribute name.

        Raises:
            FunctionNotFoundError: If function not in ABI
            AmbiguousOverloadError: If multiple overloads match
        """
        # Skip special attributes
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

        self._ensure_functions_parsed()

        if name not in self._functions:
            available = list(self._functions.keys()) if self._functions else []
            raise FunctionNotFoundError(
                name,
                self._address,
                available_functions=available,
                abi_resolved=self._abi_list is not None,
                abi_source=self._abi_source,
            )

        overloads = self._functions[name]

        # If only one overload, return it directly
        if len(overloads) == 1:
            return FunctionCaller(self, overloads[0])

        # Multiple overloads - resolve by argument count at call time
        return OverloadedFunction(self, overloads)

    def fn(self, signature: str) -> ExplicitFunctionCaller:
        """Get explicit function caller by signature.

        Use this for overloaded functions or when explicit control is needed.

        Args:
            signature: Function signature like "balanceOf(address)" or just "transfer"

        Returns:
            ExplicitFunctionCaller for the function

        Usage:
            token.fn("balanceOf(address)").call(owner)
            token.fn("transfer(address,uint256)").transact(to, amount, {"from": "worker"})
        """
        self._ensure_functions_parsed()

        # Check if it's a full signature or just a name
        if "(" in signature:
            # Full signature - find exact match
            for overloads in self._functions.values():
                for func in overloads:
                    if func.signature == signature:
                        return ExplicitFunctionCaller(self, func)

            # Try parsing and matching
            match = re.match(r"(\w+)\((.*)\)", signature)
            if match:
                name = match.group(1)
                if name in self._functions:
                    for func in self._functions[name]:
                        if func.signature == signature:
                            return ExplicitFunctionCaller(self, func)

            raise FunctionNotFoundError(
                signature,
                self._address,
                available_functions=self._get_all_signatures(),
                abi_resolved=self._abi_list is not None,
                abi_source=self._abi_source,
            )
        else:
            # Just a name - must have exactly one overload
            name = signature
            if name not in self._functions:
                raise FunctionNotFoundError(
                    name,
                    self._address,
                    available_functions=list(self._functions.keys()),
                    abi_resolved=self._abi_list is not None,
                    abi_source=self._abi_source,
                )

            overloads = self._functions[name]
            if len(overloads) > 1:
                raise AmbiguousOverloadError(
                    name, -1, [f.signature for f in overloads]
                )

            return ExplicitFunctionCaller(self, overloads[0])

    def _get_all_signatures(self) -> list[str]:
        """Get all function signatures in the ABI."""
        sigs = []
        for overloads in self._functions.values():
            for func in overloads:
                sigs.append(func.signature)
        return sigs

    def __dir__(self) -> list[str]:
        """Return available attributes for tab completion."""
        self._ensure_functions_parsed()
        return [*super().__dir__(), *(self._functions or [])]

    def _call_with_calldata(self, calldata: str, abi: FunctionABI) -> Any:
        """Execute eth_call with pre-encoded calldata.

        Used by EncodedCall.call() and FunctionCaller.call().

        Args:
            calldata: Hex-encoded calldata
            abi: Function ABI for result decoding

        Returns:
            Decoded return value
        """
        rpc = self._system.rpc

        tx_params = {
            "to": self._address,
            "data": calldata,
        }

        # Resolve block using centralized 4-level precedence:
        # 1. Explicit param (N/A here)  2. Handle's block  3. Check scope pin  4. "latest"
        block_id = resolve_block_identifier(
            explicit=None,  # _call_with_calldata doesn't accept explicit block param
            handle_block=self._block_identifier,
        )

        from brawny.multicall import enqueue_multicall_call

        def _decode_multicall(raw: bytes) -> Any:
            hex_result = "0x" + raw.hex()
            return self._decode_result(hex_result, abi)

        queued = enqueue_multicall_call(
            rpc=rpc,
            target=self._address,
            calldata=calldata,
            block_identifier=block_id,
            decoder=_decode_multicall,
            readable=abi.signature,
        )
        if queued is not None:
            return queued

        try:
            result = rpc.eth_call(tx_params, block_identifier=block_id)
        except (RPCError, ValueError, TypeError) as e:
            raise ContractCallError(
                function_name=abi.name,
                address=self._address,
                reason=str(e),
                block_identifier=self._block_identifier,
                signature=abi.signature,
                job_id=self._job_id,
                hook=self._hook,
            )

        # Convert result to hex string if bytes
        if isinstance(result, bytes):
            result = "0x" + result.hex()

        # Decode result
        return self._decode_result(result, abi)

    def _decode_result(self, result: str, abi: FunctionABI) -> Any:
        """Decode function return value with Brownie-compatible wrapping."""
        if not abi.outputs:
            return None

        if result == "0x" or not result:
            return None

        if isinstance(result, str) and result.startswith("0x0x"):
            result = "0x" + result[4:]

        # Remove 0x prefix
        data = bytes.fromhex(result[2:] if result.startswith("0x") else result)
        if not data:
            return None

        types = [out["type"] for out in abi.outputs]
        decoded = abi_decode(types, data)

        # Single return value
        if len(decoded) == 1:
            # If it's a struct, wrap it so nested fields are accessible
            if abi.outputs[0].get("components"):
                return ReturnValue(decoded, abi.outputs)[0]
            return decoded[0]

        # Multiple return values: wrap in ReturnValue for named access
        return ReturnValue(decoded, abi.outputs)

    def _transact_with_calldata(
        self,
        calldata: str,
        tx_params: dict[str, Any],
        abi: FunctionABI,
    ) -> "TxReceipt":
        """Broadcast a transaction with pre-encoded calldata.

        Works in:
        - Script context (uses TransactionBroadcaster)
        - @broadcast decorator context (uses keystore)

        Args:
            calldata: Hex-encoded calldata
            tx_params: Transaction parameters with 'from' key
            abi: Function ABI for error messages

        Returns:
            Transaction receipt after confirmation

        Raises:
            RuntimeError: If not in script or @broadcast context
            SignerNotFoundError: If 'from' address not in keystore
        """
        from brawny.scripting import (
            broadcast_enabled,
            get_broadcast_context,
            BroadcastNotAllowedError,
            SignerNotFoundError,
            TransactionRevertedError,
            TransactionTimeoutError,
        )

        # Validate 'from' parameter
        if "from" not in tx_params:
            raise ValueError(
                f".transact() requires 'from' key in tx_params. "
                f"Example: vault.{abi.name}.transact({{\"from\": \"signer\"}})"
            )

        sender_obj = tx_params["from"]

        # Extract private key if Account instance
        private_key = None
        from brawny.accounts import Account
        if isinstance(sender_obj, Account):
            from_address = sender_obj.address
            private_key = sender_obj._private_key
        else:
            from_address = str(sender_obj)

        # Try script context first (TransactionBroadcaster)
        try:
            from brawny.script_tx import _get_broadcaster
            broadcaster = _get_broadcaster()
            return broadcaster.transact(
                sender=to_checksum_address(from_address),
                to=self._address,
                data=calldata,
                value=tx_params.get("value", 0),
                gas_limit=tx_params.get("gas"),
                gas_price=tx_params.get("gasPrice"),
                max_fee_per_gas=tx_params.get("maxFeePerGas"),
                max_priority_fee_per_gas=tx_params.get("maxPriorityFeePerGas"),
                nonce=tx_params.get("nonce"),
                private_key=private_key,
            )
        except RuntimeError:
            pass  # Not in script context, try @broadcast

        # Fall back to @broadcast context
        if not broadcast_enabled():
            raise RuntimeError(
                f"transact() requires script context or @broadcast decorator. "
                f"Use 'brawny script run' or wrap function with @broadcast."
            )

        ctx = get_broadcast_context()
        if ctx is None:
            raise BroadcastNotAllowedError(abi.name, reason="broadcast context not available")

        # Resolve signer address via keystore (for @broadcast mode)
        keystore = ctx.keystore
        if keystore is None and private_key is None:
            raise SignerNotFoundError(from_address)
        if private_key is None:
            try:
                from_address = keystore.get_address(str(sender_obj))
            except (KeystoreError, ValueError, TypeError) as e:
                raise SignerNotFoundError(str(sender_obj)) from e

        rpc = self._system.rpc

        # Build transaction
        tx: dict[str, Any] = {
            "from": to_checksum_address(from_address),
            "to": to_checksum_address(self._address),
            "data": calldata,
            "chainId": int(tx_params.get("chainId") or self._system.config.chain_id),
        }

        # Add optional parameters
        def _parse_int(value: Any, field: str) -> int:
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                return int(value, 0)
            raise ValueError(f"Invalid {field} type: {type(value).__name__}")

        if "value" in tx_params:
            tx["value"] = _parse_int(tx_params["value"], "value")
        if "gas" in tx_params:
            tx["gas"] = _parse_int(tx_params["gas"], "gas")
        if "gasPrice" in tx_params:
            tx["gasPrice"] = _parse_int(tx_params["gasPrice"], "gasPrice")
        if "maxFeePerGas" in tx_params:
            tx["maxFeePerGas"] = _parse_int(tx_params["maxFeePerGas"], "maxFeePerGas")
        if "maxPriorityFeePerGas" in tx_params:
            tx["maxPriorityFeePerGas"] = _parse_int(
                tx_params["maxPriorityFeePerGas"],
                "maxPriorityFeePerGas",
            )
        if "nonce" in tx_params:
            tx["nonce"] = _parse_int(tx_params["nonce"], "nonce")

        # Auto-estimate gas if not provided
        if "gas" not in tx:
            try:
                tx["gas"] = rpc.estimate_gas(tx)
            except (RPCError, ValueError, TypeError) as e:
                raise ContractCallError(
                    function_name=abi.name,
                    address=self._address,
                    reason=f"Gas estimation failed: {e}",
                    signature=abi.signature,
                )

        # Auto-fetch nonce if not provided
        if "nonce" not in tx:
            tx["nonce"] = rpc.get_transaction_count(from_address, "pending")

        # Default gas price if no fees provided
        if (
            "gasPrice" not in tx
            and "maxFeePerGas" not in tx
            and "maxPriorityFeePerGas" not in tx
        ):
            tx["gasPrice"] = rpc.get_gas_price()

        if "maxFeePerGas" in tx or "maxPriorityFeePerGas" in tx:
            tx["type"] = 2

        # Sign and broadcast transaction
        if private_key is not None:
            # Sign with Account's private key directly
            from eth_account import Account as EthAccount
            signed = EthAccount.sign_transaction(tx, private_key)
        else:
            signed = keystore.sign_transaction(tx, str(sender_obj))
        raw_tx = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = rpc.send_raw_transaction(raw_tx)

        # Wait for receipt
        deadline = time.time() + ctx.timeout_seconds
        receipt = None
        while time.time() < deadline:
            receipt = rpc.get_transaction_receipt(tx_hash)
            if receipt is not None:
                break
            time.sleep(ctx.poll_interval_seconds)

        if receipt is None:
            raise TransactionTimeoutError(tx_hash, ctx.timeout_seconds)

        status = receipt.get("status", 1)
        if status == 0:
            raise TransactionRevertedError(tx_hash)

        tx_hash_val = receipt.get("transactionHash")
        if hasattr(tx_hash_val, "hex"):
            tx_hash_val = f"0x{tx_hash_val.hex()}"
        block_hash = receipt.get("blockHash")
        if hasattr(block_hash, "hex"):
            block_hash = f"0x{block_hash.hex()}"

        from brawny.jobs.base import TxReceipt

        return TxReceipt(
            transaction_hash=tx_hash_val,
            block_number=receipt.get("blockNumber"),
            block_hash=block_hash,
            status=status,
            gas_used=receipt.get("gasUsed", 0),
            logs=list(receipt.get("logs", [])),
        )

    def __repr__(self) -> str:
        return f"ContractHandle({self._address})"


class SimpleContractFactory:
    """ContractFactory implementation wrapping ContractSystem.

    Provides block-aware contract access per OE7:
    - at(): Get handle reading at 'latest'. Use in build/alerts.
    - at_block(): Get handle pinned to specific block. Use in check().
    - with_abi(): Get handle with explicit ABI.

    Factory stays dumb:
    - Does not silently switch endpoints/groups
    - Does not mutate global caches
    - Is deterministic under a given rpc + abi_resolver
    """

    def __init__(self, system: ContractSystem) -> None:
        self._system = system

    def at(self, name: str, address: str) -> ContractHandle:
        """Get contract handle, reads at 'latest'. Use in build/alerts.

        Args:
            name: Contract name (for ABI lookup, currently unused)
            address: Contract address

        Returns:
            ContractHandle reading at 'latest'
        """
        return self._system.handle(address=address, block_identifier=None)

    def at_block(self, name: str, address: str, block: int) -> ContractHandle:
        """Get contract handle pinned to specific block. Use in check().

        The block is baked into the handle - it cannot forget the pinning.
        This prevents TOCTOU bugs where check() reads at inconsistent blocks.

        Args:
            name: Contract name (for ABI lookup, currently unused)
            address: Contract address
            block: Block number to pin reads to

        Returns:
            ContractHandle with all reads pinned to the specified block
        """
        return self._system.handle(address=address, block_identifier=block)

    def with_abi(self, address: str, abi: list[Any]) -> ContractHandle:
        """Get contract handle with explicit ABI.

        Args:
            address: Contract address
            abi: Explicit ABI to use

        Returns:
            ContractHandle with the provided ABI
        """
        return self._system.handle(address=address, abi=abi)


__all__ = [
    "ContractSystem",
    "ContractHandle",
    "SimpleContractFactory",
    "FunctionCaller",
    "ExplicitFunctionCaller",
    "EncodedCall",
    "FunctionABI",
    "ReturnValue",
]
