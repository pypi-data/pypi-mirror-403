"""Implicit context for job hooks and console.

Provides thread-safe context storage using Python's contextvars module.
The framework sets these before calling check() / build_tx(), allowing
helper functions like Contract(), trigger(), intent() to work without explicit
ctx parameter.

Usage (in job methods):
    from brawny import Contract, trigger, intent, block

    def check(self, ctx):
        vault = Contract("vault")  # Works because context is set
        return trigger(reason="...", tx_required=True)

Usage (in lifecycle hooks):
    from brawny import Contract, shorten, explorer_link

    def on_success(self, ctx):
        vault = Contract("vault")
        ctx.alert(f"Done!\\n{explorer_link(ctx.receipt.transaction_hash)}")

Usage (in console):
    >>> claimer = interface.IClaimer("0x...")  # Works via console context
"""

from __future__ import annotations

import contextvars
from contextvars import Token
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from brawny.model.contexts import CheckContext, BuildContext, AlertContext
    from brawny.jobs.base import Job
    from brawny._rpc.clients import BroadcastClient
    from brawny.alerts.contracts import ContractSystem

# Type alias for any phase context
PhaseContext = Union["CheckContext", "BuildContext"]


@dataclass(frozen=True)
class ActiveContext:
    """Minimal context for Contract()/interface/web3 access.

    Used by console (and potentially scripts/tests) to provide the
    necessary dependencies without requiring full job/alert context.
    """

    rpc: BroadcastClient
    contract_system: ContractSystem
    chain_id: int
    network_name: str | None = None
    rpc_group: str | None = None


# Context variables - set by framework before calling job hooks
_job_ctx: contextvars.ContextVar[PhaseContext | None] = contextvars.ContextVar(
    "job_ctx", default=None
)
_current_job: contextvars.ContextVar[Job | None] = contextvars.ContextVar(
    "current_job", default=None
)
# Alert context - uses Any to support both old AlertContext and new hook contexts
_alert_ctx: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "alert_ctx", default=None
)
_console_ctx: contextvars.ContextVar[ActiveContext | None] = contextvars.ContextVar(
    "console_ctx", default=None
)

# Block pinning for check() scope - ensures consistent snapshot reads
_check_block: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "check_block", default=None
)


def get_job_context() -> PhaseContext:
    """Get the current phase context (CheckContext or BuildContext).

    Returns:
        The active context

    Raises:
        LookupError: If called outside a job hook (check/build_tx)
    """
    ctx = _job_ctx.get()
    if ctx is None:
        raise LookupError(
            "No active context. Must be called from within check() or build_tx()."
        )
    return ctx


def get_current_job() -> Job:
    """Get the current Job instance.

    Returns:
        The active Job

    Raises:
        LookupError: If called outside a job hook
    """
    job = _current_job.get()
    if job is None:
        raise LookupError("No active job.")
    return job


def get_alert_context() -> Any | None:
    """Get the current alert context if available.

    Returns:
        The active context (TriggerContext, SuccessContext, FailureContext,
        or AlertContext for legacy hooks), or None if not in a hook
    """
    return _alert_ctx.get()


def set_alert_context(ctx: Any) -> Token:
    """Set the current alert context, return token for reset.

    Called by the framework before invoking hooks. Use token-based reset
    to ensure safe nesting if hooks call helpers.

    Args:
        ctx: Context to set (TriggerContext, SuccessContext, FailureContext)

    Returns:
        Token that can be used to reset the context
    """
    return _alert_ctx.set(ctx)


def reset_alert_context(token: Token) -> None:
    """Reset alert context to previous value using token.

    Args:
        token: Token from set_alert_context()
    """
    _alert_ctx.reset(token)


def get_console_context() -> ActiveContext | None:
    """Get the current console ActiveContext if available.

    Returns:
        The active console context, or None if not in console
    """
    return _console_ctx.get()


def set_console_context(ctx: ActiveContext | None) -> contextvars.Token:
    """Set the console ActiveContext.

    Called by console at startup to enable Contract()/interface/web3 access.

    Args:
        ctx: ActiveContext to set, or None to clear

    Returns:
        Token that can be used to reset the context (useful for tests)
    """
    return _console_ctx.set(ctx)


# =============================================================================
# Block Pinning for check() Scope
# =============================================================================


def set_check_block(block_number: int) -> contextvars.Token:
    """Set the block number for check() scope.

    Called by the runner before invoking check() to pin all Contract reads
    to a consistent block snapshot.

    Args:
        block_number: Block number to pin reads to

    Returns:
        Token for reset (must call reset_check_block when check completes)
    """
    return _check_block.set(block_number)


def reset_check_block(token: contextvars.Token) -> None:
    """Reset check block after check() completes.

    Args:
        token: Token from set_check_block()
    """
    _check_block.reset(token)


def get_check_block() -> int | None:
    """Get current check block, or None if not in check scope.

    Returns:
        Block number if in check() scope, None otherwise
    """
    return _check_block.get()


def resolve_block_identifier(
    explicit: int | str | None,
    handle_block: int | None = None,
) -> int | str:
    """Resolve block identifier with 4-level precedence.

    Precedence (highest to lowest):
    1. Explicit param (caller override) - always wins
    2. Handle's baked block (from ctx.contracts.at_block())
    3. Check scope pin (_check_block contextvar)
    4. Default "latest"

    Args:
        explicit: Explicitly passed block_identifier (None if not passed)
        handle_block: Block baked into ContractHandle (None if not set)

    Returns:
        Block identifier to use for eth_call (int or "latest")
    """
    if explicit is not None:
        return explicit
    if handle_block is not None:
        return handle_block
    check_block = get_check_block()
    if check_block is not None:
        return check_block
    return "latest"
