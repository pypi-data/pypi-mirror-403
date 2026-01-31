"""Observability module for brawny.

Provides structured logging, liveness heartbeats, and readiness health checks.

See LOGGING_METRICS_PLAN.md for design rationale and usage patterns.

Quick Reference:
    # Logging via emit() gateway
    from brawny.obs import emit, get_logger, bind_intent

    log = get_logger(worker_id=1, chain_id=1)
    log = bind_intent(log, intent_id=str(intent.intent_id), job_id=intent.job_id)
    emit(log, level="info", event="tx", result="broadcast", tx_hash=hash)

    # Heartbeat for liveness
    from brawny.obs import get_heartbeat

    heartbeat = get_heartbeat("block_poller")
    heartbeat.beat()  # Call in loop

    # Health state for readiness
    from brawny.obs import get_health_state

    health = get_health_state()
    health.update_db(db.ping())
    if not health.is_ready():
        return 503
"""

from brawny.obs.emit import (
    ALLOWED,
    RUN_ID,
    bind_attempt,
    bind_intent,
    emit,
    get_logger,
)
from brawny.obs.health import (
    HealthState,
    get_health_state,
    reset_health_state,
)
from brawny.obs.heartbeat import (
    Heartbeat,
    all_heartbeat_ages,
    any_stale,
    get_heartbeat,
)

__all__ = [
    # emit.py
    "ALLOWED",
    "RUN_ID",
    "bind_attempt",
    "bind_intent",
    "emit",
    "get_logger",
    # health.py
    "HealthState",
    "get_health_state",
    "reset_health_state",
    # heartbeat.py
    "Heartbeat",
    "all_heartbeat_ages",
    "any_stale",
    "get_heartbeat",
]
