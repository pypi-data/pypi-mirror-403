"""Minimal error taxonomy for boundary logging and gates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from brawny._rpc.errors import (
    RPCDecode,
    RPCError,
    RPCFatalError,
    RPCGroupUnavailableError,
    RPCPermanent,
    RPCPoolExhaustedError,
    RPCRateLimited,
    RPCRetryableError,
    RPCTransient,
    RPCDeadlineExceeded,
)
from brawny.model.errors import (
    ConfigError,
    DatabaseCircuitBreakerOpenError,
    DatabaseError,
    InvariantViolation,
)


class ErrorClass(str, Enum):
    RPC_TRANSIENT = "RPC_TRANSIENT"
    RPC_RATE_LIMIT = "RPC_RATE_LIMIT"
    RPC_PERMANENT = "RPC_PERMANENT"
    DB_LOCKED = "DB_LOCKED"
    DB_INVARIANT = "DB_INVARIANT"
    INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
    CONFIG_ERROR = "CONFIG_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ErrorClassification:
    error_class: ErrorClass
    reason_code: str


def classify_error(exc: Exception) -> ErrorClassification:
    if isinstance(exc, RPCRateLimited):
        return ErrorClassification(ErrorClass.RPC_RATE_LIMIT, "rpc_rate_limited")
    if isinstance(exc, RPCGroupUnavailableError):
        return ErrorClassification(ErrorClass.RPC_TRANSIENT, "rpc_unhealthy")
    if isinstance(exc, RPCPoolExhaustedError):
        return ErrorClassification(ErrorClass.RPC_TRANSIENT, "rpc_unhealthy")
    if isinstance(exc, (RPCTransient, RPCRetryableError)):
        return ErrorClassification(ErrorClass.RPC_TRANSIENT, "rpc_transient")
    if isinstance(exc, RPCDeadlineExceeded):
        return ErrorClassification(ErrorClass.RPC_PERMANENT, "rpc_deadline_exhausted")
    if isinstance(exc, (RPCPermanent, RPCFatalError, RPCDecode)):
        return ErrorClassification(ErrorClass.RPC_PERMANENT, "rpc_permanent")
    if isinstance(exc, RPCError):
        return ErrorClassification(ErrorClass.RPC_TRANSIENT, "rpc_error")
    if isinstance(exc, DatabaseCircuitBreakerOpenError):
        return ErrorClassification(ErrorClass.DB_LOCKED, "db_circuit_breaker_open")
    if isinstance(exc, InvariantViolation):
        return ErrorClassification(ErrorClass.INVARIANT_VIOLATION, "invariant_violation")
    if isinstance(exc, ConfigError):
        return ErrorClassification(ErrorClass.CONFIG_ERROR, "config_error")
    if isinstance(exc, DatabaseError):
        message = str(exc).lower()
        if "locked" in message:
            return ErrorClassification(ErrorClass.DB_LOCKED, "db_locked")
        return ErrorClassification(ErrorClass.DB_INVARIANT, "db_error")
    return ErrorClassification(ErrorClass.UNKNOWN, "unknown_exception")
