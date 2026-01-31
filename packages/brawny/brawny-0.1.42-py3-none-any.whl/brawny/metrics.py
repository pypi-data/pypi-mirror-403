"""Metrics abstractions for brawny.

Provides a pluggable metrics interface that can be backed by
Prometheus, StatsD, DataDog, or any other metrics system.

Usage:
    from brawny.metrics import get_metrics

    metrics = get_metrics()
    metrics.counter("brawny_tx_confirmed_total").inc(job_id="my_job")
    metrics.gauge("brawny_pending_intents").set(5, chain_id=1)
    with metrics.histogram("brawny_tx_confirmation_seconds").time():
        await wait_for_confirmation()
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator, Protocol

from prometheus_client import (
    CollectorRegistry,
    Counter as PromCounter,
    Gauge as PromGauge,
    Histogram as PromHistogram,
    start_http_server,
)

class Counter(Protocol):
    """Counter metric that only goes up."""

    def inc(self, value: int = 1, **labels: Any) -> None:
        """Increment counter by value."""
        ...


class Gauge(Protocol):
    """Gauge metric that can go up or down."""

    def set(self, value: float, **labels: Any) -> None:
        """Set gauge to value."""
        ...

    def inc(self, value: float = 1.0, **labels: Any) -> None:
        """Increment gauge by value."""
        ...

    def dec(self, value: float = 1.0, **labels: Any) -> None:
        """Decrement gauge by value."""
        ...


class Histogram(Protocol):
    """Histogram metric for distributions."""

    def observe(self, value: float, **labels: Any) -> None:
        """Observe a value."""
        ...

    @contextmanager
    def time(self, **labels: Any) -> Iterator[None]:
        """Time a block of code."""
        ...


class MetricsProvider(ABC):
    """Abstract metrics provider interface."""

    @abstractmethod
    def counter(self, name: str) -> Counter:
        """Get or create a counter."""
        ...

    @abstractmethod
    def gauge(self, name: str) -> Gauge:
        """Get or create a gauge."""
        ...

    @abstractmethod
    def histogram(self, name: str, buckets: list[float] | None = None) -> Histogram:
        """Get or create a histogram."""
        ...


@dataclass
class NoOpCounter:
    """Counter that does nothing (for when metrics are disabled)."""

    name: str

    def inc(self, value: int = 1, **labels: Any) -> None:
        """No-op increment."""
        pass


@dataclass
class NoOpGauge:
    """Gauge that does nothing (for when metrics are disabled)."""

    name: str

    def set(self, value: float, **labels: Any) -> None:
        """No-op set."""
        pass

    def inc(self, value: float = 1.0, **labels: Any) -> None:
        """No-op increment."""
        pass

    def dec(self, value: float = 1.0, **labels: Any) -> None:
        """No-op decrement."""
        pass


@dataclass
class NoOpHistogram:
    """Histogram that does nothing (for when metrics are disabled)."""

    name: str

    def observe(self, value: float, **labels: Any) -> None:
        """No-op observe."""
        pass

    @contextmanager
    def time(self, **labels: Any) -> Iterator[None]:
        """No-op timer."""
        yield


class NoOpMetricsProvider(MetricsProvider):
    """Metrics provider that does nothing."""

    def __init__(self) -> None:
        self._counters: dict[str, NoOpCounter] = {}
        self._gauges: dict[str, NoOpGauge] = {}
        self._histograms: dict[str, NoOpHistogram] = {}

    def counter(self, name: str) -> Counter:
        if name not in self._counters:
            self._counters[name] = NoOpCounter(name)
        return self._counters[name]

    def gauge(self, name: str) -> Gauge:
        if name not in self._gauges:
            self._gauges[name] = NoOpGauge(name)
        return self._gauges[name]

    def histogram(self, name: str, buckets: list[float] | None = None) -> Histogram:
        if name not in self._histograms:
            self._histograms[name] = NoOpHistogram(name)
        return self._histograms[name]


@dataclass
class InMemoryCounter:
    """In-memory counter for testing and development."""

    name: str
    values: dict[tuple[tuple[str, Any], ...], float] = field(default_factory=dict)

    def inc(self, value: int = 1, **labels: Any) -> None:
        """Increment counter by value."""
        key = tuple(sorted(labels.items()))
        self.values[key] = self.values.get(key, 0) + value

    def get(self, **labels: Any) -> float:
        """Get current value for labels."""
        key = tuple(sorted(labels.items()))
        return self.values.get(key, 0)


@dataclass
class InMemoryGauge:
    """In-memory gauge for testing and development."""

    name: str
    values: dict[tuple[tuple[str, Any], ...], float] = field(default_factory=dict)

    def set(self, value: float, **labels: Any) -> None:
        """Set gauge to value."""
        key = tuple(sorted(labels.items()))
        self.values[key] = value

    def inc(self, value: float = 1.0, **labels: Any) -> None:
        """Increment gauge by value."""
        key = tuple(sorted(labels.items()))
        self.values[key] = self.values.get(key, 0) + value

    def dec(self, value: float = 1.0, **labels: Any) -> None:
        """Decrement gauge by value."""
        key = tuple(sorted(labels.items()))
        self.values[key] = self.values.get(key, 0) - value

    def get(self, **labels: Any) -> float:
        """Get current value for labels."""
        key = tuple(sorted(labels.items()))
        return self.values.get(key, 0)


@dataclass
class InMemoryHistogram:
    """In-memory histogram for testing and development."""

    name: str
    buckets: list[float] = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10])
    observations: dict[tuple[tuple[str, Any], ...], list[float]] = field(default_factory=dict)

    def observe(self, value: float, **labels: Any) -> None:
        """Observe a value."""
        key = tuple(sorted(labels.items()))
        if key not in self.observations:
            self.observations[key] = []
        self.observations[key].append(value)

    @contextmanager
    def time(self, **labels: Any) -> Iterator[None]:
        """Time a block of code."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.observe(duration, **labels)

    def get_observations(self, **labels: Any) -> list[float]:
        """Get all observations for labels."""
        key = tuple(sorted(labels.items()))
        return self.observations.get(key, [])


class InMemoryMetricsProvider(MetricsProvider):
    """In-memory metrics provider for testing and development."""

    def __init__(self) -> None:
        self._counters: dict[str, InMemoryCounter] = {}
        self._gauges: dict[str, InMemoryGauge] = {}
        self._histograms: dict[str, InMemoryHistogram] = {}

    def counter(self, name: str) -> InMemoryCounter:
        if name not in self._counters:
            self._counters[name] = InMemoryCounter(name)
        return self._counters[name]

    def gauge(self, name: str) -> InMemoryGauge:
        if name not in self._gauges:
            self._gauges[name] = InMemoryGauge(name)
        return self._gauges[name]

    def histogram(self, name: str, buckets: list[float] | None = None) -> InMemoryHistogram:
        if name not in self._histograms:
            resolved_buckets = _resolve_histogram_buckets(name, buckets)
            self._histograms[name] = InMemoryHistogram(
                name,
                resolved_buckets or DEFAULT_LATENCY_BUCKETS,
            )
        return self._histograms[name]

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


# =========================================================================
# Prometheus provider
# =========================================================================


class _PrometheusMetric:
    def __init__(self, metric: Any, labelnames: list[str]) -> None:
        self._metric = metric
        self._labelnames = labelnames

    def _labels(self, labels: dict[str, Any]) -> Any:
        if not self._labelnames:
            return self._metric
        normalized: dict[str, Any] = {}
        for name in self._labelnames:
            normalized[name] = labels.get(name, "unknown")
        return self._metric.labels(**normalized)


class PrometheusCounter(_PrometheusMetric):
    def inc(self, value: int = 1, **labels: Any) -> None:
        self._labels(labels).inc(value)


class PrometheusGauge(_PrometheusMetric):
    def set(self, value: float, **labels: Any) -> None:
        self._labels(labels).set(value)

    def inc(self, value: float = 1.0, **labels: Any) -> None:
        self._labels(labels).inc(value)

    def dec(self, value: float = 1.0, **labels: Any) -> None:
        self._labels(labels).dec(value)


class PrometheusHistogram(_PrometheusMetric):
    def observe(self, value: float, **labels: Any) -> None:
        self._labels(labels).observe(value)

    @contextmanager
    def time(self, **labels: Any) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.observe(duration, **labels)


class PrometheusMetricsProvider(MetricsProvider):
    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self._registry = registry or CollectorRegistry()
        self._counters: dict[str, PrometheusCounter] = {}
        self._gauges: dict[str, PrometheusGauge] = {}
        self._histograms: dict[str, PrometheusHistogram] = {}

    @property
    def registry(self) -> CollectorRegistry:
        return self._registry

    def counter(self, name: str) -> PrometheusCounter:
        if name not in self._counters:
            labelnames = METRIC_LABELS.get(name, [])
            metric = PromCounter(name, METRIC_DESCRIPTIONS.get(name, name), labelnames, registry=self._registry)
            self._counters[name] = PrometheusCounter(metric, labelnames)
        return self._counters[name]

    def gauge(self, name: str) -> PrometheusGauge:
        if name not in self._gauges:
            labelnames = METRIC_LABELS.get(name, [])
            metric = PromGauge(name, METRIC_DESCRIPTIONS.get(name, name), labelnames, registry=self._registry)
            self._gauges[name] = PrometheusGauge(metric, labelnames)
        return self._gauges[name]

    def histogram(self, name: str, buckets: list[float] | None = None) -> PrometheusHistogram:
        if name not in self._histograms:
            labelnames = METRIC_LABELS.get(name, [])
            resolved_buckets = _resolve_histogram_buckets(name, buckets)
            metric_kwargs = {
                "labelnames": labelnames,
                "registry": self._registry,
            }
            if resolved_buckets is not None:
                metric_kwargs["buckets"] = resolved_buckets
            metric = PromHistogram(
                name,
                METRIC_DESCRIPTIONS.get(name, name),
                **metric_kwargs,
            )
            self._histograms[name] = PrometheusHistogram(metric, labelnames)
        return self._histograms[name]


def start_metrics_server(bind: str, provider: PrometheusMetricsProvider) -> None:
    host, port_str = bind.rsplit(":", 1)
    port = int(port_str)
    start_http_server(port, addr=host, registry=provider.registry)


# Default histogram buckets for common use cases
DEFAULT_LATENCY_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
DEFAULT_TX_CONFIRMATION_BUCKETS = [10, 30, 60, 120, 300, 600, 1800, 3600]
DEFAULT_BLOCK_PROCESSING_BUCKETS = [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]

# Histogram bucket overrides for known metrics.
HISTOGRAM_BUCKETS = {
    "brawny_block_processing_seconds": DEFAULT_BLOCK_PROCESSING_BUCKETS,
    "brawny_tx_confirmation_seconds": DEFAULT_TX_CONFIRMATION_BUCKETS,
    "brawny_rpc_request_seconds": DEFAULT_LATENCY_BUCKETS,
    "brawny_job_check_seconds": DEFAULT_LATENCY_BUCKETS,
    "brawny_broadcast_latency_seconds": DEFAULT_LATENCY_BUCKETS,
}


def _resolve_histogram_buckets(name: str, buckets: list[float] | None) -> list[float] | None:
    if buckets is not None:
        return buckets
    return HISTOGRAM_BUCKETS.get(name)


# Global metrics provider
_metrics_provider: MetricsProvider | None = None


def set_metrics_provider(provider: MetricsProvider) -> None:
    """Set the global metrics provider.

    Args:
        provider: MetricsProvider implementation
    """
    global _metrics_provider
    _metrics_provider = provider


def get_metrics() -> MetricsProvider:
    """Get the global metrics provider.

    Returns NoOpMetricsProvider if not configured.

    Returns:
        The configured MetricsProvider
    """
    global _metrics_provider
    if _metrics_provider is None:
        _metrics_provider = NoOpMetricsProvider()
    return _metrics_provider


# =========================================================================
# Pre-defined metrics for brawny
# =========================================================================

# Counters
BLOCKS_PROCESSED = "brawny_blocks_processed_total"
JOBS_TRIGGERED = "brawny_jobs_triggered_total"
INTENTS_CREATED = "brawny_intents_created_total"
INTENT_TRANSITIONS = "brawny_intent_transitions_total"
INTENT_RETRY_ATTEMPTS = "brawny_intent_retry_attempts_total"
EXECUTOR_STAGE_STARTED = "brawny_executor_stage_started_total"
EXECUTOR_STAGE_OUTCOME = "brawny_executor_stage_outcome_total"
EXECUTOR_STAGE_TIMEOUTS = "brawny_executor_stage_timeouts_total"
EXECUTOR_RECREATES = "brawny_executor_recreates_total"
INTENT_CLAIMED = "brawny_intent_claimed_total"
INTENT_RELEASED = "brawny_intent_released_total"
CLAIM_RELEASED_PRE_ATTEMPT = "brawny_claim_released_pre_attempt_total"
CLAIM_RELEASE_SKIPPED = "brawny_claim_release_skipped_total"
CLAIM_RECLAIM_SKIPPED = "brawny_claim_reclaim_skipped_total"
INTENT_COOLDOWN_SKIPPED = "brawny_intent_cooldown_skipped_total"
INTENT_COOLDOWN_ERRORS = "brawny_intent_cooldown_errors_total"
INTENT_STATE_INCONSISTENT = "brawny_intent_state_inconsistent_total"
INTENT_CLAIMED_STUCK = "brawny_intent_claimed_stuck_total"
RECOVERY_MUTATIONS = "brawny_recovery_mutations_total"
BACKGROUND_TASK_ERRORS = "brawny_background_task_errors_total"
ERRORS_TOTAL = "brawny_errors_total"
ALERTS_ENQUEUED = "brawny_alerts_enqueued_total"
ALERTS_DROPPED = "brawny_alerts_dropped_total"
ALERTS_SENT = "brawny_alerts_sent_total"
ALERTS_RETRIED = "brawny_alerts_retried_total"
ALERTS_LAST_SUCCESS_TIMESTAMP = "brawny_alerts_last_success_timestamp"
ALERTS_LAST_ERROR_TIMESTAMP = "brawny_alerts_last_error_timestamp"
ALERTS_WORKER_ALIVE = "brawny_alerts_worker_alive"
ALERTS_OLDEST_QUEUED_AGE_SECONDS = "brawny_alerts_oldest_queued_age_seconds"
TX_BROADCAST = "brawny_tx_broadcast_total"
TX_CONFIRMED = "brawny_tx_confirmed_total"
TX_FAILED = "brawny_tx_failed_total"
TX_REPLACED = "brawny_tx_replaced_total"
RPC_REQUESTS = "brawny_rpc_requests_total"
RPC_ERRORS = "brawny_rpc_errors_total"
RPC_CALL_TIMEOUTS = "brawny_rpc_call_timeouts_total"
RPC_REQUESTS_BY_JOB = "brawny_rpc_requests_by_job_total"
RPC_FAILOVERS = "brawny_rpc_failovers_total"
RPC_ERROR_CLASSIFIED = "brawny_rpc_error_classified_total"
RPC_ERROR_UNKNOWN = "brawny_rpc_error_unknown_total"
JOB_CHECK_TIMEOUTS = "brawny_job_check_timeouts_total"
JOB_BUILD_TIMEOUTS = "brawny_job_build_timeouts_total"
REORGS_DETECTED = "brawny_reorg_detected_total"
DB_CIRCUIT_BREAKER_OPEN = "brawny_db_circuit_breaker_open_total"
SIMULATION_REVERTED = "brawny_simulation_reverted_total"
SIMULATION_NETWORK_ERRORS = "brawny_simulation_network_errors_total"
SIMULATION_RETRIES = "brawny_simulation_retries_total"
BROADCAST_ATTEMPTS = "brawny_broadcast_attempts_total"
NETWORK_GUARD_ALLOW = "brawny_network_guard_allow_total"
NETWORK_GUARD_VIOLATION = "brawny_network_guard_violation_total"
NONCE_GAP_DETECTED = "brawny_nonce_gap_detected_total"
NONCE_FORCE_RESET = "brawny_nonce_force_reset_total"

# Gauges
LAST_PROCESSED_BLOCK = "brawny_last_processed_block"
PENDING_INTENTS = "brawny_pending_intents"
INTENTS_BACKING_OFF = "brawny_intents_backing_off"
ACTIVE_WORKERS = "brawny_active_workers"
ALERTS_QUEUE_DEPTH = "brawny_alerts_queue_depth"
RPC_ENDPOINT_HEALTH = "brawny_rpc_endpoint_health"
RPC_SESSION_POOL_SIZE = "brawny_rpc_session_pool_size"
DB_CIRCUIT_BREAKER_STATE = "brawny_db_circuit_breaker_open"
AUTOMATION_ENABLED = "brawny_automation_enabled"

# Stuckness metrics (for "alive but not progressing" alerts)
# See LOGGING_METRICS_PLAN.md Section 4.1.4
OLDEST_PENDING_INTENT_AGE_SECONDS = "brawny_oldest_pending_intent_age_seconds"
LAST_BLOCK_PROCESSED_TIMESTAMP = "brawny_last_block_processed_timestamp"
LAST_BLOCK_TIMESTAMP = "brawny_last_block_timestamp"
BLOCK_PROCESSING_LAG_SECONDS = "brawny_block_processing_lag_seconds"
LAST_INTENT_COMPLETED_TIMESTAMP = "brawny_last_intent_completed_timestamp"
LAST_TX_CONFIRMED_TIMESTAMP = "brawny_last_tx_confirmed_timestamp"
LAST_INTENT_CREATED_TIMESTAMP = "brawny_last_intent_created_timestamp"

# Invariant gauges (Phase 2)
# These should be 0 in a healthy system - non-zero indicates issues
INVARIANT_STUCK_CLAIMED = "brawny_invariant_stuck_claimed"
INVARIANT_NONCE_GAP_AGE = "brawny_invariant_nonce_gap_age_seconds"
INVARIANT_BROADCASTED_NO_ATTEMPTS = "brawny_invariant_broadcasted_no_attempts"
INVARIANT_ORPHANED_CLAIMS = "brawny_invariant_orphaned_claims"
INVARIANT_ORPHANED_NONCES = "brawny_invariant_orphaned_nonces"

# Histograms
BLOCK_PROCESSING_SECONDS = "brawny_block_processing_seconds"
TX_CONFIRMATION_SECONDS = "brawny_tx_confirmation_seconds"
RPC_REQUEST_SECONDS = "brawny_rpc_request_seconds"
EXECUTOR_ATTEMPT_DURATION_SECONDS = "brawny_executor_attempt_duration_seconds"
JOB_CHECK_SECONDS = "brawny_job_check_seconds"
BROADCAST_LATENCY_SECONDS = "brawny_broadcast_latency_seconds"
RUNTIME_CONTROL_ACTIVE = "brawny_runtime_control_active"
RUNTIME_CONTROL_TTL_SECONDS = "brawny_runtime_control_ttl_seconds"

# Metric label schema (fixed, low-cardinality)
METRIC_LABELS = {
    BLOCKS_PROCESSED: ["chain_id"],
    JOBS_TRIGGERED: ["chain_id", "job_id"],
    INTENTS_CREATED: ["chain_id", "job_id"],
    INTENT_TRANSITIONS: ["chain_id", "from_status", "to_status", "reason"],
    INTENT_RETRY_ATTEMPTS: ["chain_id", "reason"],
    EXECUTOR_STAGE_STARTED: ["stage"],
    EXECUTOR_STAGE_OUTCOME: ["stage", "outcome"],
    EXECUTOR_STAGE_TIMEOUTS: ["stage"],
    EXECUTOR_RECREATES: ["chain_id", "job_id", "operation"],
    INTENT_CLAIMED: ["chain_id"],
    INTENT_RELEASED: ["chain_id", "reason"],
    CLAIM_RELEASED_PRE_ATTEMPT: ["stage"],
    CLAIM_RELEASE_SKIPPED: ["stage"],
    CLAIM_RECLAIM_SKIPPED: ["chain_id"],
    INTENT_COOLDOWN_SKIPPED: ["chain_id"],
    INTENT_COOLDOWN_ERRORS: ["chain_id"],
    INTENT_STATE_INCONSISTENT: ["chain_id", "reason"],
    INTENT_CLAIMED_STUCK: ["chain_id", "age_bucket"],
    RECOVERY_MUTATIONS: ["chain_id", "action"],
    BACKGROUND_TASK_ERRORS: ["task"],
    ERRORS_TOTAL: ["error_class", "reason_code", "subsystem"],
    ALERTS_ENQUEUED: [],
    ALERTS_DROPPED: ["reason", "channel"],
    ALERTS_SENT: [],
    ALERTS_RETRIED: [],
    TX_BROADCAST: ["chain_id", "job_id"],
    TX_CONFIRMED: ["chain_id", "job_id"],
    TX_FAILED: ["chain_id", "job_id", "reason"],
    TX_REPLACED: ["chain_id", "job_id"],
    RPC_REQUESTS: ["chain_id", "method", "rpc_category", "rpc_host"],
    RPC_ERRORS: ["chain_id", "method", "rpc_category", "rpc_host"],
    RPC_CALL_TIMEOUTS: ["chain_id", "method", "rpc_category", "rpc_host"],
    RPC_REQUESTS_BY_JOB: ["chain_id", "job_id", "rpc_category"],
    JOB_CHECK_TIMEOUTS: ["chain_id", "job_id"],
    JOB_BUILD_TIMEOUTS: ["chain_id", "job_id"],
    REORGS_DETECTED: ["chain_id"],
    DB_CIRCUIT_BREAKER_OPEN: ["db_backend"],
    SIMULATION_REVERTED: ["chain_id", "job_id"],
    SIMULATION_NETWORK_ERRORS: ["chain_id", "job_id"],
    SIMULATION_RETRIES: ["chain_id", "job_id"],
    BROADCAST_ATTEMPTS: ["chain_id", "job_id", "broadcast_group", "result"],
    RPC_ERROR_CLASSIFIED: ["kind", "method", "source"],
    RPC_ERROR_UNKNOWN: ["method", "exception_type", "provider", "http_status", "jsonrpc_code"],
    NETWORK_GUARD_ALLOW: ["reason"],
    NETWORK_GUARD_VIOLATION: ["context", "caller_module"],
    NONCE_GAP_DETECTED: ["chain_id", "signer"],
    NONCE_FORCE_RESET: ["chain_id", "signer", "source"],
    LAST_PROCESSED_BLOCK: ["chain_id"],
    PENDING_INTENTS: ["chain_id"],
    INTENTS_BACKING_OFF: ["chain_id"],
    ACTIVE_WORKERS: ["chain_id"],
    ALERTS_QUEUE_DEPTH: [],
    ALERTS_LAST_SUCCESS_TIMESTAMP: [],
    ALERTS_LAST_ERROR_TIMESTAMP: [],
    ALERTS_WORKER_ALIVE: [],
    ALERTS_OLDEST_QUEUED_AGE_SECONDS: [],
    RPC_ENDPOINT_HEALTH: ["endpoint"],
    RPC_SESSION_POOL_SIZE: [],
    DB_CIRCUIT_BREAKER_STATE: ["db_backend"],
    AUTOMATION_ENABLED: ["chain_id"],
    OLDEST_PENDING_INTENT_AGE_SECONDS: ["chain_id"],
    LAST_BLOCK_PROCESSED_TIMESTAMP: ["chain_id"],
    LAST_BLOCK_TIMESTAMP: ["chain_id"],
    BLOCK_PROCESSING_LAG_SECONDS: ["chain_id"],
    LAST_INTENT_COMPLETED_TIMESTAMP: ["chain_id"],
    LAST_TX_CONFIRMED_TIMESTAMP: ["chain_id"],
    LAST_INTENT_CREATED_TIMESTAMP: ["chain_id"],
    BLOCK_PROCESSING_SECONDS: ["chain_id"],
    TX_CONFIRMATION_SECONDS: ["chain_id"],
    RPC_REQUEST_SECONDS: ["chain_id", "method", "rpc_category", "rpc_host"],
    EXECUTOR_ATTEMPT_DURATION_SECONDS: ["stage"],
    JOB_CHECK_SECONDS: ["chain_id", "job_id"],
    BROADCAST_LATENCY_SECONDS: ["chain_id", "job_id", "broadcast_group"],
    RUNTIME_CONTROL_ACTIVE: ["control"],
    RUNTIME_CONTROL_TTL_SECONDS: ["control"],
    # Invariants (Phase 2)
    INVARIANT_STUCK_CLAIMED: ["chain_id"],
    INVARIANT_NONCE_GAP_AGE: ["chain_id"],
    INVARIANT_BROADCASTED_NO_ATTEMPTS: ["chain_id"],
    INVARIANT_ORPHANED_CLAIMS: ["chain_id"],
    INVARIANT_ORPHANED_NONCES: ["chain_id"],
}

METRIC_DESCRIPTIONS = {
    BLOCKS_PROCESSED: "Total blocks processed",
    JOBS_TRIGGERED: "Total jobs triggered",
    INTENTS_CREATED: "Total intents created",
    INTENT_TRANSITIONS: "Total intent status transitions",
    INTENT_RETRY_ATTEMPTS: "Total intent retry attempts",
    EXECUTOR_STAGE_STARTED: "Total executor stages started",
    EXECUTOR_STAGE_OUTCOME: "Total executor stage outcomes",
    EXECUTOR_STAGE_TIMEOUTS: "Total executor stage timeouts",
    EXECUTOR_RECREATES: "Total executor recreations after timeouts",
    INTENT_CLAIMED: "Total intents claimed",
    INTENT_RELEASED: "Total intents released",
    CLAIM_RELEASED_PRE_ATTEMPT: "Total claims released before attempts exist",
    CLAIM_RELEASE_SKIPPED: "Total claim releases skipped (token mismatch or attempts)",
    CLAIM_RECLAIM_SKIPPED: "Expired claims skipped due to attempts",
    INTENT_COOLDOWN_SKIPPED: "Intents skipped due to cooldown",
    INTENT_COOLDOWN_ERRORS: "Cooldown check errors",
    INTENT_STATE_INCONSISTENT: "Total inconsistent intent state detections",
    INTENT_CLAIMED_STUCK: "Total intents detected stuck in claimed state",
    RECOVERY_MUTATIONS: "Total recovery-only mutations by action",
    BACKGROUND_TASK_ERRORS: "Total background loop errors",
    ERRORS_TOTAL: "Total boundary errors by class/reason",
    ALERTS_ENQUEUED: "Total alerts enqueued for delivery",
    ALERTS_DROPPED: "Total alerts dropped before sending",
    ALERTS_SENT: "Total alerts delivered successfully",
    ALERTS_RETRIED: "Total alert send retries",
    ALERTS_LAST_SUCCESS_TIMESTAMP: "Unix timestamp of last alert success",
    ALERTS_LAST_ERROR_TIMESTAMP: "Unix timestamp of last alert error",
    ALERTS_WORKER_ALIVE: "Alert worker alive state (1=alive, 0=dead)",
    ALERTS_OLDEST_QUEUED_AGE_SECONDS: "Age in seconds of oldest queued alert",
    TX_BROADCAST: "Total transactions broadcast",
    TX_CONFIRMED: "Total transactions confirmed",
    TX_FAILED: "Total transactions failed",
    TX_REPLACED: "Total transactions replaced",
    RPC_REQUESTS: "Total RPC requests",
    RPC_ERRORS: "Total RPC errors (failed attempts)",
    RPC_CALL_TIMEOUTS: "Total RPC call timeouts",
    RPC_REQUESTS_BY_JOB: "RPC requests attributed to jobs",
    JOB_CHECK_TIMEOUTS: "Total job check timeouts",
    JOB_BUILD_TIMEOUTS: "Total job build_intent timeouts",
    REORGS_DETECTED: "Total reorgs detected",
    DB_CIRCUIT_BREAKER_OPEN: "Database circuit breaker openings",
    SIMULATION_REVERTED: "Total simulation reverts (permanent failures)",
    SIMULATION_NETWORK_ERRORS: "Total simulation network errors (after all retries)",
    SIMULATION_RETRIES: "Total simulation retry attempts",
    BROADCAST_ATTEMPTS: "Total broadcast attempts by result (success, unavailable, fatal, recoverable)",
    RPC_ERROR_CLASSIFIED: "Total RPC errors classified by the new classifier",
    RPC_ERROR_UNKNOWN: "Total RPC errors that are unknown to the new classifier",
    NETWORK_GUARD_ALLOW: "Network guard allowlist escapes (approved wrappers)",
    NETWORK_GUARD_VIOLATION: "Network guard blocked direct network calls",
    NONCE_GAP_DETECTED: "Nonce gap detected (chain_pending < db_next_nonce) - observability only, no auto-reset",
    NONCE_FORCE_RESET: "Explicit nonce force reset (CLI or allow_unsafe_nonce_reset config)",
    LAST_PROCESSED_BLOCK: "Last processed block",
    PENDING_INTENTS: "Inflight intents (created/claimed/broadcasted)",
    INTENTS_BACKING_OFF: "Intents in backoff window (retry_after in future)",
    ACTIVE_WORKERS: "Active worker threads",
    ALERTS_QUEUE_DEPTH: "Alert queue depth",
    RPC_ENDPOINT_HEALTH: "RPC endpoint health (1=healthy, 0=unhealthy)",
    RPC_SESSION_POOL_SIZE: "RPC session pool size (per transport)",
    DB_CIRCUIT_BREAKER_STATE: "Database circuit breaker open state (1=open, 0=closed)",
    AUTOMATION_ENABLED: "Automation enabled state (1=enabled, 0=disabled)",
    OLDEST_PENDING_INTENT_AGE_SECONDS: "Age in seconds of oldest pending intent (CREATED, CLAIMED, BROADCASTED)",
    LAST_BLOCK_PROCESSED_TIMESTAMP: "Unix timestamp when we last processed a block",
    LAST_BLOCK_TIMESTAMP: "Unix timestamp of the last processed block (chain time)",
    BLOCK_PROCESSING_LAG_SECONDS: "Seconds between block timestamp and processing completion",
    LAST_INTENT_COMPLETED_TIMESTAMP: "Unix timestamp when we last completed an intent",
    LAST_TX_CONFIRMED_TIMESTAMP: "Unix timestamp when we last confirmed a transaction",
    LAST_INTENT_CREATED_TIMESTAMP: "Unix timestamp when we last created an intent",
    BLOCK_PROCESSING_SECONDS: "Block processing duration in seconds",
    TX_CONFIRMATION_SECONDS: "Transaction confirmation duration in seconds",
    RPC_REQUEST_SECONDS: "RPC request duration in seconds",
    EXECUTOR_ATTEMPT_DURATION_SECONDS: "Executor stage duration in seconds",
    JOB_CHECK_SECONDS: "Job check duration in seconds",
    BROADCAST_LATENCY_SECONDS: "Broadcast transaction latency in seconds",
    RUNTIME_CONTROL_ACTIVE: "Runtime control active state (1=active, 0=inactive)",
    RUNTIME_CONTROL_TTL_SECONDS: "Runtime control TTL remaining in seconds",
    # Invariants (Phase 2)
    INVARIANT_STUCK_CLAIMED: "Intents stuck in claimed status > threshold minutes",
    INVARIANT_NONCE_GAP_AGE: "Age in seconds of oldest nonce gap (reserved below chain nonce)",
    INVARIANT_BROADCASTED_NO_ATTEMPTS: "Broadcasted intents with no attempt records (data integrity issue)",
    INVARIANT_ORPHANED_CLAIMS: "Intents with claim_token but status != claimed",
    INVARIANT_ORPHANED_NONCES: "Reserved/in_flight nonces for terminal intents",
}
