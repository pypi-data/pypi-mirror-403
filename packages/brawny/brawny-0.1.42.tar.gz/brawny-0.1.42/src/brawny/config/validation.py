"""Configuration validation for brawny.

Provides validation logic for config values and endpoint canonicalization.
"""

from __future__ import annotations

from urllib.parse import urlparse

from brawny.alerts.routing import is_chat_id
from brawny.model.enums import KeystoreType
from brawny.model.errors import ConfigError


class InvalidEndpointError(Exception):
    """Raised when an endpoint URL is malformed."""

    pass


def canonicalize_endpoint(url: str) -> str:
    """Normalize endpoint URL for consistent comparison.

    Rules:
    - Strip whitespace
    - Require http or https scheme
    - Require non-empty hostname
    - Lowercase scheme and hostname
    - Remove default ports (80/443)
    - Remove trailing slash (except root)
    - Drop query string (RPC endpoints don't use them)

    Raises:
        InvalidEndpointError: If URL is missing scheme or hostname
    """
    url = url.strip()
    if not url:
        raise InvalidEndpointError("Empty endpoint URL")

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    # Validate scheme
    if scheme not in {"http", "https"}:
        raise InvalidEndpointError(
            f"Invalid endpoint '{url}': scheme must be http or https, got '{scheme or '(none)'}'"
        )

    # Validate hostname
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise InvalidEndpointError(f"Invalid endpoint '{url}': missing hostname")

    port = parsed.port
    if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
        port = None

    # Preserve Basic Auth credentials if present (e.g., https://user:pass@host)
    userinfo = ""
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += f":{parsed.password}"
        userinfo += "@"

    netloc = f"{userinfo}{hostname}:{port}" if port else f"{userinfo}{hostname}"
    path = parsed.path.rstrip("/") if len(parsed.path) > 1 else ""

    # Drop query string — RPC endpoints don't use them, and they cause
    # accidental uniqueness (e.g., tracking params, cache busters)
    return f"{scheme}://{netloc}{path}"


def dedupe_preserve_order(endpoints: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for ep in endpoints:
        if ep not in seen:
            seen.add(ep)
            result.append(ep)
    return result


def canonicalize_endpoints(endpoints: list[str]) -> list[str]:
    """Canonicalize endpoint list for stable comparison.

    Applies canonicalize_endpoint to each entry, then sorts for deterministic
    equality checks.
    """
    canonical = [canonicalize_endpoint(ep) for ep in endpoints]
    return sorted(set(canonical))


REMOVED_FIELDS = {
    "alerts_dx_enabled",
    "allowed_signers",
    "broadcast_rpc",
    "broadcast_url",
    "rpc_endpoints",
    "deep_reorg_alert_enabled",
    "etherscan_api_key",
    "etherscan_api_url",
    "job_modules",
    "jobs_path",
    "log_level",
    "log_format",
    "metrics_enabled",
    "metrics_bind",
    "networks",
    "signers",
    "sourcify_enabled",
    "strict_job_validation",
    "telegram_chat_ids",
    "webhook_url",
    "block_hash_history_size",
    "brownie_password_fallback",
    "claim_timeout_seconds",
    "db_circuit_breaker_failures",
    "db_circuit_breaker_seconds",
    "deep_reorg_pause",
    "intent_retry_backoff_seconds",
    "rpc_circuit_breaker_seconds",
    "rpc_default_group",
    "shutdown_grace_seconds",
    "shutdown_timeout_seconds",
}


def validate_no_removed_fields(raw_config: dict) -> None:
    """Fail fast if removed config options are present."""
    forbidden: set[str] = set()
    for key in raw_config.keys():
        if key in REMOVED_FIELDS:
            forbidden.add(key)

    advanced = raw_config.get("advanced")
    if isinstance(advanced, dict):
        for key in advanced.keys():
            if key in REMOVED_FIELDS:
                forbidden.add(key)

    if forbidden:
        raise ConfigError(
            "Removed config options detected: "
            f"{sorted(forbidden)}. These options no longer exist."
        )


def validate_config(config: "Config") -> None:
    """Validate all configuration values.

    Args:
        config: Config instance to validate

    Raises:
        ConfigError: If validation fails
    """
    from brawny.config.models import Config

    errors: list[str] = []

    # Required fields
    if not config.database_url:
        errors.append("database_url is required")
    elif not config.database_url.startswith("sqlite:///"):
        errors.append("database_url must start with sqlite:///")
    elif config.worker_count > 1:
        errors.append("SQLite does not support worker_count > 1.")

    if not config.rpc_groups:
        errors.append("rpc_groups is required (at least one group)")

    if config.guardrails:
        lint_paths = config.guardrails.lint_paths
        if not isinstance(lint_paths, list):
            errors.append("guardrails.lint_paths must be a list")
        else:
            for idx, value in enumerate(lint_paths):
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"guardrails.lint_paths[{idx}] must be a non-empty string")

    if config.debug and not isinstance(config.debug.allow_console, bool):
        errors.append("debug.allow_console must be a boolean")

    if not isinstance(config.production, bool):
        errors.append("production must be a boolean")

    if config.intent_cooldown:
        cd = config.intent_cooldown
        if not isinstance(cd.enabled, bool):
            errors.append("intent_cooldown.enabled must be a boolean")
        if cd.default_seconds < 0:
            errors.append("intent_cooldown.default_seconds cannot be negative")
        if cd.max_seconds < 0:
            errors.append("intent_cooldown.max_seconds cannot be negative")
        if cd.max_seconds < cd.default_seconds:
            errors.append("intent_cooldown.max_seconds must be >= default_seconds")
        if cd.prune_older_than_days < 0:
            errors.append("intent_cooldown.prune_older_than_days cannot be negative")

    tg = config.telegram
    if not isinstance(tg.admin, list) or not tg.admin:
        errors.append("telegram.admin is required")

    if not isinstance(tg.chats, dict) or not tg.chats:
        errors.append("telegram.chats must be a non-empty mapping of name -> chat_id")
    else:
        for name, chat_id in tg.chats.items():
            if not isinstance(name, str) or not name.strip():
                errors.append("telegram.chats keys must be non-empty strings")
                break
            if not isinstance(chat_id, str) or not chat_id.strip():
                errors.append(f"telegram.chats.{name} must be a non-empty string")
                continue
            if not is_chat_id(chat_id):
                errors.append(f"telegram.chats.{name} must be a numeric chat ID")

    valid_names = set(tg.chats.keys()) if isinstance(tg.chats, dict) else set()

    def _validate_name_list(label: str, values: object, required: bool = False) -> None:
        if values is None:
            if required:
                errors.append(f"{label} is required")
            return
        if not isinstance(values, list):
            errors.append(f"{label} must be a list")
            return
        if required and not values:
            errors.append(f"{label} is required")
            return
        for value in values:
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label} entries must be non-empty strings")
                continue
            if value not in valid_names:
                errors.append(f"{label} references unknown chat '{value}'")

    _validate_name_list("telegram.admin", tg.admin, required=True)
    _validate_name_list("telegram.public", tg.public, required=False)
    _validate_name_list("telegram.default", tg.default, required=False)
    if tg.public_rate_limit_seconds <= 0:
        errors.append("telegram.rate_limits.public must be > 0")

    if config.chain_id <= 0:
        errors.append("chain_id must be positive")

    # RPC Groups validation
    if config.rpc_groups:
        for name, group in config.rpc_groups.items():
            if not group.endpoints:
                errors.append(f"rpc_groups.{name} has no endpoints")

        defaults = config.rpc_defaults
        if not defaults:
            errors.append("rpc.defaults is required")
        else:
            if defaults.read not in config.rpc_groups:
                errors.append(f"rpc.defaults.read '{defaults.read}' not found in rpc_groups")
            if defaults.broadcast not in config.rpc_groups:
                errors.append(
                    f"rpc.defaults.broadcast '{defaults.broadcast}' not found in rpc_groups"
                )

    if config.worker_count <= 0:
        errors.append("worker_count must be positive")

    # Keystore validation
    if config.keystore_type == KeystoreType.FILE and not config.keystore_path:
        errors.append("keystore_path is required when keystore_type is 'file'")

    # HTTP allowlist validation
    for domain in config.http.allowed_domains:
        if "://" in domain:
            errors.append(f"http.allowed_domains entries must be hostnames, got: {domain}")
        if "/" in domain:
            errors.append(f"http.allowed_domains entries must not include paths: {domain}")
    if config.http.connect_timeout_seconds <= 0:
        errors.append("http.connect_timeout_seconds must be positive")
    if config.http.read_timeout_seconds <= 0:
        errors.append("http.read_timeout_seconds must be positive")
    if config.http.max_retries < 0:
        errors.append("http.max_retries cannot be negative")

    if errors:
        raise ConfigError(
            "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def validate_advanced_config(advanced: "AdvancedConfig") -> None:
    """Validate advanced configuration values."""
    from brawny.config.models import AdvancedConfig

    if not isinstance(advanced, AdvancedConfig):
        raise ConfigError("advanced config must be an AdvancedConfig instance")

    errors: list[str] = []

    if advanced.poll_interval_seconds <= 0:
        errors.append("poll_interval_seconds must be positive")
    if advanced.reorg_depth <= 0:
        errors.append("reorg_depth must be positive")
    if advanced.finality_confirmations < 0:
        errors.append("finality_confirmations must be non-negative")
    if advanced.default_deadline_seconds <= 0:
        errors.append("default_deadline_seconds must be positive")
    if advanced.stuck_tx_seconds <= 0:
        errors.append("stuck_tx_seconds must be positive")
    if advanced.max_replacement_attempts < 0:
        errors.append("max_replacement_attempts cannot be negative")

    if advanced.gas_limit_multiplier < 1.0:
        errors.append("gas_limit_multiplier must be at least 1.0")
    if advanced.default_priority_fee_gwei < 0:
        errors.append("default_priority_fee_gwei must be non-negative")
    if advanced.max_fee_cap_gwei is not None and advanced.max_fee_cap_gwei <= 0:
        errors.append("max_fee_cap_gwei must be positive when set")
    if advanced.fee_bump_percent < 10:
        errors.append("fee_bump_percent must be at least 10 (Ethereum protocol minimum)")

    if advanced.rpc_timeout_seconds <= 0:
        errors.append("rpc_timeout_seconds must be positive")
    if advanced.rpc_max_retries < 0:
        errors.append("rpc_max_retries cannot be negative")

    if errors:
        raise ConfigError(
            "Advanced configuration validation failed:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
