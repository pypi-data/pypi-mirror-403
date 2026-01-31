"""Phase-specific contexts for the job lifecycle.

Each phase gets only what it needs:
- CheckContext: Read chain state, return Trigger. KV is read+write.
- BuildContext: Produces TxSpec. Has trigger + signer. KV is read-only.
- AlertContext: Receives immutable snapshots. KV is read-only.

Contract access is explicit and block-aware:
- at_block(name, addr, block): Pinned reads for check()
- at(name, addr): Latest reads for build/alerts

Lifecycle hooks (on_trigger, on_success, on_failure) have ctx.alert() for
sending alerts to job destinations. See AlertMixin for details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from brawny.alerts.events import EventDict
from brawny.model.errors import FailureType, FailureStage

if TYPE_CHECKING:
    from brawny.jobs.kv import KVReader, KVStore
    from brawny.model.types import Trigger, TxIntent, TxAttempt
    from brawny.jobs.base import TxInfo, TxReceipt
    from brawny.alerts.send import AlertConfig
    from brawny.config.models import TelegramConfig
    from brawny.telegram import TelegramBot
    import structlog


# =============================================================================
# Alert Sender Protocol + Mixin
# =============================================================================


class AlertSender(Protocol):
    """Protocol for alert sending. Injected into lifecycle contexts."""

    def send(
        self,
        message: str,
        *,
        to: str | list[str] | None = None,
        parse_mode: str | None = None,
    ) -> None:
        """Send alert to configured destinations.

        Args:
            message: Alert text
            to: Override routing (name, ID, or list). None = job's default.
            parse_mode: "Markdown", "MarkdownV2", "HTML", or None
        """
        ...


class AlertMixin:
    """Mixin providing ctx.alert() for lifecycle hooks.

    Targets job alert destinations (job._alert_to, else default/public).
    System/admin alerts are framework-owned.

    This mixin expects the class to have an `_alert_sender` attribute
    that implements the AlertSender protocol.
    """

    _alert_sender: AlertSender | None

    def alert(
        self,
        message: str,
        *,
        to: str | list[str] | None = None,
        parse_mode: str | None = None,
    ) -> None:
        """Send alert to job destinations.

        Usage:
            def on_success(self, ctx):
                ctx.alert(f"Confirmed: {ctx.receipt.transactionHash.hex()}")

        Routing:
            - Uses job's configured alert destinations (job._alert_to)
            - Falls back to telegram.default, then telegram.public
            - Respects config parse_mode and rate limiting

        Args:
            message: Alert text (up to 4096 characters)
            to: Override routing target (name, ID, or list). None = job's default.
            parse_mode: "Markdown", "MarkdownV2", "HTML", or None for config default
        """
        if self._alert_sender is not None:
            self._alert_sender.send(message, to=to, parse_mode=parse_mode)


# =============================================================================
# Contract Factory Protocol
# =============================================================================


class ContractHandle(Protocol):
    """Protocol for contract handles. Actual implementation in alerts/contracts.py."""

    @property
    def address(self) -> str:
        """Contract address (checksummed)."""
        ...

    def _call_with_calldata(self, calldata: str, abi: Any) -> Any:
        """Execute eth_call with pre-encoded calldata."""
        ...


class ContractFactory(Protocol):
    """Factory for creating contract handles.

    Block-aware contract access:
    - at(): Get handle reading at 'latest'. Use in build/alerts.
    - at_block(): Get handle pinned to specific block. Use in check().
    - with_abi(): Get handle with explicit ABI.

    Factory stays dumb:
    - Does not silently switch endpoints/groups
    - Does not mutate global caches
    - Is deterministic under a given rpc + abi_resolver
    - Factory binds handles; resolver owns policy
    """

    def at(self, name: str, address: str) -> ContractHandle:
        """Get contract handle, reads at 'latest'. Use in build/alerts."""
        ...

    def at_block(self, name: str, address: str, block: int) -> ContractHandle:
        """Get contract handle pinned to specific block. Use in check()."""
        ...

    def with_abi(self, address: str, abi: list[Any]) -> ContractHandle:
        """Get contract handle with explicit ABI."""
        ...


# =============================================================================
# Block Context (Immutable Snapshot)
# =============================================================================


@dataclass(frozen=True)
class BlockContext:
    """Immutable chain state snapshot at check() time.

    Contains only chain state metadata. Jobs can still make RPC calls,
    but check() reads should be block-pinned using ctx.block.number.
    """

    number: int
    timestamp: int
    hash: str
    base_fee: int
    chain_id: int


class CancellationToken:
    """Cooperative cancellation marker for runner-owned deadlines."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled


# =============================================================================
# Check Context
# =============================================================================


@dataclass(frozen=True)
class CheckContext:
    """Context available during check(). Read chain state, return Trigger.

    Semantic rules:
    - check() may read chain state + mutate kv
    - Returns Trigger | None
    - Use ctx.contracts.at_block(name, addr, ctx.block.number) for block-pinned reads
    """

    block: BlockContext
    kv: KVStore  # Read+write allowed
    job_id: str
    rpc: Any  # ReadClient/BroadcastClient or similar
    http: Any  # ApprovedHttpClient
    logger: "structlog.stdlib.BoundLogger"
    contracts: ContractFactory
    cancellation_token: CancellationToken | None = None
    _db: Any = None  # Internal: for log()

    def log(self, level: str = "info", **fields: Any) -> None:
        """Record structured snapshot. Best-effort, never interrupts."""
        if self._db is None:
            return
        try:
            from brawny.db.ops import logs as log_ops
            log_ops.insert_log(
                self._db, self.block.chain_id, self.job_id,
                self.block.number, level, fields
            )
        except Exception as e:
            # RECOVERABLE log snapshots are best-effort.
            self.logger.error("log_failed", error=str(e), exc_info=True)


# =============================================================================
# Build Context
# =============================================================================


@dataclass(frozen=True)
class BuildContext:
    """Context available during build_tx(). Produces transaction spec.

    Semantic rules:
    - build_tx() produces a TxSpec
    - Has trigger + signer_address
    - KV is read-only
    - ctx.contracts.at(name, addr) defaults to 'latest', fine for build
    - Safety-critical predicates should be computed in check() and encoded in Trigger.data
    """

    block: BlockContext
    trigger: "Trigger"
    job_id: str
    signer_address: str  # Signer belongs here, not on RPC
    rpc: Any  # ReadClient/BroadcastClient or similar
    http: Any  # ApprovedHttpClient
    logger: "structlog.stdlib.BoundLogger"
    contracts: ContractFactory
    kv: KVReader  # Read-only


# =============================================================================
# Alert Context
# =============================================================================


@dataclass(frozen=True)
class AlertContext:
    """Context available during alert hooks. Immutable snapshots only.

    Semantic rules:
    - Alert hooks receive immutable snapshots
    - KV is read-only
    - events is brownie-compatible EventDict (decoded from receipt)
    - chain_id comes from block.chain_id (no duplication)
    """

    block: BlockContext
    trigger: "Trigger"
    tx: "TxInfo | None"
    receipt: "TxReceipt | None"
    events: EventDict | None  # Brownie-compatible event dict
    failure_type: FailureType | None
    error_info: Any | None  # ErrorInfo for failure context
    logger: "structlog.stdlib.BoundLogger"
    contracts: ContractFactory
    kv: KVReader  # Read-only
    http: Any | None = None  # ApprovedHttpClient (optional)

    @property
    def has_receipt(self) -> bool:
        """Check if receipt is available."""
        return self.receipt is not None

    @property
    def has_error(self) -> bool:
        """Check if this is a failure context."""
        return self.failure_type is not None

    @property
    def error_message(self) -> str:
        """Convenience: error message or 'unknown'."""
        if self.error_info is not None and hasattr(self.error_info, "message"):
            return self.error_info.message
        return "unknown"

    @property
    def chain_id(self) -> int:
        """Chain ID from block context."""
        return self.block.chain_id


# =============================================================================
# Hook Contexts (New Simplified API)
# =============================================================================


@dataclass(frozen=True)
class TriggerContext(AlertMixin):
    """Passed to on_trigger. Trigger still exists here.

    Use for:
    - Monitor-only jobs (tx_required=False) - your only hook
    - Pre-transaction alerts/logging
    - KV updates before intent creation

    Note: No intent exists yet. After this hook, trigger is gone -
          only intent.metadata persists.

    Alert routing: ctx.alert() → job._alert_to → telegram.default → telegram.public
    """

    trigger: "Trigger"
    block: BlockContext
    kv: "KVStore"  # Read+write (pre-intent)
    logger: "structlog.stdlib.BoundLogger"
    http: Any  # ApprovedHttpClient
    # Alert routing
    job_id: str
    job_name: str
    chain_id: int
    alert_config: "AlertConfig"
    telegram_config: "TelegramConfig"  # Always exists (Config.telegram has default factory)
    # Optional telegram fields
    telegram_bot: "TelegramBot | None" = None
    job_alert_to: list[str] | None = None
    # Alert sender (injected by lifecycle dispatcher)
    _alert_sender: AlertSender | None = field(default=None, repr=False)


@dataclass(frozen=True)
class SuccessContext(AlertMixin):
    """Passed to on_success. No trigger - use intent.metadata.

    ctx.intent.metadata["reason"] = original trigger.reason
    ctx.intent.metadata[...] = your custom data from build_tx()

    Alert routing: ctx.alert() → job._alert_to → telegram.default → telegram.public
    """

    intent: "TxIntent"
    receipt: "TxReceipt"
    events: EventDict | None
    block: BlockContext
    kv: "KVReader"  # Read-only
    logger: "structlog.stdlib.BoundLogger"
    http: Any  # ApprovedHttpClient
    # Alert routing
    job_id: str
    job_name: str
    chain_id: int
    alert_config: "AlertConfig"
    telegram_config: "TelegramConfig"  # Always exists (Config.telegram has default factory)
    # Optional telegram fields
    telegram_bot: "TelegramBot | None" = None
    job_alert_to: list[str] | None = None
    # Alert sender (injected by lifecycle dispatcher)
    _alert_sender: AlertSender | None = field(default=None, repr=False)


@dataclass(frozen=True)
class FailureContext(AlertMixin):
    """Passed to on_failure. Intent may be None for pre-intent failures.

    Pre-intent failures include:
    - check() exception
    - build_tx() exception
    - intent creation failure

    Alert routing: ctx.alert() → job._alert_to → telegram.default → telegram.public
    """

    intent: "TxIntent | None"  # None for pre-intent failures
    attempt: "TxAttempt | None"  # intent None for pre-intent; attempt may be None even post-intent
    error: Exception
    failure_type: FailureType
    failure_stage: FailureStage | None
    block: BlockContext
    kv: "KVReader"  # Read-only (no side effects during failure handling)
    logger: "structlog.stdlib.BoundLogger"
    http: Any  # ApprovedHttpClient
    # Alert routing
    job_id: str
    job_name: str
    chain_id: int
    alert_config: "AlertConfig"
    telegram_config: "TelegramConfig"  # Always exists (Config.telegram has default factory)
    # Optional telegram fields
    telegram_bot: "TelegramBot | None" = None
    job_alert_to: list[str] | None = None
    # Alert sender (injected by lifecycle dispatcher)
    _alert_sender: AlertSender | None = field(default=None, repr=False)


# =============================================================================
# Context Size Caps (Prevent Re-Growth)
# =============================================================================

# These are validated in tests to prevent gradual re-growth into god object:
# - BlockContext: <= 5 fields
# - CheckContext: <= 8 fields
# - BuildContext: <= 9 fields
# - AlertContext: <= 11 fields


__all__ = [
    "BlockContext",
    "CheckContext",
    "BuildContext",
    "AlertContext",
    "TriggerContext",
    "SuccessContext",
    "FailureContext",
    "ContractFactory",
    "ContractHandle",
    "AlertSender",
    "AlertMixin",
]
