"""Startup reconciliation helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from brawny.model.enums import IntentStatus
from brawny.tx.monitor import ConfirmationResult

if TYPE_CHECKING:
    from brawny.db.base import Database
    from brawny.tx.monitor import TxMonitor
    import structlog


def reconcile_broadcasted_intents(
    db: Database,
    monitor: TxMonitor,
    chain_id: int,
    logger: "structlog.stdlib.BoundLogger",
) -> int:
    """Reconcile broadcasted intents at startup."""
    broadcasted_intents = db.get_intents_by_status(
        IntentStatus.BROADCASTED.value,
        chain_id=chain_id,
    )
    reconciled = 0
    for intent in broadcasted_intents:
        attempt = db.get_latest_attempt_for_intent(intent.intent_id)
        if not attempt or not attempt.tx_hash:
            continue
        status = monitor.check_confirmation(intent, attempt)
        if status.result == ConfirmationResult.CONFIRMED:
            monitor.handle_confirmed(intent, attempt, status)
            reconciled += 1
        elif status.result == ConfirmationResult.REVERTED:
            monitor.handle_reverted(intent, attempt, status)
            reconciled += 1
        elif status.result == ConfirmationResult.DROPPED:
            monitor.handle_dropped(intent, attempt)
            reconciled += 1

    if reconciled > 0:
        logger.info(
            "startup.reconcile_broadcasted",
            reconciled=reconciled,
        )
    return reconciled
