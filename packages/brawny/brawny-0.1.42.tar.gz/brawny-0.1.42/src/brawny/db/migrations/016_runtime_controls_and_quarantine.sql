-- Description: Add signer quarantine, runtime controls, and mutation audit

-- Signer containment
ALTER TABLE signers ADD COLUMN quarantined_at TIMESTAMP;
ALTER TABLE signers ADD COLUMN quarantine_reason TEXT;
ALTER TABLE signers ADD COLUMN replacements_paused INTEGER NOT NULL DEFAULT 0;

-- Runtime controls (containment with TTL)
CREATE TABLE IF NOT EXISTS runtime_controls (
    control VARCHAR(100) PRIMARY KEY,
    active INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMP,
    reason TEXT,
    actor TEXT,
    mode VARCHAR(20) NOT NULL DEFAULT 'auto',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Durable mutation audit (minimal, append-only)
CREATE TABLE IF NOT EXISTS mutation_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(50) NOT NULL,
    entity_id TEXT NOT NULL,
    action VARCHAR(100) NOT NULL,
    actor TEXT,
    reason TEXT,
    source TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version) VALUES ('016');
