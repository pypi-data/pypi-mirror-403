from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from brawny.model.enums import AttemptStatus, IntentStatus, NonceStatus
from brawny.model.types import (
    GasParams,
    JobConfig,
    NonceReservation,
    RuntimeControl,
    SignerState,
    TxAttempt,
    TxIntent,
)
from brawny.types import ClaimedIntent
from brawny.utils import db_address


def adapt_datetime(dt: datetime) -> str:
    """Adapt datetime to ISO format string for SQLite."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def convert_datetime(val: bytes) -> datetime:
    """Convert ISO format string from SQLite to datetime."""
    s = val.decode("utf-8")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def parse_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(value)


def dump_uuid(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def parse_json(raw: Any, default: Any | None = None) -> Any:
    if raw is None:
        return default
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


def parse_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def canonicalize_address(address: str) -> str:
    return db_address(address)


def _row_to_job_config(row: dict[str, Any]) -> JobConfig:
    return JobConfig(
        job_id=row["job_id"],
        job_name=row["job_name"],
        enabled=bool(row["enabled"]),
        check_interval_blocks=row["check_interval_blocks"],
        last_checked_block_number=row["last_checked_block_number"],
        last_triggered_block_number=row["last_triggered_block_number"],
        drain_until=row.get("drain_until"),
        drain_reason=row.get("drain_reason"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_signer_state(row: dict[str, Any]) -> SignerState:
    return SignerState(
        chain_id=row["chain_id"],
        signer_address=row["signer_address"],
        next_nonce=row["next_nonce"],
        last_synced_chain_nonce=row["last_synced_chain_nonce"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        gap_started_at=row.get("gap_started_at"),
        alias=row.get("alias"),
        quarantined_at=row.get("quarantined_at"),
        quarantine_reason=row.get("quarantine_reason"),
        replacements_paused=bool(row.get("replacements_paused", 0)),
    )


def _row_to_runtime_control(row: dict[str, Any]) -> RuntimeControl:
    return RuntimeControl(
        control=row["control"],
        active=bool(row["active"]),
        expires_at=parse_datetime(row.get("expires_at")),
        reason=row.get("reason"),
        actor=row.get("actor"),
        mode=row.get("mode") or "auto",
        updated_at=row["updated_at"],
    )


def _row_to_nonce_reservation(row: dict[str, Any]) -> NonceReservation:
    return NonceReservation(
        id=row["id"],
        chain_id=row["chain_id"],
        signer_address=row["signer_address"],
        nonce=row["nonce"],
        status=NonceStatus(row["status"]),
        intent_id=parse_uuid(row["intent_id"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_intent(row: dict[str, Any]) -> TxIntent:
    metadata = parse_json(row.get("metadata_json"), default={})
    return TxIntent(
        intent_id=parse_uuid(row["intent_id"]),
        job_id=row["job_id"],
        chain_id=row["chain_id"],
        signer_address=row["signer_address"],
        signer_alias=row.get("signer_alias"),
        idempotency_key=row["idempotency_key"],
        to_address=row["to_address"],
        data=row["data"],
        value_wei=row["value_wei"],
        gas_limit=row["gas_limit"],
        max_fee_per_gas=row["max_fee_per_gas"],
        max_priority_fee_per_gas=row["max_priority_fee_per_gas"],
        min_confirmations=row["min_confirmations"],
        deadline_ts=row["deadline_ts"],
        retry_after=row["retry_after"],
        retry_count=row.get("retry_count", 0),
        status=IntentStatus(row["status"]),
        claim_token=row["claim_token"],
        claimed_at=row["claimed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        claimed_by=row.get("claimed_by"),
        lease_expires_at=row.get("lease_expires_at"),
        broadcast_group=row.get("broadcast_group"),
        broadcast_endpoints_json=row.get("broadcast_endpoints_json"),
        broadcast_binding_id=parse_uuid(row.get("broadcast_binding_id")),
        metadata=metadata,
        terminal_reason=row.get("terminal_reason"),
        halt_reason=row.get("halt_reason"),
    )


def _row_to_claimed_intent(row: dict[str, Any]) -> ClaimedIntent:
    return ClaimedIntent(
        intent_id=parse_uuid(row["intent_id"]),
        claim_token=row["claim_token"],
        claimed_by=row.get("claimed_by"),
        lease_expires_at=row.get("lease_expires_at"),
        claimed_at=row["claimed_at"],
    )


def _row_to_attempt(row: dict[str, Any]) -> TxAttempt:
    return TxAttempt(
        attempt_id=parse_uuid(row["attempt_id"]),
        intent_id=parse_uuid(row["intent_id"]),
        nonce=row["nonce"],
        tx_hash=row["tx_hash"],
        gas_params=GasParams.from_json(row["gas_params_json"]),
        status=AttemptStatus(row["status"]),
        error_code=row["error_code"],
        error_detail=row["error_detail"],
        replaces_attempt_id=parse_uuid(row.get("replaces_attempt_id")),
        broadcast_block=row["broadcast_block"],
        broadcast_at=row.get("broadcast_at"),
        included_block=row.get("included_block"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        broadcast_group=row.get("broadcast_group"),
        endpoint_url=row.get("endpoint_url"),
        endpoint_binding_id=parse_uuid(row.get("endpoint_binding_id")),
    )
