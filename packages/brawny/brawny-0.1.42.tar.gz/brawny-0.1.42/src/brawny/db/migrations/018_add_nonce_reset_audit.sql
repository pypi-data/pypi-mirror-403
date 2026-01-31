-- Audit table for nonce force resets
-- Provides durable record of destructive nonce operations for incident investigation

CREATE TABLE IF NOT EXISTS nonce_reset_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL,
    signer_address TEXT NOT NULL,
    old_next_nonce INTEGER,
    new_next_nonce INTEGER NOT NULL,
    released_reservations INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL,  -- 'cli', 'executor', 'api'
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nonce_reset_audit_signer
    ON nonce_reset_audit(chain_id, signer_address);

CREATE INDEX IF NOT EXISTS idx_nonce_reset_audit_created
    ON nonce_reset_audit(created_at);
