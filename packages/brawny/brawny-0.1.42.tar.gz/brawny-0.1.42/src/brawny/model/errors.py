"""Error types for brawny."""

from dataclasses import dataclass
from enum import Enum


class HookType(Enum):
    """Alert hook types."""

    TRIGGERED = "triggered"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class TriggerReason:
    """Constants for synthetic trigger reasons (not from job.check())."""

    MISSING = "missing_trigger"
    UNKNOWN_VERSION = "unknown_version"
    INVALID_FORMAT = "invalid_format"
    # CHECK_EXCEPTION and BUILD_TX_EXCEPTION use FailureType.*.value


@dataclass
class ErrorInfo:
    """Structured error for alert context. JSON-safe."""

    error_type: str  # e.g., "SimulationReverted", "BroadcastFailed"
    message: str  # Truncated, sanitized
    code: str | None = None  # RPC error code if applicable

    @classmethod
    def from_exception(cls, e: Exception, max_len: int = 200) -> "ErrorInfo":
        """Create ErrorInfo from an exception."""
        code = getattr(e, "code", None)
        return cls(
            error_type=type(e).__name__,
            message=str(e)[:max_len],
            code=str(code) if code is not None else None,
        )


class FailureStage(Enum):
    """When in the lifecycle did the failure occur."""

    PRE_BROADCAST = "pre_broadcast"  # Never made it to chain
    BROADCAST = "broadcast"  # Failed during broadcast
    POST_BROADCAST = "post_broadcast"  # Failed after broadcast (on-chain)


class FailureType(Enum):
    """What specifically failed."""

    # Permanent (no retry will help)
    SIMULATION_REVERTED = "simulation_reverted"  # TX would revert
    TX_REVERTED = "tx_reverted"  # On-chain revert
    DEADLINE_EXPIRED = "deadline_expired"  # Intent too old

    # Transient (might resolve on retry)
    SIMULATION_NETWORK_ERROR = "simulation_network_error"  # RPC issue during sim
    BROADCAST_FAILED = "broadcast_failed"  # RPC rejected tx

    # Pre-broadcast failures (kept for backward compat)
    SIGNER_FAILED = "signer_failed"  # Keystore/signer issue
    NONCE_FAILED = "nonce_failed"  # Couldn't reserve nonce
    SIGN_FAILED = "sign_failed"  # Signing error
    NONCE_CONSUMED = "nonce_consumed"  # Nonce used elsewhere

    # Superseded (replaced by new attempt)
    SUPERSEDED = "superseded"

    # Reorg (terminal - we don't retry reorged intents)
    REORGED = "reorged"

    # Pre-intent exceptions (no intent created yet)
    CHECK_EXCEPTION = "check_exception"  # job.check() crashed
    BUILD_TX_EXCEPTION = "build_tx_exception"  # job.build_tx() crashed

    # Fallback
    UNKNOWN = "unknown"


class BrawnyError(Exception):
    """Base exception for all brawny errors."""

    pass


class ConfigError(BrawnyError):
    """Configuration error."""

    pass


class DatabaseError(BrawnyError):
    """Database operation error."""

    pass


class TransactionFailed(DatabaseError):
    """Transaction marked rollback-only due to an inner failure."""

    pass


class InvariantViolation(DatabaseError):
    """Internal invariant violated."""

    pass


class NonceError(BrawnyError):
    """Nonce management error."""

    pass


class NonceReservationError(NonceError):
    """Failed to reserve a nonce."""

    pass


class NonceUnavailable(NonceReservationError):
    """Chain nonce unavailable; reservation cannot proceed."""

    def __init__(self, message: str, endpoint: str | None = None) -> None:
        super().__init__(message)
        self.endpoint = endpoint


class IntentError(BrawnyError):
    """Transaction intent error."""

    pass


class RetriableExecutionError(BrawnyError):
    """Temporary execution error that should be retried with backoff.

    Used when execution cannot proceed temporarily (e.g., no gas quote available)
    but may succeed after a backoff period.
    """

    pass


class JobError(BrawnyError):
    """Job execution error."""

    pass


class ReorgError(BrawnyError):
    """Blockchain reorganization error."""

    pass


class KeystoreError(BrawnyError):
    """Keystore or signing error."""

    pass


class ABIResolutionError(BrawnyError):
    """ABI resolution failed."""

    pass


class ReceiptRequiredError(BrawnyError):
    """Attempted to access receipt-only features without a receipt."""

    pass


class EventNotFoundError(BrawnyError):
    """Event not found in receipt logs."""

    pass


class StateChangingCallError(BrawnyError):
    """Attempted to call a state-changing function in a read-only context."""

    pass


class CircuitBreakerOpenError(BrawnyError):
    """All RPC endpoints are unhealthy."""

    pass


class DatabaseCircuitBreakerOpenError(BrawnyError):
    """Database circuit breaker is open."""

    pass


class CancelledCheckError(BrawnyError):
    """Check was cancelled by the runner; intent creation should not proceed."""

    pass


class SimulationReverted(BrawnyError):
    """Transaction would revert on-chain. Permanent failure - do not retry or broadcast."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class SimulationNetworkError(BrawnyError):
    """Network/RPC error during simulation. Transient - may retry."""

    pass
