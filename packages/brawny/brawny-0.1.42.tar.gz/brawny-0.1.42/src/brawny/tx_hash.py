"""Helpers for transaction hash normalization."""

from __future__ import annotations

from typing import Any


def normalize_tx_hash(tx_hash: Any) -> str | None:
    """Normalize tx hash to 0x-prefixed hex string where possible."""
    if tx_hash is None:
        return None
    if isinstance(tx_hash, (bytes, bytearray)):
        return f"0x{bytes(tx_hash).hex()}"
    if isinstance(tx_hash, str) and (tx_hash.startswith("b'") or tx_hash.startswith('b"')):
        try:
            import ast

            value = ast.literal_eval(tx_hash)
            if isinstance(value, (bytes, bytearray)):
                return f"0x{bytes(value).hex()}"
        except (SyntaxError, ValueError):
            pass
    return str(tx_hash)
