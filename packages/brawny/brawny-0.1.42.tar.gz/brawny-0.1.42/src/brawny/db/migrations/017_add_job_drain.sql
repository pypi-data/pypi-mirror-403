-- Description: Add job drain controls

ALTER TABLE jobs ADD COLUMN drain_until TIMESTAMP;
ALTER TABLE jobs ADD COLUMN drain_reason TEXT;

INSERT INTO schema_migrations (version) VALUES ('017');
