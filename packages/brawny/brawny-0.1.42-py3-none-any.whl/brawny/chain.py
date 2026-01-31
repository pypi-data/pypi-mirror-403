"""Chain information singleton.

Usage:
    from brawny import chain

    chain.height             # Current block number
    chain[-1]                # Most recent block
    chain[0]                 # Genesis block
    chain.id                 # Chain ID
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from brawny._rpc.clients import ReadClient


_chain: "Chain | None" = None


class Chain:
    """Brownie-compatible chain interface.

    Provides access to block information and chain state.
    """

    def __init__(self, rpc: "ReadClient", chain_id: int) -> None:
        self._rpc = rpc
        self._chain_id = chain_id

    @property
    def height(self) -> int:
        """Current block number (same as brownie's chain.height)."""
        return self._rpc.get_block_number()

    @property
    def id(self) -> int:
        """Chain ID."""
        return self._chain_id

    def __getitem__(self, index: int) -> dict[str, Any]:
        """Get block by number. Supports negative indexing like brownie.

        Example:
            >>> chain[-1]  # most recent block
            >>> chain[0]   # genesis block
        """
        if index < 0:
            index = self.height + index + 1
        return self._rpc.get_block(index)

    def __repr__(self) -> str:
        return f"<Chain id={self._chain_id} height={self.height}>"


def _init_chain(rpc: "ReadClient", chain_id: int) -> None:
    """Initialize global chain singleton."""
    global _chain
    _chain = Chain(rpc, chain_id)


def _get_chain() -> Chain:
    """Get chain singleton."""
    if _chain is None:
        raise RuntimeError(
            "Chain not initialized. Run within script context."
        )
    return _chain


# Proxy for import-time access
class _ChainProxy:
    """Proxy that delegates to chain singleton."""

    @property
    def height(self) -> int:
        return _get_chain().height

    @property
    def id(self) -> int:
        return _get_chain().id

    def __getitem__(self, index: int) -> dict[str, Any]:
        return _get_chain()[index]

    def __repr__(self) -> str:
        return repr(_get_chain())


# Global proxy instance
chain = _ChainProxy()
