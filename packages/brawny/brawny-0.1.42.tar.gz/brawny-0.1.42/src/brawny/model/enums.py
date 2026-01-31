"""Enumerations for brawny statuses and states."""

from enum import Enum

from brawny.logging_types import LogFormat


class IntentStatus(str, Enum):
    """Transaction intent status."""

    CREATED = "created"
    CLAIMED = "claimed"
    BROADCASTED = "broadcasted"
    TERMINAL = "terminal"


class IntentTerminalReason(str, Enum):
    """Terminal reason for a completed intent."""

    CONFIRMED = "confirmed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class AttemptStatus(str, Enum):
    """Transaction attempt status."""

    SIGNED = "signed"
    PENDING_SEND = "pending_send"
    BROADCAST = "broadcast"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REPLACED = "replaced"


class NonceStatus(str, Enum):
    """Nonce reservation status."""

    RESERVED = "reserved"
    IN_FLIGHT = "in_flight"
    RELEASED = "released"
    ORPHANED = "orphaned"


class TxStatus(str, Enum):
    """Transaction lifecycle status. 4 states only.

    IMPORTANT: Do not add new statuses. This enum is intentionally minimal.
    """

    CREATED = "created"      # Exists, not yet broadcast
    BROADCAST = "broadcast"  # Has current_tx_hash, awaiting confirmation
    CONFIRMED = "confirmed"  # Terminal: receipt status=1
    FAILED = "failed"        # Terminal: permanent failure


class ABISource(str, Enum):
    """Source of ABI data."""

    ETHERSCAN = "etherscan"
    SOURCIFY = "sourcify"
    MANUAL = "manual"
    PROXY_IMPLEMENTATION = "proxy_implementation"


class KeystoreType(str, Enum):
    """Keystore type for private key management."""

    ENV = "env"
    FILE = "file"
