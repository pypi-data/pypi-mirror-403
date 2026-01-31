-- Add included_block to tx_attempts for receipt inclusion tracking
-- Version: 002

ALTER TABLE tx_attempts
    ADD COLUMN included_block BIGINT;

INSERT INTO schema_migrations (version) VALUES ('002');
