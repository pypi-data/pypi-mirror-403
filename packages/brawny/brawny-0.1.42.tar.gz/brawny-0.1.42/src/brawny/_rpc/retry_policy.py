from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Type

from brawny._rpc.errors import RPCTransient, RPCRateLimited


@dataclass(frozen=True)
class RetryPolicy:
    """Simple retry policy for RPC calls.

    attempt is 1-based (first attempt is 1).
    """

    name: str
    max_attempts: int
    base_backoff_seconds: float
    max_backoff_seconds: float
    jitter: bool
    retryable_error_classes: tuple[type[BaseException], ...] = (RPCTransient, RPCRateLimited)

    def should_retry(self, error_class: type[BaseException]) -> bool:
        return issubclass(error_class, self.retryable_error_classes)

    def backoff_seconds(self, attempt: int, *, rng: random.Random | None = None) -> float:
        if attempt <= 0:
            return 0.0
        backoff = self.base_backoff_seconds * (2 ** (attempt - 1))
        backoff = min(backoff, self.max_backoff_seconds)
        if not self.jitter:
            return backoff
        rng = rng or random
        jitter = rng.uniform(0.0, min(backoff * 0.1, max(self.max_backoff_seconds - backoff, 0.0)))
        return min(backoff + jitter, self.max_backoff_seconds)


def _default_max_backoff(max_attempts: int, base_backoff_seconds: float) -> float:
    if max_attempts <= 0:
        return base_backoff_seconds
    return base_backoff_seconds * (2 ** (max_attempts - 1))


def policy_from_values(
    name: str,
    *,
    max_attempts: int,
    base_backoff_seconds: float,
    max_backoff_seconds: float | None = None,
    jitter: bool = False,
    retryable_error_classes: Iterable[type[BaseException]] | None = None,
) -> RetryPolicy:
    if max_backoff_seconds is None:
        max_backoff_seconds = _default_max_backoff(max_attempts, base_backoff_seconds)
    if retryable_error_classes is None:
        retryable_error_classes = (RPCTransient, RPCRateLimited)
    return RetryPolicy(
        name=name,
        max_attempts=max_attempts,
        base_backoff_seconds=base_backoff_seconds,
        max_backoff_seconds=max_backoff_seconds,
        jitter=jitter,
        retryable_error_classes=tuple(retryable_error_classes),
    )


def fast_read_policy(config) -> RetryPolicy:
    return policy_from_values(
        "FAST_READ",
        max_attempts=config.rpc_max_retries,
        base_backoff_seconds=config.rpc_retry_backoff_base,
    )


def broadcast_policy(config) -> RetryPolicy:
    return policy_from_values(
        "BROADCAST",
        max_attempts=config.rpc_max_retries,
        base_backoff_seconds=config.rpc_retry_backoff_base,
    )
