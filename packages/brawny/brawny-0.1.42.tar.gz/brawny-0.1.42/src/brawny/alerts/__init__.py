"""Alerts extension with contract handles, ABI resolution, and event decoding.

This extension provides an ergonomic interface for job authors to:
- Send alerts from lifecycle hooks via ctx.alert()
- Interact with contracts in hooks
- Decode events from transaction receipts (brownie-compatible)
- Make contract reads
- Format messages with explorer links

Key components:
- SuccessContext: Context passed to on_success with receipt + events
- FailureContext: Context passed to on_failure with error info
- ContractHandle: Interface for contract function calls
- ABIResolver: Automatic ABI resolution with caching

Formatting helpers (Markdown is the default):
- shorten(hash): "0x1234...5678"
- explorer_link(hash): "[🔗 View on Explorer](url)"
- escape_markdown_v2(text): Escapes special characters

Usage in lifecycle hooks:

    from brawny.alerts import shorten, explorer_link
    from brawny.model.contexts import SuccessContext

    def on_success(self, ctx: SuccessContext) -> None:
        # Decode events from receipt (brownie-compatible)
        if ctx.events:
            deposit = ctx.events[0]  # First decoded event
            amount = deposit["assets"]

            # Format with explorer links
            tx_link = explorer_link(ctx.receipt.transaction_hash)

            ctx.alert(f"Deposited {amount}\\n{tx_link}")
        else:
            ctx.alert(f"Confirmed: {shorten(ctx.receipt.transaction_hash)}")
"""

from brawny.alerts.context import AlertContext, JobMetadata
from brawny.alerts.contracts import (
    ContractSystem,
    ContractHandle,
    FunctionCaller,
    ExplicitFunctionCaller,
)
from brawny.alerts.events import (
    EventAccessor,
    DecodedEvent,
    AttributeDict,
    LogEntry,
)
from brawny.alerts.abi_resolver import ABIResolver, ResolvedABI
from brawny.alerts.base import (
    shorten,
    explorer_link,
    escape_markdown_v2,
    get_explorer_url,
    format_tx_link,
    format_address_link,
)
from brawny.alerts.send import (
    AlertEvent,
    AlertPayload,
    AlertConfig,
    send_alert,
    alert,
)
from brawny.alerts.errors import (
    DXError,
    ABINotFoundError,
    ProxyResolutionError,
    StateChangingCallError,
    ReceiptRequiredError,
    EventNotFoundError,
    AmbiguousOverloadError,
    OverloadMatchError,
    FunctionNotFoundError,
    InvalidAddressError,
    EventDecodeError,
    ContractCallError,
    ABICacheError,
)

__all__ = [
    # Context
    "AlertContext",
    "JobMetadata",
    # Contracts
    "ContractHandle",
    "FunctionCaller",
    "ExplicitFunctionCaller",
    "ContractSystem",
    # Events
    "EventAccessor",
    "DecodedEvent",
    "AttributeDict",
    "LogEntry",
    # ABI Resolution
    "ABIResolver",
    "ResolvedABI",
    # Alert System
    "AlertEvent",
    "AlertPayload",
    "AlertConfig",
    "send_alert",
    "alert",
    # Formatting
    "shorten",
    "explorer_link",
    "escape_markdown_v2",
    "get_explorer_url",
    "format_tx_link",
    "format_address_link",
    # Errors
    "DXError",
    "ABINotFoundError",
    "ProxyResolutionError",
    "StateChangingCallError",
    "ReceiptRequiredError",
    "EventNotFoundError",
    "AmbiguousOverloadError",
    "OverloadMatchError",
    "FunctionNotFoundError",
    "InvalidAddressError",
    "EventDecodeError",
    "ContractCallError",
    "ABICacheError",
]
