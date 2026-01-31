-- Add signer_alias columns for intent/transaction auditing
-- Note: SQLite does not support "IF NOT EXISTS" for ALTER TABLE ADD COLUMN

ALTER TABLE tx_intents ADD COLUMN signer_alias VARCHAR(200);

-- Normalize existing address data to lowercase canonical form.
UPDATE signers SET signer_address = lower(signer_address);
UPDATE nonce_reservations SET signer_address = lower(signer_address);
UPDATE tx_intents SET signer_address = lower(signer_address), to_address = lower(to_address);
UPDATE abi_cache SET address = lower(address);
UPDATE proxy_cache SET proxy_address = lower(proxy_address),
    implementation_address = lower(implementation_address);

INSERT INTO schema_migrations (version) VALUES ('015');
