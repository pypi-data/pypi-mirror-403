"""SQLite database implementation for brawny.

SQLite is the supported production backend for this deployment model.

Key characteristics:
- Uses IMMEDIATE transaction mode for nonce reservation (app-level locking)
- Uses deterministic ordering with secondary sort for intent claiming
- No connection pooling (single connection)
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator
from uuid import UUID

from brawny.db.base import (
    ABICacheEntry,
    BlockHashEntry,
    BlockState,
    Database,
    IsolationLevel,
    ProxyCacheEntry,
)
from brawny.db.circuit_breaker import DatabaseCircuitBreaker
from brawny.logging import get_logger
from brawny.model.errors import DatabaseError
from brawny.model.types import (
    JobConfig,
    NonceReservation,
    RuntimeControl,
    SignerState,
    TxAttempt,
    TxIntent,
)
from brawny.types import ClaimedIntent
from brawny.config.validation import InvalidEndpointError, canonicalize_endpoints
from . import connection, execute as sqlite_execute, mappers, tx
from .repos import attempts as attempts_repo
from .repos import block_state as block_state_repo
from .repos import cache as cache_repo
from .repos import intents as intents_repo
from .repos import jobs as jobs_repo
from .repos import maintenance as maintenance_repo
from .repos import signers_nonces as signers_nonces_repo
from .connection import fcntl
from .tx import SQLiteBeginMode, _resolve_begin_cmd


# Register adapters
sqlite3.register_adapter(datetime, mappers.adapt_datetime)
sqlite3.register_converter("TIMESTAMP", mappers.convert_datetime)

logger = get_logger(__name__)
_warned_generic_isolation = False


class SQLiteDatabase(Database):
    """SQLite implementation of the Database interface.

    Thread-safety: Uses a per-thread connection model with a shared lock
    for transaction isolation.
    """

    def __init__(
        self,
        database_path: str,
        circuit_breaker_failures: int = 5,
        circuit_breaker_seconds: int = 30,
        production: bool = False,
        read_only: bool = False,
    ) -> None:
        """Initialize SQLite database.

        Args:
            database_path: Path to SQLite database file (or :memory:)
            circuit_breaker_failures: Failures before opening breaker
            circuit_breaker_seconds: Seconds to keep breaker open
        """
        # Remove sqlite:/// prefix if present
        if database_path.startswith("sqlite:///"):
            database_path = database_path[10:]

        self._database_path = database_path
        if not isinstance(production, bool):
            raise ValueError("production must be a boolean")
        self._production = production
        if not isinstance(read_only, bool):
            raise ValueError("read_only must be a boolean")
        self._read_only = read_only
        self._thread_local = threading.local()
        self._conns: dict[int, dict[str, Any]] = {}
        self._conns_lock = threading.RLock()
        self._connected = False
        self._closed = False
        self._conn_generation = 0
        self._memory_owner_thread_id: int | None = None
        self._warned_other_thread_conns = False
        self._lock_handle: Any | None = None
        self._lock_path: Path | None = None
        self._lock = threading.RLock()
        self._tx_depth = 0
        self._tx_failed = False
        self._version_checked = False
        self._circuit_breaker = DatabaseCircuitBreaker(
            failure_threshold=circuit_breaker_failures,
            open_seconds=circuit_breaker_seconds,
            backend="sqlite",
        )

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._lock:
            yield

    @property
    def dialect(self) -> str:
        """Return dialect name for query selection."""
        return "sqlite"

    def connect(self) -> None:
        """Establish database connection."""
        connection.connect(self)

    def close(self) -> None:
        """Close database connection."""
        connection.close(self)

    def is_connected(self) -> bool:
        """Check if database is connected."""
        return connection.is_connected(self)

    def _ensure_connected(self) -> sqlite3.Connection:
        """Ensure connection exists and return it."""
        with self._locked():
            return connection.ensure_connected(self)

    def _normalize_address(self, address: str) -> str:
        return mappers.canonicalize_address(address)

    def _canonicalize_endpoints(self, endpoints: list[str]) -> list[str]:
        try:
            return canonicalize_endpoints(endpoints)
        except InvalidEndpointError as exc:
            raise DatabaseError(f"Invalid endpoint(s): {exc}") from exc

    def _begin_transaction(self, conn: sqlite3.Connection, begin_cmd: str) -> None:
        tx.begin_transaction(self, conn, begin_cmd)

    def _commit_transaction(self, conn: sqlite3.Connection) -> None:
        tx.commit_transaction(self, conn)

    def _rollback_transaction(self, conn: sqlite3.Connection) -> None:
        tx.rollback_transaction(self, conn)

    def transaction(
        self, isolation_level: IsolationLevel | SQLiteBeginMode | None = None
    ) -> Iterator[None]:
        return tx.transaction(self, isolation_level)

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> None:
        """Execute a query without returning results."""
        sqlite_execute.execute(self, query, params)

    def execute_returning(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query and return all results as dicts."""
        return sqlite_execute.execute_returning(self, query, params)

    def execute_one(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a query and return a single result or None."""
        return sqlite_execute.execute_one(self, query, params)

    def execute_returning_rowcount(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> int:
        """Execute SQL and return rowcount."""
        return sqlite_execute.execute_returning_rowcount(self, query, params)

    # =========================================================================
    # Block State Operations
    # =========================================================================

    def get_block_state(self, chain_id: int) -> BlockState | None:
        return block_state_repo.get_block_state(self, chain_id)

    def upsert_block_state(
        self,
        chain_id: int,
        block_number: int,
        block_hash: str,
    ) -> None:
        block_state_repo.upsert_block_state(self, chain_id, block_number, block_hash)

    def get_block_hash_at_height(
        self, chain_id: int, block_number: int
    ) -> str | None:
        return block_state_repo.get_block_hash_at_height(self, chain_id, block_number)

    def insert_block_hash(
        self, chain_id: int, block_number: int, block_hash: str
    ) -> None:
        block_state_repo.insert_block_hash(self, chain_id, block_number, block_hash)

    def delete_block_hashes_above(self, chain_id: int, block_number: int) -> int:
        return block_state_repo.delete_block_hashes_above(self, chain_id, block_number)

    def delete_block_hash_at_height(self, chain_id: int, block_number: int) -> bool:
        return block_state_repo.delete_block_hash_at_height(self, chain_id, block_number)

    def cleanup_old_block_hashes(self, chain_id: int, keep_count: int) -> int:
        return block_state_repo.cleanup_old_block_hashes(self, chain_id, keep_count)

    def clear_block_hash_history(self, chain_id: int) -> int:
        return block_state_repo.clear_block_hash_history(self, chain_id)

    def get_oldest_block_in_history(self, chain_id: int) -> int | None:
        return block_state_repo.get_oldest_block_in_history(self, chain_id)

    def get_latest_block_in_history(self, chain_id: int) -> int | None:
        return block_state_repo.get_latest_block_in_history(self, chain_id)

    def get_inflight_intent_count(
        self, chain_id: int, job_id: str, signer_address: str
    ) -> int:
        return intents_repo.get_inflight_intent_count(
            self, chain_id, job_id, signer_address
        )

    def get_inflight_intents_for_scope(
        self,
        chain_id: int,
        job_id: str,
        signer_address: str,
        to_address: str,
    ) -> list[dict[str, Any]]:
        return intents_repo.get_inflight_intents_for_scope(
            self, chain_id, job_id, signer_address, to_address
        )

    # =========================================================================
    # Job Operations
    # =========================================================================

    def get_job(self, job_id: str) -> JobConfig | None:
        return jobs_repo.get_job(self, job_id)

    def get_enabled_jobs(self) -> list[JobConfig]:
        return jobs_repo.get_enabled_jobs(self)

    def list_all_jobs(self) -> list[JobConfig]:
        return jobs_repo.list_all_jobs(self)

    def upsert_job(
        self,
        job_id: str,
        job_name: str,
        check_interval_blocks: int,
        enabled: bool = True,
    ) -> None:
        jobs_repo.upsert_job(self, job_id, job_name, check_interval_blocks, enabled)

    def update_job_checked(
        self, job_id: str, block_number: int, triggered: bool = False
    ) -> None:
        jobs_repo.update_job_checked(self, job_id, block_number, triggered)

    def set_job_enabled(self, job_id: str, enabled: bool) -> bool:
        return jobs_repo.set_job_enabled(self, job_id, enabled)

    def set_job_drain(
        self,
        job_id: str,
        drain_until: datetime,
        reason: str | None = None,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        return jobs_repo.set_job_drain(self, job_id, drain_until, reason, actor, source)

    def clear_job_drain(
        self,
        job_id: str,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        return jobs_repo.clear_job_drain(self, job_id, actor, source)

    def delete_job(self, job_id: str) -> bool:
        return jobs_repo.delete_job(self, job_id)

    def get_job_kv(self, job_id: str, key: str) -> Any | None:
        return jobs_repo.get_job_kv(self, job_id, key)

    def set_job_kv(self, job_id: str, key: str, value: Any) -> None:
        jobs_repo.set_job_kv(self, job_id, key, value)

    def delete_job_kv(self, job_id: str, key: str) -> bool:
        return jobs_repo.delete_job_kv(self, job_id, key)

    # =========================================================================
    # Signer & Nonce Operations
    # =========================================================================

    def get_signer_state(self, chain_id: int, address: str) -> SignerState | None:
        return signers_nonces_repo.get_signer_state(self, chain_id, address)

    def get_all_signers(self, chain_id: int) -> list[SignerState]:
        return signers_nonces_repo.get_all_signers(self, chain_id)

    def upsert_signer(
        self,
        chain_id: int,
        address: str,
        next_nonce: int,
        last_synced_chain_nonce: int | None = None,
    ) -> None:
        signers_nonces_repo.upsert_signer(
            self, chain_id, address, next_nonce, last_synced_chain_nonce
        )

    def update_signer_next_nonce(
        self, chain_id: int, address: str, next_nonce: int
    ) -> None:
        signers_nonces_repo.update_signer_next_nonce(
            self, chain_id, address, next_nonce
        )

    def update_signer_chain_nonce(
        self, chain_id: int, address: str, chain_nonce: int
    ) -> None:
        signers_nonces_repo.update_signer_chain_nonce(
            self, chain_id, address, chain_nonce
        )

    def set_gap_started_at(
        self, chain_id: int, address: str, started_at: datetime
    ) -> None:
        """Record when gap blocking started for a signer."""
        signers_nonces_repo.set_gap_started_at(self, chain_id, address, started_at)

    def clear_gap_started_at(self, chain_id: int, address: str) -> None:
        """Clear gap tracking (gap resolved or force reset)."""
        signers_nonces_repo.clear_gap_started_at(self, chain_id, address)

    def set_signer_quarantined(
        self,
        chain_id: int,
        address: str,
        reason: str,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        return signers_nonces_repo.set_signer_quarantined(
            self, chain_id, address, reason, actor, source
        )

    def clear_signer_quarantined(
        self,
        chain_id: int,
        address: str,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        return signers_nonces_repo.clear_signer_quarantined(
            self, chain_id, address, actor, source
        )

    def set_replacements_paused(
        self,
        chain_id: int,
        address: str,
        paused: bool,
        reason: str | None = None,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        return signers_nonces_repo.set_replacements_paused(
            self, chain_id, address, paused, reason, actor, source
        )

    # =========================================================================
    # Runtime Controls (containment with TTL)
    # =========================================================================

    def set_runtime_control(
        self,
        control: str,
        active: bool,
        expires_at: datetime | None,
        reason: str | None,
        actor: str | None,
        mode: str,
    ) -> RuntimeControl:
        return signers_nonces_repo.set_runtime_control(
            self, control, active, expires_at, reason, actor, mode
        )

    def get_runtime_control(self, control: str) -> RuntimeControl | None:
        return signers_nonces_repo.get_runtime_control(self, control)

    def list_runtime_controls(self) -> list[RuntimeControl]:
        return signers_nonces_repo.list_runtime_controls(self)

    def record_nonce_reset_audit(
        self,
        chain_id: int,
        signer_address: str,
        old_next_nonce: int | None,
        new_next_nonce: int,
        released_reservations: int,
        source: str,
        reason: str | None,
    ) -> None:
        """Record a nonce force reset in the audit table."""
        signers_nonces_repo.record_nonce_reset_audit(
            self,
            chain_id,
            signer_address,
            old_next_nonce,
            new_next_nonce,
            released_reservations,
            source,
            reason,
        )

    def record_mutation_audit(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str | None = None,
        reason: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        signers_nonces_repo.record_mutation_audit(
            self, entity_type, entity_id, action, actor, reason, source, metadata
        )

    def get_signer_by_alias(self, chain_id: int, alias: str) -> SignerState | None:
        """Get signer by alias. Returns None if not found."""
        return signers_nonces_repo.get_signer_by_alias(self, chain_id, alias)

    def reserve_nonce_atomic(
        self,
        chain_id: int,
        address: str,
        chain_nonce: int,
        intent_id: UUID | None = None,
    ) -> int:
        return signers_nonces_repo.reserve_nonce_atomic(
            self, chain_id, address, chain_nonce, intent_id
        )

    def get_nonce_reservation(
        self, chain_id: int, address: str, nonce: int
    ) -> NonceReservation | None:
        return signers_nonces_repo.get_nonce_reservation(self, chain_id, address, nonce)

    def get_reservations_for_signer(
        self, chain_id: int, address: str, status: str | None = None
    ) -> list[NonceReservation]:
        return signers_nonces_repo.get_reservations_for_signer(
            self, chain_id, address, status
        )

    def get_reservations_below_nonce(
        self, chain_id: int, address: str, nonce: int
    ) -> list[NonceReservation]:
        return signers_nonces_repo.get_reservations_below_nonce(
            self, chain_id, address, nonce
        )

    def create_nonce_reservation(
        self,
        chain_id: int,
        address: str,
        nonce: int,
        status: str = "reserved",
        intent_id: UUID | None = None,
    ) -> NonceReservation:
        return signers_nonces_repo.create_nonce_reservation(
            self, chain_id, address, nonce, status, intent_id
        )

    def update_nonce_reservation_status(
        self,
        chain_id: int,
        address: str,
        nonce: int,
        status: str,
        intent_id: UUID | None = None,
    ) -> bool:
        return signers_nonces_repo.update_nonce_reservation_status(
            self, chain_id, address, nonce, status, intent_id
        )

    def release_nonce_reservation(
        self,
        chain_id: int,
        address: str,
        nonce: int,
        actor: str | None = None,
        reason: str | None = None,
        source: str | None = None,
    ) -> bool:
        return signers_nonces_repo.release_nonce_reservation(
            self, chain_id, address, nonce, actor, reason, source
        )

    def cleanup_orphaned_nonces(
        self, chain_id: int, older_than_hours: int = 24
    ) -> int:
        return signers_nonces_repo.cleanup_orphaned_nonces(
            self, chain_id, older_than_hours
        )

    # =========================================================================
    # Intent Operations
    # =========================================================================

    def create_intent(
        self,
        intent_id: UUID,
        job_id: str,
        chain_id: int,
        signer_address: str,
        idempotency_key: str,
        to_address: str,
        data: str | None,
        value_wei: str,
        gas_limit: int | None,
        max_fee_per_gas: str | None,
        max_priority_fee_per_gas: str | None,
        min_confirmations: int,
        deadline_ts: datetime | None,
        signer_alias: str | None = None,
        broadcast_group: str | None = None,
        broadcast_endpoints: list[str] | None = None,
        metadata: dict | None = None,
    ) -> TxIntent | None:
        return intents_repo.create_intent(
            self,
            intent_id,
            job_id,
            chain_id,
            signer_address,
            idempotency_key,
            to_address,
            data,
            value_wei,
            gas_limit,
            max_fee_per_gas,
            max_priority_fee_per_gas,
            min_confirmations,
            deadline_ts,
            signer_alias,
            broadcast_group,
            broadcast_endpoints,
            metadata,
        )

    def get_intent(self, intent_id: UUID) -> TxIntent | None:
        return intents_repo.get_intent(self, intent_id)

    def get_intent_by_idempotency_key(
        self,
        chain_id: int,
        signer_address: str,
        idempotency_key: str,
    ) -> TxIntent | None:
        return intents_repo.get_intent_by_idempotency_key(
            self, chain_id, signer_address, idempotency_key
        )

    def get_intents_by_status(
        self,
        status: str | list[str],
        chain_id: int | None = None,
        job_id: str | None = None,
        limit: int = 100,
    ) -> list[TxIntent]:
        return intents_repo.get_intents_by_status(
            self, status, chain_id, job_id, limit
        )

    def list_intents_filtered(
        self,
        status: str | None = None,
        job_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return intents_repo.list_intents_filtered(self, status, job_id, limit)

    def get_active_intent_count(self, job_id: str, chain_id: int | None = None) -> int:
        return intents_repo.get_active_intent_count(self, job_id, chain_id)

    def get_pending_intent_count(self, chain_id: int | None = None) -> int:
        return intents_repo.get_pending_intent_count(self, chain_id)

    def get_backing_off_intent_count(self, chain_id: int | None = None) -> int:
        return intents_repo.get_backing_off_intent_count(self, chain_id)

    def get_oldest_pending_intent_age(self, chain_id: int) -> float | None:
        return intents_repo.get_oldest_pending_intent_age(self, chain_id)

    def list_intent_inconsistencies(
        self,
        max_age_seconds: int,
        limit: int = 100,
        chain_id: int | None = None,
    ) -> list[dict[str, Any]]:
        return intents_repo.list_intent_inconsistencies(
            self, max_age_seconds, limit, chain_id
        )

    def list_broadcasted_intents_older_than(
        self,
        max_age_seconds: int,
        limit: int = 100,
        chain_id: int | None = None,
    ) -> list[TxIntent]:
        return intents_repo.list_broadcasted_intents_older_than(
            self, max_age_seconds, limit, chain_id
        )

    def list_claimed_intents_older_than(
        self,
        max_age_seconds: int,
        limit: int = 100,
        chain_id: int | None = None,
    ) -> list[TxIntent]:
        return intents_repo.list_claimed_intents_older_than(
            self, max_age_seconds, limit, chain_id
        )

    def claim_next_intent(
        self,
        claim_token: str,
        claimed_by: str | None = None,
        lease_seconds: int | None = None,
    ) -> ClaimedIntent | None:
        return intents_repo.claim_next_intent(self, claim_token, claimed_by, lease_seconds)

    def update_intent_status(
        self,
        intent_id: UUID,
        status: str,
        claim_token: str | None = None,
        terminal_reason: str | None = None,
        halt_reason: str | None = None,
    ) -> bool:
        return intents_repo.update_intent_status(
            self,
            intent_id,
            status,
            claim_token,
            terminal_reason,
            halt_reason,
        )

    def update_intent_status_if(
        self,
        intent_id: UUID,
        status: str,
        expected_status: str | list[str],
        terminal_reason: str | None = None,
        halt_reason: str | None = None,
    ) -> bool:
        return intents_repo.update_intent_status_if(
            self,
            intent_id,
            status,
            expected_status,
            terminal_reason,
            halt_reason,
        )

    def transition_intent_status(
        self,
        intent_id: UUID,
        from_statuses: list[str],
        to_status: str,
        terminal_reason: str | None = None,
        halt_reason: str | None = None,
    ) -> tuple[bool, str | None]:
        return intents_repo.transition_intent_status_immediate(
            self,
            intent_id,
            from_statuses,
            to_status,
            terminal_reason,
            halt_reason,
        )

    def update_intent_signer(self, intent_id: UUID, signer_address: str) -> bool:
        return intents_repo.update_intent_signer(self, intent_id, signer_address)

    def release_intent_claim(self, intent_id: UUID) -> bool:
        return intents_repo.release_intent_claim(self, intent_id)

    def release_intent_claim_if_token(self, intent_id: UUID, claim_token: str) -> bool:
        return intents_repo.release_intent_claim_if_token(self, intent_id, claim_token)

    def release_claim_if_token_and_no_attempts(
        self, intent_id: UUID, claim_token: str
    ) -> bool:
        return intents_repo.release_claim_if_token_and_no_attempts(
            self, intent_id, claim_token
        )

    def clear_intent_claim(self, intent_id: UUID) -> bool:
        return intents_repo.clear_intent_claim(self, intent_id)

    def set_intent_retry_after(
        self, intent_id: UUID, retry_after: datetime | None
    ) -> bool:
        return intents_repo.set_intent_retry_after(self, intent_id, retry_after)

    def increment_intent_retry_count(self, intent_id: UUID) -> int:
        return intents_repo.increment_intent_retry_count(self, intent_id)

    def should_create_intent(
        self,
        cooldown_key: str,
        now: int,
        cooldown_seconds: int,
    ) -> tuple[bool, int | None]:
        return intents_repo.should_create_intent(
            self, cooldown_key, now, cooldown_seconds
        )

    def prune_job_cooldowns(self, older_than_days: int) -> int:
        return intents_repo.prune_job_cooldowns(self, older_than_days)

    def requeue_expired_claims_no_attempts(
        self,
        limit: int,
        grace_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        return intents_repo.requeue_expired_claims_no_attempts(
            self, limit, grace_seconds, chain_id
        )

    def count_expired_claims_with_attempts(
        self,
        limit: int,
        grace_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        return intents_repo.count_expired_claims_with_attempts(
            self, limit, grace_seconds, chain_id
        )

    def requeue_missing_lease_claims_no_attempts(
        self,
        limit: int,
        cutoff_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        return intents_repo.requeue_missing_lease_claims_no_attempts(
            self, limit, cutoff_seconds, chain_id
        )

    def count_missing_lease_claims_with_attempts(
        self,
        limit: int,
        cutoff_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        return intents_repo.count_missing_lease_claims_with_attempts(
            self, limit, cutoff_seconds, chain_id
        )

    def abandon_intent(self, intent_id: UUID) -> bool:
        return intents_repo.abandon_intent(self, intent_id)

    def get_broadcasted_intents_for_signer(
        self, chain_id: int, address: str
    ) -> list[TxIntent]:
        return intents_repo.get_broadcasted_intents_for_signer(self, chain_id, address)

    def bind_broadcast_endpoints(
        self,
        intent_id: UUID,
        group_name: str | None,
        endpoints: list[str],
    ) -> tuple[str | None, list[str]]:
        return intents_repo.bind_broadcast_endpoints(
            self, intent_id, group_name, endpoints
        )

    def get_broadcast_binding(
        self, intent_id: UUID
    ) -> tuple[str | None, list[str]] | None:
        return intents_repo.get_broadcast_binding(self, intent_id)

    # =========================================================================
    # Attempt Operations
    # =========================================================================

    def create_attempt(
        self,
        attempt_id: UUID,
        intent_id: UUID,
        nonce: int,
        gas_params_json: str,
        status: str = "pending_send",
        tx_hash: str | None = None,
        replaces_attempt_id: UUID | None = None,
        broadcast_group: str | None = None,
        endpoint_url: str | None = None,
        binding: tuple[str | None, list[str]] | None = None,
        actor: str | None = None,
        reason: str | None = None,
        source: str | None = None,
    ) -> TxAttempt:
        return attempts_repo.create_attempt(
            self,
            attempt_id,
            intent_id,
            nonce,
            gas_params_json,
            status,
            tx_hash,
            replaces_attempt_id,
            broadcast_group,
            endpoint_url,
            binding,
            actor,
            reason,
            source,
        )

    def create_attempt_once(
        self,
        attempt_id: UUID,
        intent_id: UUID,
        nonce: int,
        gas_params_json: str,
        status: str = "pending_send",
        tx_hash: str | None = None,
        replaces_attempt_id: UUID | None = None,
        broadcast_group: str | None = None,
        endpoint_url: str | None = None,
        binding: tuple[str | None, list[str]] | None = None,
        actor: str | None = None,
        reason: str | None = None,
        source: str | None = None,
    ) -> TxAttempt:
        return attempts_repo.create_attempt_once(
            self,
            attempt_id,
            intent_id,
            nonce,
            gas_params_json,
            status,
            tx_hash,
            replaces_attempt_id,
            broadcast_group,
            endpoint_url,
            binding,
            actor,
            reason,
            source,
        )

    def require_bound_and_attempt(
        self,
        intent_id: UUID,
        nonce: int,
        endpoints: list[str],
    ) -> None:
        attempts_repo.require_bound_and_attempt(self, intent_id, nonce, endpoints)

    def get_attempt(self, attempt_id: UUID) -> TxAttempt | None:
        return attempts_repo.get_attempt(self, attempt_id)

    def get_attempts_for_intent(self, intent_id: UUID) -> list[TxAttempt]:
        return attempts_repo.get_attempts_for_intent(self, intent_id)

    def get_latest_attempt_for_intent(self, intent_id: UUID) -> TxAttempt | None:
        return attempts_repo.get_latest_attempt_for_intent(self, intent_id)

    def get_attempt_by_tx_hash(self, tx_hash: str) -> TxAttempt | None:
        return attempts_repo.get_attempt_by_tx_hash(self, tx_hash)

    def update_attempt_status(
        self,
        attempt_id: UUID,
        status: str,
        tx_hash: str | None = None,
        broadcast_block: int | None = None,
        broadcast_at: datetime | None = None,
        included_block: int | None = None,
        endpoint_url: str | None = None,
        error_code: str | None = None,
        error_detail: str | None = None,
        actor: str | None = None,
        reason: str | None = None,
        source: str | None = None,
    ) -> bool:
        return attempts_repo.update_attempt_status(
            self,
            attempt_id,
            status,
            tx_hash,
            broadcast_block,
            broadcast_at,
            included_block,
            endpoint_url,
            error_code,
            error_detail,
            actor,
            reason,
            source,
        )

    # =========================================================================
    # ABI Cache Operations
    # =========================================================================

    def get_cached_abi(self, chain_id: int, address: str) -> ABICacheEntry | None:
        return cache_repo.get_cached_abi(self, chain_id, address)

    def set_cached_abi(
        self,
        chain_id: int,
        address: str,
        abi_json: str,
        source: str,
    ) -> None:
        cache_repo.set_cached_abi(self, chain_id, address, abi_json, source)

    def clear_cached_abi(self, chain_id: int, address: str) -> bool:
        return cache_repo.clear_cached_abi(self, chain_id, address)

    def cleanup_expired_abis(self, max_age_seconds: int) -> int:
        return cache_repo.cleanup_expired_abis(self, max_age_seconds)

    # =========================================================================
    # Proxy Cache Operations
    # =========================================================================

    def get_cached_proxy(
        self, chain_id: int, proxy_address: str
    ) -> ProxyCacheEntry | None:
        return cache_repo.get_cached_proxy(self, chain_id, proxy_address)

    def set_cached_proxy(
        self,
        chain_id: int,
        proxy_address: str,
        implementation_address: str,
    ) -> None:
        cache_repo.set_cached_proxy(self, chain_id, proxy_address, implementation_address)

    def clear_cached_proxy(self, chain_id: int, proxy_address: str) -> bool:
        return cache_repo.clear_cached_proxy(self, chain_id, proxy_address)

    # =========================================================================
    # Cleanup & Maintenance
    # =========================================================================

    def cleanup_old_intents(
        self,
        older_than_days: int,
        statuses: list[str] | None = None,
    ) -> int:
        return maintenance_repo.cleanup_old_intents(self, older_than_days, statuses)

    def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics for health checks."""
        return maintenance_repo.get_database_stats(self)

    # =========================================================================
    # Reconciliation Operations
    # =========================================================================

    def clear_orphaned_claims(self, chain_id: int, older_than_minutes: int = 2) -> int:
        """Clear claim fields where status != 'claimed' and claim is stale."""
        return maintenance_repo.clear_orphaned_claims(self, chain_id, older_than_minutes)

    def release_orphaned_nonces(self, chain_id: int, older_than_minutes: int = 5) -> int:
        """Release nonces for terminal intents that are stale."""
        return maintenance_repo.release_orphaned_nonces(self, chain_id, older_than_minutes)

    def count_broadcasted_without_attempts(self, chain_id: int) -> int:
        """Count broadcasted intents with no attempt records (integrity issue)."""
        return maintenance_repo.count_broadcasted_without_attempts(self, chain_id)

    def count_stale_claims(self, chain_id: int, older_than_minutes: int = 10) -> int:
        """Count intents stuck in CLAIMED for too long."""
        return maintenance_repo.count_stale_claims(self, chain_id, older_than_minutes)

    # =========================================================================
    # Invariant Queries (Phase 2)
    # =========================================================================

    def count_stuck_claimed(self, chain_id: int, older_than_minutes: int = 10) -> int:
        """Count intents stuck in CLAIMED status for too long."""
        return maintenance_repo.count_stuck_claimed(self, chain_id, older_than_minutes)

    def count_orphaned_claims(self, chain_id: int) -> int:
        """Count intents with claim_token set but status != claimed."""
        return maintenance_repo.count_orphaned_claims(self, chain_id)

    def count_orphaned_nonces(self, chain_id: int) -> int:
        """Count reserved/in_flight nonces for failed/abandoned intents."""
        return maintenance_repo.count_orphaned_nonces(self, chain_id)

    def get_oldest_nonce_gap_age_seconds(self, chain_id: int) -> float:
        """Get age in seconds of the oldest nonce gap.

        Anchors from signers (small table) for efficiency.
        Returns 0 if no gaps or if chain nonce not synced.
        """
        return maintenance_repo.get_oldest_nonce_gap_age_seconds(self, chain_id)
