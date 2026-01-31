-- Add lease_expires_at for intent claim leases
ALTER TABLE tx_intents ADD COLUMN lease_expires_at TIMESTAMP;

INSERT INTO schema_migrations (version) VALUES ('014')
ON CONFLICT (version) DO NOTHING;
