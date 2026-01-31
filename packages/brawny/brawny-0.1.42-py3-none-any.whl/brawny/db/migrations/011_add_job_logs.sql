-- Job logs for operator-visible snapshots during check()
-- Version: 011

CREATE TABLE IF NOT EXISTS job_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL,
    job_id VARCHAR(200) NOT NULL,
    block_number BIGINT,
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    fields_json TEXT NOT NULL
);

-- Primary query: recent logs for a job
CREATE INDEX IF NOT EXISTS idx_job_logs_job_ts
    ON job_logs(chain_id, job_id, ts DESC);

-- Cleanup query: purge old logs (per-chain)
CREATE INDEX IF NOT EXISTS idx_job_logs_chain_ts
    ON job_logs(chain_id, ts);

-- Record migration
INSERT INTO schema_migrations (version) VALUES ('011');
