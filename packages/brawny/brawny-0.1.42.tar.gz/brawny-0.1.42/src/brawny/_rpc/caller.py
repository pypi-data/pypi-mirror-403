from __future__ import annotations

from typing import Any, Callable

from eth_utils import keccak

from brawny._rpc.errors import (
    RPCError,
    RPCFatalError,
    RPCRecoverableError,
    RPCDecode,
    RPCPermanent,
    RPCTransient,
    RPCRateLimited,
    RpcErrorKind,
    classify_rpc_error,
)
from brawny._rpc.transport import RpcTransport
from brawny.metrics import (
    RPC_ERROR_CLASSIFIED,
    RPC_ERROR_UNKNOWN,
    get_metrics,
)
from brawny.timeout import Deadline
from brawny.logging import get_logger, log_unexpected

logger = get_logger(__name__)


_FATAL_KINDS = frozenset({
    RpcErrorKind.NONCE_TOO_LOW,
    RpcErrorKind.NONCE_TOO_HIGH,
    RpcErrorKind.INSUFFICIENT_FUNDS,
    RpcErrorKind.INTRINSIC_GAS_TOO_LOW,
    RpcErrorKind.GAS_LIMIT_EXCEEDED,
    RpcErrorKind.TX_TYPE_NOT_SUPPORTED,
    RpcErrorKind.EXECUTION_REVERTED,
    RpcErrorKind.OUT_OF_GAS,
    RpcErrorKind.INVALID_PARAMS,
    RpcErrorKind.PARSE_ERROR,
    RpcErrorKind.BAD_REQUEST,
})

_RECOVERABLE_KINDS = frozenset({
    RpcErrorKind.REPLACEMENT_UNDERPRICED,
    RpcErrorKind.TX_UNDERPRICED,
    RpcErrorKind.MAX_FEE_TOO_LOW,
})



def _map_kind_to_class(kind: RpcErrorKind) -> type[RPCError]:
    if kind in _RECOVERABLE_KINDS:
        return RPCRecoverableError
    if kind == RpcErrorKind.RATE_LIMIT:
        return RPCRateLimited
    if kind in (RpcErrorKind.PARSE_ERROR, RpcErrorKind.BAD_REQUEST):
        return RPCDecode
    if kind in (RpcErrorKind.INVALID_PARAMS,):
        return RPCPermanent
    if kind == RpcErrorKind.DEADLINE_EXHAUSTED:
        return RPCPermanent
    if kind in _FATAL_KINDS:
        return RPCFatalError
    return RPCTransient


def _handle_already_known(raw_tx: bytes) -> str:
    if isinstance(raw_tx, str):
        raw_tx = raw_tx[2:] if raw_tx.startswith("0x") else raw_tx
        raw_tx = bytes.fromhex(raw_tx)
    return "0x" + keccak(raw_tx).hex()


class Caller:
    """Execute a single RPC call against a specific endpoint."""

    def __init__(self, endpoints: list[str], timeout_seconds: float, chain_id: int | None) -> None:
        self._timeout = timeout_seconds
        self._chain_id = chain_id
        self._transport = RpcTransport(endpoints, timeout_seconds)

    def get_web3(self, endpoint_url: str, timeout: float | None = None) -> Any:
        del timeout
        return self._transport.get_web3(endpoint_url)

    def call(
        self,
        endpoint_url: str,
        method: str,
        args: tuple[Any, ...],
        *,
        timeout: float,
        deadline: Deadline | None,
        block_identifier: int | str,
    ) -> Any:
        try:
            return self._transport.call(
                endpoint_url,
                method,
                args,
                timeout=timeout,
                block_identifier=block_identifier,
            )
        except Exception as exc:  # noqa: BLE001 - preserve original exception
            # BUG re-raise unexpected RPC errors after classification.
            if isinstance(exc, RPCError):
                if exc.method is None or exc.endpoint is None:
                    raise type(exc)(str(exc), code=exc.code, method=method, endpoint=endpoint_url) from exc
                raise

            extracted = classify_rpc_error(exc, endpoint=endpoint_url, method=method, deadline=deadline)
            if extracted.kind == RpcErrorKind.UNKNOWN:
                log_unexpected(
                    logger,
                    "rpc.call_unexpected_error",
                    endpoint=endpoint_url,
                    method=method,
                    error=str(exc)[:200],
                )
            if extracted.kind == RpcErrorKind.ALREADY_KNOWN and method == "eth_sendRawTransaction":
                raw_tx = args[0] if args else b""
                return _handle_already_known(raw_tx)
            self._raise_classified(exc, extracted, endpoint_url, method)

    def call_with_web3(
        self,
        endpoint_url: str,
        *,
        timeout: float,
        deadline: Deadline | None,
        method: str,
        fn: Callable[[Web3], Any],
    ) -> Any:
        try:
            return self._transport.call_with_web3(
                endpoint_url,
                timeout=timeout,
                fn=fn,
            )
        except Exception as exc:  # noqa: BLE001
            # BUG re-raise unexpected RPC errors after classification.
            if isinstance(exc, RPCError):
                if exc.method is None or exc.endpoint is None:
                    raise type(exc)(str(exc), code=exc.code, method=method, endpoint=endpoint_url) from exc
                raise
            extracted = classify_rpc_error(exc, endpoint=endpoint_url, method=method, deadline=deadline)
            if extracted.kind == RpcErrorKind.UNKNOWN:
                log_unexpected(
                    logger,
                    "rpc.call_unexpected_error",
                    endpoint=endpoint_url,
                    method=method,
                    error=str(exc)[:200],
                )
            self._raise_classified(exc, extracted, endpoint_url, method)

    @staticmethod
    def _raise_classified(
        exc: Exception,
        extracted,
        endpoint_url: str,
        method: str,
    ) -> None:
        metrics = get_metrics()
        if extracted.kind == RpcErrorKind.UNKNOWN:
            metrics.counter(RPC_ERROR_UNKNOWN).inc(
                method=method or "unknown",
                exception_type=type(exc).__name__,
                provider=extracted.provider or "unknown",
                http_status=str(extracted.http_status or "none"),
                jsonrpc_code=str(extracted.code or "none"),
            )
            raise exc
        metrics.counter(RPC_ERROR_CLASSIFIED).inc(
            kind=extracted.kind.value,
            method=method or "unknown",
            source=extracted.classification_source,
        )

        error_class = _map_kind_to_class(extracted.kind)
        err = error_class(
            str(exc),
            code=extracted.kind.value,
            endpoint=endpoint_url,
            method=method,
        )
        setattr(err, "failover_ok", extracted.failover_ok)
        setattr(err, "classification_kind", extracted.kind)
        raise err from exc
