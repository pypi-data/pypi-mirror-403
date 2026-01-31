"""Multicall context manager for batching eth_call requests."""

from __future__ import annotations

import contextvars
import os
import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable

from eth_abi import decode as abi_decode
from eth_abi import encode as abi_encode
from eth_utils import function_signature_to_4byte_selector, to_checksum_address

from brawny._context import _job_ctx, get_alert_context, get_console_context, resolve_block_identifier
from brawny.logging import get_logger
from brawny.networks.config import load_networks

logger = get_logger(__name__)

_ACTIVE_SESSION: contextvars.ContextVar["MulticallSession | None"] = contextvars.ContextVar(
    "multicall_session",
    default=None,
)

_TRY_AGGREGATE_SELECTOR = function_signature_to_4byte_selector(
    "tryAggregate(bool,(address,bytes)[])"
)
_UNRESOLVED = object()


@dataclass(frozen=True)
class _PendingCall:
    target: str
    calldata: bytes
    decoder: Callable[[bytes], Any]
    readable: str
    result: "MulticallResult"


class MulticallResult:
    """Lazy multicall result that resolves on first access."""

    def __init__(self, session: "MulticallSession") -> None:
        self._session = session
        self._value: object = _UNRESOLVED

    def _set_value(self, value: object) -> None:
        self._value = value

    def _resolve(self) -> object:
        if self._value is _UNRESOLVED:
            self._session.flush()
        return self._value

    def _unwrap(self, value: object) -> object:
        if isinstance(value, MulticallResult):
            return value._resolve()
        return value

    @property
    def value(self) -> object:
        return self._resolve()

    def __repr__(self) -> str:
        return repr(self._resolve())

    def __str__(self) -> str:
        return str(self._resolve())

    def __bool__(self) -> bool:
        return bool(self._resolve())

    def __eq__(self, other: object) -> bool:
        return self._resolve() == self._unwrap(other)

    def __ne__(self, other: object) -> bool:
        return self._resolve() != self._unwrap(other)

    def __lt__(self, other: object) -> bool:
        return self._resolve() < self._unwrap(other)

    def __le__(self, other: object) -> bool:
        return self._resolve() <= self._unwrap(other)

    def __gt__(self, other: object) -> bool:
        return self._resolve() > self._unwrap(other)

    def __ge__(self, other: object) -> bool:
        return self._resolve() >= self._unwrap(other)

    def __hash__(self) -> int:
        return hash(self._resolve())

    def __int__(self) -> int:
        return int(self._resolve())

    def __float__(self) -> float:
        return float(self._resolve())

    def __index__(self) -> int:
        return int(self._resolve())

    def __add__(self, other: object):
        return self._resolve() + self._unwrap(other)

    def __radd__(self, other: object):
        return self._unwrap(other) + self._resolve()

    def __sub__(self, other: object):
        return self._resolve() - self._unwrap(other)

    def __rsub__(self, other: object):
        return self._unwrap(other) - self._resolve()

    def __mul__(self, other: object):
        return self._resolve() * self._unwrap(other)

    def __rmul__(self, other: object):
        return self._unwrap(other) * self._resolve()

    def __truediv__(self, other: object):
        return self._resolve() / self._unwrap(other)

    def __rtruediv__(self, other: object):
        return self._unwrap(other) / self._resolve()

    def __floordiv__(self, other: object):
        return self._resolve() // self._unwrap(other)

    def __rfloordiv__(self, other: object):
        return self._unwrap(other) // self._resolve()

    def __mod__(self, other: object):
        return self._resolve() % self._unwrap(other)

    def __rmod__(self, other: object):
        return self._unwrap(other) % self._resolve()

    def __pow__(self, other: object):
        return self._resolve() ** self._unwrap(other)

    def __rpow__(self, other: object):
        return self._unwrap(other) ** self._resolve()

    def __neg__(self):
        return -self._resolve()

    def __pos__(self):
        return +self._resolve()

    def __abs__(self):
        return abs(self._resolve())

    def __iter__(self):
        return iter(self._resolve())

    def __len__(self) -> int:
        return len(self._resolve())

    def __contains__(self, item: object) -> bool:
        return item in self._resolve()

    def __getitem__(self, key):
        return self._resolve()[key]

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


class MulticallSession:
    """Active multicall session for batching eth_call requests."""

    def __init__(self, rpc: Any, address: str, block_identifier: int | str) -> None:
        self._rpc = rpc
        self.address = to_checksum_address(address)
        self.block_identifier = block_identifier
        self._pending: list[_PendingCall] = []
        self._lock = threading.Lock()

    def queue_call(
        self,
        *,
        target: str,
        calldata: str,
        block_identifier: int | str,
        decoder: Callable[[bytes], Any],
        readable: str,
    ) -> MulticallResult:
        self._normalize_block(block_identifier)

        result = MulticallResult(self)
        pending = _PendingCall(
            target=to_checksum_address(target),
            calldata=_hex_to_bytes(calldata),
            decoder=decoder,
            readable=readable,
            result=result,
        )
        with self._lock:
            self._pending.append(pending)
        return result

    def flush(self) -> None:
        with self._lock:
            pending = self._pending
            self._pending = []

        if not pending:
            return

        call_data = [(call.target, call.calldata) for call in pending]
        payload = _encode_try_aggregate(call_data)
        tx_params = {"to": self.address, "data": payload}

        result = self._rpc.eth_call(tx_params, block_identifier=self.block_identifier)
        result_bytes = _ensure_bytes(result)

        decoded = abi_decode(["(bool,bytes)[]"], result_bytes)[0]
        if len(decoded) != len(pending):
            raise RuntimeError(
                "multicall result length mismatch: "
                f"{len(decoded)} != {len(pending)}"
            )

        for call, (success, raw) in zip(pending, decoded):
            value = call.decoder(raw) if success else None
            call.result._set_value(value)

    def _normalize_block(self, block_identifier: int | str) -> int | str:
        if block_identifier == "latest":
            return self.block_identifier
        return block_identifier


class Multicall:
    """Context manager factory for multicall batching."""

    def __init__(
        self,
        *,
        address: str | None = None,
        block_identifier: int | str | None = None,
    ) -> None:
        self._address = address
        self._block_identifier = block_identifier

    def __call__(
        self,
        *,
        address: str | None = None,
        block_identifier: int | str | None = None,
    ) -> "Multicall":
        return Multicall(address=address, block_identifier=block_identifier)

    @property
    def address(self) -> str | None:
        session = _ACTIVE_SESSION.get()
        return session.address if session else None

    @property
    def block_number(self) -> int | str | None:
        session = _ACTIVE_SESSION.get()
        return session.block_identifier if session else None

    def flush(self) -> None:
        session = _ACTIVE_SESSION.get()
        if session:
            session.flush()

    def __enter__(self) -> "Multicall":
        if _ACTIVE_SESSION.get() is not None:
            raise RuntimeError("multicall does not support nested contexts")

        rpc, chain_id, config = _resolve_active_context()
        address = _resolve_address(self._address, chain_id, config)
        if address is None:
            raise LookupError(
                "No multicall2 address configured. "
                "Pass address=... or set BRAWNY_MULTICALL2."
            )

        base_block = resolve_block_identifier(
            explicit=self._block_identifier,
            handle_block=None,
        )
        if base_block == "latest":
            base_block = rpc.get_block_number()

        session = MulticallSession(rpc, address, base_block)
        _ACTIVE_SESSION.set(session)
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        session = _ACTIVE_SESSION.get()
        try:
            if session:
                session.flush()
        except Exception as err:
            # RECOVERABLE flush failures on context exit should not mask a prior exception.
            logger.error("multicall.flush_failed", error=str(err)[:200], exc_info=True)
            if exc_type is None:
                raise
        finally:
            _ACTIVE_SESSION.set(None)


def get_active_multicall_session() -> MulticallSession | None:
    return _ACTIVE_SESSION.get()


def enqueue_multicall_call(
    *,
    rpc: Any,
    target: str,
    calldata: str,
    block_identifier: int | str,
    decoder: Callable[[bytes], Any],
    readable: str,
) -> MulticallResult | None:
    session = _ACTIVE_SESSION.get()
    if session is None:
        return None
    if session._rpc is not rpc:
        raise RuntimeError("multicall rpc mismatch with active context")
    return session.queue_call(
        target=target,
        calldata=calldata,
        block_identifier=block_identifier,
        decoder=decoder,
        readable=readable,
    )


def _resolve_active_context() -> tuple[Any, int | None, Any | None]:
    job_ctx = _job_ctx.get()
    if job_ctx is not None:
        chain_id = getattr(getattr(job_ctx, "block", None), "chain_id", None)
        contracts = getattr(job_ctx, "contracts", None)
        if contracts is not None and hasattr(contracts, "_system"):
            system = contracts._system
            return system.rpc, chain_id or system.config.chain_id, system.config
        rpc = getattr(job_ctx, "rpc", None)
        return rpc, chain_id, None

    alert_ctx = get_alert_context()
    if alert_ctx is not None and getattr(alert_ctx, "contracts", None) is not None:
        system = alert_ctx.contracts._system
        return system.rpc, alert_ctx.block.chain_id, system.config

    console_ctx = get_console_context()
    if console_ctx is not None:
        return console_ctx.rpc, console_ctx.chain_id, console_ctx.contract_system.config

    raise LookupError(
        "No active context for multicall. "
        "Use inside jobs, alerts, console, or scripts."
    )


def _resolve_address(
    address: str | None,
    chain_id: int | None,
    config: Any | None,
) -> str | None:
    resolved = _normalize_address(address)
    if resolved:
        return resolved

    env_address = os.environ.get("BRAWNY_MULTICALL2")
    if env_address:
        return to_checksum_address(env_address)

    config_address = getattr(config, "multicall2", None) if config else None
    if config_address:
        return to_checksum_address(config_address)

    if chain_id is None:
        return None
    default_address = _multicall_by_chain_id().get(chain_id)
    if default_address:
        return to_checksum_address(default_address)
    return None


def _normalize_address(address: str | None) -> str | None:
    if address is None:
        return None
    if not isinstance(address, str):
        if hasattr(address, "address"):
            address = address.address
        else:
            raise TypeError("multicall address must be a string or contract handle")
    return to_checksum_address(address)


@lru_cache(maxsize=1)
def _multicall_by_chain_id() -> dict[int, str]:
    networks = load_networks()
    mapping: dict[int, str] = {}
    for _net_id, net in sorted(networks.items(), key=lambda item: item[0]):
        if net.chainid is None or net.multicall2 is None:
            continue
        if net.chainid not in mapping:
            mapping[net.chainid] = net.multicall2
    return mapping


def _encode_try_aggregate(calls: list[tuple[str, bytes]]) -> str:
    encoded = abi_encode(["bool", "(address,bytes)[]"], [False, calls])
    data = _TRY_AGGREGATE_SELECTOR + encoded
    return "0x" + data.hex()


def _hex_to_bytes(value: str) -> bytes:
    if value.startswith("0x"):
        return bytes.fromhex(value[2:])
    return bytes.fromhex(value)


def _ensure_bytes(value: Any) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return _hex_to_bytes(value)
    raise TypeError(f"Expected bytes or hex string, got {type(value).__name__}")


multicall = Multicall()

__all__ = [
    "Multicall",
    "MulticallResult",
    "MulticallSession",
    "enqueue_multicall_call",
    "get_active_multicall_session",
    "multicall",
]
