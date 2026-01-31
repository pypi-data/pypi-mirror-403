-- Collapse intent statuses to: created, claimed, broadcasted, terminal

CREATE TABLE tx_intents_new (
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
        status IN ('created', 'claimed', 'broadcasted', 'terminal')
    ),
    claim_token VARCHAR(100),
    claimed_at TIMESTAMP,
    claimed_by VARCHAR(200),
    lease_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retry_after TIMESTAMP,
    retry_count INTEGER NOT NULL DEFAULT 0,
    broadcast_group VARCHAR(100),
    broadcast_endpoints_json TEXT,
    metadata_json TEXT,
    broadcast_binding_id UUID,
    signer_alias VARCHAR(200),
    terminal_reason VARCHAR(30),
    halt_reason VARCHAR(50)
);

INSERT INTO tx_intents_new (
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
    status,
    claim_token,
    claimed_at,
    claimed_by,
    lease_expires_at,
    created_at,
    updated_at,
    retry_after,
    retry_count,
    broadcast_group,
    broadcast_endpoints_json,
    metadata_json,
    broadcast_binding_id,
    signer_alias,
    terminal_reason,
    halt_reason
)
SELECT
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
    CASE
        WHEN status = 'created' THEN 'created'
        WHEN status = 'claimed' THEN 'claimed'
        WHEN status IN ('sending', 'pending') AND EXISTS (
            SELECT 1 FROM tx_attempts
            WHERE tx_attempts.intent_id = tx_intents.intent_id
              AND tx_attempts.tx_hash IS NOT NULL
        ) THEN 'broadcasted'
        WHEN status IN ('confirmed', 'failed', 'abandoned') THEN 'terminal'
        WHEN status IN ('sending', 'pending') THEN 'terminal'
        ELSE 'terminal'
    END AS status,
    claim_token,
    claimed_at,
    claimed_by,
    lease_expires_at,
    created_at,
    updated_at,
    retry_after,
    retry_count,
    broadcast_group,
    broadcast_endpoints_json,
    metadata_json,
    broadcast_binding_id,
    signer_alias,
    CASE
        WHEN status IN ('confirmed', 'failed', 'abandoned') THEN COALESCE(terminal_reason, status)
        ELSE NULL
    END AS terminal_reason,
    CASE
        WHEN status IN ('sending', 'pending') AND NOT EXISTS (
            SELECT 1 FROM tx_attempts
            WHERE tx_attempts.intent_id = tx_intents.intent_id
              AND tx_attempts.tx_hash IS NOT NULL
        ) THEN 'missing_tx_hash'
        WHEN status NOT IN (
            'created',
            'claimed',
            'sending',
            'pending',
            'confirmed',
            'failed',
            'abandoned'
        ) THEN 'legacy_unmapped_status'
        ELSE NULL
    END AS halt_reason
FROM tx_intents;

DROP TABLE tx_intents;
ALTER TABLE tx_intents_new RENAME TO tx_intents;

CREATE INDEX IF NOT EXISTS idx_tx_intents_status ON tx_intents(status);
CREATE INDEX IF NOT EXISTS idx_tx_intents_job_status ON tx_intents(job_id, status);
CREATE INDEX IF NOT EXISTS idx_tx_intents_signer_status ON tx_intents(chain_id, signer_address, status);
CREATE INDEX IF NOT EXISTS idx_tx_intents_created ON tx_intents(created_at);
CREATE INDEX IF NOT EXISTS idx_tx_intents_broadcast_group
    ON tx_intents(broadcast_group);
CREATE INDEX IF NOT EXISTS idx_tx_intents_retry_after
    ON tx_intents(retry_after);
CREATE INDEX IF NOT EXISTS idx_tx_intents_retry_count
    ON tx_intents(retry_count) WHERE retry_count > 0;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tx_intents_idempotency_scoped
    ON tx_intents(chain_id, signer_address, idempotency_key);

INSERT INTO schema_migrations (version) VALUES ('022');
