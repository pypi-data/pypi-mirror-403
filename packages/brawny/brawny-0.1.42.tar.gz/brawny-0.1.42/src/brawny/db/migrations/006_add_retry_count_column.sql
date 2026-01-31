-- Add retry_count to tx_intents for tracking execution attempts
-- Version: 006
-- Description: Move retry tracking from job_kv to native column for atomicity

ALTER TABLE tx_intents ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0;

-- Index for querying intents by retry count (e.g., finding frequently retried intents)
CREATE INDEX IF NOT EXISTS idx_tx_intents_retry_count
    ON tx_intents(retry_count) WHERE retry_count > 0;

INSERT INTO schema_migrations (version) VALUES ('006');
