-- Enforce single initial attempt per intent+nonce (replacements allowed)

CREATE UNIQUE INDEX IF NOT EXISTS uq_tx_attempts_intent_nonce_initial
    ON tx_attempts(intent_id, nonce)
    WHERE replaces_attempt_id IS NULL;

INSERT INTO schema_migrations (version) VALUES ('020');
