"""Approved HTTP client for job code with allowlist enforcement."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from brawny.logging import get_logger
from brawny.network_guard import allow_network_calls

logger = get_logger(__name__)

_RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class HttpConfig:
    """HTTP policy for job-originated requests."""

    allowed_domains: list[str] = field(default_factory=list)
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 10.0
    max_retries: int = 2
    backoff_base_seconds: float = 0.5


class ApprovedHttpClient:
    """HTTP client with retries, timeouts, and domain allowlist.

    Retries apply to GET/HEAD by default. Non-idempotent methods require
    explicit opt-in or an idempotency key.
    """

    def __init__(self, config: HttpConfig) -> None:
        self._config = config
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    @property
    def config(self) -> HttpConfig:
        return self._config

    def _is_allowed_host(self, host: str) -> bool:
        if not host:
            return False
        allowed = self._config.allowed_domains
        if not allowed:
            return False
        if "*" in allowed:
            return True
        host = host.lower().rstrip(".")
        try:
            import ipaddress

            ip = ipaddress.ip_address(host)
            return any(entry.strip().lower() == str(ip) for entry in allowed)
        except ValueError:
            pass
        for entry in allowed:
            entry = entry.lower().strip()
            if not entry:
                continue
            if entry.startswith("*."):
                suffix = entry[1:]
                if host.endswith(suffix):
                    return True
            elif entry.startswith("."):
                if host.endswith(entry):
                    return True
            elif host == entry:
                return True
        return False

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Only http/https URLs are allowed: {url}")
        host = parsed.hostname or ""
        if not self._is_allowed_host(host):
            raise ValueError(f"HTTP domain not allowed: {host or url}")

    def close(self) -> None:
        client = self._client
        self._client = None
        if client is not None:
            client.close()

    async def async_close(self) -> None:
        client = self._async_client
        self._async_client = None
        if client is not None:
            await client.aclose()

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout())
        return self._client

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self._timeout())
        return self._async_client

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        retry_non_idempotent: bool = False,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        self._validate_url(url)
        timeout = timeout or self._timeout()
        last_error: Exception | None = None
        attempts = max(0, self._config.max_retries) + 1
        method_upper = method.upper()
        allow_retry = method_upper in ("GET", "HEAD") or retry_non_idempotent or idempotency_key is not None
        headers = dict(kwargs.pop("headers", {}) or {})
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        kwargs["headers"] = headers

        for attempt in range(attempts):
            try:
                with allow_network_calls(reason="approved_http_client"):
                    client = self._get_client()
                    resp = client.request(method, url, timeout=timeout, **kwargs)
                if resp.status_code in _RETRY_STATUS and attempt < attempts - 1 and allow_retry:
                    self._sleep_backoff(attempt)
                    continue
                resp.raise_for_status()
                return resp
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt < attempts - 1 and allow_retry:
                    self._sleep_backoff(attempt)
                    continue
                raise
        if last_error:
            raise last_error
        raise RuntimeError("HTTP request failed without error")

    async def async_request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        retry_non_idempotent: bool = False,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        self._validate_url(url)
        timeout = timeout or self._timeout()
        last_error: Exception | None = None
        attempts = max(0, self._config.max_retries) + 1
        method_upper = method.upper()
        allow_retry = method_upper in ("GET", "HEAD") or retry_non_idempotent or idempotency_key is not None
        headers = dict(kwargs.pop("headers", {}) or {})
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        kwargs["headers"] = headers

        for attempt in range(attempts):
            try:
                with allow_network_calls(reason="approved_http_client"):
                    client = self._get_async_client()
                    resp = await client.request(method, url, timeout=timeout, **kwargs)
                if resp.status_code in _RETRY_STATUS and attempt < attempts - 1 and allow_retry:
                    await self._async_sleep_backoff(attempt)
                    continue
                resp.raise_for_status()
                return resp
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt < attempts - 1 and allow_retry:
                    await self._async_sleep_backoff(attempt)
                    continue
                raise
        if last_error:
            raise last_error
        raise RuntimeError("HTTP request failed without error")

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    async def async_get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.async_request("GET", url, **kwargs)

    async def async_post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.async_request("POST", url, **kwargs)

    def _sleep_backoff(self, attempt: int) -> None:
        delay = self._config.backoff_base_seconds * (2 ** attempt)
        time.sleep(delay)

    async def _async_sleep_backoff(self, attempt: int) -> None:
        import asyncio

        delay = self._config.backoff_base_seconds * (2 ** attempt)
        await asyncio.sleep(delay)

    def _timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            connect=self._config.connect_timeout_seconds,
            read=self._config.read_timeout_seconds,
            write=self._config.read_timeout_seconds,
            pool=self._config.connect_timeout_seconds,
        )
