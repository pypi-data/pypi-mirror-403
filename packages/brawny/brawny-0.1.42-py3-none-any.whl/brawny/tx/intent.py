"""Transaction intent creation and management.

Implements durable intent model from SPEC 6:
- Idempotency via unique key constraint
- Create-or-get semantics for deduplication
- Intents are persisted BEFORE signing/sending

Golden Rule: Persist intent before signing/sending - this is non-negotiable.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from brawny.logging import LogEvents, get_logger
from brawny.metrics import INTENT_TRANSITIONS, get_metrics
from brawny.model.enums import IntentStatus, IntentTerminalReason
from brawny.model.errors import CancelledCheckError
from brawny.model.types import TxIntent, TxIntentSpec, Trigger, idempotency_key
from brawny.types import ClaimedIntent
from brawny.utils import db_address, is_valid_address

if TYPE_CHECKING:
    from brawny.db.base import Database
    from brawny.model.contexts import CancellationToken

logger = get_logger(__name__)

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    IntentStatus.CREATED.value: {IntentStatus.CLAIMED.value},
    IntentStatus.CLAIMED.value: {
        IntentStatus.BROADCASTED.value,
        IntentStatus.TERMINAL.value,
    },
    IntentStatus.BROADCASTED.value: {IntentStatus.TERMINAL.value},
    IntentStatus.TERMINAL.value: set(),  # terminal
}


def create_intent(
    db: Database,
    job_id: str,
    chain_id: int,
    spec: TxIntentSpec,
    idem_parts: list[str | int | bytes],
    broadcast_group: str | None = None,
    broadcast_endpoints: list[str] | None = None,
    trigger: Trigger | None = None,
    cancellation_token: "CancellationToken | None" = None,
) -> tuple[TxIntent, bool]:
    """Create a new transaction intent with idempotency.

    Implements create-or-get semantics:
    - If intent with same idempotency key exists, return it
    - Otherwise create new intent

    Args:
        db: Database connection
        job_id: Job that triggered this intent
        chain_id: Chain ID for the transaction
        spec: Transaction specification
        idem_parts: Parts to include in idempotency key
        trigger: Trigger that caused this intent (for metadata auto-merge)

    Returns:
        Tuple of (intent, is_new) where is_new is True if newly created
    """
    # Resolve signer alias early; idempotency is scoped to canonical address.
    signer_alias: str | None = None
    if is_valid_address(spec.signer_address):
        resolved_signer = spec.signer_address
    else:
        if isinstance(spec.signer_address, str) and spec.signer_address.startswith("0x"):
            raise ValueError(f"Invalid signer address: {spec.signer_address}")
        from brawny.api import get_address_from_alias

        signer_alias = spec.signer_address
        resolved_signer = get_address_from_alias(spec.signer_address)

    canonical_signer = db_address(resolved_signer)
    canonical_to = db_address(spec.to_address)

    # Generate idempotency key from job_id and parts
    idem_key = idempotency_key(job_id, *idem_parts)

    # Check for existing intent (scoped to chain + signer)
    existing = db.get_intent_by_idempotency_key(
        chain_id=chain_id,
        signer_address=canonical_signer,
        idempotency_key=idem_key,
    )
    if existing:
        logger.info(
            LogEvents.INTENT_DEDUPE,
            job_id=job_id,
            idempotency_key=idem_key,
            chain_id=chain_id,
            signer=canonical_signer,
            existing_intent_id=str(existing.intent_id),
            existing_status=existing.status.value,
        )
        return existing, False

    if cancellation_token is not None and cancellation_token.cancelled:
        raise CancelledCheckError("Check cancelled before intent creation")

    # Calculate deadline if specified
    deadline_ts: datetime | None = None
    if spec.deadline_seconds:
        deadline_ts = datetime.now(timezone.utc) + timedelta(seconds=spec.deadline_seconds)

    # Generate new intent ID
    intent_id = uuid4()

    # Merge trigger.reason into metadata (job metadata wins on key collision)
    # This is immutable - don't mutate spec.metadata
    base = spec.metadata or {}
    if trigger:
        metadata = {"reason": trigger.reason, **base}
    else:
        metadata = base if base else None

    # Create intent in database
    intent = db.create_intent(
        intent_id=intent_id,
        job_id=job_id,
        chain_id=chain_id,
        signer_address=canonical_signer,
        signer_alias=signer_alias,
        idempotency_key=idem_key,
        to_address=canonical_to,
        data=spec.data,
        value_wei=spec.value_wei,
        gas_limit=spec.gas_limit,
        max_fee_per_gas=str(spec.max_fee_per_gas) if spec.max_fee_per_gas else None,
        max_priority_fee_per_gas=str(spec.max_priority_fee_per_gas) if spec.max_priority_fee_per_gas else None,
        min_confirmations=spec.min_confirmations,
        deadline_ts=deadline_ts,
        broadcast_group=broadcast_group,
        broadcast_endpoints=broadcast_endpoints,
        metadata=metadata,
    )

    if intent is None:
        # Race condition: another process created it between our check and insert
        # This is expected with idempotency - just get the existing one
        existing = db.get_intent_by_idempotency_key(
            chain_id=chain_id,
            signer_address=canonical_signer,
            idempotency_key=idem_key,
        )
        if existing:
            logger.info(
                LogEvents.INTENT_DEDUPE,
                job_id=job_id,
                idempotency_key=idem_key,
                chain_id=chain_id,
                signer=canonical_signer,
                existing_intent_id=str(existing.intent_id),
                note="race_condition",
            )
            return existing, False
        else:
            raise RuntimeError(f"Failed to create or find intent with key {idem_key}")

    logger.info(
        LogEvents.INTENT_CREATE,
        intent_id=str(intent.intent_id),
        job_id=job_id,
        idempotency_key=idem_key,
        signer=canonical_signer,
        to=canonical_to,
    )

    return intent, True


def get_or_create_intent(
    db: Database,
    job_id: str,
    chain_id: int,
    spec: TxIntentSpec,
    idem_parts: list[str | int | bytes],
    broadcast_group: str | None = None,
    broadcast_endpoints: list[str] | None = None,
) -> TxIntent:
    """Get existing intent by idempotency key or create new one.

    This is the primary API for jobs creating intents.
    Ensures exactly-once semantics via idempotency.

    Args:
        db: Database connection
        job_id: Job that triggered this intent
        chain_id: Chain ID for the transaction
        spec: Transaction specification
        idem_parts: Parts to include in idempotency key

    Returns:
        The intent (existing or newly created)
    """
    intent, _ = create_intent(
        db,
        job_id,
        chain_id,
        spec,
        idem_parts,
        broadcast_group=broadcast_group,
        broadcast_endpoints=broadcast_endpoints,
    )
    return intent


def claim_intent(
    db: Database,
    worker_id: str,
    claimed_by: str | None = None,
    lease_seconds: int = 300,
) -> ClaimedIntent | None:
    """Claim the next available intent for processing.

    Uses IMMEDIATE transaction locking (SQLite) to prevent
    multiple workers from claiming the same intent.

    Args:
        db: Database connection
        worker_id: Unique identifier for this worker

    Returns:
        Claimed intent or None if no intents available
    """
    # Generate unique claim token
    claim_token = f"{worker_id}_{uuid4().hex[:8]}"

    claimed = db.claim_next_intent(
        claim_token,
        claimed_by=claimed_by,
        lease_seconds=lease_seconds,
    )

    if claimed:
        logger.info(
            LogEvents.INTENT_CLAIM,
            intent_id=str(claimed.intent_id),
            worker_id=worker_id,
            claim_token=claim_token,
        )

    return claimed


def release_claim(db: Database, intent_id: UUID) -> bool:
    """Release an intent claim without processing.

    Use when a worker picks up an intent but cannot process it
    (e.g., during graceful shutdown).

    Args:
        db: Database connection
        intent_id: Intent to release

    Returns:
        True if released successfully
    """
    released = db.release_intent_claim(intent_id)

    if released:
        logger.info(
            LogEvents.INTENT_STATUS,
            intent_id=str(intent_id),
            status="created",
            action="claim_released",
        )

    return released


def update_status(
    db: Database,
    intent_id: UUID,
    status: IntentStatus,
    terminal_reason: str | None = None,
    halt_reason: str | None = None,
) -> bool:
    """Update intent status.

    Args:
        db: Database connection
        intent_id: Intent to update
        status: New status

    Returns:
        True if updated successfully
    """
    updated = db.update_intent_status(
        intent_id,
        status.value,
        terminal_reason=terminal_reason,
        halt_reason=halt_reason,
    )

    if updated:
        logger.info(
            LogEvents.INTENT_STATUS,
            intent_id=str(intent_id),
            status=status.value,
        )

    return updated


def transition_intent(
    db: Database,
    intent_id: UUID,
    to_status: IntentStatus,
    reason: str,
    chain_id: int | None = None,
    actor: str | None = None,
    source: str | None = None,
    terminal_reason: str | None = None,
    halt_reason: str | None = None,
) -> bool:
    """Transition an intent using the centralized transition map.

    Uses atomic transition that clears claim fields when leaving CLAIMED status.
    """
    allowed_from = [
        from_status
        for from_status, allowed in ALLOWED_TRANSITIONS.items()
        if to_status.value in allowed
    ]

    if not allowed_from:
        logger.error(
            "intent.transition.forbidden",
            intent_id=str(intent_id),
            to_status=to_status.value,
            reason=reason,
        )
        return False

    if to_status == IntentStatus.TERMINAL:
        if terminal_reason is not None and halt_reason is not None:
            raise ValueError("terminal_reason and halt_reason are mutually exclusive")
        if terminal_reason is None and halt_reason is None:
            raise ValueError("terminal_reason or halt_reason is required for terminal status")
    elif terminal_reason is not None or halt_reason is not None:
        raise ValueError("terminal_reason/halt_reason only valid for terminal status")

    # Single atomic operation - DB handles claim clearing internally
    success, old_status = db.transition_intent_status(
        intent_id=intent_id,
        from_statuses=allowed_from,
        to_status=to_status.value,
        terminal_reason=terminal_reason,
        halt_reason=halt_reason,
    )

    if success:
        # Emit metrics with ACTUAL previous status
        metrics = get_metrics()
        metrics.counter(INTENT_TRANSITIONS).inc(
            chain_id=chain_id if chain_id is not None else "unknown",
            from_status=old_status if old_status else "unknown",
            to_status=to_status.value,
            reason=reason,
        )
        db.record_mutation_audit(
            entity_type="intent",
            entity_id=str(intent_id),
            action=f"transition:{to_status.value}",
            actor=actor,
            reason=reason,
            source=source,
            metadata={"from_status": old_status, "to_status": to_status.value},
        )
        logger.info(
            "intent.transition",
            intent_id=str(intent_id),
            from_status=old_status,
            to_status=to_status.value,
            reason=reason,
        )
    else:
        logger.debug(
            "intent.transition.skipped",
            intent_id=str(intent_id),
            to_status=to_status.value,
            reason="status_mismatch",
        )

    return success


def abandon_intent(
    db: Database,
    intent_id: UUID,
    reason: str = "abandoned",
    chain_id: int | None = None,
) -> bool:
    """Mark an intent as abandoned.

    Delegates to transition_intent() for validated state transitions.

    Use when:
    - Deadline expired
    - Max replacement attempts exceeded
    - Manual intervention required

    Args:
        db: Database connection
        intent_id: Intent to abandon
        reason: Reason for abandonment
        chain_id: Chain ID for metrics

    Returns:
        True if abandoned successfully
    """
    return transition_intent(
        db,
        intent_id,
        IntentStatus.TERMINAL,
        reason,
        chain_id=chain_id,
        terminal_reason=IntentTerminalReason.ABANDONED.value,
    )


def get_broadcasted_for_signer(
    db: Database,
    chain_id: int,
    signer_address: str,
) -> list[TxIntent]:
    """Get all broadcasted intents for a signer.

    Use for startup reconciliation to find in-flight transactions.

    Args:
        db: Database connection
        chain_id: Chain ID
        signer_address: Signer address

    Returns:
        List of broadcasted intents
    """
    return db.get_broadcasted_intents_for_signer(chain_id, signer_address.lower())


def halt_intent(
    db: Database,
    intent_id: UUID,
    reason: str,
    chain_id: int | None = None,
) -> bool:
    """Halt an intent without guessing recovery paths."""
    return transition_intent(
        db,
        intent_id,
        IntentStatus.TERMINAL,
        reason,
        chain_id=chain_id,
        halt_reason=reason,
    )
