from __future__ import annotations

import threading
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit
from web3 import Web3
from web3.exceptions import TransactionNotFound

from brawny.logging import get_logger
from brawny.metrics import RPC_SESSION_POOL_SIZE, get_metrics
from brawny.network_guard import allow_network_calls

logger = get_logger(__name__)

def _extract_url_auth(url: str) -> tuple[str, tuple[str, str] | None]:
    split = urlsplit(url)
    if split.username or split.password:
        auth = (split.username or "", split.password or "")
        clean_netloc = split.hostname or ""
        if split.port:
            clean_netloc = f"{clean_netloc}:{split.port}"
        clean_url = urlunsplit((split.scheme, clean_netloc, split.path, split.query, split.fragment))
        return clean_url, auth
    return url, None

class RpcTransport:
    """Owns RPC HTTP sessions and executes JSON-RPC calls."""

    def __init__(self, endpoints: list[str], timeout_seconds: float) -> None:
        self._default_timeout = timeout_seconds
        self._web3_instances: dict[str, Web3] = {}
        self._locks: dict[str, threading.Lock] = {}
        for endpoint in endpoints:
            clean_url, auth = _extract_url_auth(endpoint)
            request_kwargs: dict[str, Any] = {"timeout": timeout_seconds}
            if auth:
                request_kwargs["auth"] = auth
            self._web3_instances[endpoint] = Web3(
                Web3.HTTPProvider(clean_url, request_kwargs=request_kwargs)
            )
            self._locks[endpoint] = threading.Lock()

        metrics = get_metrics()
        metrics.gauge(RPC_SESSION_POOL_SIZE).set(len(self._web3_instances))

    def session_pool_size(self) -> int:
        return len(self._web3_instances)

    def get_web3(self, endpoint_url: str) -> Web3:
        return self._web3_instances[endpoint_url]

    def call(
        self,
        endpoint_url: str,
        method: str,
        args: tuple[Any, ...],
        *,
        timeout: float,
        block_identifier: int | str,
    ) -> Any:
        w3 = self.get_web3(endpoint_url)
        return self._with_timeout(
            endpoint_url,
            timeout,
            lambda: self._execute_method(w3, method, args, block_identifier),
        )

    def call_with_web3(
        self,
        endpoint_url: str,
        *,
        timeout: float,
        fn: Callable[[Web3], Any],
    ) -> Any:
        w3 = self.get_web3(endpoint_url)
        return self._with_timeout(endpoint_url, timeout, lambda: fn(w3))

    def _with_timeout(
        self,
        endpoint_url: str,
        timeout: float,
        fn: Callable[[], Any],
    ) -> Any:
        lock = self._locks[endpoint_url]
        # Timeout mutation is not concurrency-safe; serialize per-endpoint calls.
        with lock:
            provider = self._web3_instances[endpoint_url].provider
            if not hasattr(provider, "_request_kwargs"):
                logger.error(
                    "rpc.transport.missing_request_kwargs",
                    endpoint=endpoint_url,
                )
                raise RuntimeError("RPC provider does not expose request kwargs for timeouts")
            request_kwargs = provider._request_kwargs
            if not isinstance(request_kwargs, dict):
                logger.error(
                    "rpc.transport.invalid_request_kwargs",
                    endpoint=endpoint_url,
                )
                raise RuntimeError("RPC provider request kwargs must be a dict")
            request_kwargs["timeout"] = timeout
            with allow_network_calls(reason="rpc"):
                return fn()

    @staticmethod
    def _execute_method(
        w3: Web3,
        method: str,
        args: tuple[Any, ...],
        block_identifier: int | str,
    ) -> Any:
        if method == "eth_blockNumber":
            return w3.eth.block_number
        if method == "eth_getBlockByNumber":
            block_num = args[0] if args else "latest"
            full_tx = args[1] if len(args) > 1 else False
            return w3.eth.get_block(block_num, full_transactions=full_tx)
        if method == "eth_getTransactionCount":
            address = args[0]
            block = args[1] if len(args) > 1 else "pending"
            return w3.eth.get_transaction_count(address, block)
        if method == "eth_getTransactionReceipt":
            tx_hash = args[0]
            try:
                return w3.eth.get_transaction_receipt(tx_hash)
            except TransactionNotFound:
                return None
        if method == "eth_sendRawTransaction":
            return w3.eth.send_raw_transaction(args[0])
        if method == "eth_estimateGas":
            return w3.eth.estimate_gas(args[0], block_identifier=block_identifier)
        if method == "eth_call":
            tx = args[0]
            block = args[1] if len(args) > 1 else block_identifier
            return w3.eth.call(tx, block_identifier=block)
        if method == "eth_getStorageAt":
            address = args[0]
            slot = args[1]
            block = args[2] if len(args) > 2 else block_identifier
            return w3.eth.get_storage_at(address, slot, block_identifier=block)
        if method == "eth_chainId":
            return w3.eth.chain_id
        if method == "eth_gasPrice":
            return w3.eth.gas_price
        if method == "eth_getBalance":
            address = args[0]
            block = args[1] if len(args) > 1 else block_identifier
            return w3.eth.get_balance(address, block_identifier=block)
        return w3.provider.make_request(method, list(args))
