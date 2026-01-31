-- Add job cooldown tracking
CREATE TABLE IF NOT EXISTS job_cooldowns (
    cooldown_key TEXT PRIMARY KEY,
    last_intent_at INTEGER NOT NULL
);

INSERT INTO schema_migrations (version) VALUES ('019')
ON CONFLICT (version) DO NOTHING;
