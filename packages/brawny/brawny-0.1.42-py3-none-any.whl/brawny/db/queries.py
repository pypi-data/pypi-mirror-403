"""Canonical SQL queries for brawny database operations (SQLite-only)."""

from __future__ import annotations

# =============================================================================
# Block State
# =============================================================================

GET_BLOCK_STATE = """
    SELECT * FROM block_state WHERE chain_id = :chain_id
"""

UPSERT_BLOCK_STATE = """
    INSERT INTO block_state (chain_id, last_processed_block_number, last_processed_block_hash)
    VALUES (:chain_id, :block_number, :block_hash)
    ON CONFLICT(chain_id) DO UPDATE SET
        last_processed_block_number = EXCLUDED.last_processed_block_number,
        last_processed_block_hash = EXCLUDED.last_processed_block_hash,
        updated_at = CURRENT_TIMESTAMP
"""

GET_BLOCK_HASH_AT_HEIGHT = """
    SELECT block_hash FROM block_hash_history
    WHERE chain_id = :chain_id AND block_number = :block_number
"""

INSERT_BLOCK_HASH = """
    INSERT INTO block_hash_history (chain_id, block_number, block_hash)
    VALUES (:chain_id, :block_number, :block_hash)
    ON CONFLICT(chain_id, block_number) DO UPDATE SET
        block_hash = EXCLUDED.block_hash,
        inserted_at = CURRENT_TIMESTAMP
"""

DELETE_BLOCK_HASHES_ABOVE = """
    DELETE FROM block_hash_history
    WHERE chain_id = :chain_id AND block_number > :block_number
"""

DELETE_BLOCK_HASH_AT_HEIGHT = """
    DELETE FROM block_hash_history
    WHERE chain_id = :chain_id AND block_number = :block_number
"""

GET_MAX_BLOCK_IN_HISTORY = """
    SELECT MAX(block_number) as max_block FROM block_hash_history
    WHERE chain_id = :chain_id
"""

DELETE_BLOCK_HASHES_BELOW = """
    DELETE FROM block_hash_history
    WHERE chain_id = :chain_id AND block_number < :cutoff
"""

GET_OLDEST_BLOCK_IN_HISTORY = """
    SELECT MIN(block_number) as min_block FROM block_hash_history
    WHERE chain_id = :chain_id
"""

# =============================================================================
# Jobs
# =============================================================================

GET_JOB = "SELECT * FROM jobs WHERE job_id = :job_id"

GET_ENABLED_JOBS = (
    "SELECT * FROM jobs WHERE enabled = 1 "
    "AND (drain_until IS NULL OR drain_until <= CURRENT_TIMESTAMP) "
    "ORDER BY job_id"
)

LIST_ALL_JOBS = "SELECT * FROM jobs ORDER BY job_id"

UPSERT_JOB = """
    INSERT INTO jobs (job_id, job_name, check_interval_blocks, enabled)
    VALUES (:job_id, :job_name, :check_interval_blocks, :enabled)
    ON CONFLICT(job_id) DO UPDATE SET
        job_name = EXCLUDED.job_name,
        check_interval_blocks = EXCLUDED.check_interval_blocks,
        updated_at = CURRENT_TIMESTAMP
"""

UPDATE_JOB_ENABLED = """
    UPDATE jobs SET enabled = :enabled, updated_at = CURRENT_TIMESTAMP
    WHERE job_id = :job_id
"""

UPDATE_JOB_CHECKED = """
    UPDATE jobs SET
        last_checked_block_number = :block_number,
        updated_at = CURRENT_TIMESTAMP
    WHERE job_id = :job_id
"""

UPDATE_JOB_TRIGGERED = """
    UPDATE jobs SET
        last_checked_block_number = :block_number,
        last_triggered_block_number = :block_number,
        updated_at = CURRENT_TIMESTAMP
    WHERE job_id = :job_id
"""

DELETE_JOB = "DELETE FROM jobs WHERE job_id = :job_id"

# =============================================================================
# Job KV Store
# =============================================================================

GET_JOB_KV = """
    SELECT value_json FROM job_kv
    WHERE job_id = :job_id AND key = :key
"""

UPSERT_JOB_KV = """
    INSERT INTO job_kv (job_id, key, value_json)
    VALUES (:job_id, :key, :value_json)
    ON CONFLICT(job_id, key) DO UPDATE SET
        value_json = EXCLUDED.value_json,
        updated_at = CURRENT_TIMESTAMP
"""

DELETE_JOB_KV = """
    DELETE FROM job_kv WHERE job_id = :job_id AND key = :key
"""

DELETE_ALL_JOB_KV = """
    DELETE FROM job_kv WHERE job_id = :job_id
"""

# =============================================================================
# Signers / Nonce Management
# =============================================================================

GET_SIGNER = """
    SELECT * FROM signers
    WHERE chain_id = :chain_id AND signer_address = :address
"""

LIST_SIGNERS = """
    SELECT * FROM signers WHERE chain_id = :chain_id ORDER BY signer_address
"""

UPSERT_SIGNER = """
    INSERT INTO signers (chain_id, signer_address, next_nonce, last_synced_chain_nonce)
    VALUES (:chain_id, :address, :next_nonce, :last_synced_chain_nonce)
    ON CONFLICT(chain_id, signer_address) DO UPDATE SET
        next_nonce = EXCLUDED.next_nonce,
        last_synced_chain_nonce = EXCLUDED.last_synced_chain_nonce,
        updated_at = CURRENT_TIMESTAMP
"""

UPDATE_SIGNER_NEXT_NONCE = """
    UPDATE signers SET next_nonce = :next_nonce, updated_at = CURRENT_TIMESTAMP
    WHERE chain_id = :chain_id AND signer_address = :address
"""

UPDATE_SIGNER_CHAIN_NONCE = """
    UPDATE signers SET last_synced_chain_nonce = :chain_nonce, updated_at = CURRENT_TIMESTAMP
    WHERE chain_id = :chain_id AND signer_address = :address
"""

SET_GAP_STARTED_AT = """
    UPDATE signers SET gap_started_at = :started_at, updated_at = CURRENT_TIMESTAMP
    WHERE chain_id = :chain_id AND signer_address = :address
"""

CLEAR_GAP_STARTED_AT = """
    UPDATE signers SET gap_started_at = NULL, updated_at = CURRENT_TIMESTAMP
    WHERE chain_id = :chain_id AND signer_address = :address
"""

GET_SIGNER_BY_ALIAS = """
    SELECT * FROM signers
    WHERE chain_id = :chain_id AND alias = :alias
"""

# =============================================================================
# Nonce Reservations
# =============================================================================

GET_NONCE_RESERVATION = """
    SELECT * FROM nonce_reservations
    WHERE chain_id = :chain_id AND signer_address = :address AND nonce = :nonce
"""

GET_RESERVATIONS_FOR_SIGNER = """
    SELECT * FROM nonce_reservations
    WHERE chain_id = :chain_id AND signer_address = :address
    ORDER BY nonce
"""

GET_RESERVATIONS_FOR_SIGNER_WITH_STATUS = """
    SELECT * FROM nonce_reservations
    WHERE chain_id = :chain_id AND signer_address = :address AND status = :status
    ORDER BY nonce
"""

GET_RESERVATIONS_BELOW_NONCE = """
    SELECT * FROM nonce_reservations
    WHERE chain_id = :chain_id AND signer_address = :address AND nonce < :nonce
    ORDER BY nonce
"""

GET_NON_RELEASED_RESERVATIONS = """
    SELECT * FROM nonce_reservations
    WHERE chain_id = :chain_id AND signer_address = :address
    AND status != :released_status
    AND nonce >= :base_nonce
    ORDER BY nonce
"""

UPSERT_NONCE_RESERVATION = """
    INSERT INTO nonce_reservations (chain_id, signer_address, nonce, status, intent_id)
    VALUES (:chain_id, :address, :nonce, :status, :intent_id)
    ON CONFLICT(chain_id, signer_address, nonce) DO UPDATE SET
        status = EXCLUDED.status,
        intent_id = EXCLUDED.intent_id,
        updated_at = CURRENT_TIMESTAMP
"""

UPDATE_NONCE_RESERVATION_STATUS = """
    UPDATE nonce_reservations SET status = :status, updated_at = CURRENT_TIMESTAMP
    WHERE chain_id = :chain_id AND signer_address = :address AND nonce = :nonce
"""

UPDATE_NONCE_RESERVATION_STATUS_WITH_INTENT = """
    UPDATE nonce_reservations SET status = :status, intent_id = :intent_id, updated_at = CURRENT_TIMESTAMP
    WHERE chain_id = :chain_id AND signer_address = :address AND nonce = :nonce
"""

# Lock signer for nonce reservation (SQLite uses BEGIN IMMEDIATE in caller).
LOCK_SIGNER_FOR_UPDATE = """
    SELECT * FROM signers
    WHERE chain_id = :chain_id AND signer_address = :address
"""

ENSURE_SIGNER_EXISTS = """
    INSERT INTO signers (chain_id, signer_address, next_nonce, last_synced_chain_nonce)
    VALUES (:chain_id, :address, 0, NULL)
    ON CONFLICT(chain_id, signer_address) DO NOTHING
"""

# Cleanup orphaned nonces (SQLite).
CLEANUP_ORPHANED_NONCES = """
    DELETE FROM nonce_reservations
    WHERE chain_id = :chain_id
      AND status = 'orphaned'
      AND updated_at < datetime('now', :hours_offset)
"""

# =============================================================================
# Intents
# =============================================================================

CREATE_INTENT = """
    INSERT INTO tx_intents (
        intent_id, job_id, chain_id, signer_address, idempotency_key,
        to_address, data, value_wei, gas_limit, max_fee_per_gas,
        max_priority_fee_per_gas, min_confirmations, deadline_ts,
        broadcast_group, broadcast_endpoints_json, retry_after, status,
        metadata_json
    ) VALUES (
        :intent_id, :job_id, :chain_id, :signer_address, :idempotency_key,
        :to_address, :data, :value_wei, :gas_limit, :max_fee_per_gas,
        :max_priority_fee_per_gas, :min_confirmations, :deadline_ts,
        :broadcast_group, :broadcast_endpoints_json, NULL, 'created',
        :metadata_json
    )
    ON CONFLICT (chain_id, signer_address, idempotency_key) DO NOTHING
    RETURNING *
"""

GET_INTENT = "SELECT * FROM tx_intents WHERE intent_id = :intent_id"

GET_INTENT_BY_IDEMPOTENCY_KEY = """
    SELECT * FROM tx_intents
    WHERE chain_id = :chain_id
      AND signer_address = :signer_address
      AND idempotency_key = :idempotency_key
"""

# Claim next intent (SQLite).
CLAIM_NEXT_INTENT = """
    UPDATE tx_intents
    SET status = 'claimed', claim_token = :claim_token,
        claimed_at = CURRENT_TIMESTAMP, claimed_by = :claimed_by,
        lease_expires_at = datetime(CURRENT_TIMESTAMP, :lease_offset),
        retry_after = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE intent_id = (
        SELECT intent_id FROM tx_intents
        WHERE status = 'created'
        AND (deadline_ts IS NULL OR deadline_ts > CURRENT_TIMESTAMP)
        AND (retry_after IS NULL OR retry_after <= CURRENT_TIMESTAMP)
        ORDER BY created_at ASC
        LIMIT 1
    )
    RETURNING *
"""

UPDATE_INTENT_STATUS = """
    UPDATE tx_intents
    SET status = :status, updated_at = CURRENT_TIMESTAMP
    WHERE intent_id = :intent_id
"""


UPDATE_INTENT_RETRY_AFTER = """
    UPDATE tx_intents
    SET retry_after = :retry_after, retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
    WHERE intent_id = :intent_id
"""

RELEASE_INTENT_CLAIM = """
    UPDATE tx_intents
    SET status = 'created', claim_token = NULL, claimed_at = NULL,
        retry_after = :retry_after, updated_at = CURRENT_TIMESTAMP
    WHERE intent_id = :intent_id AND claim_token = :claim_token
"""

UPDATE_INTENT_BROADCAST_BINDING = """
    UPDATE tx_intents
    SET broadcast_group = :broadcast_group, broadcast_endpoints_json = :broadcast_endpoints_json,
        updated_at = CURRENT_TIMESTAMP
    WHERE intent_id = :intent_id
"""

GET_INTENT_COUNT_BY_STATUS = """
    SELECT COUNT(*) AS count FROM tx_intents
    WHERE status IN ({placeholders}) AND job_id = :job_id
"""

GET_PENDING_INTENT_COUNT = """
    SELECT COUNT(*) AS count FROM tx_intents
    WHERE status IN ({placeholders})
"""

GET_BACKING_OFF_INTENT_COUNT = """
    SELECT COUNT(*) AS count FROM tx_intents
    WHERE retry_after > CURRENT_TIMESTAMP
"""

# =============================================================================
# Attempts
# =============================================================================

CREATE_ATTEMPT = """
    INSERT INTO tx_attempts (
        attempt_id, intent_id, nonce, tx_hash, gas_params_json,
        status, broadcast_block, broadcast_at, broadcast_group, endpoint_url,
        endpoint_binding_id
    ) VALUES (
        :attempt_id, :intent_id, :nonce, :tx_hash, :gas_params_json,
        :status, :broadcast_block, :broadcast_at, :broadcast_group, :endpoint_url,
        :endpoint_binding_id
    )
    RETURNING *
"""

GET_ATTEMPT = "SELECT * FROM tx_attempts WHERE attempt_id = :attempt_id"

GET_ATTEMPT_BY_TX_HASH = "SELECT * FROM tx_attempts WHERE tx_hash = :tx_hash"

GET_ATTEMPTS_FOR_INTENT = """
    SELECT * FROM tx_attempts WHERE intent_id = :intent_id ORDER BY created_at DESC
"""

GET_LATEST_ATTEMPT_FOR_INTENT = """
    SELECT * FROM tx_attempts
    WHERE intent_id = :intent_id
    ORDER BY created_at DESC
    LIMIT 1
"""

UPDATE_ATTEMPT_STATUS = """
    UPDATE tx_attempts
    SET status = :status, updated_at = CURRENT_TIMESTAMP
    WHERE attempt_id = :attempt_id
"""

UPDATE_ATTEMPT_INCLUDED = """
    UPDATE tx_attempts
    SET status = :status, included_block = :included_block, updated_at = CURRENT_TIMESTAMP
    WHERE attempt_id = :attempt_id
"""

UPDATE_ATTEMPT_ERROR = """
    UPDATE tx_attempts
    SET status = :status, error_code = :error_code, error_detail = :error_detail,
        updated_at = CURRENT_TIMESTAMP
    WHERE attempt_id = :attempt_id
"""

GET_PENDING_ATTEMPTS = """
    SELECT * FROM tx_attempts
    WHERE status = 'pending' AND intent_id IN (
        SELECT intent_id FROM tx_intents WHERE chain_id = :chain_id
    )
    ORDER BY created_at ASC
"""

# =============================================================================
# ABI Cache
# =============================================================================

GET_ABI_CACHE = """
    SELECT * FROM abi_cache
    WHERE chain_id = :chain_id AND address = :address
"""

UPSERT_ABI_CACHE = """
    INSERT INTO abi_cache (chain_id, address, abi_json, source)
    VALUES (:chain_id, :address, :abi_json, :source)
    ON CONFLICT(chain_id, address) DO UPDATE SET
        abi_json = EXCLUDED.abi_json,
        source = EXCLUDED.source,
        resolved_at = CURRENT_TIMESTAMP
"""

DELETE_ABI_CACHE = """
    DELETE FROM abi_cache WHERE chain_id = :chain_id AND address = :address
"""

# =============================================================================
# Proxy Cache
# =============================================================================

GET_PROXY_CACHE = """
    SELECT * FROM proxy_cache
    WHERE chain_id = :chain_id AND proxy_address = :proxy_address
"""

UPSERT_PROXY_CACHE = """
    INSERT INTO proxy_cache (chain_id, proxy_address, implementation_address)
    VALUES (:chain_id, :proxy_address, :implementation_address)
    ON CONFLICT(chain_id, proxy_address) DO UPDATE SET
        implementation_address = EXCLUDED.implementation_address,
        resolved_at = CURRENT_TIMESTAMP
"""

DELETE_PROXY_CACHE = """
    DELETE FROM proxy_cache WHERE chain_id = :chain_id AND proxy_address = :proxy_address
"""

# =============================================================================
# Cleanup / Maintenance
# =============================================================================

DELETE_ABANDONED_INTENTS = """
    DELETE FROM tx_intents
    WHERE status = 'created'
    AND created_at < :cutoff_time
"""

# =============================================================================
# Job Logs
# =============================================================================

INSERT_JOB_LOG = """
    INSERT INTO job_logs (chain_id, job_id, block_number, level, fields_json)
    VALUES (:chain_id, :job_id, :block_number, :level, :fields_json)
"""

LIST_JOB_LOGS = """
    SELECT * FROM job_logs
    WHERE chain_id = :chain_id AND job_id = :job_id
    ORDER BY ts DESC
    LIMIT :limit
"""

LIST_ALL_JOB_LOGS = """
    SELECT * FROM job_logs
    WHERE chain_id = :chain_id
    ORDER BY ts DESC
    LIMIT :limit
"""

LIST_LATEST_JOB_LOGS = """
    SELECT * FROM job_logs l1
    WHERE chain_id = :chain_id
    AND ts = (SELECT MAX(ts) FROM job_logs l2
              WHERE l2.job_id = l1.job_id AND l2.chain_id = :chain_id)
    ORDER BY job_id
"""

DELETE_OLD_JOB_LOGS = """
    DELETE FROM job_logs
    WHERE chain_id = :chain_id AND ts < :cutoff
"""
