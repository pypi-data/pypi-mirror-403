-- Migration 007: Add gap tracking columns to signers table
--
-- Adds:
--   - gap_started_at: Timestamp when nonce gap blocking started (for alerts)
--   - alias: Optional human-readable alias for signers
--
-- Part of nonce policy simplification - see NONCE.md

-- Add gap tracking column (nullable timestamp)
ALTER TABLE signers ADD COLUMN gap_started_at TIMESTAMP;

-- Add optional alias column
ALTER TABLE signers ADD COLUMN alias VARCHAR(50);

-- Index for alias lookup (partial index, only non-null aliases)
CREATE INDEX IF NOT EXISTS idx_signers_alias ON signers (chain_id, alias) WHERE alias IS NOT NULL;

INSERT INTO schema_migrations (version) VALUES ('007');
