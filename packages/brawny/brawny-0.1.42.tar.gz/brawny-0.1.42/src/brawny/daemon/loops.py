"""Worker and monitor loops for brawny daemon.

Provides the main loop functions for intent execution and transaction monitoring.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from threading import Event
from typing import TYPE_CHECKING

from brawny.metrics import (
    ACTIVE_WORKERS,
    BACKGROUND_TASK_ERRORS,
    ERRORS_TOTAL,
    INTENT_CLAIMED,
    INTENT_RELEASED,
    INTENTS_BACKING_OFF,
    get_metrics,
)
from brawny.recovery.runner import run_periodic_recovery
from brawny.invariants import collect_invariants
from brawny.error_taxonomy import classify_error

if TYPE_CHECKING:
    from threading import Thread
    from brawny.daemon.context import DaemonContext, DaemonState

from brawny.alerts.health import cleanup_stale_fingerprints, health_alert


def run_worker(
    worker_id: int,
    stop_event: Event,
    wakeup_hint: Event,
    ctx: "DaemonContext",
    state: "DaemonState",
    dry_run: bool = False,
) -> None:
    """Worker thread for executing intents.

    Args:
        worker_id: Worker identifier for logging
        stop_event: Event signaling shutdown
        wakeup_hint: Event for immediate wakeup on new intents
        ctx: Daemon context with shared components
        state: Daemon state with callbacks
        dry_run: If True, claim and release without executing
    """
    if ctx.executor is None and not dry_run:
        raise RuntimeError("run_worker requires executor unless dry_run")

    ctx.log.debug("worker.started", worker_id=worker_id)

    while not stop_event.is_set():
        if ctx.automation and not ctx.automation.enabled():
            time.sleep(1.0)
            continue
        if ctx.controls and ctx.controls.is_active("drain_workers"):
            ctx.log.warning("runtime.control.drain_workers", worker_id=worker_id)
            time.sleep(1.0)
            continue
        claim_token = state.make_claim_token(worker_id)
        claimed_by = state.make_claimed_by(worker_id)
        claimed = ctx.db.claim_next_intent(
            claim_token,
            claimed_by=claimed_by,
            lease_seconds=ctx.config.claim_timeout_seconds,
        )

        if claimed is None:
            wakeup_hint.wait(timeout=1.0)
            wakeup_hint.clear()
            continue

        if ctx.automation and not ctx.automation.enabled():
            released = ctx.db.release_claim_if_token_and_no_attempts(
                intent_id=claimed.intent_id,
                claim_token=claimed.claim_token,
            )
            if released:
                metrics = get_metrics()
                metrics.counter(INTENT_RELEASED).inc(
                    chain_id=ctx.chain_id,
                    reason="automation_disabled",
                )
            time.sleep(0.1)
            continue

        intent = ctx.db.get_intent(claimed.intent_id)
        if intent is None:
            ctx.log.error(
                "worker.claimed_intent_missing",
                intent_id=str(claimed.intent_id),
                claim_token=claimed.claim_token,
                claimed_by=claimed.claimed_by,
                worker_id=worker_id,
            )
            continue

        ctx.log.info(
            "intent.claimed",
            intent_id=str(intent.intent_id),
            job_id=intent.job_id,
            claim_token=claim_token,
            claimed_by=claimed_by,
            worker_id=worker_id,
        )
        metrics = get_metrics()
        metrics.counter(INTENT_CLAIMED).inc(
            chain_id=ctx.chain_id,
        )

        if dry_run:
            ctx.log.info("worker.dry_run", intent_id=str(intent.intent_id))
            released = ctx.db.release_claim_if_token_and_no_attempts(
                intent_id=claimed.intent_id,
                claim_token=claimed.claim_token,
            )
            if not released:
                ctx.log.warning(
                    "worker.dry_run_release_failed",
                    intent_id=str(intent.intent_id),
                )
            else:
                metrics = get_metrics()
                metrics.counter(INTENT_RELEASED).inc(
                    chain_id=ctx.chain_id,
                    reason="dry_run",
                )
            continue

        state.inflight_inc()
        try:
            outcome = ctx.executor.process_claimed_intent(claimed, intent=intent)
            ctx.log.info(
                "worker.executed",
                intent_id=str(intent.intent_id),
                job_id=intent.job_id,
                result=outcome.result.value,
            )
        except Exception as e:
            # BUG re-raise unexpected executor failures.
            classification = classify_error(e)
            ctx.log.error(
                "worker.execute_exception",
                exc_info=True,
                intent_id=str(intent.intent_id),
                job_id=intent.job_id,
                error=str(e)[:200],
                error_class=classification.error_class.value,
                reason_code=classification.reason_code,
            )
            metrics = get_metrics()
            metrics.counter(ERRORS_TOTAL).inc(
                error_class=classification.error_class.value,
                reason_code=classification.reason_code,
                subsystem="worker",
            )
            setattr(e, "_logged_unexpected", True)
            health_alert(
                component="brawny.tx.executor",
                chain_id=ctx.chain_id,
                error=e,
                job_id=intent.job_id,
                intent_id=str(intent.intent_id),
                claim_token=claimed.claim_token,
                status=intent.status.value if hasattr(intent.status, "value") else str(intent.status),
                action="Check logs; intent will retry or timeout",
                db_dialect=ctx.db.dialect,
                send_fn=ctx.health_send_fn,
                admin_chat_ids=ctx.admin_chat_ids,
                cooldown_seconds=ctx.health_cooldown,
            )
            raise
        finally:
            state.inflight_dec()

    ctx.log.debug("worker.stopped", worker_id=worker_id)


def run_monitor(
    stop_event: Event,
    ctx: "DaemonContext",
    worker_threads: list["Thread"],
) -> None:
    """Background loop for monitoring broadcasted transactions.

    Args:
        stop_event: Event signaling shutdown
        ctx: Daemon context with shared components
        worker_threads: List of worker threads for gauge reporting
    """
    if ctx.monitor is None:
        raise RuntimeError("run_monitor requires monitor")
    if ctx.replacer is None:
        raise RuntimeError("run_monitor requires replacer")
    if ctx.nonce_manager is None:
        raise RuntimeError("run_monitor requires nonce_manager")

    ctx.log.debug("monitor.started")
    last_rpc_health = 0.0
    last_worker_gauge = 0.0
    last_log_cleanup = 0.0
    last_claim_reap = 0.0
    last_recovery = 0.0

    while not stop_event.is_set():
        try:
            ctx.monitor.monitor_all_broadcasted()
            automation_enabled = ctx.automation.enabled() if ctx.automation else True
            if automation_enabled:
                ctx.replacer.process_stuck_transactions()

            now = time.time()
            if now - last_rpc_health >= 30:
                ctx.rpc.get_health()
                last_rpc_health = now

            if now - last_worker_gauge >= 10:
                metrics = get_metrics()
                active = sum(1 for t in worker_threads if t.is_alive())
                metrics.gauge(ACTIVE_WORKERS).set(
                    active,
                    chain_id=ctx.chain_id,
                )
                backing_off = ctx.db.get_backing_off_intent_count(chain_id=ctx.chain_id)
                metrics.gauge(INTENTS_BACKING_OFF).set(
                    backing_off,
                    chain_id=ctx.chain_id,
                )
                last_worker_gauge = now

            if now - last_recovery >= 30:
                if automation_enabled:
                    summary = run_periodic_recovery(
                        ctx.db,
                        ctx.config,
                        ctx.nonce_manager,
                        now=datetime.now(timezone.utc),
                        actor="daemon",
                        source="periodic_recovery",
                    )
                    if summary.total_errors > 0 and ctx.automation:
                        ctx.automation.disable(
                            "recovery_error",
                            source="monitor",
                            detail=f"errors={summary.total_errors}",
                        )
                    try:
                        collect_invariants(
                            ctx.db,
                            ctx.chain_id,
                            health_send_fn=ctx.health_send_fn,
                            admin_chat_ids=ctx.admin_chat_ids,
                            health_cooldown=ctx.health_cooldown,
                            log_violations=True,
                        )
                    except Exception as e:
                        # RECOVERABLE invariant collection is best-effort.
                        ctx.log.error(
                            "invariants.collection_failed",
                            error=str(e),
                            exc_info=True,
                        )
                last_recovery = now

            if now - last_claim_reap >= 30:
                if automation_enabled:
                    _reap_stale_claims(ctx)
                last_claim_reap = now

            # Job log cleanup (hourly)
            if now - last_log_cleanup >= 3600:
                try:
                    from brawny.db.ops import logs as log_ops
                    cutoff = datetime.utcnow() - timedelta(days=ctx.config.log_retention_days)
                    deleted = log_ops.delete_old_logs(ctx.db, ctx.chain_id, cutoff)
                    if deleted > 0:
                        ctx.log.info("job_logs.cleanup", deleted=deleted)
                except Exception as cleanup_err:
                    # RECOVERABLE log cleanup is best-effort.
                    ctx.log.error(
                        "job_logs.cleanup_failed",
                        error=str(cleanup_err),
                        exc_info=True,
                    )

                # Health alert fingerprint cleanup (also hourly)
                try:
                    removed = cleanup_stale_fingerprints(ctx.health_cooldown)
                    if removed > 0:
                        ctx.log.debug("health_fingerprints.cleanup", removed=removed)
                except Exception as cleanup_err:
                    # RECOVERABLE fingerprint cleanup is best-effort.
                    ctx.log.error(
                        "health_fingerprints.cleanup_failed",
                        error=str(cleanup_err),
                        exc_info=True,
                    )

                last_log_cleanup = now
        except Exception as e:
            # RECOVERABLE monitor loop failures are logged and retried.
            classification = classify_error(e)
            ctx.log.error(
                "monitor.error",
                error=str(e)[:200],
                error_class=classification.error_class.value,
                reason_code=classification.reason_code,
                exc_info=True,
            )
            metrics = get_metrics()
            metrics.counter(BACKGROUND_TASK_ERRORS).inc(task="monitor")
            metrics.counter(ERRORS_TOTAL).inc(
                error_class=classification.error_class.value,
                reason_code=classification.reason_code,
                subsystem="monitor",
            )
            if ctx.automation and classification.reason_code in {"db_locked", "db_circuit_breaker_open", "rpc_unhealthy"}:
                ctx.automation.disable(
                    classification.reason_code,
                    source="monitor",
                    detail=str(e)[:200],
                )
            health_alert(
                component="brawny.tx.monitor",
                chain_id=ctx.chain_id,
                error=e,
                action="Check DB/RPC connectivity",
                db_dialect=ctx.db.dialect,
                send_fn=ctx.health_send_fn,
                admin_chat_ids=ctx.admin_chat_ids,
                cooldown_seconds=ctx.health_cooldown,
            )

        stop_event.wait(timeout=ctx.config.poll_interval_seconds * 2)

    ctx.log.debug("monitor.stopped")


def _reap_stale_claims(ctx: "DaemonContext") -> None:
    """Detect stale claimed intents with attempts.

    Containment only: pause new intents to avoid compounding drift.
    """
    if ctx.nonce_manager is None:
        raise RuntimeError("_reap_stale_claims requires nonce_manager")

    stale = ctx.db.list_claimed_intents_older_than(
        max_age_seconds=ctx.config.claim_timeout_seconds,
        chain_id=ctx.chain_id,
    )
    if not stale:
        return

    ctx.log.warning(
        "claim.reap_detected",
        count=len(stale),
        action="containment_only",
    )
    ctx.db.set_runtime_control(
        control="pause_new_intents",
        active=True,
        expires_at=datetime.utcnow() + timedelta(seconds=300),
        reason="stale_claims_detected",
        actor="reaper",
        mode="auto",
    )
