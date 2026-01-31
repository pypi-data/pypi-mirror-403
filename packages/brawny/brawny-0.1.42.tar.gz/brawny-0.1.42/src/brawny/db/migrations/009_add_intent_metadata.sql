-- Add metadata_json column to tx_intents table
-- Stores per-intent context for alerts (JSON-serializable dict)
-- trigger.reason is auto-merged into this field

ALTER TABLE tx_intents ADD COLUMN metadata_json TEXT;
