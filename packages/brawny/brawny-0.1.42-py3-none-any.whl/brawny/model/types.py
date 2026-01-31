"""Core data types and dataclasses for brawny."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

# JSON-serializable value type for metadata
JSONValue = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]

# Hook names for type-safe dispatch
HookName = Literal["on_trigger", "on_success", "on_failure"]

from brawny.model.enums import AttemptStatus, IntentStatus, NonceStatus


def to_wei(value: int | float | str) -> int:
    """Convert a value to wei as an integer.

    Safely handles:
    - int: returned as-is
    - float: converted if whole number (e.g., 1e18, 10e18)
    - str: parsed as int first, then as float if needed

    Note on float precision:
        Float64 can only exactly represent integers up to 2^53 (~9e15).
        Wei values (1e18+) exceed this, but common values like 1e18, 10e18,
        1.5e18 convert correctly. For guaranteed precision with unusual
        values, use integer strings: "10000000000000000001"

    Raises:
        ValueError: if value has a fractional part (can't have 0.5 wei)
        TypeError: if value is not int, float, or str

    Examples:
        >>> to_wei(1000000000000000000)
        1000000000000000000
        >>> to_wei(1e18)
        1000000000000000000
        >>> to_wei(10e18)
        10000000000000000000
        >>> to_wei("1000000000000000000")
        1000000000000000000
        >>> to_wei(1.5e18)  # 1.5 * 10^18 is a whole number of wei
        1500000000000000000
        >>> to_wei(1.5)  # Raises ValueError - can't have 0.5 wei
        ValueError: Wei value must be a whole number, got 1.5
    """
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return 0
        # Try parsing as int first (handles "123", "-456")
        try:
            return int(value)
        except ValueError:
            pass
        # Try parsing as float (handles "1e18", "1.5e18")
        try:
            value = float(value)
        except ValueError:
            raise ValueError(f"Cannot parse '{value}' as a number")

    if not isinstance(value, float):
        raise TypeError(f"Expected int, float, or str, got {type(value).__name__}")

    if not math.isfinite(value):
        raise ValueError(f"Invalid wei value: {value} (must be finite)")

    # Check for fractional part using modulo
    # This correctly identifies 1.5 as fractional but 1.5e18 as whole
    remainder = value % 1
    if remainder != 0:
        raise ValueError(
            f"Wei value must be a whole number, got {value} "
            f"(fractional part: {remainder})"
        )

    return int(value)


@dataclass(frozen=True)
class BlockInfo:
    """Information about a specific block."""

    chain_id: int
    block_number: int
    block_hash: str
    timestamp: int
    base_fee: int = 0

    def __post_init__(self) -> None:
        if not self.block_hash.startswith("0x"):
            object.__setattr__(self, "block_hash", f"0x{self.block_hash}")
        base_fee = self.base_fee
        if base_fee is None:
            base_fee = 0
        elif isinstance(base_fee, str):
            base_fee = int(base_fee, 16) if base_fee.startswith("0x") else int(base_fee)
        else:
            base_fee = int(base_fee)
        object.__setattr__(self, "base_fee", base_fee)


@dataclass
class Trigger:
    """Result of a job check indicating action needed.

    Note: trigger.reason is auto-stamped into intent.metadata["reason"].
    Use intent(..., metadata={}) for per-intent context for alerts.
    """

    reason: str
    tx_required: bool = True
    idempotency_parts: list[str | int | bytes] = field(default_factory=list)


@dataclass
class TxIntentSpec:
    """Specification for creating a transaction intent."""

    signer_address: str
    to_address: str
    data: str | None = None
    value_wei: str = "0"
    gas_limit: int | None = None
    max_fee_per_gas: int | None = None
    max_priority_fee_per_gas: int | None = None
    min_confirmations: int = 1
    deadline_seconds: int | None = None
    metadata: dict[str, JSONValue] | None = None  # Per-intent context for alerts


@dataclass
class TxIntent:
    """Persisted transaction intent record."""

    intent_id: UUID
    job_id: str
    chain_id: int
    signer_address: str
    idempotency_key: str
    to_address: str
    data: str | None
    value_wei: str
    gas_limit: int | None
    max_fee_per_gas: str | None
    max_priority_fee_per_gas: str | None
    min_confirmations: int
    deadline_ts: datetime | None
    retry_after: datetime | None
    status: IntentStatus
    claim_token: str | None
    claimed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    claimed_by: str | None = None
    lease_expires_at: datetime | None = None
    signer_alias: str | None = None
    retry_count: int = 0

    # Broadcast binding (set on first successful broadcast)
    # These fields preserve the privacy invariant: retries use the SAME endpoints
    broadcast_group: str | None = None
    broadcast_endpoints_json: str | None = None
    broadcast_binding_id: UUID | None = None

    # Per-intent context for alerts (parsed dict, not JSON string)
    metadata: dict[str, JSONValue] = field(default_factory=dict)

    # Terminal and halt reasons (nullable; terminal_finality is derived)
    terminal_reason: str | None = None
    halt_reason: str | None = None


@dataclass
class GasParams:
    """Gas parameters for a transaction."""

    gas_limit: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int

    def __post_init__(self) -> None:
        """Validate gas parameters are non-negative."""
        def _coerce_int(value: int | float | str) -> int:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    from decimal import Decimal

                    return int(Decimal(value))
            return int(value)

        self.gas_limit = _coerce_int(self.gas_limit)
        self.max_fee_per_gas = _coerce_int(self.max_fee_per_gas)
        self.max_priority_fee_per_gas = _coerce_int(self.max_priority_fee_per_gas)
        if self.gas_limit < 0:
            raise ValueError(f"gas_limit must be non-negative, got {self.gas_limit}")
        if self.max_fee_per_gas < 0:
            raise ValueError(f"max_fee_per_gas must be non-negative, got {self.max_fee_per_gas}")
        if self.max_priority_fee_per_gas < 0:
            raise ValueError(f"max_priority_fee_per_gas must be non-negative, got {self.max_priority_fee_per_gas}")

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "gas_limit": self.gas_limit,
            "max_fee_per_gas": str(self.max_fee_per_gas),
            "max_priority_fee_per_gas": str(self.max_priority_fee_per_gas),
        })

    @classmethod
    def from_json(cls, data: str) -> GasParams:
        """Deserialize from JSON string."""
        parsed = json.loads(data)
        return cls(
            gas_limit=parsed["gas_limit"],
            max_fee_per_gas=parsed["max_fee_per_gas"],
            max_priority_fee_per_gas=parsed["max_priority_fee_per_gas"],
        )


@dataclass
class TxAttempt:
    """Persisted transaction attempt record."""

    attempt_id: UUID
    intent_id: UUID
    nonce: int
    tx_hash: str | None
    gas_params: GasParams
    status: AttemptStatus
    error_code: str | None
    error_detail: str | None
    replaces_attempt_id: UUID | None
    broadcast_block: int | None
    broadcast_at: datetime | None
    included_block: int | None
    created_at: datetime
    updated_at: datetime

    # Audit trail (which group and endpoint were used for this attempt)
    broadcast_group: str | None = None
    endpoint_url: str | None = None
    endpoint_binding_id: UUID | None = None


@dataclass
class BroadcastInfo:
    """Broadcast binding information (privacy invariant).

    Preserves which RPC group/endpoints were used for first broadcast.
    Retries MUST use the same endpoints to prevent privacy leaks.
    """

    group: str | None
    endpoints: list[str] | None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "group": self.group,
            "endpoints": self.endpoints,
        })

    @classmethod
    def from_json(cls, data: str | None) -> "BroadcastInfo | None":
        """Deserialize from JSON string."""
        if data is None:
            return None
        parsed = json.loads(data)
        return cls(
            group=parsed.get("group"),
            endpoints=parsed.get("endpoints"),
        )


@dataclass
class NonceReservation:
    """Nonce reservation record."""

    id: int
    chain_id: int
    signer_address: str
    nonce: int
    status: NonceStatus
    intent_id: UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass
class SignerState:
    """Signer nonce tracking state."""

    chain_id: int
    signer_address: str
    next_nonce: int
    last_synced_chain_nonce: int | None
    created_at: datetime
    updated_at: datetime
    gap_started_at: datetime | None = None  # When nonce gap blocking started (for alerts)
    alias: str | None = None  # Optional human-readable alias
    quarantined_at: datetime | None = None
    quarantine_reason: str | None = None
    replacements_paused: bool = False


@dataclass
class RuntimeControl:
    """Runtime containment control with TTL."""

    control: str
    active: bool
    expires_at: datetime | None
    reason: str | None
    actor: str | None
    mode: str
    updated_at: datetime


@dataclass
class MutationAudit:
    """Durable mutation audit record."""

    entity_type: str
    entity_id: str
    action: str
    actor: str | None
    reason: str | None
    source: str | None
    metadata_json: str | None
    created_at: datetime


@dataclass
class JobConfig:
    """Job configuration from database."""

    job_id: str
    job_name: str
    enabled: bool
    check_interval_blocks: int
    last_checked_block_number: int | None
    last_triggered_block_number: int | None
    drain_until: datetime | None
    drain_reason: str | None
    created_at: datetime
    updated_at: datetime


def idempotency_key(job_id: str, *parts: str | int | bytes) -> str:
    """
    Generate a stable, deterministic idempotency key.

    Format: {job_id}:{hash}

    Rules:
    - bytes are hex-encoded (lowercase, no 0x prefix)
    - ints are decimal string-encoded
    - dicts are sorted by key before serialization
    - hash is SHA256, truncated to 16 hex chars

    Example:
        >>> idempotency_key("vault_deposit", "0xabc...", 42)
        "vault_deposit:a1b2c3d4e5f6g7h8"
    """
    normalized_parts: list[str] = []

    for part in parts:
        if isinstance(part, bytes):
            normalized_parts.append(part.hex())
        elif isinstance(part, int):
            normalized_parts.append(str(part))
        elif isinstance(part, dict):
            normalized_parts.append(json.dumps(part, sort_keys=True, separators=(",", ":")))
        elif isinstance(part, str):
            # Remove 0x prefix if present for consistency
            if part.startswith("0x"):
                normalized_parts.append(part[2:].lower())
            else:
                normalized_parts.append(part)
        else:
            normalized_parts.append(str(part))

    combined = ":".join(normalized_parts)
    hash_bytes = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]

    return f"{job_id}:{hash_bytes}"
