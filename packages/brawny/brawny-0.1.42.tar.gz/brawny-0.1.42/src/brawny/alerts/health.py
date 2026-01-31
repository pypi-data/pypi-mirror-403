"""Daemon health alerts with fingerprint-based deduplication."""

from __future__ import annotations

import hashlib
import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Literal

from cachetools import TTLCache

from brawny.logging import get_logger

logger = get_logger(__name__)

DEFAULT_COOLDOWN_SECONDS = 1800
MAX_FIELD_LEN = 200

# Multi-threaded access - protected by _lock
# Medium cardinality keys (fingerprint hashes): maxsize=10K, ttl=1h
_last_fired: TTLCache[str, datetime] = TTLCache(maxsize=10_000, ttl=3600)
_first_seen: TTLCache[str, datetime] = TTLCache(maxsize=10_000, ttl=3600)
_suppressed_count: TTLCache[str, int] = TTLCache(maxsize=10_000, ttl=3600)
_lock = threading.Lock()


def _fingerprint(
    component: str,
    exc_type: str,
    chain_id: int,
    db_dialect: str | None = None,
    fingerprint_key: str | None = None,
) -> str:
    """Compute stable fingerprint for deduplication.

    Default: component + exc_type + chain_id + db_dialect (message excluded for stability).
    Override with fingerprint_key for explicit grouping (e.g., invariant names).
    """
    if fingerprint_key:
        key = f"{fingerprint_key}:{chain_id}:{db_dialect or 'unknown'}"
    else:
        key = f"{component}:{exc_type}:{chain_id}:{db_dialect or 'unknown'}"
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def health_alert(
    *,
    component: str,
    chain_id: int,
    error: Exception | str,
    level: Literal["warning", "error", "critical"] = "error",
    job_id: str | None = None,
    intent_id: str | None = None,
    claim_token: str | None = None,
    status: str | None = None,
    action: str | None = None,
    db_dialect: str | None = None,
    fingerprint_key: str | None = None,
    force_send: bool = False,
    send_fn: Callable[..., None] | None = None,
    admin_chat_ids: list[str] | None = None,
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
) -> None:
    """Send a daemon health alert with deduplication.

    First occurrence: sends immediately (if level >= error).
    Within cooldown: suppressed, count incremented.
    After cooldown: sends summary with suppressed count + duration.
    Warnings are logged only, never sent to Telegram.

    Args:
        component: Component identifier (e.g., "brawny.tx.executor")
        chain_id: Chain ID for context
        error: Exception or error message
        level: Severity level (warning, error, critical)
        job_id: Optional job identifier
        intent_id: Optional intent identifier
        claim_token: Optional claim token for debugging stuckness
        status: Optional intent status for debugging
        action: Suggested remediation action
        db_dialect: Database dialect for fingerprinting
        fingerprint_key: Override default fingerprint for explicit grouping
        force_send: Bypass deduplication entirely (e.g., startup alerts)
        send_fn: Function to send alerts (e.g., alerts.send.send_health)
        admin_chat_ids: Telegram chat IDs for admin alerts
        cooldown_seconds: Deduplication window in seconds
    """
    exc_type = type(error).__name__ if isinstance(error, Exception) else "Error"
    message = str(error)[:MAX_FIELD_LEN]
    fp = _fingerprint(component, exc_type, chain_id, db_dialect, fingerprint_key)

    now = datetime.utcnow()
    should_send = False
    suppressed = 0
    first_seen = now

    if force_send:
        should_send = True
    else:
        with _lock:
            last = _last_fired.get(fp)
            if last is None:
                # First occurrence
                should_send = True
                _last_fired[fp] = now
                _first_seen[fp] = now
                _suppressed_count[fp] = 0
            elif now - last > timedelta(seconds=cooldown_seconds):
                # Cooldown expired, send summary
                should_send = True
                suppressed = _suppressed_count.get(fp, 0)
                first_seen = _first_seen.get(fp, now)
                _last_fired[fp] = now
                _first_seen[fp] = now  # Reset for next incident window
                _suppressed_count[fp] = 0
            else:
                # Within cooldown, suppress
                _suppressed_count[fp] = _suppressed_count.get(fp, 0) + 1

    # Always log (use appropriate log level)
    if level == "critical":
        log_fn = logger.critical
    elif level == "warning":
        log_fn = logger.warning
    else:
        log_fn = logger.error

    log_fn(
        "daemon.health_alert",
        component=component,
        chain_id=chain_id,
        error=message,
        exc_type=exc_type,
        level=level,
        job_id=job_id,
        intent_id=intent_id,
        claim_token=claim_token,
        status=status,
        fingerprint=fp,
        suppressed=not should_send,
    )

    # Warnings are logged only, never sent to Telegram
    if level == "warning":
        return

    if not should_send:
        return

    if send_fn is None or not admin_chat_ids:
        return

    # Build message (cap all fields)
    lines = ["⚠️ Brawny Health Alert" if level == "error" else "🔴 CRITICAL Health Alert"]
    lines.append(f"chain_id={chain_id}")
    if job_id:
        lines.append(f"job={job_id[:MAX_FIELD_LEN]}")
    if intent_id:
        lines.append(f"intent={intent_id[:12]}...")
    if claim_token:
        lines.append(f"claim_token={claim_token[:12]}...")
    if status:
        lines.append(f"status={status}")
    lines.append(f"{exc_type}: {message}")
    if suppressed > 0:
        duration_seconds = (now - first_seen).total_seconds()
        duration_str = f"{duration_seconds / 60:.0f}m" if duration_seconds >= 60 else f"{duration_seconds:.0f}s"
        lines.append(f"(suppressed {suppressed}x over {duration_str})")
    if action:
        lines.append(f"Action: {action[:MAX_FIELD_LEN]}")

    for chat_id in admin_chat_ids:
        try:
            send_fn(chat_id=chat_id, text="\n".join(lines))
        except Exception as e:
            # RECOVERABLE health alert delivery failures should not crash caller.
            logger.error("health_alert.send_failed", error=str(e), exc_info=True)


def cleanup_stale_fingerprints(cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS) -> int:
    """Remove fingerprints older than 2x cooldown. Returns count removed.

    Note: With TTLCache, stale entries are automatically evicted. This function
    now triggers cache expiration and returns 0 (actual eviction count is not
    tracked by TTLCache). Kept for API compatibility.
    """
    with _lock:
        # TTLCache automatically evicts expired entries on access
        # Trigger expiration by calling expire() if available, or just access
        _last_fired.expire()
        _first_seen.expire()
        _suppressed_count.expire()
    return 0  # TTLCache doesn't track eviction count
