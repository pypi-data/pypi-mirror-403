from __future__ import annotations

import time
import threading
from typing import Any, Callable

from cachetools import TTLCache

from brawny._rpc.errors import (
    RPCDeadlineExceeded,
    RPCError,
    RPCFatalError,
    RPCPoolExhaustedError,
    RpcErrorKind,
)
from brawny._rpc.retry_policy import RetryPolicy
from brawny._rpc.pool import EndpointPool
from brawny._rpc.caller import Caller
from brawny._rpc.context import get_intent_budget_context, get_job_context
from brawny.metrics import (
    RPC_CALL_TIMEOUTS,
    RPC_ERRORS,
    RPC_FAILOVERS,
    RPC_REQUESTS,
    RPC_REQUESTS_BY_JOB,
    RPC_REQUEST_SECONDS,
    get_metrics,
)
from brawny.timeout import Deadline
from brawny.logging import get_logger, log_unexpected

logger = get_logger(__name__)

# High cardinality keys (intent budget keys): maxsize=10K, ttl=15min
_unknown_budget_counts: TTLCache[str, int] = TTLCache(maxsize=10_000, ttl=900)
_unknown_budget_lock = threading.Lock()
_MAX_UNKNOWN_RETRIES_PER_INTENT = 2
def _should_log_rpc_success_info(method: str, attempt: int, bound: bool) -> bool:
    if bound:
        return True
    if method == "eth_sendRawTransaction":
        return True
    if method == "eth_getTransactionReceipt":
        return attempt > 1
    return False


def _unknown_budget_exhausted(budget_key: str | None) -> bool:
    if not budget_key:
        return False
    with _unknown_budget_lock:
        current = _unknown_budget_counts.get(budget_key, 0)
        if current >= _MAX_UNKNOWN_RETRIES_PER_INTENT:
            return True
        _unknown_budget_counts[budget_key] = current + 1
        return False


def call_with_retries(
    pool: EndpointPool,
    caller: Caller,
    policy: RetryPolicy,
    method: str,
    args: tuple[Any, ...],
    *,
    timeout: float,
    deadline: Deadline | None,
    block_identifier: int | str,
    chain_id: int | None,
    request_id: str,
    bound: bool,
    attempt_event: str = "rpc.attempt",
    allowed_hosts: frozenset[str] | None = None,
    return_endpoint: bool = False,
    pre_call: Callable[[str], None] | None = None,
) -> Any:
    endpoints = pool.order_endpoints()
    attempts_to_try = min(policy.max_attempts, len(endpoints))
    if attempts_to_try <= 0:
        raise RPCPoolExhaustedError("No endpoints available for call", endpoints=[], last_error=None)

    metrics = get_metrics()
    last_error: Exception | None = None

    for attempt, endpoint in enumerate(endpoints[:attempts_to_try], start=1):
        if deadline is not None and deadline.expired():
            metrics.counter(RPC_CALL_TIMEOUTS).inc(
                chain_id=chain_id,
                method=method,
                rpc_category=_rpc_category(method),
                rpc_host=_rpc_host(endpoint, allowed_hosts),
            )
            raise RPCDeadlineExceeded(
                "RPC deadline exhausted before call",
                code="deadline_exceeded",
                method=method,
                endpoint=endpoint,
            )

        if pre_call is not None:
            pre_call(endpoint)

        effective_timeout = timeout
        if deadline is not None:
            remaining = deadline.remaining()
            if remaining <= 0:
                metrics.counter(RPC_CALL_TIMEOUTS).inc(
                    chain_id=chain_id,
                    method=method,
                    rpc_category=_rpc_category(method),
                    rpc_host=_rpc_host(endpoint, allowed_hosts),
                )
                raise RPCDeadlineExceeded(
                    "RPC deadline exhausted before call",
                    code="deadline_exceeded",
                    method=method,
                    endpoint=endpoint,
                )
            effective_timeout = min(timeout, remaining)

        metrics.counter(RPC_REQUESTS).inc(
            chain_id=chain_id,
            method=method,
            rpc_category=_rpc_category(method),
            rpc_host=_rpc_host(endpoint, allowed_hosts),
        )
        job_id = get_job_context()
        if job_id:
            metrics.counter(RPC_REQUESTS_BY_JOB).inc(
                chain_id=chain_id,
                job_id=job_id,
                rpc_category=_rpc_category(method),
            )

        start_time = time.time()
        try:
            result = caller.call(
                endpoint,
                method,
                args,
                timeout=effective_timeout,
                deadline=deadline,
                block_identifier=block_identifier,
            )
            latency = time.time() - start_time
            metrics.histogram(RPC_REQUEST_SECONDS).observe(
                latency,
                chain_id=chain_id,
                method=method,
                rpc_category=_rpc_category(method),
                rpc_host=_rpc_host(endpoint, allowed_hosts),
            )
            log_fields = {
                "chain_id": chain_id,
                "endpoint": _safe_endpoint_label(endpoint),
                "request_id": request_id,
                "method": method,
                "attempt": attempt,
                "policy_name": policy.name,
                "bound": bound,
                "error_class": None,
            }
            if job_id:
                log_fields["job_id"] = job_id
            log_fn = logger.info if _should_log_rpc_success_info(method, attempt, bound) else logger.debug
            log_fn(attempt_event, **log_fields)
            if return_endpoint:
                return result, endpoint
            return result
        except RPCError as exc:
            latency = time.time() - start_time
            metrics.histogram(RPC_REQUEST_SECONDS).observe(
                latency,
                chain_id=chain_id,
                method=method,
                rpc_category=_rpc_category(method),
                rpc_host=_rpc_host(endpoint, allowed_hosts),
            )

            error_class = type(exc)
            should_retry = isinstance(exc, policy.retryable_error_classes)
            failover_ok = getattr(exc, "failover_ok", True)
            error_kind = getattr(exc, "classification_kind", None)
            if error_kind == RpcErrorKind.UNKNOWN and _unknown_budget_exhausted(
                get_intent_budget_context()
            ):
                logger.error(
                    "rpc.unknown_budget_exhausted",
                    budget_key=get_intent_budget_context(),
                    method=method,
                    endpoint=_safe_endpoint_label(endpoint),
                )
                raise RPCFatalError(
                    "unknown_budget_exhausted",
                    code="unknown_budget_exhausted",
                    method=method,
                    endpoint=endpoint,
                ) from exc

            log_fields = {
                "chain_id": chain_id,
                "endpoint": _safe_endpoint_label(endpoint),
                "request_id": request_id,
                "method": method,
                "attempt": attempt,
                "policy_name": policy.name,
                "bound": bound,
                "error_class": error_class.__name__,
            }
            if job_id:
                log_fields["job_id"] = job_id
            logger.info(attempt_event, **log_fields)

            if not should_retry or not failover_ok:
                raise

            metrics.counter(RPC_ERRORS).inc(
                chain_id=chain_id,
                method=method,
                rpc_category=_rpc_category(method),
                rpc_host=_rpc_host(endpoint, allowed_hosts),
            )
            last_error = exc
            if attempt < attempts_to_try:
                metrics.counter(RPC_FAILOVERS).inc(chain_id=chain_id, method=method)
                backoff = policy.backoff_seconds(attempt)
                if backoff > 0:
                    time.sleep(backoff)
                continue
        except Exception as exc:  # noqa: BLE001 - unexpected bug
            # BUG
            # Re-raise unexpected RPC errors.
            log_unexpected(
                logger,
                "rpc.retry_unexpected_error",
                chain_id=chain_id,
                endpoint=_safe_endpoint_label(endpoint),
                request_id=request_id,
                method=method,
                attempt=attempt,
                policy_name=policy.name,
                bound=bound,
                error_class=type(exc).__name__,
                job_id=job_id,
            )
            raise

    raise RPCPoolExhaustedError(
        f"All {attempts_to_try} attempts failed",
        endpoints=endpoints[:attempts_to_try],
        last_error=last_error,
    )


def _rpc_category(method: str) -> str:
    return "broadcast" if method in {"eth_sendRawTransaction", "eth_sendTransaction"} else "read"


def _rpc_host(url: str, allowed_hosts: frozenset[str] | None = None) -> str:
    try:
        split = url.split("://", 1)[1]
    except IndexError:
        return "unknown"
    host = split.split("/", 1)[0]
    host = host.split("@", 1)[-1]
    host = host.split(":", 1)[0]
    if allowed_hosts is not None and host not in allowed_hosts:
        return "other"
    return host or "unknown"


def _safe_endpoint_label(url: str) -> str:
    parts = url.split("://", 1)
    if len(parts) == 2:
        scheme, rest = parts
    else:
        scheme, rest = "http", parts[0]
    host = rest.split("/", 1)[0]
    host = host.split("@", 1)[-1]
    return f"{scheme}://{host}"
