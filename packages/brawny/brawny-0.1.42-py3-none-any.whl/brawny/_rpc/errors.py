"""RPC error types and classification for brawny.

Error classification per SPEC:
- Retryable: Network/RPC issues, should retry with backoff
- Fatal TX: Transaction issues, do not retry with same params
- Recoverable TX: May succeed with different params (e.g., bumped gas)
"""

from __future__ import annotations

import asyncio
import enum
import socket
from dataclasses import dataclass
from typing import Any

from brawny.model.errors import BrawnyError


class RpcErrorKind(enum.Enum):
    """Canonical error kinds for RPC classification."""

    # Transport
    TIMEOUT = "timeout"
    DEADLINE_EXHAUSTED = "deadline_exhausted"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    SERVER_ERROR = "server_error"

    # JSON-RPC protocol
    METHOD_NOT_FOUND = "method_not_found"
    INVALID_PARAMS = "invalid_params"
    BAD_REQUEST = "bad_request"
    PARSE_ERROR = "parse_error"

    # Execution
    EXECUTION_REVERTED = "execution_reverted"
    OUT_OF_GAS = "out_of_gas"

    # TX rejection (fatal)
    NONCE_TOO_LOW = "nonce_too_low"
    NONCE_TOO_HIGH = "nonce_too_high"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INTRINSIC_GAS_TOO_LOW = "intrinsic_gas_too_low"
    GAS_LIMIT_EXCEEDED = "gas_limit_exceeded"
    TX_TYPE_NOT_SUPPORTED = "tx_type_not_supported"
    ALREADY_KNOWN = "already_known"

    # TX rejection (recoverable)
    REPLACEMENT_UNDERPRICED = "replacement_underpriced"
    TX_UNDERPRICED = "tx_underpriced"
    MAX_FEE_TOO_LOW = "max_fee_too_low"

    UNKNOWN = "unknown"


@dataclass
class RpcErrorInfo:
    """Structured classification result."""

    kind: RpcErrorKind
    retryable: bool
    failover_ok: bool
    message: str
    code: int | None = None
    http_status: int | None = None
    provider: str | None = None
    method: str | None = None
    classification_source: str = "unknown"
    deadline_remaining: float | None = None


ERROR_KIND_DEFAULTS: dict[RpcErrorKind, tuple[bool, bool]] = {
    # Transport
    RpcErrorKind.TIMEOUT: (True, True),
    RpcErrorKind.DEADLINE_EXHAUSTED: (False, False),
    RpcErrorKind.NETWORK: (True, True),
    RpcErrorKind.RATE_LIMIT: (True, True),
    RpcErrorKind.SERVER_ERROR: (True, True),
    RpcErrorKind.AUTH: (False, False),

    # Protocol
    RpcErrorKind.METHOD_NOT_FOUND: (False, True),
    RpcErrorKind.INVALID_PARAMS: (False, False),
    RpcErrorKind.BAD_REQUEST: (False, True),
    RpcErrorKind.PARSE_ERROR: (False, False),

    # Execution
    RpcErrorKind.EXECUTION_REVERTED: (False, False),
    RpcErrorKind.OUT_OF_GAS: (False, False),

    # TX fatal
    RpcErrorKind.NONCE_TOO_LOW: (False, False),
    RpcErrorKind.NONCE_TOO_HIGH: (False, False),
    RpcErrorKind.INSUFFICIENT_FUNDS: (False, False),
    RpcErrorKind.INTRINSIC_GAS_TOO_LOW: (False, False),
    RpcErrorKind.GAS_LIMIT_EXCEEDED: (False, False),
    RpcErrorKind.TX_TYPE_NOT_SUPPORTED: (False, False),
    RpcErrorKind.ALREADY_KNOWN: (False, False),

    # TX recoverable
    RpcErrorKind.REPLACEMENT_UNDERPRICED: (False, False),
    RpcErrorKind.TX_UNDERPRICED: (False, False),
    RpcErrorKind.MAX_FEE_TOO_LOW: (False, False),

    # Unknown - retry same endpoint only; failover only when transport is clear.
    RpcErrorKind.UNKNOWN: (True, False),
}


@dataclass
class ExtractedError:
    """Raw extracted error data."""

    http_status: int | None = None
    jsonrpc_code: int | None = None
    jsonrpc_message: str | None = None
    jsonrpc_data: Any = None
    exception_type: str = ""
    exception_message: str = ""
    provider_hint: str | None = None
    is_timeout: bool = False
    is_connection_error: bool = False


def extract_rpc_error(exc: Exception, endpoint: str | None = None) -> ExtractedError:
    """Extract structured error data from exception.

    IMPORTANT: CancelledError must NOT be passed here - let it propagate.
    """
    if isinstance(exc, asyncio.CancelledError):
        raise exc

    result = ExtractedError(
        exception_type=f"{type(exc).__module__}.{type(exc).__name__}",
        exception_message=str(exc)[:500],
    )

    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, socket.timeout)):
        result.is_timeout = True

    if isinstance(exc, (ConnectionError, ConnectionRefusedError, ConnectionResetError)):
        result.is_connection_error = True
    if isinstance(exc, OSError) and exc.errno in (111, 104, 32):
        result.is_connection_error = True

    for arg in getattr(exc, "args", []):
        if isinstance(arg, dict):
            _extract_from_dict(arg, result)
        elif isinstance(arg, str):
            _try_parse_json(arg, result)

    response = getattr(exc, "response", None)
    if response is not None:
        result.http_status = getattr(response, "status_code", None)
        _try_parse_json(getattr(response, "text", ""), result)

    if hasattr(exc, "status"):
        result.http_status = getattr(exc, "status", None)

    for attr in ("body", "text", "error"):
        val = getattr(exc, attr, None)
        if val is None:
            continue
        if isinstance(val, str):
            _try_parse_json(val, result)
        elif isinstance(val, dict):
            _extract_from_dict(val, result)

    if endpoint:
        result.provider_hint = _infer_provider(endpoint)

    return result


def _extract_from_dict(data: dict, result: ExtractedError) -> None:
    if "code" in data and "message" in data:
        result.jsonrpc_code = data.get("code")
        result.jsonrpc_message = data.get("message")
        result.jsonrpc_data = data.get("data")
        return
    error = data.get("error")
    if isinstance(error, dict):
        result.jsonrpc_code = error.get("code")
        result.jsonrpc_message = error.get("message")
        result.jsonrpc_data = error.get("data")


def _try_parse_json(s: str, result: ExtractedError) -> None:
    import json

    try:
        data = json.loads(s)
        if isinstance(data, dict):
            _extract_from_dict(data, result)
    except (json.JSONDecodeError, ValueError):
        pass


def _infer_provider(endpoint: str) -> str | None:
    e = endpoint.lower()
    if "alchemy" in e:
        return "alchemy"
    if "infura" in e:
        return "infura"
    if "quicknode" in e:
        return "quicknode"
    if "ankr" in e:
        return "ankr"
    if "localhost" in e or "127.0.0.1" in e:
        return "local"
    return None


class RPCError(BrawnyError):
    """Base RPC error."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        endpoint: str | None = None,
        method: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.endpoint = endpoint
        self.method = method


class RPCRetryableError(RPCError):
    """RPC error that should be retried.

    These are network/infrastructure issues that may resolve
    on retry or with a different endpoint.
    """

    pass


class RPCTransient(RPCRetryableError):
    """Transient RPC error (timeouts, network, server errors)."""

    pass


class RPCRateLimited(RPCRetryableError):
    """Rate-limited RPC error (HTTP 429 / provider throttling)."""

    pass


class RPCDeadlineExceeded(RPCError):
    """RPC deadline exhausted before call could be executed."""

    pass


class RPCFatalError(RPCError):
    """Fatal RPC error that should not be retried.

    These are transaction-level errors that won't be fixed
    by retrying with the same parameters.
    """

    pass


class RPCPermanent(RPCFatalError):
    """Permanent RPC error (auth, invalid params, method not found)."""

    pass


class RPCDecode(RPCFatalError):
    """RPC decode error (malformed JSON or invalid response)."""

    pass


class RPCRecoverableError(RPCError):
    """RPC error that may succeed with different parameters.

    Examples: underpriced transactions that need gas bump.
    """

    pass


class RPCPoolExhaustedError(RPCError):
    """All endpoints in a pool failed (internal, group-agnostic).

    This is raised when all endpoints fail during an operation.
    It does not include group context - the caller (broadcast layer) wraps
    this into RPCGroupUnavailableError with group context.
    """

    def __init__(
        self,
        message: str,
        endpoints: list[str],
        last_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.endpoints = endpoints
        self.last_error = last_error


class RPCGroupUnavailableError(RPCError):
    """All endpoints in a broadcast group are unavailable (user-facing).

    This is the user-facing error that includes group context. It wraps
    RPCPoolExhaustedError with the group name for logging and diagnostics.
    """

    def __init__(
        self,
        message: str,
        group_name: str | None,
        endpoints: list[str],
        last_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.group_name = group_name
        self.endpoints = endpoints
        self.last_error = last_error


# ============================================================================
# Retryable errors (network/infrastructure issues)
# ============================================================================
RETRYABLE_ERROR_CODES = frozenset({
    "timeout",
    "connection_refused",
    "connection_reset",
    "connection_error",
    "rate_limited",           # HTTP 429
    "bad_gateway",            # HTTP 502
    "service_unavailable",    # HTTP 503
    "gateway_timeout",        # HTTP 504
    "internal_error",         # JSON-RPC -32603
    "server_error",           # JSON-RPC -32000 to -32099
    "request_timeout",
    "network_error",
})

# HTTP status codes that indicate retryable errors
RETRYABLE_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})

# JSON-RPC error codes that are retryable
# -32603: Internal error
# -32000 to -32099: Server error (implementation defined)
RETRYABLE_RPC_CODES = frozenset({-32603} | set(range(-32099, -32000 + 1)))


# ============================================================================
# Fatal transaction errors (do not retry with same params)
# ============================================================================
FATAL_TX_ERROR_CODES = frozenset({
    "nonce_too_low",          # Already used nonce
    "insufficient_funds",      # Need more ETH
    "gas_limit_exceeded",      # TX exceeds block gas limit
    "execution_reverted",      # Contract rejected
    "invalid_sender",          # Bad signature
    "invalid_nonce",          # Nonce issues
    "intrinsic_gas_too_low",  # Gas below intrinsic
    "exceeds_block_gas_limit",
    "account_balance_too_low",
    "tx_type_not_supported",
    "max_fee_too_low",
})

# Substrings in error messages that indicate fatal errors
FATAL_TX_SUBSTRINGS = frozenset({
    "nonce too low",
    "insufficient funds",
    "execution reverted",
    "invalid sender",
    "gas limit exceeded",
    "intrinsic gas too low",
    "already known",  # Transaction already in mempool
})


# ============================================================================
# Recoverable transaction errors (may succeed with different params)
# ============================================================================
RECOVERABLE_TX_ERROR_CODES = frozenset({
    "replacement_underpriced",  # Retry with bumped gas
    "transaction_underpriced",  # Base fee too low
    "underpriced",
    "max_priority_fee_too_low",
    "max_fee_per_gas_too_low",
})

# Substrings in error messages that indicate recoverable errors
RECOVERABLE_TX_SUBSTRINGS = frozenset({
    "replacement transaction underpriced",
    "transaction underpriced",
    "max priority fee",
    "max fee per gas",
})


def classify_error(
    error: Exception,
    http_status: int | None = None,
    rpc_code: int | None = None,
) -> type[RPCError]:
    """Classify an error into a coarse RPC error taxonomy.

    Args:
        error: The exception to classify
        http_status: HTTP status code if available
        rpc_code: JSON-RPC error code if available

    Returns:
        The appropriate error class
    """
    error_msg = str(error).lower()

    # Check HTTP status first
    if http_status == 429:
        return RPCRateLimited
    if http_status and http_status in RETRYABLE_HTTP_STATUS:
        return RPCTransient

    # Check JSON-RPC error code
    if rpc_code and rpc_code in RETRYABLE_RPC_CODES:
        return RPCTransient

    # Check for recoverable TX errors (check before fatal)
    for substring in RECOVERABLE_TX_SUBSTRINGS:
        if substring in error_msg:
            return RPCRecoverableError

    # Check for fatal TX errors
    for substring in FATAL_TX_SUBSTRINGS:
        if substring in error_msg:
            return RPCFatalError

    # Check common error patterns
    if "timeout" in error_msg or "timed out" in error_msg:
        return RPCTransient
    if "connection" in error_msg:
        return RPCTransient
    if "rate limit" in error_msg:
        return RPCRateLimited
    if "reverted" in error_msg:
        return RPCFatalError
    if "nonce" in error_msg and ("low" in error_msg or "invalid" in error_msg):
        return RPCFatalError
    if "insufficient" in error_msg:
        return RPCFatalError

    # Default to retryable for unknown errors
    return RPCTransient


ERROR_SELECTOR = "0x08c379a0"
PANIC_SELECTOR = "0x4e487b71"


def classify_rpc_error(
    exc: Exception,
    endpoint: str | None = None,
    method: str | None = None,
    deadline: "Any | None" = None,
) -> RpcErrorInfo:
    """Classify RPC error with structured extraction and metrics-ready info.

    IMPORTANT: CancelledError must NOT be passed here - let it propagate.
    """
    if isinstance(exc, asyncio.CancelledError):
        raise exc

    if isinstance(exc, RPCDeadlineExceeded):
        info = _make_info(RpcErrorKind.DEADLINE_EXHAUSTED, ExtractedError(), "deadline_exhausted")
        info.method = method
        info.deadline_remaining = 0.0
        return info

    extracted = extract_rpc_error(exc, endpoint)
    info: RpcErrorInfo | None = None

    info = _classify_revert_first(extracted, method)

    if info is None and extracted.http_status is not None:
        info = _classify_by_http_status(extracted)
    if info is None and extracted.jsonrpc_code is not None:
        info = _classify_by_jsonrpc_code(extracted, method)
    if info is None:
        info = _classify_by_provider_patterns(extracted)
    if info is None:
        info = _classify_by_structured(extracted, method)
    if info is None:
        info = _classify_by_heuristics(extracted, method)

    info.method = method
    info.provider = extracted.provider_hint
    info.http_status = extracted.http_status
    info.code = extracted.jsonrpc_code
    if deadline is not None and hasattr(deadline, "remaining"):
        info.deadline_remaining = deadline.remaining()

    return info


def _classify_by_http_status(ext: ExtractedError) -> RpcErrorInfo | None:
    status = ext.http_status
    if status == 429:
        return _make_info(RpcErrorKind.RATE_LIMIT, ext, "http_429")
    if status in (401, 403):
        return _make_info(RpcErrorKind.AUTH, ext, "http_auth")
    if status == 400:
        if ext.jsonrpc_code == -32602:
            return _make_info(RpcErrorKind.INVALID_PARAMS, ext, "http_400_jsonrpc")
        return _make_info(RpcErrorKind.BAD_REQUEST, ext, "http_400")
    if status == 502:
        return _make_info(RpcErrorKind.NETWORK, ext, "http_502")
    if status == 503:
        return _make_info(RpcErrorKind.SERVER_ERROR, ext, "http_503")
    if status == 504:
        return _make_info(RpcErrorKind.TIMEOUT, ext, "http_504")
    if status is not None and status >= 500:
        return _make_info(RpcErrorKind.SERVER_ERROR, ext, "http_5xx")
    return None


def _classify_by_jsonrpc_code(ext: ExtractedError, method: str | None) -> RpcErrorInfo | None:
    code = ext.jsonrpc_code

    if code == -32700:
        return _make_info(RpcErrorKind.PARSE_ERROR, ext, "jsonrpc_-32700")
    if code == -32600:
        return _make_info(RpcErrorKind.BAD_REQUEST, ext, "jsonrpc_-32600")
    if code == -32601:
        return _make_info(RpcErrorKind.METHOD_NOT_FOUND, ext, "jsonrpc_-32601")
    if code == -32602:
        return _make_info(RpcErrorKind.INVALID_PARAMS, ext, "jsonrpc_-32602")
    if code == -32603:
        return _make_info(RpcErrorKind.SERVER_ERROR, ext, "jsonrpc_-32603")

    if code == 3:
        if method in ("eth_call", "eth_estimateGas"):
            return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "jsonrpc_3")
        return _make_info(RpcErrorKind.SERVER_ERROR, ext, "jsonrpc_3_send")

    if code is not None and -32099 <= code <= -32000:
        return _classify_server_error_message(ext, method)

    return None


def _classify_server_error_message(ext: ExtractedError, method: str | None) -> RpcErrorInfo | None:
    msg = (ext.jsonrpc_message or "").lower()

    if "nonce too low" in msg:
        return _make_info(RpcErrorKind.NONCE_TOO_LOW, ext, "msg_nonce_low")
    if "nonce too high" in msg:
        return _make_info(RpcErrorKind.NONCE_TOO_HIGH, ext, "msg_nonce_high")
    if "insufficient funds" in msg:
        return _make_info(RpcErrorKind.INSUFFICIENT_FUNDS, ext, "msg_funds")
    if "intrinsic gas too low" in msg:
        return _make_info(RpcErrorKind.INTRINSIC_GAS_TOO_LOW, ext, "msg_intrinsic_gas")
    if "gas limit" in msg and "exceeded" in msg:
        return _make_info(RpcErrorKind.GAS_LIMIT_EXCEEDED, ext, "msg_gas_limit")
    if "out of gas" in msg:
        return _make_info(RpcErrorKind.OUT_OF_GAS, ext, "msg_out_of_gas")
    if "already known" in msg or "known transaction" in msg:
        return _make_info(RpcErrorKind.ALREADY_KNOWN, ext, "msg_already_known")
    if "replacement transaction underpriced" in msg:
        return _make_info(RpcErrorKind.REPLACEMENT_UNDERPRICED, ext, "msg_replacement")
    if "underpriced" in msg:
        return _make_info(RpcErrorKind.TX_UNDERPRICED, ext, "msg_underpriced")

    if "execution reverted" in msg or "reverted" in msg:
        if method in ("eth_call", "eth_estimateGas"):
            return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "msg_reverted")
        return _make_info(RpcErrorKind.SERVER_ERROR, ext, "msg_reverted_send")

    return _make_info(RpcErrorKind.SERVER_ERROR, ext, "jsonrpc_-32000_generic")


def _classify_by_provider_patterns(ext: ExtractedError) -> RpcErrorInfo | None:
    code = ext.jsonrpc_code
    msg = (ext.jsonrpc_message or "").lower()

    if ext.provider_hint == "alchemy" and code == 429:
        return _make_info(RpcErrorKind.RATE_LIMIT, ext, "alchemy_429")

    if code == -32005 and any(kw in msg for kw in ("exceeded", "limit", "rate", "requests")):
        return _make_info(RpcErrorKind.RATE_LIMIT, ext, "infura_-32005")

    return None


def _classify_by_structured(ext: ExtractedError, method: str | None) -> RpcErrorInfo | None:
    if ext.exception_type.endswith(("ContractLogicError", "ContractCustomError")):
        if method in ("eth_call", "eth_estimateGas"):
            return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "web3_revert_exception")

    if ext.is_timeout:
        return _make_info(RpcErrorKind.TIMEOUT, ext, "flag_timeout")
    if ext.is_connection_error:
        return _make_info(RpcErrorKind.NETWORK, ext, "flag_connection")

    data = ext.jsonrpc_data
    if isinstance(data, str) and data.startswith("0x") and len(data) >= 10:
        selector = data[:10]
        if selector in (ERROR_SELECTOR, PANIC_SELECTOR):
            if method in ("eth_call", "eth_estimateGas"):
                return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "revert_data")
    if isinstance(data, dict):
        inner = data.get("data") or data.get("result") or ""
        if isinstance(inner, str) and inner.startswith("0x") and len(inner) >= 10:
            if inner[:10] in (ERROR_SELECTOR, PANIC_SELECTOR):
                if method in ("eth_call", "eth_estimateGas"):
                    return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "revert_data_nested")

    return None


def _classify_by_heuristics(ext: ExtractedError, method: str | None) -> RpcErrorInfo:
    msg = " ".join((ext.jsonrpc_message or ext.exception_message or "").lower().split())
    heuristics = [
        ("nonce_low", ["nonce too low"], RpcErrorKind.NONCE_TOO_LOW),
        ("funds", ["insufficient funds", "insufficient balance"], RpcErrorKind.INSUFFICIENT_FUNDS),
        ("already_known", ["already known", "known transaction"], RpcErrorKind.ALREADY_KNOWN),
        ("replacement", ["replacement transaction underpriced"], RpcErrorKind.REPLACEMENT_UNDERPRICED),
        ("underpriced", ["underpriced"], RpcErrorKind.TX_UNDERPRICED),
        ("reverted", ["execution reverted", "reverted"], RpcErrorKind.EXECUTION_REVERTED),
        ("timeout", ["timeout", "timed out"], RpcErrorKind.TIMEOUT),
        ("rate_limit", ["rate limit", "too many requests"], RpcErrorKind.RATE_LIMIT),
        ("connection", ["connection refused", "connection reset"], RpcErrorKind.NETWORK),
    ]

    for name, patterns, kind in heuristics:
        if any(p in msg for p in patterns):
            if kind == RpcErrorKind.EXECUTION_REVERTED and method not in ("eth_call", "eth_estimateGas"):
                return _make_info(RpcErrorKind.SERVER_ERROR, ext, "heuristic_reverted_send")
            return _make_info(kind, ext, f"heuristic_{name}")

    return _make_info(RpcErrorKind.UNKNOWN, ext, "no_match")


def _classify_revert_first(ext: ExtractedError, method: str | None) -> RpcErrorInfo | None:
    if method not in ("eth_call", "eth_estimateGas"):
        return None

    if ext.exception_type.endswith(("ContractLogicError", "ContractCustomError")):
        return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "revert_exception")

    msg = (ext.jsonrpc_message or "").lower()
    if "execution reverted" in msg or msg == "reverted":
        return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "revert_message")

    if ext.jsonrpc_code == 3:
        return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "revert_code")

    data = ext.jsonrpc_data
    if isinstance(data, str) and data.startswith("0x") and len(data) >= 10:
        if data[:10] in (ERROR_SELECTOR, PANIC_SELECTOR):
            return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "revert_data")
    if isinstance(data, dict):
        inner = data.get("data") or data.get("result") or ""
        if isinstance(inner, str) and inner.startswith("0x") and len(inner) >= 10:
            if inner[:10] in (ERROR_SELECTOR, PANIC_SELECTOR):
                return _make_info(RpcErrorKind.EXECUTION_REVERTED, ext, "revert_data_nested")

    return None


def _make_info(kind: RpcErrorKind, ext: ExtractedError, source: str) -> RpcErrorInfo:
    retryable, failover_ok = ERROR_KIND_DEFAULTS.get(kind, (True, True))
    return RpcErrorInfo(
        kind=kind,
        retryable=retryable,
        failover_ok=failover_ok,
        message=ext.jsonrpc_message or ext.exception_message or "",
        code=ext.jsonrpc_code,
        http_status=ext.http_status,
        provider=ext.provider_hint,
        classification_source=source,
    )
