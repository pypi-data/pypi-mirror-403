"""Database abstraction layer for brawny (SQLite-only)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterator, Literal
from uuid import UUID

if TYPE_CHECKING:
    from brawny.model.errors import ErrorInfo, FailureType
    from brawny.model.types import (
        BroadcastInfo,
        GasParams,
        JobConfig,
        NonceReservation,
        RuntimeControl,
        SignerState,
        TxAttempt,
        TxIntent,
    )
    from brawny.types import ClaimedIntent


IsolationLevel = Literal["SERIALIZABLE", "REPEATABLE READ", "READ COMMITTED", "READ UNCOMMITTED"]


@dataclass
class BlockState:
    """Block processing state."""

    chain_id: int
    last_processed_block_number: int
    last_processed_block_hash: str
    created_at: datetime
    updated_at: datetime


@dataclass
class BlockHashEntry:
    """Block hash history entry for reorg detection."""

    id: int
    chain_id: int
    block_number: int
    block_hash: str
    inserted_at: datetime


@dataclass
class ABICacheEntry:
    """Cached ABI entry."""

    chain_id: int
    address: str
    abi_json: str
    source: str
    resolved_at: datetime


@dataclass
class ProxyCacheEntry:
    """Cached proxy resolution entry."""

    chain_id: int
    proxy_address: str
    implementation_address: str
    resolved_at: datetime


class Database(ABC):
    """Abstract database interface.

    Implementations must provide thread-safe connection management
    and proper transaction isolation.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close database connection and cleanup resources."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected."""
        ...

    @abstractmethod
    @contextmanager
    def transaction(
        self, isolation_level: IsolationLevel | None = None
    ) -> Iterator[None]:
        """Context manager for database transactions.

        Args:
            isolation_level: Optional isolation level override
        """
        ...

    @abstractmethod
    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> None:
        """Execute a query without returning results."""
        ...

    @abstractmethod
    def execute_returning(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query and return all results as dicts."""
        ...

    @abstractmethod
    def execute_one(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a query and return a single result or None."""
        ...

    @abstractmethod
    def execute_returning_rowcount(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> int:
        """Execute a query and return affected rowcount."""
        ...

    # =========================================================================
    # Block State Operations
    # =========================================================================

    @abstractmethod
    def get_block_state(self, chain_id: int) -> BlockState | None:
        """Get the current block processing state."""
        ...

    @abstractmethod
    def upsert_block_state(
        self,
        chain_id: int,
        block_number: int,
        block_hash: str,
    ) -> None:
        """Update or insert block processing state."""
        ...

    @abstractmethod
    def get_block_hash_at_height(
        self, chain_id: int, block_number: int
    ) -> str | None:
        """Get stored block hash at a specific height."""
        ...

    @abstractmethod
    def insert_block_hash(
        self, chain_id: int, block_number: int, block_hash: str
    ) -> None:
        """Insert a block hash into history."""
        ...

    @abstractmethod
    def delete_block_hashes_above(self, chain_id: int, block_number: int) -> int:
        """Delete block hashes above a certain height (for reorg rewind)."""
        ...

    @abstractmethod
    def delete_block_hash_at_height(self, chain_id: int, block_number: int) -> bool:
        """Delete a specific block hash (for stale hash cleanup)."""
        ...

    @abstractmethod
    def cleanup_old_block_hashes(self, chain_id: int, keep_count: int) -> int:
        """Delete old block hashes beyond the history window."""
        ...

    @abstractmethod
    def clear_block_hash_history(self, chain_id: int) -> int:
        """Delete all block hashes for a chain."""
        ...

    @abstractmethod
    def get_oldest_block_in_history(self, chain_id: int) -> int | None:
        """Get the oldest block number in hash history."""
        ...

    @abstractmethod
    def get_latest_block_in_history(self, chain_id: int) -> int | None:
        """Get the newest block number in hash history."""
        ...

    @abstractmethod
    def get_inflight_intent_count(
        self, chain_id: int, job_id: str, signer_address: str
    ) -> int:
        """Count inflight intents (created/claimed/broadcasted) for job+signer."""
        ...

    @abstractmethod
    def get_inflight_intents_for_scope(
        self,
        chain_id: int,
        job_id: str,
        signer_address: str,
        to_address: str,
    ) -> list[dict[str, Any]]:
        """List inflight intents (created/claimed/broadcasted) for job+signer+to."""
        ...

    # =========================================================================
    # Job Operations
    # =========================================================================

    @abstractmethod
    def get_job(self, job_id: str) -> JobConfig | None:
        """Get job configuration by ID."""
        ...

    @abstractmethod
    def get_enabled_jobs(self) -> list[JobConfig]:
        """Get all enabled jobs ordered by job_id."""
        ...

    @abstractmethod
    def list_all_jobs(self) -> list[JobConfig]:
        """Get all jobs (enabled and disabled) ordered by job_id."""
        ...

    @abstractmethod
    def upsert_job(
        self,
        job_id: str,
        job_name: str,
        check_interval_blocks: int,
        enabled: bool = True,
    ) -> None:
        """Insert or update job configuration."""
        ...

    @abstractmethod
    def update_job_checked(
        self, job_id: str, block_number: int, triggered: bool = False
    ) -> None:
        """Update job's last checked/triggered block numbers."""
        ...

    @abstractmethod
    def set_job_enabled(self, job_id: str, enabled: bool) -> bool:
        """Enable or disable a job. Returns True if job exists."""
        ...

    @abstractmethod
    def set_job_drain(
        self,
        job_id: str,
        drain_until: datetime,
        reason: str | None = None,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        """Drain a job until a timestamp. Returns True if job exists."""
        ...

    @abstractmethod
    def clear_job_drain(
        self,
        job_id: str,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        """Clear job drain. Returns True if job exists."""
        ...

    @abstractmethod
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from the database. Returns True if job existed."""
        ...

    @abstractmethod
    def get_job_kv(self, job_id: str, key: str) -> Any | None:
        """Get a value from job's key-value store."""
        ...

    @abstractmethod
    def set_job_kv(self, job_id: str, key: str, value: Any) -> None:
        """Set a value in job's key-value store."""
        ...

    @abstractmethod
    def delete_job_kv(self, job_id: str, key: str) -> bool:
        """Delete a key from job's key-value store."""
        ...

    # =========================================================================
    # Signer & Nonce Operations
    # =========================================================================

    @abstractmethod
    def get_signer_state(self, chain_id: int, address: str) -> SignerState | None:
        """Get signer state including next nonce."""
        ...

    @abstractmethod
    def get_all_signers(self, chain_id: int) -> list[SignerState]:
        """Get all signers for a chain."""
        ...

    @abstractmethod
    def upsert_signer(
        self,
        chain_id: int,
        address: str,
        next_nonce: int,
        last_synced_chain_nonce: int | None = None,
    ) -> None:
        """Insert or update signer state."""
        ...

    @abstractmethod
    def update_signer_next_nonce(
        self, chain_id: int, address: str, next_nonce: int
    ) -> None:
        """Update signer's next nonce value."""
        ...

    @abstractmethod
    def update_signer_chain_nonce(
        self, chain_id: int, address: str, chain_nonce: int
    ) -> None:
        """Update signer's last synced chain nonce."""
        ...

    @abstractmethod
    def set_gap_started_at(
        self, chain_id: int, address: str, started_at: datetime
    ) -> None:
        """Record when gap blocking started for a signer."""
        ...

    @abstractmethod
    def clear_gap_started_at(self, chain_id: int, address: str) -> None:
        """Clear gap tracking (gap resolved or force reset)."""
        ...

    @abstractmethod
    def set_signer_quarantined(
        self,
        chain_id: int,
        address: str,
        reason: str,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        """Quarantine signer (block nonce reservations/broadcast)."""
        ...

    @abstractmethod
    def clear_signer_quarantined(
        self,
        chain_id: int,
        address: str,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        """Clear signer quarantine."""
        ...

    @abstractmethod
    def set_replacements_paused(
        self,
        chain_id: int,
        address: str,
        paused: bool,
        reason: str | None = None,
        actor: str | None = None,
        source: str | None = None,
    ) -> bool:
        """Pause or resume replacements for a signer."""
        ...

    @abstractmethod
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
        """Record a nonce force reset in the audit table.

        Provides durable record for incident investigation.
        """
        ...

    @abstractmethod
    def get_signer_by_alias(self, chain_id: int, alias: str) -> SignerState | None:
        """Get signer by alias. Returns None if not found."""
        ...

    @abstractmethod
    def reserve_nonce_atomic(
        self,
        chain_id: int,
        address: str,
        chain_nonce: int,
        intent_id: UUID | None = None,
    ) -> int:
        """Atomically reserve the next available nonce for a signer."""
        ...

    @abstractmethod
    def get_nonce_reservation(
        self, chain_id: int, address: str, nonce: int
    ) -> NonceReservation | None:
        """Get a specific nonce reservation."""
        ...

    @abstractmethod
    def get_reservations_for_signer(
        self, chain_id: int, address: str, status: str | None = None
    ) -> list[NonceReservation]:
        """Get all reservations for a signer, optionally filtered by status."""
        ...

    @abstractmethod
    def get_reservations_below_nonce(
        self, chain_id: int, address: str, nonce: int
    ) -> list[NonceReservation]:
        """Get reservations with nonce less than given value."""
        ...

    @abstractmethod
    def create_nonce_reservation(
        self,
        chain_id: int,
        address: str,
        nonce: int,
        status: str = "reserved",
        intent_id: UUID | None = None,
    ) -> NonceReservation:
        """Create a new nonce reservation."""
        ...

    @abstractmethod
    def update_nonce_reservation_status(
        self,
        chain_id: int,
        address: str,
        nonce: int,
        status: str,
        intent_id: UUID | None = None,
    ) -> bool:
        """Update nonce reservation status. Returns True if updated."""
        ...

    @abstractmethod
    def release_nonce_reservation(
        self,
        chain_id: int,
        address: str,
        nonce: int,
        actor: str | None = None,
        reason: str | None = None,
        source: str | None = None,
    ) -> bool:
        """Release (mark as released) a nonce reservation."""
        ...

    @abstractmethod
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
        """Record durable mutation audit entry."""
        ...

    @abstractmethod
    def set_runtime_control(
        self,
        control: str,
        active: bool,
        expires_at: datetime | None,
        reason: str | None,
        actor: str | None,
        mode: str,
    ) -> "RuntimeControl":
        """Create or update runtime control with TTL."""
        ...

    @abstractmethod
    def get_runtime_control(self, control: str) -> "RuntimeControl | None":
        """Fetch runtime control by name."""
        ...

    @abstractmethod
    def list_runtime_controls(self) -> list["RuntimeControl"]:
        """List all runtime controls."""
        ...

    @abstractmethod
    def cleanup_orphaned_nonces(
        self, chain_id: int, older_than_hours: int = 24
    ) -> int:
        """Delete orphaned nonce reservations older than specified hours.

        Args:
            chain_id: Chain ID to cleanup
            older_than_hours: Delete orphaned reservations older than this (default: 24h)

        Returns:
            Number of deleted reservations
        """
        ...

    # =========================================================================
    # Intent Operations
    # =========================================================================

    @abstractmethod
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
    ) -> TxIntent | None:
        """Create a new intent. Returns None if idempotency_key exists."""
        ...

    @abstractmethod
    def get_intent(self, intent_id: UUID) -> TxIntent | None:
        """Get an intent by ID."""
        ...

    @abstractmethod
    def get_intent_by_idempotency_key(
        self,
        chain_id: int,
        signer_address: str,
        idempotency_key: str,
    ) -> TxIntent | None:
        """Get an intent by idempotency key (scoped to chain and signer)."""
        ...

    @abstractmethod
    def get_intents_by_status(
        self,
        status: str | list[str],
        chain_id: int | None = None,
        job_id: str | None = None,
        limit: int = 100,
    ) -> list[TxIntent]:
        """Get intents by status."""
        ...

    @abstractmethod
    def list_intents_filtered(
        self,
        status: str | None = None,
        job_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List intents with optional filters, returning raw dict data for CLI display."""
        ...

    @abstractmethod
    def get_active_intent_count(self, job_id: str, chain_id: int | None = None) -> int:
        """Count active intents for a job (created/claimed/broadcasted)."""
        ...

    @abstractmethod
    def get_pending_intent_count(self, chain_id: int | None = None) -> int:
        """Count active intents across all jobs (created/claimed/broadcasted)."""
        ...

    @abstractmethod
    def get_backing_off_intent_count(self, chain_id: int | None = None) -> int:
        """Count intents with retry_after in the future."""
        ...

    @abstractmethod
    def bind_broadcast_endpoints(
        self,
        intent_id: UUID,
        group_name: str | None,
        endpoints: list[str],
    ) -> tuple[str | None, list[str]]:
        """Bind broadcast endpoints to an intent (idempotent)."""
        ...

    @abstractmethod
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
        """Create attempt once per intent+nonce; return existing if present."""
        ...

    @abstractmethod
    def require_bound_and_attempt(
        self,
        intent_id: UUID,
        nonce: int,
        endpoints: list[str],
    ) -> None:
        """Assert broadcast binding and attempt existence before side effects."""
        ...

    @abstractmethod
    def get_oldest_pending_intent_age(self, chain_id: int) -> float | None:
        """Get age in seconds of the oldest pending intent.

        Considers intents in: CREATED, CLAIMED, BROADCASTED status.

        Returns:
            Age in seconds, or None if no pending intents.
        """
        ...

    @abstractmethod
    def list_intent_inconsistencies(
        self,
        max_age_seconds: int,
        limit: int = 100,
        chain_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """List intents with inconsistent state/metadata."""
        ...

    @abstractmethod
    def list_broadcasted_intents_older_than(
        self,
        max_age_seconds: int,
        limit: int = 100,
        chain_id: int | None = None,
    ) -> list[TxIntent]:
        """List broadcasted intents older than a threshold."""
        ...

    @abstractmethod
    def list_claimed_intents_older_than(
        self,
        max_age_seconds: int,
        limit: int = 100,
        chain_id: int | None = None,
    ) -> list[TxIntent]:
        """List claimed intents older than a threshold (with attempts)."""
        ...

    @abstractmethod
    def claim_next_intent(
        self,
        claim_token: str,
        claimed_by: str | None = None,
        lease_seconds: int | None = None,
    ) -> ClaimedIntent | None:
        """Claim the next available intent for processing."""
        ...

    @abstractmethod
    def update_intent_status(
        self,
        intent_id: UUID,
        status: str,
        claim_token: str | None = None,
        terminal_reason: str | None = None,
        halt_reason: str | None = None,
    ) -> bool:
        """Update intent status. Returns True if updated."""
        ...

    @abstractmethod
    def update_intent_status_if(
        self,
        intent_id: UUID,
        status: str,
        expected_status: str | list[str],
        terminal_reason: str | None = None,
        halt_reason: str | None = None,
    ) -> bool:
        """Update intent status only if current status matches expected."""
        ...

    @abstractmethod
    def transition_intent_status(
        self,
        intent_id: UUID,
        from_statuses: list[str],
        to_status: str,
        terminal_reason: str | None = None,
        halt_reason: str | None = None,
    ) -> tuple[bool, str | None]:
        """Atomically transition intent status, clearing claim if leaving CLAIMED.

        The claim fields (claim_token, claimed_at, claimed_by) are cleared
        automatically when:
        - The actual previous status is 'claimed', AND
        - The new status is NOT 'claimed'

        This prevents clearing claim on claimed->claimed transitions.

        Returns:
            (success, old_status) - old_status is the actual previous status,
            or None if no row matched the WHERE clause.
        """
        ...

    @abstractmethod
    def update_intent_signer(self, intent_id: UUID, signer_address: str) -> bool:
        """Update intent signer address (for alias resolution)."""
        ...

    @abstractmethod
    def release_intent_claim(self, intent_id: UUID) -> bool:
        """Release an intent claim (revert to created status)."""
        ...

    @abstractmethod
    def release_intent_claim_if_token(self, intent_id: UUID, claim_token: str) -> bool:
        """Release claim only if claim_token matches. Returns True if released."""
        ...

    @abstractmethod
    def release_claim_if_token_and_no_attempts(
        self, intent_id: UUID, claim_token: str
    ) -> bool:
        """Atomically release claim only if token matches AND no attempts exist.

        Safe primitive for pre-attempt failure handling:
        - Returns True iff release succeeded (ownership + no work started)
        - Returns False if token mismatch, attempts exist, or not claimed
        """
        ...

    @abstractmethod
    def clear_intent_claim(self, intent_id: UUID) -> bool:
        """Clear claim token and claimed_at without changing status."""
        ...

    @abstractmethod
    def set_intent_retry_after(self, intent_id: UUID, retry_after: datetime | None) -> bool:
        """Set intent retry-after timestamp (null clears backoff)."""
        ...

    @abstractmethod
    def increment_intent_retry_count(self, intent_id: UUID) -> int:
        """Atomically increment retry count and return new value."""
        ...

    @abstractmethod
    def requeue_expired_claims_no_attempts(
        self,
        limit: int,
        grace_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        """Requeue expired claimed intents with no attempts. Returns count requeued."""
        ...

    @abstractmethod
    def count_expired_claims_with_attempts(
        self,
        limit: int,
        grace_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        """Count expired claimed intents that have attempts."""
        ...

    @abstractmethod
    def requeue_missing_lease_claims_no_attempts(
        self,
        limit: int,
        cutoff_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        """Requeue claimed intents with NULL lease_expires_at and no attempts."""
        ...

    @abstractmethod
    def count_missing_lease_claims_with_attempts(
        self,
        limit: int,
        cutoff_seconds: int,
        chain_id: int | None = None,
    ) -> int:
        """Count claimed intents with NULL lease_expires_at that have attempts."""
        ...

    @abstractmethod
    def should_create_intent(
        self,
        cooldown_key: str,
        now: int,
        cooldown_seconds: int,
    ) -> tuple[bool, int | None]:
        """Check cooldown key and update if allowed. Returns (allowed, last_intent_at)."""
        ...

    @abstractmethod
    def prune_job_cooldowns(self, older_than_days: int) -> int:
        """Delete stale cooldown keys older than N days. Returns count deleted."""
        ...

    @abstractmethod
    def abandon_intent(self, intent_id: UUID) -> bool:
        """Mark an intent as abandoned."""
        ...

    @abstractmethod
    def get_broadcasted_intents_for_signer(
        self, chain_id: int, address: str
    ) -> list[TxIntent]:
        """Get broadcasted intents for a signer (for reconciliation)."""
        ...

    # =========================================================================
    # Attempt Operations
    # =========================================================================

    @abstractmethod
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
        binding: tuple[str, list[str]] | None = None,
        actor: str | None = None,
        reason: str | None = None,
        source: str | None = None,
    ) -> TxAttempt:
        """Create a new transaction attempt.

        Args:
            attempt_id: Unique attempt ID
            intent_id: Parent intent ID
            nonce: Transaction nonce
            gas_params_json: Gas parameters as JSON
            status: Initial status (default: "pending_send")
            tx_hash: Transaction hash if known
            replaces_attempt_id: ID of attempt being replaced
            broadcast_group: RPC group used for broadcast
            endpoint_url: Endpoint URL that accepted the transaction
            binding: If provided (first broadcast), persist binding atomically.
                     Tuple of (group_name, endpoint_list).
        """
        ...

    @abstractmethod
    def get_attempt(self, attempt_id: UUID) -> TxAttempt | None:
        """Get an attempt by ID."""
        ...

    @abstractmethod
    def get_attempts_for_intent(self, intent_id: UUID) -> list[TxAttempt]:
        """Get all attempts for an intent."""
        ...

    @abstractmethod
    def get_latest_attempt_for_intent(self, intent_id: UUID) -> TxAttempt | None:
        """Get the most recent attempt for an intent."""
        ...

    @abstractmethod
    def get_attempt_by_tx_hash(self, tx_hash: str) -> TxAttempt | None:
        """Get an attempt by transaction hash."""
        ...

    @abstractmethod
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
        """Update attempt status and related fields."""
        ...

    # =========================================================================
    # ABI Cache Operations
    # =========================================================================

    @abstractmethod
    def get_cached_abi(self, chain_id: int, address: str) -> ABICacheEntry | None:
        """Get cached ABI for a contract."""
        ...

    @abstractmethod
    def set_cached_abi(
        self,
        chain_id: int,
        address: str,
        abi_json: str,
        source: str,
    ) -> None:
        """Cache an ABI for a contract."""
        ...

    @abstractmethod
    def clear_cached_abi(self, chain_id: int, address: str) -> bool:
        """Clear cached ABI for a contract."""
        ...

    @abstractmethod
    def cleanup_expired_abis(self, max_age_seconds: int) -> int:
        """Delete ABIs older than max_age_seconds. Returns count deleted."""
        ...

    # =========================================================================
    # Proxy Cache Operations
    # =========================================================================

    @abstractmethod
    def get_cached_proxy(
        self, chain_id: int, proxy_address: str
    ) -> ProxyCacheEntry | None:
        """Get cached proxy implementation address."""
        ...

    @abstractmethod
    def set_cached_proxy(
        self,
        chain_id: int,
        proxy_address: str,
        implementation_address: str,
    ) -> None:
        """Cache a proxy implementation address."""
        ...

    @abstractmethod
    def clear_cached_proxy(self, chain_id: int, proxy_address: str) -> bool:
        """Clear cached proxy resolution."""
        ...

    # =========================================================================
    # Cleanup & Maintenance
    # =========================================================================

    @abstractmethod
    def cleanup_old_intents(
        self,
        older_than_days: int,
        statuses: list[str] | None = None,
    ) -> int:
        """Delete old terminal intents by terminal_reason. Returns count deleted."""
        ...

    @abstractmethod
    def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics for health checks."""
        ...

    # =========================================================================
    # Reconciliation Operations
    # =========================================================================

    @abstractmethod
    def clear_orphaned_claims(self, chain_id: int, older_than_minutes: int = 2) -> int:
        """Clear claim fields where status != 'claimed' and claim is stale.

        Only clears if claimed_at is older than threshold to avoid racing
        with in-progress transitions.

        Returns number of rows updated.
        """
        ...

    @abstractmethod
    def release_orphaned_nonces(self, chain_id: int, older_than_minutes: int = 5) -> int:
        """Release nonces for terminal intents that are stale.

        Only releases 'reserved' nonces (not 'in_flight') where:
        - Intent is in terminal state (failed/abandoned/reverted)
        - Intent hasn't been updated recently (avoids race with recovery)

        Returns number of rows updated.
        """
        ...

    @abstractmethod
    def count_broadcasted_without_attempts(self, chain_id: int) -> int:
        """Count broadcasted intents with no attempt records (integrity issue)."""
        ...

    @abstractmethod
    def count_stale_claims(self, chain_id: int, older_than_minutes: int = 10) -> int:
        """Count intents stuck in CLAIMED for too long."""
        ...

    # =========================================================================
    # Invariant Queries (Phase 2)
    # =========================================================================

    @abstractmethod
    def count_stuck_claimed(self, chain_id: int, older_than_minutes: int = 10) -> int:
        """Count intents stuck in CLAIMED status for too long.

        Normal claim duration is seconds to a few minutes. If an intent
        has been claimed for >10 minutes, the worker likely crashed.
        """
        ...

    @abstractmethod
    def count_orphaned_claims(self, chain_id: int) -> int:
        """Count intents with claim_token set but status != claimed.

        Violates invariant: claim_token should only exist when claimed.
        Note: Phase 1's clear_orphaned_claims repairs these; this just counts.
        """
        ...

    @abstractmethod
    def count_orphaned_nonces(self, chain_id: int) -> int:
        """Count reserved/in_flight nonces for failed/abandoned intents.

        These nonces are wasted and should be released.
        Note: Phase 1's release_orphaned_nonces repairs these; this just counts.
        """
        ...

    @abstractmethod
    def get_oldest_nonce_gap_age_seconds(self, chain_id: int) -> float:
        """Get age in seconds of the oldest nonce gap.

        A "gap" is a reserved nonce below the current chain nonce that
        hasn't been released. This indicates a transaction that was never
        broadcast or was dropped without proper cleanup.

        Returns 0 if no gaps exist OR if last_synced_chain_nonce is NULL
        (stale sync state should not trigger false-positive alerts).
        """
        ...
