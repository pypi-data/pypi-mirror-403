"""alerts-specific error classes for the Alerts extension.

These errors provide clear, actionable feedback when developers
misuse the contract interaction APIs in alert hooks.
"""

from __future__ import annotations


class DXError(Exception):
    """Base class for all alerts-related errors."""

    pass


class ABINotFoundError(DXError):
    """Raised when ABI cannot be resolved for a contract address.

    Includes details about which sources were checked.
    """

    def __init__(self, address: str, checked_sources: list[str]) -> None:
        self.address = address
        self.checked_sources = checked_sources
        sources_str = ", ".join(checked_sources) if checked_sources else "none"
        super().__init__(
            f"ABI not found for {address}. Checked: {sources_str}. "
            f"Consider setting ABI manually with 'brawny abi set {address} --file abi.json'"
        )


class ProxyResolutionError(DXError):
    """Raised when proxy resolution fails.

    This can happen when:
    - EIP-1967 slots don't contain valid addresses
    - Beacon implementation call fails
    - Max recursion depth exceeded
    """

    def __init__(self, address: str, reason: str) -> None:
        self.address = address
        self.reason = reason
        super().__init__(f"Failed to resolve proxy {address}: {reason}")


class StateChangingCallError(DXError):
    """Raised when attempting to call a state-changing function.

    State-changing functions (nonpayable/payable) cannot be called
    via eth_call in alert hooks. Use .encode_input() or .transact() in @broadcast.
    """

    def __init__(
        self,
        function_name: str,
        signature: str,
        address: str | None = None,
        job_id: str | None = None,
        hook: str | None = None,
    ) -> None:
        self.function_name = function_name
        self.signature = signature
        self.address = address
        self.job_id = job_id
        self.hook = hook
        context = _format_context(job_id, hook, address, signature)
        super().__init__(
            f"{function_name}() is a state-changing function{context}. "
            f"Use .encode_input() for calldata or .transact(...) inside @broadcast."
        )


class ReceiptRequiredError(DXError):
    """Raised when accessing events without a receipt context.

    Events are only available in alert_confirmed hook where
    ctx.receipt is populated.
    """

    def __init__(self, operation: str = "Events") -> None:
        self.operation = operation
        super().__init__(
            f"{operation} are only available in alert_confirmed context where receipt is present. "
            f"For other hooks, use ctx.block for current block information."
        )


class EventNotFoundError(DXError):
    """Raised when expected event is not found in receipt logs.

    Provides helpful information about what events are available.
    """

    def __init__(
        self,
        event_name: str,
        address: str,
        available_events: list[str],
    ) -> None:
        self.event_name = event_name
        self.address = address
        self.available_events = available_events
        available_str = ", ".join(available_events) if available_events else "none"
        super().__init__(
            f"No '{event_name}' events found in receipt for {address}. "
            f"Available decoded events: [{available_str}]"
        )


class AmbiguousOverloadError(DXError):
    """Raised when function call matches multiple ABI overloads.

    Provides guidance on using explicit signatures.
    """

    def __init__(
        self,
        function_name: str,
        arg_count: int,
        candidates: list[str],
    ) -> None:
        self.function_name = function_name
        self.arg_count = arg_count
        self.candidates = candidates
        candidates_str = ", ".join(candidates)
        super().__init__(
            f"Multiple matches for '{function_name}' with {arg_count} argument(s). "
            f"Candidates: {candidates_str}. "
            f"Use explicit signature: contract.fn(\"{candidates[0]}\").call(...) "
            f"or contract.fn(\"{candidates[0]}\").transact(...)."
        )


class OverloadMatchError(DXError):
    """Raised when no overload matches the provided arguments."""

    def __init__(
        self,
        function_name: str,
        arg_count: int,
        candidates: list[str],
    ) -> None:
        self.function_name = function_name
        self.arg_count = arg_count
        self.candidates = candidates
        candidates_str = ", ".join(candidates)
        super().__init__(
            f"No overload of '{function_name}' matches {arg_count} argument(s). "
            f"Available: {candidates_str}. "
            f"Use explicit signature: contract.fn(\"{candidates[0]}\").call(...)."
        )


class FunctionNotFoundError(DXError):
    """Raised when function is not found in contract ABI.

    Includes context about ABI resolution status to help diagnose
    whether the ABI was never fetched vs fetched but missing the function.
    """

    def __init__(
        self,
        function_name: str,
        address: str,
        available_functions: list[str] | None = None,
        abi_resolved: bool | None = None,
        abi_source: str | None = None,
    ) -> None:
        self.function_name = function_name
        self.address = address
        self.available_functions = available_functions
        self.abi_resolved = abi_resolved
        self.abi_source = abi_source

        # Build message based on ABI resolution status
        if abi_resolved is False:
            # ABI fetch failed completely
            msg = (
                f"Function '{function_name}' not found for {address}: "
                f"ABI resolution failed. Check logs for etherscan.abi_fetch_failed "
                f"or use ctx.contracts.with_abi() to provide ABI manually."
            )
        elif available_functions:
            # ABI resolved but function not in it
            available_str = ", ".join(available_functions[:10])
            if len(available_functions) > 10:
                available_str += f" ... ({len(available_functions) - 10} more)"
            source_hint = f" (source: {abi_source})" if abi_source else ""
            msg = (
                f"Function '{function_name}' not found in ABI for {address}{source_hint}. "
                f"Available functions: [{available_str}]"
            )
        elif abi_resolved is True:
            # ABI resolved but empty (no functions)
            source_hint = f" (source: {abi_source})" if abi_source else ""
            msg = (
                f"Function '{function_name}' not found for {address}: "
                f"ABI was resolved{source_hint} but contains no functions."
            )
        else:
            # Legacy fallback (no resolution status provided)
            msg = f"Function '{function_name}' not found in ABI for {address}."
        super().__init__(msg)


class InvalidAddressError(DXError):
    """Raised when an invalid Ethereum address is provided."""

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(
            f"Invalid Ethereum address: {address}. "
            f"Address must be a 40-character hex string with 0x prefix."
        )


class EventDecodeError(DXError):
    """Raised when event log cannot be decoded.

    This typically happens when the log signature doesn't match
    any known event in the ABI.
    """

    def __init__(self, log_index: int, topic0: str | None = None) -> None:
        self.log_index = log_index
        self.topic0 = topic0
        if topic0:
            super().__init__(
                f"Failed to decode event at log index {log_index} "
                f"with topic0 {topic0}. Event may not be in ABI."
            )
        else:
            super().__init__(
                f"Failed to decode event at log index {log_index}. "
                f"Log has no topic0 (anonymous event)."
            )


class ContractCallError(DXError):
    """Raised when a contract call fails.

    Wraps underlying RPC errors with context about the call.
    """

    def __init__(
        self,
        function_name: str,
        address: str,
        reason: str,
        block_identifier: int | str | None = None,
        signature: str | None = None,
        job_id: str | None = None,
        hook: str | None = None,
    ) -> None:
        self.function_name = function_name
        self.address = address
        self.reason = reason
        self.block_identifier = block_identifier
        self.signature = signature
        self.job_id = job_id
        self.hook = hook
        block_str = f" at block {block_identifier}" if block_identifier else ""
        context = _format_context(job_id, hook, address, signature)
        super().__init__(
            f"Call to {function_name}() on {address}{block_str}{context} failed: {reason}"
        )


def _format_context(
    job_id: str | None,
    hook: str | None,
    address: str | None,
    signature: str | None,
) -> str:
    parts = []
    if job_id:
        parts.append(f"job={job_id}")
    if hook:
        parts.append(f"hook={hook}")
    if signature:
        parts.append(f"sig={signature}")
    if not parts:
        return ""
    return f" ({', '.join(parts)})"


class ABICacheError(DXError):
    """Raised when ABI cache operations fail."""

    def __init__(self, operation: str, reason: str) -> None:
        self.operation = operation
        self.reason = reason
        super().__init__(f"ABI cache {operation} failed: {reason}")
