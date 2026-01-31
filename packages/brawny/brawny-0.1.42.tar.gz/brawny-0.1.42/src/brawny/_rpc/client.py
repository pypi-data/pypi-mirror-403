from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Callable

from brawny._rpc.caller import Caller
from brawny._rpc.pool import EndpointPool
from brawny._rpc.retry import call_with_retries
from brawny._rpc.retry_policy import RetryPolicy, policy_from_values
from brawny._rpc.errors import (
    RPCDeadlineExceeded,
    RPCError,
    RPCFatalError,
    RPCRecoverableError,
)
from brawny.logging import get_logger, log_unexpected
from brawny.timeout import Deadline
from brawny.model.errors import SimulationNetworkError, SimulationReverted
from brawny.tx_hash import normalize_tx_hash

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny._rpc.gas import GasQuote, GasQuoteCache

logger = get_logger(__name__)


def _rpc_host(url: str) -> str:
    try:
        split = url.split("://", 1)[1]
    except IndexError:
        return "unknown"
    host = split.split("/", 1)[0]
    host = host.split("@", 1)[-1]
    host = host.split(":", 1)[0]
    return host or "unknown"


class ReadClient:
    """Read RPC client using EndpointPool + Caller + call_with_retries."""

    def __init__(
        self,
        endpoints: list[str],
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
        retry_policy: RetryPolicy | None = None,
        chain_id: int | None = None,
        gas_refresh_seconds: int = 15,
        log_init: bool = True,
        request_id_factory: Callable[[], str] | None = None,
        bound: bool = False,
    ) -> None:
        if not endpoints:
            raise ValueError("At least one RPC endpoint is required")

        self._pool = EndpointPool(endpoints)
        self._timeout = timeout_seconds
        if retry_policy is None:
            retry_policy = policy_from_values(
                "DEFAULT",
                max_attempts=max_retries,
                base_backoff_seconds=retry_backoff_base,
            )
        self._retry_policy = retry_policy
        self._chain_id = chain_id
        self._gas_refresh_seconds = gas_refresh_seconds
        self._gas_cache: "GasQuoteCache | None" = None
        self._caller = Caller(self._pool.endpoints, timeout_seconds, chain_id)
        self._request_id_factory = request_id_factory or _default_request_id
        self._bound = bound

        hosts = []
        for ep in self._pool.endpoints:
            h = _rpc_host(ep)
            if h not in ("unknown", "other"):
                hosts.append(h)
        self._allowed_hosts = frozenset(hosts)

        if log_init:
            logger.info(
                "rpc.client.initialized",
                endpoints=len(endpoints),
                timeout=timeout_seconds,
                max_retries=retry_policy.max_attempts,
            )

    @classmethod
    def from_config(cls, config: Config) -> "ReadClient":
        from brawny.config.routing import resolve_default_read_group
        from brawny._rpc.retry_policy import fast_read_policy

        default_group = resolve_default_read_group(config)
        endpoints = config.rpc_groups[default_group].endpoints
        return cls(
            endpoints=endpoints,
            timeout_seconds=config.rpc_timeout_seconds,
            max_retries=config.rpc_max_retries,
            retry_backoff_base=config.rpc_retry_backoff_base,
            retry_policy=fast_read_policy(config),
            chain_id=config.chain_id,
            gas_refresh_seconds=config.gas_refresh_seconds,
        )

    @property
    def web3(self):
        # Direct Web3 access is not concurrency-safe with transport timeouts.
        endpoint = self._pool.order_endpoints()[0]
        return self._caller.get_web3(endpoint)

    @property
    def gas(self) -> "GasQuoteCache":
        if self._gas_cache is None:
            from brawny._rpc.gas import GasQuoteCache

            self._gas_cache = GasQuoteCache(
                self,
                ttl_seconds=self._gas_refresh_seconds,
            )
        return self._gas_cache

    async def gas_quote(self) -> "GasQuote":
        return await self.gas.get_quote()

    def gas_quote_sync(self, deadline: Deadline | None = None) -> "GasQuote | None":
        return self.gas.get_quote_sync(deadline=deadline)

    def call(
        self,
        method: str,
        *args: Any,
        timeout: float | None = None,
        deadline: Deadline | None = None,
        block_identifier: int | str = "latest",
    ) -> Any:
        timeout = timeout or self._timeout
        request_id = self._request_id_factory()
        return call_with_retries(
            self._pool,
            self._caller,
            self._retry_policy,
            method,
            args,
            timeout=timeout,
            deadline=deadline,
            block_identifier=block_identifier,
            chain_id=self._chain_id,
            request_id=request_id,
            bound=self._bound,
            allowed_hosts=self._allowed_hosts,
        )

    def with_retry(
        self,
        fn: Callable[[Any], Any],
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> Any:
        timeout = timeout or self._timeout
        request_id = self._request_id_factory()

        class _FnCaller:
            def __init__(self, caller: Caller, fn: Callable[[Any], Any]) -> None:
                self._caller = caller
                self._fn = fn

            def call(
                self,
                endpoint: str,
                method: str,
                _args: tuple[Any, ...],
                *,
                timeout: float,
                deadline: Deadline | None,
                block_identifier: int | str,
            ) -> Any:
                return self._caller.call_with_web3(
                    endpoint,
                    timeout=timeout,
                    deadline=deadline,
                    method=method,
                    fn=self._fn,
                )

        return call_with_retries(
            self._pool,
            _FnCaller(self._caller, fn),  # type: ignore[arg-type]
            self._retry_policy,
            "with_retry",
            (),
            timeout=timeout,
            deadline=deadline,
            block_identifier="latest",
            chain_id=self._chain_id,
            request_id=request_id,
            bound=self._bound,
            allowed_hosts=self._allowed_hosts,
        )

    def get_block_number(
        self,
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> int:
        return self.call("eth_blockNumber", timeout=timeout, deadline=deadline)

    def get_block(
        self,
        block_identifier: int | str = "latest",
        full_transactions: bool = False,
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> dict[str, Any]:
        return self.call(
            "eth_getBlockByNumber",
            block_identifier,
            full_transactions,
            timeout=timeout,
            deadline=deadline,
        )

    def get_transaction_count(
        self,
        address: str,
        block_identifier: int | str = "pending",
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> int:
        return self.call(
            "eth_getTransactionCount",
            address,
            block_identifier,
            timeout=timeout,
            deadline=deadline,
        )

    def get_transaction_receipt(
        self,
        tx_hash: str,
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> dict[str, Any] | None:
        tx_hash = normalize_tx_hash(tx_hash)
        return self.call("eth_getTransactionReceipt", tx_hash, timeout=timeout, deadline=deadline)

    def get_transaction_by_hash(
        self,
        tx_hash: str,
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> dict[str, Any] | None:
        tx_hash = normalize_tx_hash(tx_hash)
        return self.call("eth_getTransactionByHash", tx_hash, timeout=timeout, deadline=deadline)

    def send_raw_transaction(
        self,
        raw_tx: bytes,
        timeout: float | None = None,
        deadline: Deadline | None = None,
        pre_call: Callable[[str], None] | None = None,
    ) -> tuple[str, str]:
        timeout = timeout or self._timeout
        request_id = self._request_id_factory()
        tx_hash, endpoint = call_with_retries(
            self._pool,
            self._caller,
            self._retry_policy,
            "eth_sendRawTransaction",
            (raw_tx,),
            timeout=timeout,
            deadline=deadline,
            block_identifier="latest",
            chain_id=self._chain_id,
            request_id=request_id,
            bound=self._bound,
            allowed_hosts=self._allowed_hosts,
            return_endpoint=True,
            pre_call=pre_call,
        )
        return normalize_tx_hash(tx_hash), endpoint

    def estimate_gas(
        self,
        tx_params: dict[str, Any],
        block_identifier: int | str = "latest",
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> int:
        return self.call(
            "eth_estimateGas",
            tx_params,
            timeout=timeout,
            deadline=deadline,
            block_identifier=block_identifier,
        )

    def eth_call(
        self,
        tx_params: dict[str, Any],
        block_identifier: int | str = "latest",
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> bytes:
        return self.call(
            "eth_call",
            tx_params,
            block_identifier,
            timeout=timeout,
            deadline=deadline,
        )

    def get_storage_at(
        self,
        address: str,
        slot: int,
        block_identifier: int | str = "latest",
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> bytes:
        return self.call(
            "eth_getStorageAt",
            address,
            slot,
            block_identifier,
            timeout=timeout,
            deadline=deadline,
        )

    def get_chain_id(self, timeout: float | None = None, deadline: Deadline | None = None) -> int:
        return self.call("eth_chainId", timeout=timeout, deadline=deadline)

    def get_gas_price(self, timeout: float | None = None, deadline: Deadline | None = None) -> int:
        return self.call("eth_gasPrice", timeout=timeout, deadline=deadline)

    def get_base_fee(
        self, timeout: float | None = None, deadline: Deadline | None = None
    ) -> int:
        block = self.get_block("latest", timeout=timeout, deadline=deadline)
        return int(block.get("baseFeePerGas", 0))

    def get_balance(
        self,
        address: str,
        block_identifier: int | str = "latest",
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> int:
        return self.call(
            "eth_getBalance",
            address,
            block_identifier,
            timeout=timeout,
            deadline=deadline,
        )

    def simulate_transaction(
        self,
        tx: dict[str, Any],
        rpc_url: str | None = None,
        timeout: float | None = None,
        deadline: Deadline | None = None,
    ) -> dict[str, Any]:
        if deadline is not None and deadline.expired():
            raise SimulationNetworkError("Simulation deadline exhausted")
        try:
            timeout = timeout or self._timeout
            if rpc_url:
                result = self._caller.call(
                    rpc_url,
                    "eth_call",
                    (tx, "latest"),
                    timeout=timeout,
                    deadline=deadline,
                    block_identifier="latest",
                )
            else:
                result = self.eth_call(tx, timeout=timeout, deadline=deadline)
            return {"success": True, "result": result.hex() if isinstance(result, bytes) else result}
        except Exception as exc:  # noqa: BLE001
            # RECOVERABLE simulation errors are surfaced as typed exceptions.
            revert_reason = self._parse_revert_reason(exc)
            if revert_reason:
                raise SimulationReverted(revert_reason) from exc
            log_unexpected(
                logger,
                "simulation.call_failed",
                error=str(exc)[:200],
            )
            raise SimulationNetworkError(str(exc)) from exc

    def _parse_revert_reason(self, error: Exception) -> str | None:
        error_str = str(error).lower()

        error_code = None
        if hasattr(error, "args"):
            for arg in error.args:
                if isinstance(arg, dict):
                    error_code = arg.get("code")
                    if error_code is None:
                        error_code = arg.get("error", {}).get("code")
                if error_code is not None:
                    break

        revert_error_codes = {-32000, -32015, 3}
        if error_code in revert_error_codes:
            return self._extract_revert_message(error)

        revert_keywords = [
            "execution reverted",
            "revert",
            "out of gas",
            "insufficient funds",
            "invalid opcode",
            "stack underflow",
            "stack overflow",
        ]
        if any(kw in error_str for kw in revert_keywords):
            return self._extract_revert_message(error)

        return None

    def _extract_revert_message(self, error: Exception) -> str:
        error_str = str(error)
        if "execution reverted:" in error_str.lower():
            idx = error_str.lower().find("execution reverted:")
            return error_str[idx + len("execution reverted:"):].strip() or "execution reverted"

        revert_data = self._extract_revert_data(error)
        if revert_data:
            decoded = self._decode_revert_data(revert_data)
            if decoded:
                return decoded

        clean_msg = error_str
        if len(clean_msg) > 200:
            clean_msg = clean_msg[:200] + "..."
        return clean_msg or "Transaction reverted"

    def _extract_revert_data(self, error: Exception) -> str | None:
        if hasattr(error, "args"):
            for arg in error.args:
                if isinstance(arg, dict):
                    data = arg.get("data")
                    if data is None:
                        data = arg.get("error", {}).get("data")
                    if isinstance(data, dict):
                        data = data.get("data") or data.get("result")
                    if isinstance(data, str) and data.startswith("0x"):
                        return data

        error_str = str(error)
        hex_match = re.search(r"0x[0-9a-fA-F]{8,}", error_str)
        if hex_match:
            return hex_match.group()

        return None

    def _decode_revert_data(self, data: str) -> str | None:
        if len(data) < 10:
            return None

        selector = data[:10]

        if selector == "0x08c379a0" and len(data) >= 138:
            try:
                from eth_abi import decode

                decoded = decode(["string"], bytes.fromhex(data[10:]))
                return decoded[0]
            except Exception as exc:  # noqa: BLE001
                # RECOVERABLE revert decode failures fall back to raw data.
                log_unexpected(
                    logger,
                    "rpc.revert_decode_failed",
                    selector=selector,
                    error=str(exc)[:200],
                )

        if selector == "0x4e487b71" and len(data) >= 74:
            try:
                from eth_abi import decode

                decoded = decode(["uint256"], bytes.fromhex(data[10:]))
                panic_code = decoded[0]
                panic_names = {
                    0x00: "generic panic",
                    0x01: "assertion failed",
                    0x11: "arithmetic overflow",
                    0x12: "division by zero",
                    0x21: "invalid enum value",
                    0x22: "storage encoding error",
                    0x31: "pop on empty array",
                    0x32: "array out of bounds",
                    0x41: "memory allocation error",
                    0x51: "zero function pointer",
                }
                return f"Panic({panic_code:#x}): {panic_names.get(panic_code, 'unknown')}"
            except Exception as exc:  # noqa: BLE001
                # RECOVERABLE revert decode failures fall back to raw data.
                log_unexpected(
                    logger,
                    "rpc.revert_decode_failed",
                    selector=selector,
                    error=str(exc)[:200],
                )

        if len(data) > 74:
            return f"Custom error {selector} ({len(data)//2 - 4} bytes)"
        if len(data) > 10:
            return f"Custom error {selector}"

        return None

    def get_health(self) -> dict[str, Any]:
        total = len(self._pool.endpoints)
        return {
            "endpoints": list(self._pool.endpoints),
            "healthy_endpoints": total,
            "total_endpoints": total,
            "all_unhealthy": total == 0,
        }

    def close(self) -> None:
        return None


class BroadcastClient(ReadClient):
    """Broadcast client with bound endpoint semantics."""

    def __init__(self, *args: Any, bound: bool = True, **kwargs: Any) -> None:
        super().__init__(*args, bound=bound, **kwargs)


def _default_request_id() -> str:
    from uuid import uuid4

    return uuid4().hex
