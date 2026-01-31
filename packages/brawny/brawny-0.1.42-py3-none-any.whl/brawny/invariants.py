"""System invariants exposed as metrics.

These queries should return 0 in a healthy system. Non-zero values
indicate potential issues that need investigation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from brawny.alerts.health import health_alert
from brawny.logging import get_logger
from brawny.metrics import (
    INVARIANT_NONCE_GAP_AGE,
    INVARIANT_ORPHANED_CLAIMS,
    INVARIANT_ORPHANED_NONCES,
    INVARIANT_BROADCASTED_NO_ATTEMPTS,
    INVARIANT_STUCK_CLAIMED,
    get_metrics,
)

if TYPE_CHECKING:
    from brawny.db.base import Database

logger = get_logger(__name__)

# Threshold for "stuck" claimed intents (minutes)
STUCK_CLAIM_THRESHOLD_MINUTES = 10


def _get_stuck_claim_details(
    db: "Database",
    chain_id: int,
    older_than_minutes: int = STUCK_CLAIM_THRESHOLD_MINUTES,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Fetch sample of stuck claimed intents for debugging context."""
    query = """
        SELECT intent_id, job_id,
               (julianday('now') - julianday(claimed_at)) * 86400 as age_seconds
        FROM tx_intents
        WHERE chain_id = :chain_id
          AND status = 'claimed'
          AND datetime(claimed_at) < datetime('now', :offset || ' minutes')
        ORDER BY claimed_at ASC
        LIMIT :limit
    """
    params = {"chain_id": chain_id, "offset": -older_than_minutes, "limit": limit}

    return db.execute_returning(query, params)


@dataclass
class InvariantMetrics:
    """Current values of all invariant checks."""

    stuck_claimed_intents: int
    nonce_gap_oldest_age_seconds: float
    broadcasted_without_attempts: int
    orphaned_claims: int
    orphaned_nonces: int


def collect_invariants(
    db: Database,
    chain_id: int,
    health_send_fn: Any = None,
    admin_chat_ids: list[str] | None = None,
    health_cooldown: int = 1800,
    log_violations: bool = True,
) -> InvariantMetrics:
    """Collect all invariant metrics for a chain.

    Call periodically (e.g., every 30 seconds) to update Prometheus gauges.
    Uses DB methods added in Phase 1 (count_broadcasted_without_attempts) and
    Phase 2 (count_stuck_claimed, etc.).
    """
    m = InvariantMetrics(
        stuck_claimed_intents=db.count_stuck_claimed(chain_id),
        nonce_gap_oldest_age_seconds=db.get_oldest_nonce_gap_age_seconds(chain_id),
        broadcasted_without_attempts=db.count_broadcasted_without_attempts(chain_id),
        orphaned_claims=db.count_orphaned_claims(chain_id),
        orphaned_nonces=db.count_orphaned_nonces(chain_id),
    )

    # Export to Prometheus using metric constants
    metrics = get_metrics()
    metrics.gauge(INVARIANT_STUCK_CLAIMED).set(
        m.stuck_claimed_intents, chain_id=chain_id
    )
    metrics.gauge(INVARIANT_NONCE_GAP_AGE).set(
        m.nonce_gap_oldest_age_seconds, chain_id=chain_id
    )
    metrics.gauge(INVARIANT_BROADCASTED_NO_ATTEMPTS).set(
        m.broadcasted_without_attempts, chain_id=chain_id
    )
    metrics.gauge(INVARIANT_ORPHANED_CLAIMS).set(
        m.orphaned_claims, chain_id=chain_id
    )
    metrics.gauge(INVARIANT_ORPHANED_NONCES).set(
        m.orphaned_nonces, chain_id=chain_id
    )

    # Log if any non-zero
    if log_violations and any([
        m.stuck_claimed_intents,
        m.broadcasted_without_attempts,
        m.orphaned_claims,
        m.orphaned_nonces,
    ]):
        extra: dict[str, Any] = {}
        if m.stuck_claimed_intents:
            details = _get_stuck_claim_details(db, chain_id)
            extra = {
                "stuck_intents_sample": [d["intent_id"] for d in details],
                "stuck_jobs_sample": list(set(d["job_id"] for d in details)),
                "oldest_claim_age_seconds": details[0]["age_seconds"] if details else 0,
            }

            # Send health alert for stuck claimed intents
            health_alert(
                component="brawny.invariants",
                chain_id=chain_id,
                error=f"stuck_claimed_intents={m.stuck_claimed_intents}, oldest_age={extra.get('oldest_claim_age_seconds', 0):.0f}s",
                fingerprint_key="invariant.stuck_claimed",
                job_id=extra.get("stuck_jobs_sample", [None])[0],
                intent_id=extra.get("stuck_intents_sample", [None])[0],
                action="Run: brawny intents clear-stuck",
                db_dialect=db.dialect,
                send_fn=health_send_fn,
                admin_chat_ids=admin_chat_ids,
                cooldown_seconds=health_cooldown,
            )

        logger.warning(
            "invariants.violations_detected",
            **asdict(m),
            chain_id=chain_id,
            **extra,
        )

    return m
