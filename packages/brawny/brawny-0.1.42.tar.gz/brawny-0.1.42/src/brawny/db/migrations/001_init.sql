-- brawny initial schema migration
-- Version: 001
-- Description: Create all core tables for the brawny framework

-- ============================================================================
-- Migration tracking table
-- ============================================================================
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 1. Block State - tracks last processed block per chain
-- ============================================================================
CREATE TABLE IF NOT EXISTS block_state (
    chain_id INTEGER PRIMARY KEY,
    last_processed_block_number BIGINT NOT NULL,
    last_processed_block_hash VARCHAR(66) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. Block Hash History - for reorg detection
-- ============================================================================
CREATE TABLE IF NOT EXISTS block_hash_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL,
    block_number BIGINT NOT NULL,
    block_hash VARCHAR(66) NOT NULL,
    inserted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (chain_id, block_number)
);

CREATE INDEX IF NOT EXISTS idx_block_hash_history_chain_block
    ON block_hash_history(chain_id, block_number DESC);

-- ============================================================================
-- 3. Jobs - job registry and configuration
-- ============================================================================
CREATE TABLE IF NOT EXISTS jobs (
    job_id VARCHAR(200) PRIMARY KEY,
    job_name VARCHAR(200) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    check_interval_blocks INTEGER NOT NULL DEFAULT 1,
    last_checked_block_number BIGINT,
    last_triggered_block_number BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_enabled ON jobs(enabled) WHERE enabled = true;

-- ============================================================================
-- 4. Job KV Store - persistent key-value storage per job
-- ============================================================================
CREATE TABLE IF NOT EXISTS job_kv (
    job_id VARCHAR(200) NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    key VARCHAR(200) NOT NULL,
    value_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id, key)
);

-- ============================================================================
-- 5. Signers - tracks nonce state per signer per chain
-- ============================================================================
CREATE TABLE IF NOT EXISTS signers (
    chain_id INTEGER NOT NULL,
    signer_address VARCHAR(42) NOT NULL,
    next_nonce BIGINT NOT NULL DEFAULT 0,
    last_synced_chain_nonce BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chain_id, signer_address)
);

-- ============================================================================
-- 6. Nonce Reservations - tracks nonce allocation and status
-- ============================================================================
CREATE TABLE IF NOT EXISTS nonce_reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL,
    signer_address VARCHAR(42) NOT NULL,
    nonce BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('reserved', 'in_flight', 'released', 'orphaned')),
    intent_id UUID,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (chain_id, signer_address, nonce)
);

CREATE INDEX IF NOT EXISTS idx_nonce_reservations_signer_status
    ON nonce_reservations(chain_id, signer_address, status);

-- ============================================================================
-- 7. Transaction Intents - durable transaction intent records
-- ============================================================================
CREATE TABLE IF NOT EXISTS tx_intents (
    intent_id UUID PRIMARY KEY,
    job_id VARCHAR(200) NOT NULL,
    chain_id INTEGER NOT NULL,
    signer_address VARCHAR(42) NOT NULL,
    idempotency_key VARCHAR(200) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    data TEXT,
    value_wei VARCHAR(78) NOT NULL DEFAULT '0',
    gas_limit BIGINT,
    max_fee_per_gas VARCHAR(78),
    max_priority_fee_per_gas VARCHAR(78),
    min_confirmations INTEGER NOT NULL DEFAULT 1,
    deadline_ts TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'created' CHECK (
        status IN ('created', 'claimed', 'sending', 'pending', 'confirmed', 'failed', 'abandoned')
    ),
    claim_token VARCHAR(100),
    claimed_at TIMESTAMP,
    claimed_by VARCHAR(200),
    lease_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tx_intents_status ON tx_intents(status);
CREATE INDEX IF NOT EXISTS idx_tx_intents_job_status ON tx_intents(job_id, status);
CREATE INDEX IF NOT EXISTS idx_tx_intents_signer_status ON tx_intents(chain_id, signer_address, status);
CREATE INDEX IF NOT EXISTS idx_tx_intents_created ON tx_intents(created_at);

-- Idempotency is scoped to (chain_id, signer_address)
CREATE UNIQUE INDEX IF NOT EXISTS uq_tx_intents_idempotency_scoped
    ON tx_intents(chain_id, signer_address, idempotency_key);

-- ============================================================================
-- 8. Transaction Attempts - individual broadcast attempts
-- ============================================================================
CREATE TABLE IF NOT EXISTS tx_attempts (
    attempt_id UUID PRIMARY KEY,
    intent_id UUID NOT NULL REFERENCES tx_intents(intent_id),
    nonce BIGINT NOT NULL,
    tx_hash VARCHAR(66),
    gas_params_json TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'signed' CHECK (
        status IN ('signed', 'pending_send', 'broadcast', 'pending', 'confirmed', 'failed', 'replaced')
    ),
    error_code VARCHAR(100),
    error_detail TEXT,
    replaces_attempt_id UUID REFERENCES tx_attempts(attempt_id),
    broadcast_block BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tx_attempts_intent ON tx_attempts(intent_id);
CREATE INDEX IF NOT EXISTS idx_tx_attempts_tx_hash ON tx_attempts(tx_hash) WHERE tx_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tx_attempts_status ON tx_attempts(status);

-- ============================================================================
-- 9. ABI Cache - cached contract ABIs
-- ============================================================================
CREATE TABLE IF NOT EXISTS abi_cache (
    chain_id INTEGER NOT NULL,
    address VARCHAR(42) NOT NULL,
    abi_json TEXT NOT NULL,
    source VARCHAR(30) NOT NULL CHECK (source IN ('etherscan', 'sourcify', 'manual', 'proxy_implementation')),
    resolved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chain_id, address)
);

CREATE INDEX IF NOT EXISTS idx_abi_cache_resolved ON abi_cache(resolved_at);

-- ============================================================================
-- 10. Proxy Cache - cached proxy-to-implementation mappings
-- ============================================================================
CREATE TABLE IF NOT EXISTS proxy_cache (
    chain_id INTEGER NOT NULL,
    proxy_address VARCHAR(42) NOT NULL,
    implementation_address VARCHAR(42) NOT NULL,
    resolved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chain_id, proxy_address)
);

-- ============================================================================
-- Record this migration
-- ============================================================================
INSERT INTO schema_migrations (version) VALUES ('001');
