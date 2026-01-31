-- Add terminal_reason and halt_reason to tx_intents
ALTER TABLE tx_intents ADD COLUMN terminal_reason VARCHAR(30);
ALTER TABLE tx_intents ADD COLUMN halt_reason VARCHAR(50);

UPDATE tx_intents
SET terminal_reason = status
WHERE status IN ('confirmed', 'failed', 'abandoned')
  AND terminal_reason IS NULL;

INSERT INTO schema_migrations (version) VALUES ('021');
