"""Broadcast helpers with isolation guarantees.

This is the ONLY place that wraps RPCPoolExhaustedError → RPCGroupUnavailableError.
BroadcastClient does the endpoint iteration; this module adds group context.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable

from brawny.metrics import (
    BROADCAST_ATTEMPTS,
    BROADCAST_LATENCY_SECONDS,
    get_metrics,
)
from brawny._rpc.errors import (
    RPCFatalError,
    RPCPoolExhaustedError,
    RPCGroupUnavailableError,
    RPCRecoverableError,
)
from brawny.timeout import Deadline

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny._rpc.clients import BroadcastClient


def create_broadcast_manager(endpoints: list[str], config: "Config") -> "BroadcastClient":
    """Create a BroadcastClient for broadcasting to specific endpoints.

    This creates a dedicated BroadcastClient instance for broadcasting.
    Each call uses the provided endpoints (from binding snapshot for retries,
    or from current config for first broadcast).

    Args:
        endpoints: List of endpoint URLs to use (must be canonical)
        config: Config for RPC settings

    Returns:
        BroadcastClient configured for the provided endpoints
    """
    from brawny._rpc.retry_policy import broadcast_policy
    from brawny._rpc.clients import BroadcastClient

    return BroadcastClient(
        endpoints=endpoints,
        timeout_seconds=config.rpc_timeout_seconds,
        max_retries=config.rpc_max_retries,
        retry_backoff_base=config.rpc_retry_backoff_base,
        retry_policy=broadcast_policy(config),
        chain_id=config.chain_id,
        log_init=False,  # Don't log ephemeral broadcast managers
    )


def broadcast_transaction(
    raw_tx: bytes,
    endpoints: list[str],
    group_name: str | None,
    config: "Config",
    job_id: str | None = None,
    deadline: Deadline | None = None,
    pre_call: "Callable[[str], None] | None" = None,
) -> tuple[str, str]:
    """Broadcast transaction with isolation guarantee.

    This function creates a dedicated BroadcastClient for the broadcast,
    ensuring the transaction is only sent to the specified endpoints.

    Args:
        raw_tx: Signed transaction bytes
        endpoints: Endpoint list (MUST be binding snapshot for retries)
        group_name: Group name for logging/errors (None for ungrouped)
        config: Config for RPC settings
        job_id: Job ID for metrics (optional)
        pre_call: Optional hook invoked with endpoint before send (e.g., simulation)

    Returns:
        Tuple of (tx_hash, endpoint_url)

    Raises:
        RPCGroupUnavailableError: All endpoints in group failed
        RPCFatalError: TX rejected (nonce, funds, revert)
        RPCRecoverableError: TX may succeed with different params
    """
    manager = create_broadcast_manager(endpoints, config)
    metrics = get_metrics()
    chain_id = config.chain_id
    start_time = time.perf_counter()
    group_label = group_name or "ungrouped"

    try:
        tx_hash, endpoint_url = manager.send_raw_transaction(
            raw_tx,
            deadline=deadline,
            pre_call=pre_call,
        )

        # Record success metrics
        latency = time.perf_counter() - start_time
        metrics.counter(BROADCAST_ATTEMPTS).inc(
            chain_id=chain_id,
            job_id=job_id or "unknown",
            broadcast_group=group_label,
            result="success",
        )
        metrics.histogram(BROADCAST_LATENCY_SECONDS).observe(
            latency,
            chain_id=chain_id,
            job_id=job_id or "unknown",
            broadcast_group=group_label,
        )

        return tx_hash, endpoint_url

    except RPCPoolExhaustedError as e:
        # Record unavailable metrics
        metrics.counter(BROADCAST_ATTEMPTS).inc(
            chain_id=chain_id,
            job_id=job_id or "unknown",
            broadcast_group=group_label,
            result="unavailable",
        )
        # Wrap with group context for user-facing error
        raise RPCGroupUnavailableError(
            f"All endpoints in group '{group_label}' failed",
            group_name=group_name,
            endpoints=e.endpoints,
            last_error=e.last_error,
        ) from e

    except RPCFatalError:
        # Record fatal error metrics
        metrics.counter(BROADCAST_ATTEMPTS).inc(
            chain_id=chain_id,
            job_id=job_id or "unknown",
            broadcast_group=group_label,
            result="fatal",
        )
        raise

    except RPCRecoverableError:
        # Record recoverable error metrics
        metrics.counter(BROADCAST_ATTEMPTS).inc(
            chain_id=chain_id,
            job_id=job_id or "unknown",
            broadcast_group=group_label,
            result="recoverable",
        )
        raise


def get_broadcast_endpoints(config: "Config", group_name: str) -> list[str]:
    """Get endpoints for a broadcast group (already canonical + deduped).

    This returns the endpoint list from the current config. For first broadcasts,
    this list should be persisted as the binding. For retries, use the
    persisted binding instead of calling this function.

    Args:
        config: Application configuration
        group_name: Name of the broadcast group

    Returns:
        List of canonical endpoint URLs

    Raises:
        ValueError: If group not found or has no endpoints
    """
    if group_name not in config.rpc_groups:
        raise ValueError(f"Broadcast group '{group_name}' not found")

    group = config.rpc_groups[group_name]
    if not group.endpoints:
        raise ValueError(f"Broadcast group '{group_name}' has no endpoints")

    return group.endpoints
