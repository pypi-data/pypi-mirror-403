-- Add broadcast_at to tx_attempts for accurate confirmation timing

ALTER TABLE tx_attempts
    ADD COLUMN broadcast_at TIMESTAMP;

UPDATE tx_attempts
SET broadcast_at = updated_at
WHERE broadcast_at IS NULL;

INSERT INTO schema_migrations (version) VALUES ('003');
