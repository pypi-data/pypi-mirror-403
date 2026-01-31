"""Alert context for the Alerts extension.

AlertContext is passed to all alert hooks and provides:
- Job metadata and trigger information
- Transaction and receipt data
- Contract handles with ABI resolution
- Brownie-compatible event access via ctx.events
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from brawny.alerts.base import (
    shorten as _shorten,
    explorer_link as _explorer_link,
    get_explorer_url,
)
from brawny.alerts.contracts import ContractHandle, ContractSystem
from brawny.alerts.events import EventDict, decode_logs

if TYPE_CHECKING:
    from brawny.jobs.base import Job, TxReceipt, TxInfo, BlockInfo
    from brawny.model.types import Trigger

from brawny.model.errors import ErrorInfo, FailureType, FailureStage, HookType


@dataclass
class JobMetadata:
    """Job metadata for alert context."""

    id: str
    name: str


@dataclass
class AlertContext:
    """Context passed to alert hooks.

    Provides access to job metadata, trigger data, transaction info,
    receipt data, and contract handles.

    Attributes:
        job: Job metadata (id, name)
        trigger: The trigger that initiated this flow
        chain_id: Chain ID
        hook: HookType indicating which hook is being called
        tx: Transaction info (hash, nonce, gas params) - available after submit
        receipt: Transaction receipt - only available in alert_confirmed
        block: Block info - available in alert_confirmed
        error_info: Structured error info (JSON-safe) - available in alert_failed
        failure_type: Type of failure - available in alert_failed
        events: Brownie-compatible decoded events (only in alert_confirmed)

    Contract access:
        Use Contract("0x...") from brawny.

    Event access (brownie-compatible):
        ctx.events["Deposit"][0]        # First Deposit event
        ctx.events["Deposit"]["amount"] # Field from first Deposit
        "Deposit" in ctx.events         # Check if event exists
    """

    job: JobMetadata
    trigger: Trigger
    chain_id: int = 1
    hook: HookType | None = None
    tx: TxInfo | None = None
    receipt: TxReceipt | None = None
    block: BlockInfo | None = None
    error_info: ErrorInfo | None = None
    failure_type: FailureType | None = None
    failure_stage: FailureStage | None = None  # Kept for backward compat
    _contract_system: ContractSystem | None = None
    _events: EventDict | None = None

    # Backward compat: error property
    @property
    def error(self) -> Exception | None:
        """Deprecated: use error_info instead. Returns None."""
        return None

    @property
    def is_permanent_failure(self) -> bool:
        """True if retrying won't help (simulation revert, on-chain revert, deadline)."""
        return self.failure_type is not None and self.failure_type in {
            FailureType.SIMULATION_REVERTED,
            FailureType.TX_REVERTED,
            FailureType.DEADLINE_EXPIRED,
        }

    @property
    def is_transient_failure(self) -> bool:
        """True if failure might resolve on retry (network issues)."""
        return self.failure_type is not None and self.failure_type in {
            FailureType.SIMULATION_NETWORK_ERROR,
            FailureType.BROADCAST_FAILED,
        }

    @property
    def error_message(self) -> str:
        """Convenience helper: error message or 'unknown'."""
        return self.error_info.message if self.error_info else "unknown"

    @property
    def events(self) -> EventDict:
        """Decoded events from receipt. Brownie-compatible access.

        Usage:
            ctx.events["Transfer"][0]        # First Transfer event
            ctx.events["Transfer"]["amount"] # Field from first Transfer
            len(ctx.events)                  # Total event count
            "Transfer" in ctx.events         # Check if event type exists

        Returns:
            EventDict with all decoded events

        Raises:
            ReceiptRequiredError: If accessed without a receipt
            RuntimeError: If contract system not configured
        """
        from brawny.alerts.errors import ReceiptRequiredError

        if self.receipt is None:
            raise ReceiptRequiredError(
                "ctx.events requires receipt. Only available in alert_confirmed."
            )

        if self._contract_system is None:
            raise RuntimeError(
                "Contract system not configured. Initialize ContractSystem for alert contexts."
            )

        if self._events is None:
            self._events = decode_logs(
                logs=self.receipt.logs,
                contract_system=self._contract_system,
            )

        return self._events

    @classmethod
    def from_job(
        cls,
        job: Job,
        trigger: Trigger,
        chain_id: int = 1,
        hook: HookType | None = None,
        tx: TxInfo | None = None,
        receipt: TxReceipt | None = None,
        block: BlockInfo | None = None,
        error_info: ErrorInfo | None = None,
        failure_type: FailureType | None = None,
        failure_stage: FailureStage | None = None,
        contract_system: ContractSystem | None = None,
    ) -> AlertContext:
        """Create AlertContext from a Job instance.

        Args:
            job: The job instance
            trigger: The trigger that initiated this flow
            chain_id: Chain ID
            hook: HookType indicating which hook is being called
            tx: Transaction info (optional)
            receipt: Transaction receipt (optional, required for alert_confirmed)
            block: Block info (optional)
            error_info: Structured error info (optional, for alert_failed)
            failure_type: Type of failure (optional, for alert_failed)
            failure_stage: Stage when failure occurred (optional, for alert_failed)
            contract_system: Contract system for event decoding

        Returns:
            AlertContext instance
        """
        return cls(
            job=JobMetadata(
                id=job.job_id,
                name=job.name,
            ),
            trigger=trigger,
            chain_id=chain_id,
            hook=hook,
            tx=tx,
            receipt=receipt,
            block=block,
            error_info=error_info,
            failure_type=failure_type,
            failure_stage=failure_stage,
            _contract_system=contract_system,
        )

    def has_receipt(self) -> bool:
        """Check if receipt is available.

        Use this to conditionally access receipt-only features.
        """
        return self.receipt is not None

    def has_error(self) -> bool:
        """Check if error_info is available.

        Use this to conditionally handle error information.
        """
        return self.error_info is not None

    def format_tx_link(self, explorer_url: str | None = None) -> str:
        """Format a link to the transaction on a block explorer.

        Args:
            explorer_url: Base explorer URL (e.g., "https://etherscan.io")
                         If None, returns just the tx hash

        Returns:
            Formatted link or tx hash
        """
        if self.tx is None:
            return "No transaction"

        tx_hash = self.tx.hash
        if explorer_url:
            return f"{explorer_url}/tx/{tx_hash}"
        return tx_hash

    def shorten(self, hex_string: str, prefix: int = 6, suffix: int = 4) -> str:
        """Shorten a hex string (address or hash) for display.

        Args:
            hex_string: Full hex string (e.g., 0x1234...abcd)
            prefix: Characters to keep at start (including 0x)
            suffix: Characters to keep at end

        Returns:
            Shortened string like "0x1234...abcd"

        Example:
            ctx.shorten(ctx.receipt.transactionHash.hex())
            # Returns: "0x1234...5678"
        """
        return _shorten(hex_string, prefix, suffix)

    def explorer_link(
        self,
        hash_or_address: str,
        label: str | None = None,
    ) -> str:
        """Create a Markdown explorer link with emoji.

        Automatically uses the chain_id from the trigger context.
        Detects if input is a tx hash or address.

        Args:
            hash_or_address: Transaction hash or address
            label: Custom label (default: "🔗 View on Explorer")

        Returns:
            Markdown formatted link like "[🔗 View on Explorer](url)"

        Example:
            ctx.explorer_link(ctx.receipt.transactionHash.hex())
            # Returns: "[🔗 View on Explorer](https://etherscan.io/tx/0x...)"
        """
        return _explorer_link(hash_or_address, self.chain_id, label)


# Re-export types for convenience
__all__ = [
    "AlertContext",
    "JobMetadata",
]
