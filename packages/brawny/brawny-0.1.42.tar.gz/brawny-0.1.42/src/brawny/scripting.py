"""Scripting utilities for brawny.

Provides the @broadcast decorator for enabling transaction broadcasting
in standalone scripts. Job hooks cannot use @broadcast.
"""

from __future__ import annotations

import functools
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from brawny.alerts.contracts import ContractSystem
    from brawny.keystore import Keystore

# Thread-local context for broadcast and job execution state
_context = threading.local()

F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# Context Management
# =============================================================================


def broadcast_enabled() -> bool:
    """Check if broadcast context is active.

    Returns:
        True if inside a @broadcast decorated function
    """
    return getattr(_context, "broadcast_active", False)


def in_job_context() -> bool:
    """Check if currently executing inside a job hook.

    Returns:
        True if inside a job hook (check, build_intent, alert hooks)
    """
    return getattr(_context, "job_active", False)


def set_job_context(active: bool) -> None:
    """Set the job execution context flag.

    Called by the job runner before/after executing job hooks.

    Args:
        active: True when entering job hook, False when exiting
    """
    _context.job_active = active


def get_broadcast_context() -> BroadcastContext | None:
    """Get the current broadcast context if active.

    Returns:
        BroadcastContext or None if not in broadcast mode
    """
    return getattr(_context, "broadcast_context", None)


# =============================================================================
# Errors
# =============================================================================


class BroadcastNotAllowedError(Exception):
    """Raised when .transact() is called outside @broadcast context."""

    def __init__(self, function_name: str, reason: str | None = None) -> None:
        self.function_name = function_name
        self.reason = reason or "not inside @broadcast context"
        super().__init__(
            f"Cannot broadcast '{function_name}': {self.reason}. "
            f"Use @broadcast decorator to enable transaction broadcasting."
        )


class SignerNotFoundError(Exception):
    """Raised when the 'from' address cannot be resolved to a signer."""

    def __init__(self, signer: str) -> None:
        self.signer = signer
        super().__init__(
            f"Signer '{signer}' not found in keystore. "
            f"Provide a valid wallet name or address."
        )


class TransactionRevertedError(Exception):
    """Raised when a broadcasted transaction reverts on-chain."""

    def __init__(self, tx_hash: str, reason: str | None = None) -> None:
        self.tx_hash = tx_hash
        self.reason = reason
        msg = f"Transaction {tx_hash} reverted"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class TransactionTimeoutError(Exception):
    """Raised when waiting for a transaction receipt times out."""

    def __init__(self, tx_hash: str, timeout_seconds: int) -> None:
        self.tx_hash = tx_hash
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Timeout waiting for transaction {tx_hash} after {timeout_seconds}s"
        )


# =============================================================================
# Broadcast Context
# =============================================================================


@dataclass
class BroadcastContext:
    """Context object available inside @broadcast decorated functions.

    Provides access to contract system and broadcast configuration.
    """

    system: ContractSystem
    keystore: "Keystore | None" = None
    timeout_seconds: int = 120
    poll_interval_seconds: float = 2.0

    def contract(self, address: str, abi: list[dict[str, Any]] | None = None):
        """Get a contract handle for the given address.

        Prefer using Contract() from brawny instead:
            from brawny import Contract
            vault = Contract("0x...")

        Args:
            address: Contract address
            abi: Optional ABI (resolved automatically if not provided)

        Returns:
            ContractHandle for interacting with the contract
        """
        return self.system.handle(address=address, abi=abi)


# =============================================================================
# Broadcast Decorator
# =============================================================================


def broadcast(
    system: ContractSystem | None = None,
    keystore: "Keystore | None" = None,
    timeout_seconds: int = 120,
    poll_interval_seconds: float = 2.0,
) -> Callable[[F], F]:
    """Decorator to enable transaction broadcasting in a script.

    The decorated function receives a BroadcastContext as its first argument,
    which provides access to contract handles that can use .transact().

    Usage:
        from brawny import Contract

        @broadcast(system=my_system)
        def run(ctx):
            vault = Contract("0x...")
            receipt = vault.harvest.transact({"from": "yearn-worker"})
            return receipt

    Args:
        system: ContractSystem instance for contract resolution and RPC access
        keystore: Keystore instance for signing
        timeout_seconds: Max time to wait for transaction receipts (default: 120)
        poll_interval_seconds: Interval between receipt checks (default: 2.0)

    Raises:
        BroadcastNotAllowedError: If called from within a job hook
        ValueError: If system is not provided
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if we're inside a job hook
            if in_job_context():
                raise BroadcastNotAllowedError(
                    func.__name__,
                    reason="@broadcast cannot be used inside job hooks",
                )

            # Require system to be provided
            nonlocal system
            if system is None:
                raise ValueError(
                    "@broadcast requires a ContractSystem. "
                    "Use @broadcast(system=my_system)"
                )
            if keystore is None:
                raise ValueError(
                    "@broadcast requires a Keystore for signing. "
                    "Use @broadcast(system=my_system, keystore=my_keystore)"
                )

            # Create broadcast context
            ctx = BroadcastContext(
                system=system,
                keystore=keystore,
                timeout_seconds=timeout_seconds,
                poll_interval_seconds=poll_interval_seconds,
            )

            # Set thread-local flags
            previous_broadcast = getattr(_context, "broadcast_active", False)
            previous_context = getattr(_context, "broadcast_context", None)

            try:
                _context.broadcast_active = True
                _context.broadcast_context = ctx

                # Call function with context as first argument
                return func(ctx, *args, **kwargs)

            finally:
                # Restore previous state
                _context.broadcast_active = previous_broadcast
                _context.broadcast_context = previous_context

        return wrapper  # type: ignore

    return decorator


__all__ = [
    "broadcast",
    "broadcast_enabled",
    "in_job_context",
    "set_job_context",
    "get_broadcast_context",
    "BroadcastContext",
    "BroadcastNotAllowedError",
    "SignerNotFoundError",
    "TransactionRevertedError",
    "TransactionTimeoutError",
]
