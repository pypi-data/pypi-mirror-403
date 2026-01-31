-- Add binding identifier for attempts and enforce uniqueness per binding

ALTER TABLE tx_intents ADD COLUMN broadcast_binding_id UUID;
ALTER TABLE tx_attempts ADD COLUMN endpoint_binding_id UUID;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tx_attempts_intent_nonce_binding_hash
    ON tx_attempts(intent_id, nonce, endpoint_binding_id, tx_hash)
    WHERE tx_hash IS NOT NULL AND endpoint_binding_id IS NOT NULL;

INSERT INTO schema_migrations (version) VALUES ('013');
