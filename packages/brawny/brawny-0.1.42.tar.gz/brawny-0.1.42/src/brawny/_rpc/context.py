"""RPC job context for attribution metrics.

Provides a contextvar to track which job is making RPC calls,
allowing per-job RPC pressure metrics without high-cardinality labels
on the main RPC metrics.

Usage:
    from brawny._rpc.context import set_job_context, reset_job_context

    token = set_job_context(job.job_id)
    try:
        # ... RPC calls here get attributed to job_id ...
    finally:
        reset_job_context(token)
"""

from contextvars import ContextVar, Token

_rpc_job_ctx: ContextVar[str | None] = ContextVar("rpc_job_ctx", default=None)
_rpc_intent_budget_ctx: ContextVar[str | None] = ContextVar("rpc_intent_budget_ctx", default=None)


def set_job_context(job_id: str | None) -> Token:
    """Set the current job context for RPC attribution.

    Args:
        job_id: Job ID to attribute RPC calls to, or None to clear

    Returns:
        Token for resetting context via reset_job_context()
    """
    return _rpc_job_ctx.set(job_id)


def reset_job_context(token: Token) -> None:
    """Reset job context to previous value.

    Args:
        token: Token returned by set_job_context()
    """
    _rpc_job_ctx.reset(token)


def get_job_context() -> str | None:
    """Get the current job context.

    Returns:
        Job ID if set, None otherwise
    """
    return _rpc_job_ctx.get()


def set_intent_budget_context(budget_key: str | None) -> Token:
    """Set the current intent budget key for retry policies.

    Args:
        budget_key: Budget key string (chain_id:signer:intent_id), or None to clear

    Returns:
        Token for resetting context via reset_intent_budget_context()
    """
    return _rpc_intent_budget_ctx.set(budget_key)


def reset_intent_budget_context(token: Token) -> None:
    """Reset intent budget context to previous value."""
    _rpc_intent_budget_ctx.reset(token)


def get_intent_budget_context() -> str | None:
    """Get the current intent budget key."""
    return _rpc_intent_budget_ctx.get()
