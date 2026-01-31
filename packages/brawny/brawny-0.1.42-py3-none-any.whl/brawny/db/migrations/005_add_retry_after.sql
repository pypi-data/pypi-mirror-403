-- Add retry_after to tx_intents for execution backoff
-- Version: 005

ALTER TABLE tx_intents ADD COLUMN retry_after TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_tx_intents_retry_after
    ON tx_intents(retry_after);

INSERT INTO schema_migrations (version) VALUES ('005');
