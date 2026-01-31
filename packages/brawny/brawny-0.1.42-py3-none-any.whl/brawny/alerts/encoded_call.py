"""Encoded call types for contract interactions.

Provides EncodedCall, ReturnValue, and FunctionABI classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from brawny.alerts.contracts import ContractHandle
    from brawny.jobs.base import TxReceipt


@dataclass
class FunctionABI:
    """Parsed function ABI entry."""

    name: str
    inputs: list[dict[str, Any]]
    outputs: list[dict[str, Any]]
    state_mutability: str
    signature: str
    selector: bytes

    @property
    def is_view(self) -> bool:
        """Check if function is view or pure (read-only)."""
        return self.state_mutability in ("view", "pure")

    @property
    def is_state_changing(self) -> bool:
        """Check if function modifies state."""
        return self.state_mutability in ("nonpayable", "payable")

    @property
    def is_payable(self) -> bool:
        """Check if function accepts ETH value."""
        return self.state_mutability == "payable"


class ReturnValue(tuple):
    """Tuple with named field access for contract return values.

    Brownie-compatible: prints as tuple, supports named access.

    Supports multiple access patterns:
        result[0]              # Index access
        result["fieldName"]    # Dict-style access
        result.fieldName       # Attribute access
        result.keys()          # Get field names
        result.items()         # Get (name, value) pairs
        dict(result.items())   # Convert to dict
    """

    _names: tuple[str, ...]
    _dict: dict[str, Any]

    def __new__(
        cls, values: tuple | list, abi: list[dict[str, Any]] | None = None
    ) -> "ReturnValue":
        values = list(values)

        # Recursively wrap nested tuples based on ABI components
        if abi is not None:
            for i in range(len(values)):
                if isinstance(values[i], (tuple, list)) and not isinstance(
                    values[i], ReturnValue
                ):
                    if "components" in abi[i]:
                        components = abi[i]["components"]
                        if abi[i]["type"] == "tuple":
                            # Single struct
                            values[i] = ReturnValue(values[i], components)
                        else:
                            # Array of structs - wrap each element, keep as list
                            values[i] = [ReturnValue(v, components) for v in values[i]]

        instance = super().__new__(cls, values)

        # Build names from ABI or use fallback (arg0, arg1 - no brackets for attr access)
        if abi is not None:
            names = tuple(out.get("name") or f"arg{i}" for i, out in enumerate(abi))
        else:
            names = tuple(f"arg{i}" for i in range(len(values)))

        object.__setattr__(instance, "_names", names)
        object.__setattr__(instance, "_dict", dict(zip(names, values)))
        return instance

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                return self._dict[key]
            except KeyError:
                raise KeyError(f"No field '{key}'. Available: {list(self._names)}")
        return super().__getitem__(key)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._dict[name]
        except KeyError:
            raise AttributeError(f"No field '{name}'. Available: {list(self._names)}")

    def keys(self) -> tuple[str, ...]:
        """Return output names."""
        return self._names

    def items(self):
        """Return (name, value) pairs."""
        return self._dict.items()

    def dict(self) -> dict[str, object]:
        """Convert to dict, recursively unwrapping nested ReturnValues."""

        def _norm(x: object) -> object:
            if isinstance(x, ReturnValue):
                return x.dict()
            if isinstance(x, list):
                return [_norm(v) for v in x]
            return x

        return {k: _norm(v) for k, v in self._dict.items()}

    # Use tuple's __repr__ for Brownie parity: prints as (val1, val2)
    __repr__ = tuple.__repr__


class EncodedCall(str):
    """Encoded calldata with .call() and .transact() methods.

    This is a str subclass so it can be used directly as calldata,
    while also providing Brownie-style modifiers for execution.

    Usage:
        # Get calldata (str)
        calldata = vault.harvest()

        # Force eth_call simulation
        result = vault.harvest().call()

        # Broadcast transaction (only in @broadcast context)
        receipt = vault.harvest().transact({"from": "yearn-worker"})
    """

    _contract: "ContractHandle"
    _abi: FunctionABI

    def __new__(
        cls,
        calldata: str,
        contract: "ContractHandle",
        abi: FunctionABI,
    ) -> "EncodedCall":
        instance = super().__new__(cls, calldata)
        instance._contract = contract
        instance._abi = abi
        return instance

    def call(self) -> Any:
        """Execute eth_call and return decoded result.

        Performs a static call (simulation) without broadcasting.
        Works regardless of function state mutability.

        Returns:
            Decoded return value from the function
        """
        return self._contract._call_with_calldata(str(self), self._abi)

    def transact(self, tx_params: dict[str, Any] | None = None) -> "TxReceipt":
        """Broadcast the transaction and wait for receipt.

        Only works inside a @broadcast decorated function.
        Raises BroadcastNotAllowedError if not in broadcast context.

        Args:
            tx_params: Transaction parameters (Brownie-style)
                - from: Signer name or address (required)
                - value: ETH value to send (optional, for payable functions)
                - gas: Gas limit (optional, auto-estimated if not provided)
                - gasPrice: Gas price (optional)
                - maxFeePerGas: EIP-1559 max fee (optional)
                - maxPriorityFeePerGas: EIP-1559 priority fee (optional)
                - nonce: Transaction nonce (optional, auto-fetched if not provided)

        Returns:
            Transaction receipt after confirmation

        Raises:
            BroadcastNotAllowedError: If not in @broadcast context
            SignerNotFoundError: If 'from' address not in keystore
            TransactionRevertedError: If transaction reverts
            TransactionTimeoutError: If receipt wait times out
        """
        if tx_params is None:
            tx_params = {}
        return self._contract._transact_with_calldata(str(self), tx_params, self._abi)
