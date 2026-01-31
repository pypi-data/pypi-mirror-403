-- Add composite index for efficient nonce gap age queries
-- Makes the MIN(created_at) scan an index walk instead of heap scan
-- Version: 010
-- Note: CONCURRENTLY removed for SQLite compatibility

CREATE INDEX IF NOT EXISTS idx_nonce_res_chain_signer_status_nonce_created
ON nonce_reservations (chain_id, signer_address, status, nonce, created_at);

INSERT INTO schema_migrations (version) VALUES ('010');
