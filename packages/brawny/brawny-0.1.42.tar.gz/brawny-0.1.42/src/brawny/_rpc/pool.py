from __future__ import annotations


class EndpointPool:
    """Endpoint pool with deterministic ordering only."""

    def __init__(self, endpoints: list[str]) -> None:
        cleaned = [ep.strip() for ep in endpoints if ep and ep.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty endpoint is required")
        self._endpoints = cleaned

    @property
    def endpoints(self) -> list[str]:
        return list(self._endpoints)

    def order_endpoints(self) -> list[str]:
        return list(self._endpoints)
