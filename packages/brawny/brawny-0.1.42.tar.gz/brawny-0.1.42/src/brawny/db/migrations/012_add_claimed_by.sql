-- SQLite handled in migrator (idempotent)
ALTER TABLE tx_intents ADD COLUMN claimed_by VARCHAR(200);

INSERT INTO schema_migrations (version) VALUES ('012')
ON CONFLICT (version) DO NOTHING;
