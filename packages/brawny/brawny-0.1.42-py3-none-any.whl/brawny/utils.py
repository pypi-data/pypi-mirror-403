"""Utility functions for brawny.

Provides shared helpers for address normalization, datetime handling, and other
common operations used across the codebase.
"""

from __future__ import annotations

from datetime import datetime, timezone

from web3 import Web3


# =============================================================================
# Address Normalization
# =============================================================================

def normalize_address(address: str) -> str:
    """Normalize Ethereum address to lowercase for storage.

    All addresses should be stored lowercase in the database to ensure
    consistent lookups and comparisons.

    Args:
        address: Ethereum address (any case)

    Returns:
        Lowercase address

    Example:
        >>> normalize_address("0xABC123...")
        "0xabc123..."
    """
    return address.lower()


def db_address(address: str) -> str:
    """Canonicalize address for database storage and comparisons.

    Enforces 0x-prefixed, 40-hex format and returns lowercase.
    """
    if not is_valid_address(address):
        raise ValueError(f"Invalid address: {address}")
    return address.lower()


def checksum_address(address: str) -> str:
    """Convert address to checksum format for RPC calls.

    EIP-55 checksum addresses are required by web3.py for RPC calls
    and provide error detection for typos.

    Args:
        address: Ethereum address (any case)

    Returns:
        Checksummed address

    Raises:
        ValueError: If address is invalid

    Example:
        >>> checksum_address("0xabc123...")
        "0xABC123..."
    """
    return Web3.to_checksum_address(address)


def addresses_equal(a: str, b: str) -> bool:
    """Compare two addresses case-insensitively.

    Args:
        a: First address
        b: Second address

    Returns:
        True if addresses are equal (ignoring case)

    Example:
        >>> addresses_equal("0xABC", "0xabc")
        True
    """
    return a.lower() == b.lower()


def is_valid_address(address: str) -> bool:
    """Check if string is a valid Ethereum address.

    Args:
        address: String to check

    Returns:
        True if valid 40-char hex address with 0x prefix

    Example:
        >>> is_valid_address("0x" + "a" * 40)
        True
        >>> is_valid_address("not an address")
        False
    """
    if not address or not address.startswith("0x"):
        return False
    try:
        # web3 validation
        Web3.to_checksum_address(address)
        return True
    except ValueError:
        return False


# =============================================================================
# Datetime Utilities
# =============================================================================

def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime.

    Returns:
        Current time in UTC with tzinfo set

    Example:
        >>> utc_now().tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is timezone-aware UTC.

    Handles both naive datetimes (assumed UTC) and timezone-aware datetimes
    (converted to UTC).

    Args:
        dt: Datetime to normalize, or None

    Returns:
        UTC datetime with tzinfo, or None if input was None

    Example:
        >>> ensure_utc(datetime(2024, 1, 1))  # naive
        datetime(2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive datetimes are UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_expired(deadline: datetime | None) -> bool:
    """Check if a deadline has passed.

    Handles None deadlines (never expires), timezone-naive deadlines
    (assumed UTC), and timezone-aware deadlines.

    Args:
        deadline: Deadline datetime, or None for no deadline

    Returns:
        True if deadline has passed, False if deadline is None or in future

    Example:
        >>> is_expired(None)
        False
        >>> is_expired(datetime(2020, 1, 1))
        True
    """
    if deadline is None:
        return False
    return utc_now() > ensure_utc(deadline)


def seconds_until(deadline: datetime | None) -> float | None:
    """Get seconds until a deadline.

    Args:
        deadline: Deadline datetime, or None

    Returns:
        Seconds until deadline (negative if passed), or None if no deadline

    Example:
        >>> seconds_until(utc_now() + timedelta(seconds=60))
        ~60.0
    """
    if deadline is None:
        return None
    deadline_utc = ensure_utc(deadline)
    return (deadline_utc - utc_now()).total_seconds()


# =============================================================================
# String Utilities
# =============================================================================

def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append if truncated

    Returns:
        Truncated text with suffix, or original if within limit

    Example:
        >>> truncate("hello world", 8)
        "hello..."
    """
    if len(text) <= max_length:
        return text
    if max_length <= len(suffix):
        return text[:max_length]
    return text[: max_length - len(suffix)] + suffix


# =============================================================================
# Error Utilities
# =============================================================================

def serialize_error(e: BaseException) -> dict[str, object]:
    """Serialize an exception into JSON-safe fields."""
    message = str(e) or repr(e)
    payload: dict[str, object] = {
        "exc_type": e.__class__.__name__,
        "error": message,
    }
    error_code = getattr(e, "error_code", None)
    if error_code is not None:
        payload["error_code"] = error_code
    code = getattr(e, "code", None)
    if code is not None:
        payload["rpc_code"] = code
    http_status = getattr(e, "status_code", None)
    if http_status is not None:
        payload["http_status"] = http_status
    response = getattr(e, "response", None)
    if response is not None:
        status = getattr(response, "status_code", None)
        if status is not None:
            payload.setdefault("http_status", status)
    return payload
    return text[: max_length - len(suffix)] + suffix
