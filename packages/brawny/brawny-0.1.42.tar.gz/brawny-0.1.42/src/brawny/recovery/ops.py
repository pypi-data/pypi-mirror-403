"""Small, idempotent recovery operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from brawny.logging import get_logger
from brawny.metrics import (
    CLAIM_RECLAIM_SKIPPED,
    INTENT_RELEASED,
    INTENT_CLAIMED_STUCK,
    INTENT_TRANSITIONS,
    RECOVERY_MUTATIONS,
    get_metrics,
)
from brawny.model.enums import IntentStatus, IntentTerminalReason, NonceStatus
if TYPE_CHECKING:
    from brawny.db.base import Database

logger = get_logger(__name__)

_SAFE_NONCE_RELEASE_REASONS = {
    IntentTerminalReason.CONFIRMED.value,
    IntentTerminalReason.FAILED.value,
    IntentTerminalReason.ABANDONED.value,
}


@dataclass(frozen=True)
class RecoveryContext:
    """Shared context for recovery operations."""

    db: Database
    chain_id: int
    actor: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class RecoveryOutcome:
    """Structured outcome for recovery operations."""

    changed: bool
    reason: str
    before_status: str | None
    after_status: str | None


@dataclass(frozen=True)
class RecoveryOpOutcome:
    """Outcome for batch-style recovery operations."""

    changed: int


def transition_intent_if_current_status(
    intent_id: UUID,
    from_status: IntentStatus,
    to_status: IntentStatus,
    reason: str,
    ctx: RecoveryContext,
    terminal_reason: str | None = None,
    halt_reason: str | None = None,
) -> RecoveryOutcome:
    """Transition an intent only if it is currently in from_status."""
    action = "transition_intent_if_current_status"
    # Local import avoids import-time cycles with brawny.tx.__init__.
    from brawny.tx.intent import ALLOWED_TRANSITIONS

    allowed = ALLOWED_TRANSITIONS.get(from_status.value, set())
    if to_status.value not in allowed:
        logger.error(
            "recovery.action",
            action=action,
            intent_id=str(intent_id),
            before_status=from_status.value,
            after_status=to_status.value,
            reason=reason,
            skip_reason="transition_forbidden",
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(False, reason, from_status.value, to_status.value)

    success, old_status = ctx.db.transition_intent_status(
        intent_id=intent_id,
        from_statuses=[from_status.value],
        to_status=to_status.value,
        terminal_reason=terminal_reason,
        halt_reason=halt_reason,
    )

    if success:
        metrics = get_metrics()
        metrics.counter(INTENT_TRANSITIONS).inc(
            chain_id=ctx.chain_id,
            from_status=old_status if old_status else "unknown",
            to_status=to_status.value,
            reason=reason,
        )
        ctx.db.record_mutation_audit(
            entity_type="intent",
            entity_id=str(intent_id),
            action=f"transition:{to_status.value}",
            actor=ctx.actor,
            reason=reason,
            source=ctx.source,
            metadata={"from_status": old_status, "to_status": to_status.value},
        )
        logger.info(
            "recovery.action",
            action=action,
            intent_id=str(intent_id),
            before_status=old_status,
            after_status=to_status.value,
            reason=reason,
            changed=True,
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(True, reason, old_status, to_status.value)

    intent = ctx.db.get_intent(intent_id)
    current_status = intent.status.value if intent else None
    skip_reason = "status_mismatch" if intent else "intent_missing"
    logger.debug(
        "recovery.action",
        action=action,
        intent_id=str(intent_id),
        before_status=current_status,
        after_status=to_status.value,
        reason=reason,
        changed=False,
        skip_reason=skip_reason,
        chain_id=ctx.chain_id,
    )
    return RecoveryOutcome(False, reason, current_status, to_status.value)


def release_nonce_if_safe(
    signer_address: str,
    nonce: int,
    intent_id: UUID,
    reason: str,
    ctx: RecoveryContext,
) -> RecoveryOutcome:
    """Release a nonce reservation only when it is safe."""
    action = "release_nonce_if_safe"
    signer_address = signer_address.lower()

    reservation = ctx.db.get_nonce_reservation(ctx.chain_id, signer_address, nonce)
    if not reservation:
        logger.debug(
            "recovery.action",
            action=action,
            signer=signer_address,
            nonce=nonce,
            reason=reason,
            changed=False,
            skip_reason="reservation_missing",
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(False, reason, None, None)

    if reservation.status == NonceStatus.RELEASED:
        logger.debug(
            "recovery.action",
            action=action,
            intent_id=str(intent_id),
            signer=signer_address,
            nonce=nonce,
            before_status=reservation.status.value,
            after_status=reservation.status.value,
            reason=reason,
            changed=False,
            skip_reason="already_released",
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(False, reason, reservation.status.value, reservation.status.value)

    if reservation.intent_id != intent_id:
        logger.warning(
            "recovery.action",
            action=action,
            intent_id=str(intent_id),
            signer=signer_address,
            nonce=nonce,
            before_status=reservation.status.value,
            after_status=reservation.status.value,
            reason=reason,
            changed=False,
            skip_reason="intent_mismatch",
            reservation_intent_id=str(reservation.intent_id) if reservation.intent_id else None,
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(False, reason, reservation.status.value, reservation.status.value)

    intent = ctx.db.get_intent(intent_id)
    if not intent:
        logger.debug(
            "recovery.action",
            action=action,
            intent_id=str(intent_id),
            signer=signer_address,
            nonce=nonce,
            before_status=reservation.status.value,
            after_status=NonceStatus.RELEASED.value,
            reason=reason,
            changed=False,
            skip_reason="intent_missing",
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(False, reason, reservation.status.value, NonceStatus.RELEASED.value)

    attempt = ctx.db.get_latest_attempt_for_intent(intent_id)
    if attempt and (
        intent.status != IntentStatus.TERMINAL
        or intent.terminal_reason not in _SAFE_NONCE_RELEASE_REASONS
    ):
        logger.debug(
            "recovery.action",
            action=action,
            intent_id=str(intent_id),
            signer=signer_address,
            nonce=nonce,
            before_status=reservation.status.value,
            after_status=NonceStatus.RELEASED.value,
            reason=reason,
            changed=False,
            skip_reason="intent_not_terminal",
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(False, reason, reservation.status.value, NonceStatus.RELEASED.value)

    updated = ctx.db.release_nonce_reservation(
        ctx.chain_id,
        signer_address,
        nonce,
        reason=reason,
        source=ctx.source,
        actor=ctx.actor,
    )
    if updated:
        logger.info(
            "recovery.action",
            action=action,
            intent_id=str(intent_id),
            signer=signer_address,
            nonce=nonce,
            before_status=reservation.status.value,
            after_status=NonceStatus.RELEASED.value,
            reason=reason,
            changed=True,
            chain_id=ctx.chain_id,
        )
        return RecoveryOutcome(True, reason, reservation.status.value, NonceStatus.RELEASED.value)

    logger.debug(
        "recovery.action",
        action=action,
        intent_id=str(intent_id),
        signer=signer_address,
        nonce=nonce,
        before_status=reservation.status.value,
        after_status=NonceStatus.RELEASED.value,
        reason=reason,
        changed=False,
        skip_reason="release_failed",
        chain_id=ctx.chain_id,
    )
    return RecoveryOutcome(False, reason, reservation.status.value, NonceStatus.RELEASED.value)


def _record_recovery_mutation(ctx: RecoveryContext, action: str, count: int) -> None:
    if count <= 0:
        return
    metrics = get_metrics()
    metrics.counter(RECOVERY_MUTATIONS).inc(
        count,
        chain_id=ctx.chain_id,
        action=action,
    )


def clear_orphaned_claims(
    ctx: RecoveryContext,
    *,
    older_than_minutes: int = 2,
) -> RecoveryOpOutcome:
    """Clear orphaned claims using the DB helper."""
    count = ctx.db.clear_orphaned_claims(ctx.chain_id, older_than_minutes=older_than_minutes)
    if count > 0:
        logger.info(
            "recovery.orphaned_claims_cleared",
            count=count,
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
        metrics = get_metrics()
        metrics.counter(INTENT_RELEASED).inc(
            count,
            chain_id=ctx.chain_id,
            reason="orphaned_claim",
        )
        _record_recovery_mutation(ctx, "clear_orphaned_claims", count)
    else:
        logger.debug(
            "recovery.orphaned_claims_clear_noop",
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
    return RecoveryOpOutcome(changed=count)


def release_orphaned_nonces(
    ctx: RecoveryContext,
    *,
    older_than_minutes: int = 5,
) -> RecoveryOpOutcome:
    """Release orphaned nonces using the DB helper."""
    count = ctx.db.release_orphaned_nonces(ctx.chain_id, older_than_minutes=older_than_minutes)
    if count > 0:
        logger.info(
            "recovery.orphaned_nonces_released",
            count=count,
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
        _record_recovery_mutation(ctx, "release_orphaned_nonces", count)
    else:
        logger.debug(
            "recovery.orphaned_nonces_release_noop",
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
    return RecoveryOpOutcome(changed=count)


def requeue_expired_claims_no_attempts(
    ctx: RecoveryContext,
    *,
    grace_seconds: int = 15,
    limit: int = 50,
) -> RecoveryOpOutcome:
    """Requeue expired claims without attempts."""
    requeued = ctx.db.requeue_expired_claims_no_attempts(
        limit=limit,
        grace_seconds=grace_seconds,
        chain_id=ctx.chain_id,
    )
    skipped = ctx.db.count_expired_claims_with_attempts(
        limit=limit,
        grace_seconds=grace_seconds,
        chain_id=ctx.chain_id,
    )
    if requeued > 0:
        logger.info(
            "recovery.claims_requeued",
            count=requeued,
            chain_id=ctx.chain_id,
            source=ctx.source,
            reason="lease_expired",
        )
        metrics = get_metrics()
        metrics.counter(INTENT_RELEASED).inc(
            requeued,
            chain_id=ctx.chain_id,
            reason="lease_expired",
        )
        _record_recovery_mutation(ctx, "requeue_expired_claims_no_attempts", requeued)
    else:
        logger.debug(
            "recovery.claims_requeue_noop",
            chain_id=ctx.chain_id,
            source=ctx.source,
            reason="lease_expired",
        )
    if skipped > 0:
        metrics = get_metrics()
        metrics.counter(CLAIM_RECLAIM_SKIPPED).inc(
            skipped,
            chain_id=ctx.chain_id,
        )
        logger.debug(
            "recovery.claims_requeue_skipped_with_attempts",
            count=skipped,
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
    return RecoveryOpOutcome(changed=requeued)


def requeue_missing_lease_claims_no_attempts(
    ctx: RecoveryContext,
    *,
    cutoff_seconds: int = 15 * 60,
    limit: int = 50,
    enabled: bool = False,
) -> RecoveryOpOutcome:
    """Requeue missing-lease claims without attempts (optional)."""
    if not enabled:
        logger.debug(
            "recovery.missing_lease_requeue_disabled",
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
        return RecoveryOpOutcome(changed=0)

    requeued = ctx.db.requeue_missing_lease_claims_no_attempts(
        limit=limit,
        cutoff_seconds=cutoff_seconds,
        chain_id=ctx.chain_id,
    )
    skipped = ctx.db.count_missing_lease_claims_with_attempts(
        limit=limit,
        cutoff_seconds=cutoff_seconds,
        chain_id=ctx.chain_id,
    )
    if requeued > 0:
        logger.info(
            "recovery.missing_lease_requeued",
            count=requeued,
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
        metrics = get_metrics()
        metrics.counter(INTENT_RELEASED).inc(
            requeued,
            chain_id=ctx.chain_id,
            reason="missing_lease",
        )
        _record_recovery_mutation(ctx, "requeue_missing_lease_claims_no_attempts", requeued)
    else:
        logger.debug(
            "recovery.missing_lease_requeue_noop",
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
    if skipped > 0:
        metrics = get_metrics()
        metrics.counter(CLAIM_RECLAIM_SKIPPED).inc(
            skipped,
            chain_id=ctx.chain_id,
        )
        logger.debug(
            "recovery.missing_lease_requeue_skipped_with_attempts",
            count=skipped,
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
    return RecoveryOpOutcome(changed=requeued)


def transition_stuck_claimed_with_tx_hash(
    ctx: RecoveryContext,
    *,
    max_age_seconds: int,
) -> RecoveryOpOutcome:
    """Transition CLAIMED intents to BROADCASTED when a tx_hash exists."""
    intents = ctx.db.list_claimed_intents_older_than(
        max_age_seconds=max_age_seconds,
        chain_id=ctx.chain_id,
    )
    if not intents:
        logger.debug(
            "recovery.stuck_claimed_noop",
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
        return RecoveryOpOutcome(changed=0)

    transitioned = 0
    for intent in intents:
        attempt = ctx.db.get_latest_attempt_for_intent(intent.intent_id)
        if not attempt or not attempt.tx_hash:
            continue
        success, old_status = ctx.db.transition_intent_status(
            intent_id=intent.intent_id,
            from_statuses=[IntentStatus.CLAIMED.value],
            to_status=IntentStatus.BROADCASTED.value,
        )
        if success:
            transitioned += 1
            metrics = get_metrics()
            metrics.counter(INTENT_TRANSITIONS).inc(
                chain_id=ctx.chain_id,
                from_status=old_status if old_status else "unknown",
                to_status=IntentStatus.BROADCASTED.value,
                reason="recover_stuck_claimed",
            )
            logger.info(
                "recovery.claimed_recovered",
                intent_id=str(intent.intent_id),
                job_id=intent.job_id,
                attempt_id=str(attempt.attempt_id),
                chain_id=ctx.chain_id,
                source=ctx.source,
            )
        else:
            logger.debug(
                "recovery.claimed_recover_skipped",
                intent_id=str(intent.intent_id),
                chain_id=ctx.chain_id,
                source=ctx.source,
            )

    if transitioned > 0:
        _record_recovery_mutation(ctx, "transition_stuck_claimed_with_tx_hash", transitioned)
    return RecoveryOpOutcome(changed=transitioned)


def quarantine_stuck_claimed_without_tx_hash(
    ctx: RecoveryContext,
    *,
    max_age_seconds: int,
) -> RecoveryOpOutcome:
    """Quarantine signers for CLAIMED intents without tx_hash."""
    intents = ctx.db.list_claimed_intents_older_than(
        max_age_seconds=max_age_seconds,
        chain_id=ctx.chain_id,
    )
    if not intents:
        logger.debug(
            "recovery.stuck_claimed_noop",
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
        return RecoveryOpOutcome(changed=0)

    quarantined = 0
    for intent in intents:
        attempt = ctx.db.get_latest_attempt_for_intent(intent.intent_id)
        if attempt and attempt.tx_hash:
            continue
        updated = ctx.db.set_signer_quarantined(
            ctx.chain_id,
            intent.signer_address,
            reason="stuck_claimed",
            actor=ctx.actor,
            source=ctx.source,
        )
        if updated:
            quarantined += 1
            metrics = get_metrics()
            metrics.counter(INTENT_CLAIMED_STUCK).inc(
                chain_id=ctx.chain_id,
                age_bucket=">claim_timeout",
            )
            logger.info(
                "recovery.claimed_quarantined",
                intent_id=str(intent.intent_id),
                job_id=intent.job_id,
                attempt_id=str(attempt.attempt_id) if attempt else None,
                chain_id=ctx.chain_id,
                source=ctx.source,
            )
        else:
            logger.debug(
                "recovery.claimed_quarantine_skipped",
                intent_id=str(intent.intent_id),
                chain_id=ctx.chain_id,
                source=ctx.source,
            )

    if quarantined > 0:
        _record_recovery_mutation(ctx, "quarantine_stuck_claimed_without_tx_hash", quarantined)
    return RecoveryOpOutcome(changed=quarantined)
