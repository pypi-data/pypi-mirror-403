"""Simplified alert system.

Send alerts to Telegram or webhooks. No classes. No inheritance. No plugin architecture.

Usage:
    payload = AlertPayload(
        job_id="my-job",
        job_name="My Job",
        event_type=AlertEvent.CONFIRMED,
        message="Transaction confirmed!",
    )
    config = AlertConfig(
        telegram_token="...",
        telegram_chat_ids=["123456"],
    )
    await send_alert(payload, config)
"""

from __future__ import annotations

import asyncio
import hashlib
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from cachetools import TTLCache

if TYPE_CHECKING:
    from brawny.telegram import TelegramBot

import httpx

from brawny.logging import get_logger, log_unexpected
from brawny.metrics import (
    ALERTS_ENQUEUED,
    ALERTS_DROPPED,
    ALERTS_LAST_ERROR_TIMESTAMP,
    ALERTS_LAST_SUCCESS_TIMESTAMP,
    ALERTS_OLDEST_QUEUED_AGE_SECONDS,
    ALERTS_QUEUE_DEPTH,
    ALERTS_RETRIED,
    ALERTS_SENT,
    ALERTS_WORKER_ALIVE,
    get_metrics,
)
from brawny.alerts.routing import resolve_targets
from brawny.network_guard import allow_network_calls

logger = get_logger(__name__)

TELEGRAM_MESSAGE_MAX_LEN = 4096
TELEGRAM_TRUNCATION_SUFFIX = "...(truncated)"


class AlertEvent(str, Enum):
    """Alert event types. Aligned with OE2 hook reduction."""

    TRIGGERED = "triggered"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass
class AlertPayload:
    """Data object for alert content."""

    job_id: str
    job_name: str
    event_type: AlertEvent
    message: str
    parse_mode: str = "Markdown"
    chain_id: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertConfig:
    """Transport configuration. Passed once, not spread across callsites."""

    telegram_token: str | None = None
    telegram_chat_ids: list[str] = field(default_factory=list)
    webhook_url: str | None = None
    rate_limit_seconds: float = 3.0


# Module-level state for rate limiting only
# NOTE: No module-level httpx.AsyncClient - asyncio objects are not safe to share
# across multiple event loops / loop lifetimes. For low-volume alerts, we create
# a fresh client per request (httpx context manager handles cleanup).
# Multi-threaded access - protected by _last_sent_lock
# Medium cardinality keys (job_id:event:dest:dest_id): maxsize=10K, ttl=1h
_last_sent: TTLCache[str, datetime] = TTLCache(maxsize=10_000, ttl=3600)
# Use threading.Lock, not asyncio.Lock - avoids event loop binding issues
_last_sent_lock = threading.Lock()

ALERT_QUEUE_MAXSIZE = 1000
ALERT_SEND_MAX_ATTEMPTS = 5
ALERT_SEND_BACKOFF_BASE_SECONDS = 1.0
ALERT_SEND_BACKOFF_MAX_SECONDS = 30.0
ALERT_WORKER_POLL_SECONDS = 0.1
ALERT_FLUSH_TIMEOUT_SECONDS = 3.0
ALERT_LOG_THROTTLE_SECONDS = 60.0
ALERT_HEALTH_MAX_OLDEST_AGE_SECONDS = 120.0


@dataclass
class _AlertTask:
    payload: AlertPayload
    destination_type: str
    destination_id: str
    channel: str
    enqueued_at: float
    attempt: int = 0
    next_attempt_at: float = 0.0
    alert_id: str = ""
    telegram_token: str | None = None
    webhook_url: str | None = None


class AlertService:
    def __init__(
        self,
        *,
        maxsize: int,
        max_attempts: int,
        backoff_base_seconds: float,
        backoff_max_seconds: float,
        health_max_oldest_age_seconds: float,
    ) -> None:
        self._queue: deque[_AlertTask] = deque()
        self._delayed: list[_AlertTask] = []
        self._maxsize = maxsize
        self._max_attempts = max_attempts
        self._backoff_base_seconds = backoff_base_seconds
        self._backoff_max_seconds = backoff_max_seconds
        self._health_max_oldest_age_seconds = health_max_oldest_age_seconds
        self._accepting = True
        self._stop = False
        self._stop_deadline: float | None = None
        self._worker_task: asyncio.Task | None = None
        self._wakeup: asyncio.Event | None = None
        self._worker_alive = False
        self._last_success_ts: float | None = None
        self._last_error_ts: float | None = None
        self._last_error_type: str | None = None
        self._last_error_message: str | None = None
        self._log_throttle: dict[str, float] = {}

    async def start(self) -> None:
        if self._worker_task and not self._worker_task.done():
            return
        self._accepting = True
        self._stop = False
        self._stop_deadline = None
        self._wakeup = asyncio.Event()
        self._worker_task = asyncio.create_task(self._run(), name="alert-sender")

    async def stop(self, flush_timeout: float) -> None:
        self._accepting = False
        self._stop = True
        self._stop_deadline = time.time() + flush_timeout
        if self._wakeup is not None:
            self._wakeup.set()
        task = self._worker_task
        if task is None:
            return
        try:
            await asyncio.wait_for(task, timeout=flush_timeout)
        except asyncio.TimeoutError:
            task.cancel()
        self._update_queue_metrics(now=time.time())

    def enqueue(self, task: _AlertTask) -> bool:
        if not self._accepting:
            self._record_drop("shutdown", channel=task.channel)
            return False
        if self._queue_size() >= self._maxsize:
            self._record_drop("queue_full", channel=task.channel)
            self._log_throttled(
                "queue_full",
                "alert.queue_full",
                maxsize=self._maxsize,
                channel=task.channel,
            )
            return False
        self._queue.append(task)
        metrics = get_metrics()
        metrics.counter(ALERTS_ENQUEUED).inc()
        self._update_queue_metrics(now=time.time())
        if self._wakeup is not None:
            self._wakeup.set()
        return True

    def configure_health_threshold(self, max_oldest_age_seconds: float) -> None:
        self._health_max_oldest_age_seconds = max_oldest_age_seconds

    async def _run(self) -> None:
        self._set_worker_alive(True)
        try:
            while True:
                now = time.time()
                if self._stop and self._stop_deadline and now >= self._stop_deadline:
                    self._drop_remaining("shutdown_timeout")
                    break
                self._move_due_delayed(now)
                if self._stop and not self._queue and not self._delayed:
                    break
                if self._queue:
                    task = self._queue.popleft()
                    self._update_queue_metrics(now=now)
                    await self._process_task(task)
                    continue
                wait = self._next_wait_seconds(now)
                try:
                    if self._wakeup is not None:
                        self._wakeup.clear()
                        await asyncio.wait_for(self._wakeup.wait(), timeout=wait)
                    else:
                        await asyncio.sleep(wait)
                except asyncio.TimeoutError:
                    pass
        finally:
            self._set_worker_alive(False)

    async def _process_task(self, task: _AlertTask) -> None:
        metrics = get_metrics()
        task.attempt += 1
        attempt = task.attempt
        self._log_state(task, state="sending")
        try:
            await _send_task(task)
        except Exception as exc:
            # RECOVERABLE alert send failures are retried or dropped.
            log_unexpected(
                logger,
                "alerts.send_failed",
                job_id=task.payload.job_id,
                channel=task.channel,
                attempt=attempt,
                error=str(exc)[:200],
            )
            retryable, error_type = _classify_error(exc)
            self._record_error(error_type, str(exc))
            if retryable and attempt < self._max_attempts:
                metrics.counter(ALERTS_RETRIED).inc()
                task.next_attempt_at = time.time() + _backoff_seconds(
                    attempt,
                    base_seconds=self._backoff_base_seconds,
                    max_seconds=self._backoff_max_seconds,
                )
                self._log_state(task, state="retry_scheduled", error_type=error_type)
                self._delayed.append(task)
                self._update_queue_metrics(now=time.time())
                if self._wakeup is not None:
                    self._wakeup.set()
                return
            reason = "max_attempts" if attempt >= self._max_attempts else "non_retryable"
            self._log_state(task, state="dropped", error_type=error_type)
            self._record_drop(reason, channel=task.channel)
            return

        metrics.counter(ALERTS_SENT).inc()
        self._record_success()
        self._log_state(task, state="sent")

    def _record_drop(self, reason: str, *, channel: str) -> None:
        metrics = get_metrics()
        metrics.counter(ALERTS_DROPPED).inc(reason=reason, channel=channel)

    def _record_success(self) -> None:
        self._last_success_ts = time.time()
        metrics = get_metrics()
        metrics.gauge(ALERTS_LAST_SUCCESS_TIMESTAMP).set(self._last_success_ts)

    def _record_error(self, error_type: str, message: str) -> None:
        self._last_error_ts = time.time()
        self._last_error_type = error_type
        self._last_error_message = message[:200]
        metrics = get_metrics()
        metrics.gauge(ALERTS_LAST_ERROR_TIMESTAMP).set(self._last_error_ts)

    def _queue_size(self) -> int:
        return len(self._queue) + len(self._delayed)

    def _oldest_age_seconds(self, now: float) -> float:
        if not self._queue and not self._delayed:
            return 0.0
        oldest = min(
            [task.enqueued_at for task in self._queue]
            + [task.enqueued_at for task in self._delayed]
        )
        return max(0.0, now - oldest)

    def _update_queue_metrics(self, now: float) -> None:
        metrics = get_metrics()
        metrics.gauge(ALERTS_QUEUE_DEPTH).set(self._queue_size())
        metrics.gauge(ALERTS_OLDEST_QUEUED_AGE_SECONDS).set(self._oldest_age_seconds(now))

    def _move_due_delayed(self, now: float) -> None:
        if not self._delayed:
            return
        due: list[_AlertTask] = []
        remaining: list[_AlertTask] = []
        for task in self._delayed:
            if task.next_attempt_at <= now:
                due.append(task)
            else:
                remaining.append(task)
        self._delayed = remaining
        if due:
            self._queue.extend(due)
            self._update_queue_metrics(now=now)

    def _next_wait_seconds(self, now: float) -> float:
        if not self._delayed:
            return ALERT_WORKER_POLL_SECONDS
        next_due = min(task.next_attempt_at for task in self._delayed)
        wait = max(0.0, next_due - now)
        return min(ALERT_WORKER_POLL_SECONDS, wait)

    def _set_worker_alive(self, alive: bool) -> None:
        self._worker_alive = alive
        metrics = get_metrics()
        metrics.gauge(ALERTS_WORKER_ALIVE).set(1.0 if alive else 0.0)

    def _drop_remaining(self, reason: str) -> None:
        while self._queue:
            task = self._queue.popleft()
            self._record_drop(reason, channel=task.channel)
        while self._delayed:
            task = self._delayed.pop()
            self._record_drop(reason, channel=task.channel)
        self._update_queue_metrics(now=time.time())

    def _log_state(self, task: _AlertTask, *, state: str, error_type: str | None = None) -> None:
        logger.info(
            "alert.delivery_state",
            alert_id=task.alert_id,
            attempt=task.attempt,
            state=state,
            error_type=error_type,
            channel=task.channel,
        )

    def _log_throttled(self, reason: str, event: str, **fields: object) -> None:
        now = time.time()
        last = self._log_throttle.get(reason)
        if last is not None and now - last < ALERT_LOG_THROTTLE_SECONDS:
            return
        self._log_throttle[reason] = now
        logger.warning(event, reason=reason, **fields)

    def health_snapshot(self) -> dict[str, object]:
        now = time.time()
        queue_depth = self._queue_size()
        oldest_age = self._oldest_age_seconds(now)
        alive = self._worker_alive
        healthy = queue_depth == 0 or (alive and oldest_age < self._health_max_oldest_age_seconds)
        return {
            "alive": alive,
            "queue_depth": queue_depth,
            "oldest_queued_age_seconds": oldest_age,
            "healthy": healthy,
            "last_success_timestamp": self._last_success_ts,
            "last_error_timestamp": self._last_error_ts,
            "last_error_type": self._last_error_type,
            "last_error_message": self._last_error_message,
        }


def _make_task(
    payload: AlertPayload,
    *,
    destination_type: str,
    destination_id: str,
    telegram_token: str | None = None,
    webhook_url: str | None = None,
) -> _AlertTask:
    enqueued_at = time.time()
    alert_id = _make_alert_id(payload, destination_type, destination_id)
    return _AlertTask(
        payload=payload,
        destination_type=destination_type,
        destination_id=destination_id,
        channel=destination_type,
        enqueued_at=enqueued_at,
        next_attempt_at=enqueued_at,
        alert_id=alert_id,
        telegram_token=telegram_token,
        webhook_url=webhook_url,
    )


def _make_alert_id(payload: AlertPayload, destination_type: str, destination_id: str) -> str:
    raw = f"{destination_type}:{destination_id}:{payload.job_id}:{payload.event_type.value}:{payload.message}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _backoff_seconds(attempt: int, *, base_seconds: float, max_seconds: float) -> float:
    return min(base_seconds * (2 ** (attempt - 1)), max_seconds)


def _classify_error(exc: Exception) -> tuple[bool, str]:
    if isinstance(exc, httpx.TimeoutException):
        return True, "timeout"
    if isinstance(exc, httpx.RequestError):
        return True, "network_error"
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        error_type = f"http_{status}"
        if status == 429 or 500 <= status < 600:
            return True, error_type
        if status in (400, 401, 403, 404):
            return False, error_type
        return False, error_type
    return False, type(exc).__name__

_alert_service: AlertService | None = None


def set_alert_service(service: AlertService | None) -> None:
    global _alert_service
    _alert_service = service


def _require_alert_service() -> AlertService:
    if _alert_service is None:
        raise RuntimeError("AlertService is not initialized")
    return _alert_service


async def send_alert(payload: AlertPayload, config: AlertConfig) -> None:
    """Enqueue alert for background delivery. Never blocks core path."""
    service = _require_alert_service()
    if config.telegram_token and config.telegram_chat_ids:
        for chat_id in config.telegram_chat_ids:
            if _should_send(payload, "telegram", chat_id, config.rate_limit_seconds):
                service.enqueue(
                    _make_task(
                        payload,
                        destination_type="telegram",
                        destination_id=str(chat_id),
                        telegram_token=config.telegram_token,
                    )
                )

    if config.webhook_url:
        if _should_send(payload, "webhook", config.webhook_url, config.rate_limit_seconds):
            service.enqueue(
                _make_task(
                    payload,
                    destination_type="webhook",
                    destination_id=config.webhook_url,
                    webhook_url=config.webhook_url,
                )
            )


def enqueue_alert(payload: AlertPayload, config: AlertConfig) -> None:
    """Sync wrapper for enqueuing alerts from non-async code."""
    from brawny.async_runtime import run_sync

    run_sync(send_alert(payload, config))


def configure_alert_worker(*, health_max_oldest_age_seconds: float | None = None) -> None:
    service = _require_alert_service()
    if health_max_oldest_age_seconds is not None:
        service.configure_health_threshold(health_max_oldest_age_seconds)


def get_alert_worker_health() -> dict[str, object]:
    service = _require_alert_service()
    return service.health_snapshot()


def _should_send(
    payload: AlertPayload,
    dest_type: str,
    destination_id: str,
    limit_seconds: float,
) -> bool:
    """Check rate limit. Key includes dest_type to avoid collisions.

    Key format: job_id:event_type:dest_type:destination_id
    - Multiple chat IDs rate-limited independently
    - Telegram + webhook don't suppress each other
    - dest_type prevents test collisions

    Uses threading.Lock (not asyncio.Lock) to avoid event loop binding issues.
    """
    key = f"{payload.job_id}:{payload.event_type.value}:{dest_type}:{destination_id}"

    with _last_sent_lock:
        now = datetime.utcnow()
        if key in _last_sent:
            if (now - _last_sent[key]).total_seconds() < limit_seconds:
                return False
        _last_sent[key] = now
        return True


def _parse_telegram_error(resp: httpx.Response) -> tuple[int | None, str | None]:
    error_code: int | None = None
    description: str | None = None
    try:
        body = resp.json()
        if isinstance(body, dict):
            error_code = body.get("error_code")
            description = body.get("description")
    except ValueError:
        description = None
    except Exception as exc:
        # RECOVERABLE
        log_unexpected(
            logger,
            "telegram.error_parse_failed",
            error=str(exc)[:200],
        )
        description = None
    if description is None:
        text = resp.text
        if text:
            description = text[:200]
    return error_code, description


def _looks_like_parse_error(description: str | None) -> bool:
    if not description:
        return False
    desc = description.lower()
    return "parse" in desc and ("entity" in desc or "entities" in desc or "parse_mode" in desc)


async def _send_telegram(token: str, chat_id: str, payload: AlertPayload) -> None:
    """Send message to Telegram. Pure function, no state."""
    parse_mode = payload.parse_mode or "Markdown"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    message = payload.message or ""
    if len(message) > TELEGRAM_MESSAGE_MAX_LEN:
        truncated = TELEGRAM_MESSAGE_MAX_LEN - len(TELEGRAM_TRUNCATION_SUFFIX)
        message = message[:max(truncated, 0)] + TELEGRAM_TRUNCATION_SUFFIX
        logger.warning(
            "telegram.message_truncated",
            job_id=payload.job_id,
            chain_id=payload.chain_id,
            original_length=len(payload.message or ""),
            truncated_length=len(message),
        )
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    with allow_network_calls(reason="alerts"):
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=data)
            if resp.status_code >= 400:
                error_code, description = _parse_telegram_error(resp)
                logger.error(
                    "telegram.send_failed",
                    job_id=payload.job_id,
                    chain_id=payload.chain_id,
                    chat_id=chat_id,
                    parse_mode=parse_mode,
                    message_length=len(message),
                    http_status=resp.status_code,
                    error_code=error_code,
                    description=description,
                )
                if resp.status_code == 400 and parse_mode and _looks_like_parse_error(description):
                    logger.warning(
                        "telegram.retry_without_parse_mode",
                        job_id=payload.job_id,
                        chain_id=payload.chain_id,
                        chat_id=chat_id,
                        parse_mode=parse_mode,
                    )
                    data.pop("parse_mode", None)
                    resp = await client.post(url, json=data)
                    if resp.status_code >= 400:
                        error_code, description = _parse_telegram_error(resp)
                        logger.error(
                            "telegram.send_failed",
                            job_id=payload.job_id,
                            chain_id=payload.chain_id,
                            chat_id=chat_id,
                            parse_mode=None,
                            message_length=len(message),
                            http_status=resp.status_code,
                            error_code=error_code,
                            description=description,
                        )
                        resp.raise_for_status()
                    return
            resp.raise_for_status()


async def _send_webhook(url: str, payload: AlertPayload) -> None:
    """Send payload to webhook. Pure function, no state.

    Schema (frozen):
    - job_id: str
    - job_name: str
    - event_type: str (enum value)
    - message: str
    - chain_id: int
    - timestamp: str (ISO8601 UTC)

    Do not add fields without versioning discussion.
    """
    with allow_network_calls(reason="alerts"):
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                json={
                    "job_id": payload.job_id,
                    "job_name": payload.job_name,
                    "event_type": payload.event_type.value,
                    "message": payload.message,
                    "chain_id": payload.chain_id,
                    "timestamp": payload.timestamp.isoformat() + "Z",
                },
            )
            resp.raise_for_status()


async def _send_task(task: _AlertTask) -> None:
    if task.destination_type == "telegram":
        if task.telegram_token is None:
            raise RuntimeError("telegram_token is required")
        await _send_telegram(task.telegram_token, task.destination_id, task.payload)
        return
    if task.destination_type == "webhook":
        if task.webhook_url is None:
            raise RuntimeError("webhook_url is required")
        await _send_webhook(task.webhook_url, task.payload)
        return
    raise RuntimeError(f"Unknown destination type: {task.destination_type}")


def flush_alert_queue(timeout_seconds: float | None = None) -> None:
    timeout = ALERT_FLUSH_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    service = _require_alert_service()
    from brawny.async_runtime import run_sync

    run_sync(service.stop(flush_timeout=timeout))


# =============================================================================
# Public alert() Function for Job Hooks
# =============================================================================


def alert(
    message: str,
    *,
    to: str | list[str] | None = None,
    parse_mode: str | None = None,
    disable_web_page_preview: bool = True,
    disable_notification: bool = False,
) -> None:
    """Send alert from within a job hook.

    Handles routing resolution, then delegates to TelegramBot.send_message().

    Uses Telegram Bot API parameter names verbatim. No aliases or renaming.
    Refer to https://core.telegram.org/bots/api#sendmessage for parameter docs.

    Args:
        message: Alert text (up to 4096 characters, auto-truncated)
        to: Override routing target (name or list). If None,
            uses job's alert_to config, then telegram.default/public.
            Note: This is a routing concept, not a Telegram API field.
        parse_mode: "Markdown", "MarkdownV2", "HTML", or None
        disable_web_page_preview: Disable link previews (default True)
        disable_notification: Send without notification sound (default False)

    Resolution order:
        1. `to` parameter (if provided)
        2. Job's alert_to config (if set)
        3. telegram.default (if set)
        4. telegram.public (if set)

    Raises:
        RuntimeError: If called outside a job hook

    Note:
        Unknown chat names are logged and skipped. If no destinations remain
        after resolution, this raises to surface misconfiguration.

    Example:
        alert("Harvested successfully")
        alert("Debug info", to="dev", disable_notification=True)
        alert("Check https://etherscan.io/tx/...", disable_web_page_preview=False)
    """
    from brawny._context import get_alert_context
    ctx = get_alert_context()
    if ctx is None:
        raise RuntimeError("alert() must be called from within a job hook")

    # Get telegram config and bot from context
    tg_config = getattr(ctx, "telegram_config", None)
    bot = getattr(ctx, "telegram_bot", None)
    if not tg_config or not bot:
        return  # Silent no-op (warned once at startup)

    # Determine target
    if to is not None:
        target = to
    else:
        job_alert_to = getattr(ctx, "job_alert_to", None)
        if job_alert_to is not None:
            target = job_alert_to
        elif tg_config.default:
            target = tg_config.default
        elif tg_config.public:
            target = tg_config.public
        else:
            target = None

    # Resolve to chat IDs (unknown names logged + skipped, not raised)
    job_id = getattr(ctx, "job_id", None)
    chat_ids = resolve_targets(target, tg_config.chats, [], job_id=job_id)

    if not chat_ids:
        raise RuntimeError(
            "No alert destinations configured; "
            "set telegram.default, telegram.public, or job.alert_to."
        )

    payload = AlertPayload(
        job_id=job_id or "unknown",
        job_name=job_id or "unknown",
        event_type=AlertEvent.TRIGGERED,
        message=message,
        parse_mode=parse_mode or tg_config.parse_mode or "Markdown",
        chain_id=getattr(ctx, "chain_id", 1),
    )

    # Send to each resolved chat
    for chat_id in chat_ids:
        if not _should_send(payload, "telegram", chat_id, tg_config.public_rate_limit_seconds):
            continue
        effective_parse_mode = (
            parse_mode if parse_mode is not None else tg_config.parse_mode or "Markdown"
        )
        bot.send_message(
            message,
            chat_id=chat_id,
            parse_mode=effective_parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
        )


async def _send_alert_logged(payload: AlertPayload, config: AlertConfig) -> None:
    """Fire-and-forget alert with exception logging."""
    try:
        await send_alert(payload, config)
    except Exception as exc:
        # RECOVERABLE alert send failures are logged and ignored.
        log_unexpected(
            logger,
            "alert.send_failed",
            job_id=payload.job_id,
            error=str(exc)[:200],
        )


# =============================================================================
# Health Alert Sender (distinct rate limiting from job alerts)
# =============================================================================

# Separate rate limiting for health alerts (prevents job alert noise from blocking health)
# Multi-threaded access - protected by _health_lock
# Low cardinality keys (chat IDs): maxsize=1K, ttl=1h
_health_last_sent: TTLCache[str, datetime] = TTLCache(maxsize=1_000, ttl=3600)
_health_lock = threading.Lock()

HEALTH_RATE_LIMIT_SECONDS = 1.0  # Min interval between health messages to same chat


def _should_send_health(chat_id: str) -> bool:
    """Check rate limit for health alerts. Uses separate namespace from job alerts."""
    key = f"health:{chat_id}"
    with _health_lock:
        now = datetime.utcnow()
        if key in _health_last_sent:
            if (now - _health_last_sent[key]).total_seconds() < HEALTH_RATE_LIMIT_SECONDS:
                return False
        _health_last_sent[key] = now
        return True


def create_send_health(bot: "TelegramBot") -> "Callable[[str, str], None]":
    """Create a health alert sender bound to a TelegramBot instance.

    Returns a callable that accepts (chat_id, text) kwargs.
    Uses distinct rate limiting from job alerts to prevent cross-blocking.

    Args:
        bot: TelegramBot instance to use for sending

    Returns:
        Function that sends health alerts: fn(chat_id=..., text=...)

    Usage:
        send_fn = create_send_health(telegram_bot)
        send_fn(chat_id="-100...", text="Health alert message")
    """
    def send_health(*, chat_id: str, text: str) -> None:
        """Send a health alert via the standard pipeline.

        Uses distinct rate_limit_key to prevent job alerts from blocking health alerts.
        """
        if not bot.configured:
            return

        if not _should_send_health(chat_id):
            logger.debug(
                "health_alert.rate_limited",
                chat_id=chat_id,
            )
            return

        try:
            bot.send_message(
                text,
                chat_id=chat_id,
                disable_web_page_preview=True,
            )
        except Exception as e:
            # RECOVERABLE health alert delivery failures should not crash callers.
            log_unexpected(
                logger,
                "health_alert.send_failed",
                chat_id=chat_id,
                error=str(e)[:200],
            )

    return send_health


# =============================================================================
# JobAlertSender for ctx.alert() in Lifecycle Hooks
# =============================================================================


class JobAlertSender:
    """Alert sender bound to a specific job's routing configuration.

    Used by lifecycle contexts (TriggerContext, SuccessContext, FailureContext)
    to provide ctx.alert() that routes to job-specific destinations.

    This class implements the AlertSender protocol from model.contexts.
    """

    def __init__(
        self,
        *,
        telegram_bot: "TelegramBot | None",
        telegram_config: Any,  # TelegramConfig
        job_alert_to: list[str] | None,
        job_id: str,
    ) -> None:
        """Initialize with job-specific routing.

        Args:
            telegram_bot: TelegramBot instance (None if not configured)
            telegram_config: TelegramConfig with chats, default, parse_mode
            job_alert_to: Job-specific alert destinations (or None for default)
            job_id: Job ID for logging
        """
        self._bot = telegram_bot
        self._tg_config = telegram_config
        self._job_alert_to = job_alert_to
        self._job_id = job_id

    def send(
        self,
        message: str,
        *,
        to: str | list[str] | None = None,
        parse_mode: str | None = None,
    ) -> None:
        """Send alert to configured destinations.

        Routing priority:
        1. `to` parameter (explicit override)
        2. job_alert_to (job-specific config)
        3. telegram.default (global default)
        4. telegram.public (public fallback)

        Args:
            message: Alert text (up to 4096 characters)
            to: Override routing target (name or list)
            parse_mode: "Markdown", "MarkdownV2", "HTML", or None for config default
        """
        if not self._bot or not self._tg_config:
            return  # Silent no-op (warned once at startup)

        # Determine target
        if to is not None:
            target = to
        else:
            if self._job_alert_to is not None:
                target = self._job_alert_to
            elif self._tg_config.default:
                target = self._tg_config.default
            elif self._tg_config.public:
                target = self._tg_config.public
            else:
                target = None

        # Resolve to chat IDs
        chat_ids = resolve_targets(target, self._tg_config.chats, [], job_id=self._job_id)

        if not chat_ids:
            raise RuntimeError(
                "No alert destinations configured; "
                "set telegram.default, telegram.public, or job.alert_to."
            )

        payload = AlertPayload(
            job_id=self._job_id,
            job_name=self._job_id,
            event_type=AlertEvent.TRIGGERED,
            message=message,
            parse_mode=parse_mode or self._tg_config.parse_mode or "Markdown",
        )

        # Send to each resolved chat
        for chat_id in chat_ids:
            if not _should_send(payload, "telegram", chat_id, self._tg_config.public_rate_limit_seconds):
                continue
            effective_parse_mode = (
                parse_mode if parse_mode is not None
                else self._tg_config.parse_mode or "Markdown"
            )
            self._bot.send_message(
                message,
                chat_id=chat_id,
                parse_mode=effective_parse_mode,
                disable_web_page_preview=True,
            )
