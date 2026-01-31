from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from brawny.timeout import Deadline

class StageName(str, Enum):
    GAP_CHECK = "gap_check"
    RESERVE_NONCE = "reserve_nonce"
    BUILD_TX = "build_tx"
    SIGN = "sign"
    BROADCAST = "broadcast"
    MONITOR_TICK = "monitor_tick"
    FINALIZE = "finalize"


@dataclass(frozen=True)
class RunContext:
    intent: Any
    chain_id: int
    signer_address: str
    to_address: str
    job: Any | None
    logger: Any
    config: Any
    rpc: Any
    db: Any
    nonce_manager: Any
    keystore: Any
    lifecycle: Any | None
    deadline: Deadline


@dataclass(frozen=True)
class RetryDecision:
    retry_in_seconds: float | None
    same_endpoint: bool = True
    rotate_endpoint: bool = False
    increase_fees: bool = False
    max_attempts_key: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class Ok:
    next_stage: StageName
    data: dict[str, Any]


@dataclass(frozen=True)
class Retry:
    next_stage: StageName
    retry: RetryDecision
    data: dict[str, Any]


@dataclass(frozen=True)
class Fail:
    reason: str
    fatal: bool
    data: dict[str, Any]


StageResult = Ok | Retry | Fail


@dataclass
class StageOutcome:
    done: bool
    final: Any | None = None
    next_stage: StageName | None = None
    data: dict[str, Any] | None = None
