-- Migration: Broadcast binding for RPC groups privacy invariant
--
-- This adds columns to track which RPC group and endpoints were used for
-- the first broadcast of an intent. Retries MUST use the same endpoint list
-- to preserve the privacy invariant (no cross-group fallback).

-- Broadcast binding on intents (set on first successful broadcast)
ALTER TABLE tx_intents ADD COLUMN broadcast_group VARCHAR(100);
ALTER TABLE tx_intents ADD COLUMN broadcast_endpoints_json TEXT;

-- Index for querying by broadcast group
CREATE INDEX IF NOT EXISTS idx_tx_intents_broadcast_group
    ON tx_intents(broadcast_group);

-- Audit trail on attempts (which endpoint was actually used)
ALTER TABLE tx_attempts ADD COLUMN broadcast_group VARCHAR(100);
ALTER TABLE tx_attempts ADD COLUMN endpoint_url VARCHAR(500);

-- Record migration
INSERT INTO schema_migrations (version) VALUES ('004');
