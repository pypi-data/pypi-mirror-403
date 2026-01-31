"""Base Job class for brawny.

Jobs are the core abstraction for scheduling and executing Ethereum transactions
based on block events. Jobs implement check() to evaluate conditions and
build_tx() to create transactions.

Phase-specific contexts (OE7):
- CheckContext: Read chain state, return Trigger. KV is read+write.
- BuildContext: Produces TxSpec. Has trigger + signer. KV is read-only.
- AlertContext: Receives immutable snapshots. KV is read-only.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from brawny.model.contexts import (
        CheckContext,
        BuildContext,
        AlertContext,
        TriggerContext,
        SuccessContext,
        FailureContext,
    )
    from brawny.model.types import Trigger, TxIntent, TxIntentSpec, TxAttempt


class TxInfo:
    """Transaction info for alert context."""

    def __init__(
        self,
        hash: str,
        nonce: int,
        from_address: str,
        to_address: str,
        gas_limit: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
    ) -> None:
        self.hash = hash
        self.nonce = nonce
        self.from_address = from_address
        self.to_address = to_address
        self.gas_limit = gas_limit
        self.max_fee_per_gas = max_fee_per_gas
        self.max_priority_fee_per_gas = max_priority_fee_per_gas


class TxReceipt:
    """Transaction receipt for alert context."""

    def __init__(
        self,
        transaction_hash: str,
        block_number: int,
        block_hash: str,
        status: int,
        gas_used: int,
        logs: list[dict[str, Any]],
    ) -> None:
        self.transactionHash = transaction_hash
        self.blockNumber = block_number
        self.blockHash = block_hash
        self.status = status
        self.gasUsed = gas_used
        self.logs = logs


class BlockInfo:
    """Block info for alert context."""

    def __init__(
        self,
        number: int,
        hash: str,
        timestamp: int,
    ) -> None:
        self.number = number
        self.hash = hash
        self.timestamp = timestamp


class Job(ABC):
    """Base class for all jobs.

    Jobs are the core abstraction for scheduling and executing Ethereum
    transactions based on block events.

    Attributes:
        job_id: Stable identifier, must not change across deployments
        name: Human-readable name for logging and alerts
        check_interval_blocks: Minimum blocks between check() calls
        check_timeout_seconds: Timeout for check() execution
        build_timeout_seconds: Timeout for build_intent() execution
        max_in_flight_intents: Optional cap on active intents for this job
    """

    job_id: str
    name: str
    check_interval_blocks: int = 1
    check_timeout_seconds: int = 30
    build_timeout_seconds: int = 10
    max_in_flight_intents: int | None = None
    cooldown_seconds: int | None = None

    # Send override
    rpc: str | None = None  # Override broadcast endpoint for send only

    # Gas overrides (None = inherit from config, all values in wei)
    max_fee: int | None = None
    priority_fee: int | None = None

    # Alert config
    # NOTE: Use None as sentinel to avoid mutable default sharing across subclasses
    telegram_chat_ids: list[str] | None = None  # Override global alert targets (None = use global)

    # Signer config (set by @job(signer="...") decorator)
    _signer_name: str | None = None

    # Alert routing (set by @job(alert_to="...") decorator)
    _alert_to: list[str] | None = None

    @property
    def signer(self) -> str | None:
        """Signer alias from @job(signer="..."), or None if not set."""
        return self._signer_name

    @signer.setter
    def signer(self, value: str | None) -> None:
        """Allow setting signer dynamically (tests/dev flows)."""
        self._signer_name = value

    @property
    def signer_address(self) -> str:
        """Resolved checksummed address for this job's signer.

        Raises:
            RuntimeError: If no signer configured.
            KeystoreError: If signer not found in keystore.
        """
        if self._signer_name is None:
            raise RuntimeError(f"Job '{self.job_id}' has no signer configured.")
        if self._signer_name.startswith("0x") and len(self._signer_name) == 42:
            from web3 import Web3

            return Web3.to_checksum_address(self._signer_name)
        from brawny.api import get_address_from_alias
        return get_address_from_alias(self._signer_name)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Ensure each subclass has its own mutable containers.

        This prevents the Python mutable default argument bug where all
        subclasses would share the same dict/list instance.
        """
        super().__init_subclass__(**kwargs)

        # Create fresh containers for each subclass if not explicitly defined
        # Check if the attribute is inherited from Job (shared) vs defined on cls
        if "telegram_chat_ids" not in cls.__dict__:
            cls.telegram_chat_ids = []
        elif cls.telegram_chat_ids is None:
            cls.telegram_chat_ids = []

    def cooldown_key(self, trigger: Trigger) -> str | None:
        """Optional cooldown key for this trigger.

        Return None for job-wide cooldown.
        """
        return None

    def check(self, *args: Any, **kwargs: Any) -> Trigger | None:
        """Check if job should trigger.

        Called at most once per check_interval_blocks.

        Supported signatures:
            def check(self) -> Trigger | None           # Implicit context
            def check(self, ctx) -> Trigger | None      # Explicit context

        When using implicit context, access via:
            - block.number, block.timestamp (from brawny.api)
            - kv.get(), kv.set() (from brawny.api)
            - Contract() (from brawny.api)
            - ctx() for full context access

        Note:
            Explicit style requires the parameter to be named 'ctx' so the
            runner can detect it safely. Using a different name will be
            treated as implicit style.

        Returns:
            Trigger if action needed, None otherwise
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement check()")

    def build_tx(self, *args: Any, **kwargs: Any) -> TxIntentSpec:
        """Build transaction spec from trigger.

        Only called if trigger.tx_required is True. Trigger is available
        via ctx.trigger (explicit) or via the ctx() helper (implicit).

        Supported signatures:
            def build_tx(self) -> TxIntentSpec           # Implicit context
            def build_tx(self, ctx) -> TxIntentSpec      # Explicit context

        Use ctx.contracts.at(name, addr) for 'latest' reads.
        Safety-critical predicates should be computed in check() and
        encoded in ctx.trigger.reason or intent.metadata.

        Note:
            Explicit style requires the parameter to be named 'ctx' so the
            runner can detect it safely.

        Returns:
            Transaction intent specification

        Raises:
            NotImplementedError: For monitor-only jobs
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement build_tx()")

    # =========================================================================
    # Lifecycle Hooks (New Simplified API)
    # =========================================================================

    def on_trigger(self, ctx: "TriggerContext") -> None:
        """Called when check() returns a Trigger, BEFORE build_tx().

        Use for:
        - Monitor-only jobs (tx_required=False) - your only hook
        - Pre-transaction alerts/logging
        - KV updates before intent creation

        Note: No intent exists yet. After this hook, trigger is gone -
              only intent.metadata persists.

        To send alerts, use:
            from brawny import alert
            alert(f"Triggered: {ctx.trigger.reason}")
        """
        pass

    def on_success(self, ctx: "SuccessContext") -> None:
        """Called when transaction confirms.

        ctx.intent.metadata["reason"] = original trigger.reason
        ctx.intent.metadata[...] = your custom data from build_tx()

        To send alerts, use:
            from brawny import alert
            alert(f"Confirmed: {ctx.intent.metadata['reason']}")
        """
        pass

    def on_failure(self, ctx: "FailureContext") -> None:
        """Called on failures. ctx.intent may be None for pre-intent failures.

        Pre-intent failures include:
        - check() exception
        - build_tx() exception
        - intent creation failure

        To send alerts, use:
            from brawny import alert
            if ctx.intent:
                alert(f"Failed: {ctx.intent.metadata['reason']}")
            else:
                alert(f"Pre-intent failure: {ctx.error}")
        """
        pass
