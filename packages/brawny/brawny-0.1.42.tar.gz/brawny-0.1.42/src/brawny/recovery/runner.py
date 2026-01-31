"""Recovery runner for recovery-only durable mutations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable, TYPE_CHECKING

from brawny.error_taxonomy import classify_error
from brawny.logging import get_logger
from brawny.metrics import ERRORS_TOTAL, get_metrics
from brawny.recovery import ops
from brawny.recovery.ops import RecoveryContext, RecoveryOpOutcome

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny.tx.nonce import NonceManager

logger = get_logger(__name__)


@dataclass(frozen=True)
class RecoveryStepResult:
    name: str
    changed: int
    noops: int
    errors: int


@dataclass(frozen=True)
class RecoveryRunSummary:
    mode: str
    steps: tuple[RecoveryStepResult, ...]
    total_changed: int
    total_noops: int
    total_errors: int

    def as_log_fields(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "total_changed": self.total_changed,
            "total_noops": self.total_noops,
            "total_errors": self.total_errors,
            "steps": [
                {
                    "name": step.name,
                    "changed": step.changed,
                    "noops": step.noops,
                    "errors": step.errors,
                }
                for step in self.steps
            ],
        }


RecoveryStep = Callable[
    [RecoveryContext, "Config", "NonceManager", datetime], RecoveryOpOutcome
]


def _step_clear_orphaned_claims(
    ctx: RecoveryContext,
    _config: "Config",
    _nonce_manager: "NonceManager",
    _now: datetime,
) -> RecoveryOpOutcome:
    return ops.clear_orphaned_claims(ctx)


def _step_release_orphaned_nonces(
    ctx: RecoveryContext,
    _config: "Config",
    _nonce_manager: "NonceManager",
    _now: datetime,
) -> RecoveryOpOutcome:
    return ops.release_orphaned_nonces(ctx)


def _step_transition_stuck_claimed(
    ctx: RecoveryContext,
    config: "Config",
    _nonce_manager: "NonceManager",
    _now: datetime,
) -> RecoveryOpOutcome:
    return ops.transition_stuck_claimed_with_tx_hash(
        ctx,
        max_age_seconds=config.claim_timeout_seconds,
    )


def _step_quarantine_stuck_claimed(
    ctx: RecoveryContext,
    config: "Config",
    _nonce_manager: "NonceManager",
    _now: datetime,
) -> RecoveryOpOutcome:
    return ops.quarantine_stuck_claimed_without_tx_hash(
        ctx,
        max_age_seconds=config.claim_timeout_seconds,
    )


def _step_requeue_expired_claims(
    ctx: RecoveryContext,
    _config: "Config",
    _nonce_manager: "NonceManager",
    _now: datetime,
) -> RecoveryOpOutcome:
    return ops.requeue_expired_claims_no_attempts(ctx)


def _step_requeue_missing_lease_claims(
    ctx: RecoveryContext,
    config: "Config",
    _nonce_manager: "NonceManager",
    _now: datetime,
) -> RecoveryOpOutcome:
    return ops.requeue_missing_lease_claims_no_attempts(
        ctx,
        enabled=config.debug.enable_null_lease_reclaim,
    )


def _step_nonce_reconcile(
    ctx: RecoveryContext,
    _config: "Config",
    nonce_manager: "NonceManager",
    _now: datetime,
) -> RecoveryOpOutcome:
    stats = nonce_manager.reconcile()
    changed = int(stats.get("nonces_released", 0)) + int(stats.get("orphans_marked", 0))
    changed += int(stats.get("stale_released", 0))
    changed += int(stats.get("orphans_cleaned", 0))
    if changed == 0:
        logger.debug(
            "recovery.nonce_reconcile_noop",
            chain_id=ctx.chain_id,
            source=ctx.source,
        )
    return RecoveryOpOutcome(changed=changed)


STARTUP_STEPS: list[RecoveryStep] = [
    _step_clear_orphaned_claims,
    _step_release_orphaned_nonces,
    _step_transition_stuck_claimed,
    _step_quarantine_stuck_claimed,
    _step_nonce_reconcile,
]

PERIODIC_STEPS: list[RecoveryStep] = [
    _step_transition_stuck_claimed,
    _step_quarantine_stuck_claimed,
    _step_requeue_expired_claims,
    _step_requeue_missing_lease_claims,
    _step_nonce_reconcile,
]


def run_startup_recovery(
    db: "Database",
    config: "Config",
    nonce_manager: "NonceManager",
    *,
    now: datetime | None = None,
    actor: str | None = None,
    source: str = "startup_recovery",
) -> RecoveryRunSummary:
    return _run_recovery(
        mode="startup",
        steps=STARTUP_STEPS,
        db=db,
        config=config,
        nonce_manager=nonce_manager,
        now=now,
        actor=actor,
        source=source,
    )


def run_periodic_recovery(
    db: "Database",
    config: "Config",
    nonce_manager: "NonceManager",
    *,
    now: datetime | None = None,
    actor: str | None = None,
    source: str = "periodic_recovery",
) -> RecoveryRunSummary:
    return _run_recovery(
        mode="periodic",
        steps=PERIODIC_STEPS,
        db=db,
        config=config,
        nonce_manager=nonce_manager,
        now=now,
        actor=actor,
        source=source,
    )


def _run_recovery(
    *,
    mode: str,
    steps: Iterable[RecoveryStep],
    db: "Database",
    config: "Config",
    nonce_manager: "NonceManager",
    now: datetime | None,
    actor: str | None,
    source: str,
) -> RecoveryRunSummary:
    if nonce_manager is None:
        raise RuntimeError("Recovery runner requires nonce_manager")

    timestamp = now or datetime.now(timezone.utc)
    ctx = RecoveryContext(
        db=db,
        chain_id=config.chain_id,
        actor=actor,
        source=source,
    )

    results: list[RecoveryStepResult] = []
    for step in steps:
        name = step.__name__.removeprefix("_step_")
        try:
            outcome = step(ctx, config, nonce_manager, timestamp)
        except Exception as exc:
            # RECOVERABLE continue other recovery steps after a failure.
            classification = classify_error(exc)
            logger.error(
                "recovery.step_failed",
                exc_info=True,
                step=name,
                error=str(exc)[:200],
                error_class=classification.error_class.value,
                reason_code=classification.reason_code,
                chain_id=ctx.chain_id,
                source=source,
            )
            metrics = get_metrics()
            metrics.counter(ERRORS_TOTAL).inc(
                error_class=classification.error_class.value,
                reason_code=classification.reason_code,
                subsystem="recovery",
            )
            results.append(
                RecoveryStepResult(
                    name=name,
                    changed=0,
                    noops=0,
                    errors=1,
                )
            )
            continue

        changed = outcome.changed
        results.append(
            RecoveryStepResult(
                name=name,
                changed=changed,
                noops=1 if changed == 0 else 0,
                errors=0,
            )
        )

    total_changed = sum(step.changed for step in results)
    total_noops = sum(step.noops for step in results)
    total_errors = sum(step.errors for step in results)
    summary = RecoveryRunSummary(
        mode=mode,
        steps=tuple(results),
        total_changed=total_changed,
        total_noops=total_noops,
        total_errors=total_errors,
    )
    if total_changed == 0 and total_errors == 0:
        logger.debug("recovery.run_complete", **summary.as_log_fields(), chain_id=ctx.chain_id)
    else:
        logger.info("recovery.run_complete", **summary.as_log_fields(), chain_id=ctx.chain_id)
    return summary
