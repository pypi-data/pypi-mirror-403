"""Transaction history tracking.

Usage:
    from brawny import history

    history[-1]                    # Last transaction
    history.filter(sender="0x...")  # Filter by attribute
    len(history)                   # Count
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterator

if TYPE_CHECKING:
    from brawny.jobs.base import TxReceipt


_history: "TxHistory | None" = None


class TxHistory:
    """Container for transaction receipts in current session.

    Brownie-compatible interface for tracking transactions.
    Note: Scripts are single-threaded, so no locking is needed.
    """

    def __init__(self) -> None:
        self._receipts: list["TxReceipt"] = []

    def _add(self, receipt: "TxReceipt") -> None:
        """Add receipt to history (internal use)."""
        self._receipts.append(receipt)

    def __getitem__(self, index: int) -> "TxReceipt":
        return self._receipts[index]

    def __len__(self) -> int:
        return len(self._receipts)

    def __iter__(self) -> Iterator["TxReceipt"]:
        return iter(self._receipts)

    def filter(
        self,
        key: Callable[["TxReceipt"], bool] | None = None,
        **kwargs: Any,
    ) -> list["TxReceipt"]:
        """Filter transactions by attribute or function.

        Args:
            key: Optional filter function
            **kwargs: Attribute filters (e.g., sender="0x...")

        Returns:
            List of matching receipts
        """
        results = list(self._receipts)

        if key:
            results = [r for r in results if key(r)]

        for attr, value in kwargs.items():
            results = [r for r in results if getattr(r, attr, None) == value]

        return results

    def clear(self) -> None:
        """Clear transaction history."""
        self._receipts.clear()

    def copy(self) -> list["TxReceipt"]:
        """Get copy of receipts as list."""
        return list(self._receipts)

    def __repr__(self) -> str:
        return f"<TxHistory [{len(self)} txs]>"


def _init_history() -> None:
    """Initialize global history singleton."""
    global _history
    _history = TxHistory()


def _get_history() -> TxHistory:
    """Get history singleton."""
    if _history is None:
        _init_history()
    return _history


def _add_to_history(receipt: "TxReceipt") -> None:
    """Add receipt to global history."""
    _get_history()._add(receipt)


# Proxy for import-time access
class _HistoryProxy:
    """Proxy that delegates to history singleton."""

    def __getitem__(self, index: int) -> "TxReceipt":
        return _get_history()[index]

    def __len__(self) -> int:
        return len(_get_history())

    def __iter__(self) -> Iterator["TxReceipt"]:
        return iter(_get_history())

    def filter(self, key: Callable | None = None, **kwargs: Any) -> list["TxReceipt"]:
        return _get_history().filter(key, **kwargs)

    def clear(self) -> None:
        _get_history().clear()

    def copy(self) -> list["TxReceipt"]:
        return _get_history().copy()

    def __repr__(self) -> str:
        return repr(_get_history())


# Global proxy instance
history = _HistoryProxy()
