"""Function caller classes for contract interactions.

Provides FunctionCaller, OverloadedFunction, and ExplicitFunctionCaller classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eth_abi import encode as abi_encode, decode as abi_decode

from brawny._context import resolve_block_identifier
from brawny.alerts.encoded_call import EncodedCall, FunctionABI, ReturnValue
from brawny.alerts.errors import (
    AmbiguousOverloadError,
    ContractCallError,
    OverloadMatchError,
)
from brawny._rpc.errors import RPCError

if TYPE_CHECKING:
    from brawny.alerts.contracts import ContractHandle
    from brawny.jobs.base import TxReceipt


class FunctionCaller:
    """Callable wrapper for contract functions with Brownie-style interface.

    Behavior varies by function state mutability:
    - View/pure functions: __call__ executes eth_call, returns decoded value
    - State-changing functions:
        - With {"from": ...} as last arg: broadcasts transaction, returns receipt
        - Without tx_params: returns EncodedCall (calldata with modifiers)

    Methods:
    - encode_input(*args): Get calldata without executing
    - call(*args): Force eth_call simulation
    - transact(*args, tx_params): Broadcast transaction

    Usage (Brownie-style):
        token.balanceOf(owner)  # View - returns value
        token.transfer(to, amount, {"from": accounts[0]})  # Broadcasts, returns receipt
        token.transfer(to, amount)  # Returns EncodedCall (calldata)
    """

    def __init__(
        self,
        contract: "ContractHandle",
        function_abi: FunctionABI,
    ) -> None:
        self._contract = contract
        self._abi = function_abi

    def __call__(self, *args: Any, block_identifier: int | str | None = None) -> Any:
        """Call the function with automatic state mutability handling.

        For view/pure functions: executes eth_call and returns decoded result.
        For state-changing functions:
            - With tx_params dict (Brownie-style): broadcasts and returns receipt
            - Without tx_params: returns EncodedCall for deferred execution

        Args:
            *args: Function arguments. For state-changing functions, may include
                   tx_params dict as last argument (Brownie-style).
            block_identifier: Optional block number/tag override for view calls.
                             If None, uses handle's block or "latest".

        Usage:
            # View function - returns value directly
            decimals = token.decimals()  # 18
            decimals = token.decimals(block_identifier=21000000)  # at specific block

            # State-changing function - Brownie-style (broadcasts immediately)
            receipt = token.transfer(to, amount, {"from": accounts[0]})

            # State-changing function - returns EncodedCall (for calldata)
            calldata = vault.harvest()  # "0x4641257d"

            # EncodedCall can be used as calldata or with modifiers
            result = vault.harvest().call()  # Simulate
            receipt = vault.harvest().transact({"from": "worker"})  # Broadcast
        """
        if self._abi.is_state_changing:
            # Check if last arg is tx_params dict (Brownie-style immediate broadcast)
            if args and isinstance(args[-1], dict) and "from" in args[-1]:
                tx_params = args[-1]
                func_args = args[:-1]
                calldata = self._encode_calldata(*func_args)
                return self._contract._transact_with_calldata(calldata, tx_params, self._abi)

            # No tx_params - return EncodedCall for calldata or deferred .transact()
            calldata = self._encode_calldata(*args)
            return EncodedCall(calldata, self._contract, self._abi)

        # View/pure functions execute immediately
        return self._execute_call(*args, block_identifier=block_identifier)

    def encode_input(self, *args: Any) -> str:
        """Encode function calldata without executing.

        Works for any function regardless of state mutability.

        Usage:
            data = vault.harvest.encode_input()
            data = token.transfer.encode_input(recipient, amount)

        Returns:
            Hex-encoded calldata string
        """
        return self._encode_calldata(*args)

    def call(self, *args: Any, block_identifier: int | str | None = None) -> Any:
        """Force eth_call simulation and return decoded result.

        Works for any function regardless of state mutability.
        Useful for simulating state-changing functions without broadcasting.

        Args:
            *args: Function arguments
            block_identifier: Optional block number/tag override.
                             If None, uses handle's block or "latest".

        Usage:
            # Simulate state-changing function
            result = vault.harvest.call()

            # Also works for view functions (same as direct call)
            decimals = token.decimals.call()

            # Query at specific block
            decimals = token.decimals.call(block_identifier=21000000)

        Returns:
            Decoded return value from the function
        """
        return self._execute_call(*args, block_identifier=block_identifier)

    def transact(self, *args: Any) -> "TxReceipt":
        """Broadcast the transaction and wait for receipt.

        Only works inside a @broadcast decorated function.
        Transaction params dict must be the last argument.

        Usage:
            # No-arg function
            receipt = vault.harvest.transact({"from": "yearn-worker"})

            # With function args (tx_params is last)
            receipt = token.transfer.transact(recipient, amount, {"from": "worker"})

        Args:
            *args: Function arguments, with tx_params dict as last arg

        Returns:
            Transaction receipt after confirmation

        Raises:
            BroadcastNotAllowedError: If not in @broadcast context
            ValueError: If tx_params dict not provided
        """
        # Extract tx_params from last arg
        if not args or not isinstance(args[-1], dict):
            raise ValueError(
                f"{self._abi.name}.transact() requires tx_params dict as last argument. "
                f"Example: vault.{self._abi.name}.transact({{\"from\": \"signer\"}})"
            )

        tx_params = args[-1]
        func_args = args[:-1]

        # Encode calldata and delegate to contract helper
        calldata = self._encode_calldata(*func_args)
        return self._contract._transact_with_calldata(calldata, tx_params, self._abi)

    def _execute_call(self, *args: Any, block_identifier: int | str | None = None) -> Any:
        """Execute eth_call and decode result.

        Args:
            *args: Function arguments
            block_identifier: Optional block override. If None, uses handle's block or "latest".
        """
        rpc = self._contract._system.rpc

        # Encode call data
        calldata = self._encode_calldata(*args)

        # Build tx params for eth_call
        tx_params = {
            "to": self._contract.address,
            "data": calldata,
        }

        # Resolve block using centralized 4-level precedence:
        # 1. Explicit param  2. Handle's block  3. Check scope pin  4. "latest"
        block_id = resolve_block_identifier(
            explicit=block_identifier,
            handle_block=self._contract._block_identifier,
        )

        from brawny.multicall import enqueue_multicall_call

        def _decode_multicall(raw: bytes) -> Any:
            hex_result = "0x" + raw.hex()
            return self._decode_result(hex_result)

        queued = enqueue_multicall_call(
            rpc=rpc,
            target=self._contract.address,
            calldata=calldata,
            block_identifier=block_id,
            decoder=_decode_multicall,
            readable=self._abi.signature,
        )
        if queued is not None:
            return queued

        # Execute call with block pinning
        try:
            result = rpc.eth_call(tx_params, block_identifier=block_id)
        except (RPCError, ValueError, TypeError) as e:
            raise ContractCallError(
                function_name=self._abi.name,
                address=self._contract.address,
                reason=str(e),
                block_identifier=self._contract._block_identifier,
                signature=self._abi.signature,
                job_id=self._contract._job_id,
                hook=self._contract._hook,
            )

        # Convert result to hex string if bytes
        if isinstance(result, bytes):
            result = "0x" + result.hex()

        # Decode result
        return self._decode_result(result)

    def _encode_calldata(self, *args: Any) -> str:
        """Encode function call data."""
        if not self._abi.inputs:
            return "0x" + self._abi.selector.hex()

        # Convert floats to ints (supports scientific notation like 1e18)
        converted_args = [int(a) if isinstance(a, float) else a for a in args]
        types = [inp["type"] for inp in self._abi.inputs]
        encoded_args = abi_encode(types, converted_args)
        return "0x" + self._abi.selector.hex() + encoded_args.hex()

    def _decode_result(self, result: str) -> Any:
        """Decode function return value with Brownie-compatible wrapping."""
        if not self._abi.outputs:
            return None

        if result == "0x" or not result:
            return None

        if isinstance(result, str) and result.startswith("0x0x"):
            result = "0x" + result[4:]

        # Remove 0x prefix
        data = bytes.fromhex(result[2:] if result.startswith("0x") else result)
        if not data:
            return None

        types = [out["type"] for out in self._abi.outputs]
        decoded = abi_decode(types, data)

        # Single return value
        if len(decoded) == 1:
            # If it's a struct, wrap it so nested fields are accessible
            if self._abi.outputs[0].get("components"):
                return ReturnValue(decoded, self._abi.outputs)[0]
            return decoded[0]

        # Multiple return values: wrap in ReturnValue for named access
        return ReturnValue(decoded, self._abi.outputs)


class OverloadedFunction:
    """Dispatcher for overloaded contract functions.

    Resolves the correct overload based on argument count and delegates
    to FunctionCaller. If multiple overloads match, raises AmbiguousOverloadError.
    """

    def __init__(self, contract: "ContractHandle", overloads: list[FunctionABI]) -> None:
        self._contract = contract
        self._overloads = overloads

    def __call__(self, *args: Any) -> Any:
        # Check if last arg is tx_params dict (Brownie-style)
        if args and isinstance(args[-1], dict) and "from" in args[-1]:
            tx_params = args[-1]
            func_args = args[:-1]
            caller = self._resolve(func_args)  # Resolve based on func_args count
            return caller(*func_args, tx_params)  # FunctionCaller handles tx_params
        else:
            caller = self._resolve(args)
            return caller(*args)

    def call(self, *args: Any) -> Any:
        caller = self._resolve(args)
        return caller.call(*args)

    def encode_input(self, *args: Any) -> str:
        caller = self._resolve(args)
        return caller.encode_input(*args)

    def transact(self, *args: Any) -> "TxReceipt":
        caller, func_args = self._resolve_for_transact(args)
        return caller.transact(*func_args)

    def _resolve(self, args: tuple[Any, ...]) -> FunctionCaller:
        matches = [f for f in self._overloads if len(f.inputs) == len(args)]
        if not matches:
            candidates = [f.signature for f in self._overloads]
            raise OverloadMatchError(
                self._overloads[0].name,
                len(args),
                candidates,
            )
        if len(matches) > 1:
            candidates = [f.signature for f in matches]
            raise AmbiguousOverloadError(
                self._overloads[0].name,
                len(args),
                candidates,
            )
        return FunctionCaller(self._contract, matches[0])

    def _resolve_for_transact(
        self, args: tuple[Any, ...]
    ) -> tuple[FunctionCaller, tuple[Any, ...]]:
        if not args or not isinstance(args[-1], dict):
            raise ValueError(
                f"{self._overloads[0].name}.transact() requires tx_params dict as last argument."
            )
        func_args = args[:-1]
        caller = self._resolve(func_args)
        return caller, args


class ExplicitFunctionCaller:
    """Explicit function caller for overloaded functions.

    Usage:
        token.fn("balanceOf(address)").call(owner)
        token.fn("transfer(address,uint256)").transact(to, amount, {"from": "worker"})
    """

    def __init__(
        self,
        contract: "ContractHandle",
        function_abi: FunctionABI,
    ) -> None:
        self._contract = contract
        self._abi = function_abi

    def call(self, *args: Any) -> Any:
        """Execute eth_call and return decoded result.

        Works for both view and state-changing functions (simulates the call).
        """
        caller = FunctionCaller(self._contract, self._abi)
        return caller._execute_call(*args)

    def transact(self, *args: Any) -> "TxReceipt":
        """Broadcast the transaction and wait for receipt.

        Only works inside a @broadcast decorated function.
        Transaction params dict must be the last argument.
        """
        caller = FunctionCaller(self._contract, self._abi)
        return caller.transact(*args)

    def encode_input(self, *args: Any) -> str:
        """Encode function call data without executing.

        Returns hex-encoded calldata.
        """
        caller = FunctionCaller(self._contract, self._abi)
        return caller._encode_calldata(*args)
