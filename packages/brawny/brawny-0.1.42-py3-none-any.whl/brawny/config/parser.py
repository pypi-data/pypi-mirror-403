"""Configuration parsing for brawny.

Provides functions to load config from YAML files and environment variables.
"""

from __future__ import annotations

import os
import re
from typing import Callable
from dataclasses import replace

from brawny.model.enums import KeystoreType
from brawny.model.errors import ConfigError

try:
    import yaml
except ImportError:  # pragma: no cover - handled by dependency management
    yaml = None

# Pattern to match ${VAR_NAME}, ${VAR_NAME:-default}, or ${{VAR_NAME}} forms
ENV_VAR_PATTERN = re.compile(r"\$\{\{?([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}?\}")

_ADVANCED_FIELDS = {
    "poll_interval_seconds",
    "reorg_depth",
    "finality_confirmations",
    "default_deadline_seconds",
    "stuck_tx_seconds",
    "max_replacement_attempts",
    "gas_limit_multiplier",
    "default_priority_fee_gwei",
    "max_fee_cap_gwei",
    "fee_bump_percent",
    "rpc_timeout_seconds",
    "rpc_max_retries",
}

_REMOVED_ENV_KEYS = {
    "ALERTS_DX_ENABLED",
    "ALLOWED_SIGNERS",
    "BLOCK_HASH_HISTORY_SIZE",
    "ENABLE_BROWNIE_PASSWORD_FALLBACK",
    "CLAIM_TIMEOUT_SECONDS",
    "DB_CIRCUIT_BREAKER_FAILURES",
    "DB_CIRCUIT_BREAKER_SECONDS",
    "DEEP_REORG_PAUSE",
    "DEEP_REORG_ALERT_ENABLED",
    "ETHERSCAN_API_URL",
    "INTENT_RETRY_BACKOFF_SECONDS",
    "JOB_MODULES",
    "JOBS_PATH",
    "LOG_FORMAT",
    "RPC_CIRCUIT_BREAKER_SECONDS",
    "SHUTDOWN_GRACE_SECONDS",
    "SHUTDOWN_TIMEOUT_SECONDS",
    "MAX_FEE",
    "METRICS_BIND",
    "METRICS_ENABLED",
    "PRIORITY_FEE",
    "RPC_DEFAULT_GROUP",
    "SOURCIFY_ENABLED",
    "TELEGRAM_CHAT_IDS",
    "WEBHOOK_URL",
}


def _is_chat_id(s: str) -> bool:
    """Check if string looks like a raw Telegram chat ID."""
    return s.lstrip("-").isdigit()


def _parse_rate_limit(value: object) -> int:
    """Parse a rate limit value into seconds.

    Supports:
    - int/float (seconds)
    - "N/min" (per-minute)
    """
    if value is None:
        raise ConfigError("telegram.rate_limits.public must be set if rate_limits is provided")
    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds <= 0:
            raise ConfigError("telegram.rate_limits.public must be > 0")
        return int(seconds)
    if isinstance(value, str):
        s = value.strip().lower()
        if "/min" in s:
            try:
                rate = float(s.replace("/min", "").strip())
            except ValueError as exc:
                raise ConfigError("telegram.rate_limits.public must be a number or 'N/min'") from exc
            if rate <= 0:
                raise ConfigError("telegram.rate_limits.public must be > 0")
            return max(1, int(60.0 / rate))
        try:
            seconds = float(s)
        except ValueError as exc:
            raise ConfigError("telegram.rate_limits.public must be a number or 'N/min'") from exc
        if seconds <= 0:
            raise ConfigError("telegram.rate_limits.public must be > 0")
        return int(seconds)
    raise ConfigError("telegram.rate_limits.public must be a number or 'N/min'")


def _parse_telegram(raw: dict) -> "TelegramConfig":
    """Parse telegram config, handling both old and new formats.

    Normalizes all inputs (strips whitespace) and canonicalizes to TelegramConfig.
    """
    from brawny.config.models import TelegramConfig

    # New format: telegram.bot_token, telegram.chats, telegram.admin/public/default, telegram.parse_mode
    if "telegram" in raw and isinstance(raw["telegram"], dict):
        tg = raw["telegram"]

        # Normalize bot_token
        bot_token = tg.get("bot_token")
        if bot_token:
            bot_token = bot_token.strip()

        # Normalize chats (strip keys and values, validate IDs look numeric)
        raw_chats = tg.get("chats", {})
        chats: dict[str, str] = {}
        for k, v in raw_chats.items():
            if not k or not v:
                continue
            k = k.strip()
            v = str(v).strip()
            if not _is_chat_id(v):
                raise ConfigError(f"telegram.chats.{k} must be a numeric chat ID, got: '{v}'")
            chats[k] = v

        def _normalize_targets(value: object) -> list[str]:
            if value is None:
                return []
            if isinstance(value, str):
                value = [value]
            if not isinstance(value, list):
                raise ConfigError("telegram target lists must be a list or string")
            result: list[str] = []
            for item in value:
                if not item or not str(item).strip():
                    continue
                result.append(str(item).strip())
            return result

        # Normalize admin/public/default to list, strip each entry
        admin = _normalize_targets(tg.get("admin"))
        public = _normalize_targets(tg.get("public"))
        default = _normalize_targets(tg.get("default"))

        parse_mode_provided = "parse_mode" in tg
        parse_mode = tg.get("parse_mode")
        if isinstance(parse_mode, str):
            parse_mode = parse_mode.strip() or None
        if parse_mode not in (None, "Markdown", "MarkdownV2", "HTML"):
            raise ConfigError(
                "telegram.parse_mode must be one of: Markdown, MarkdownV2, HTML, or null"
            )
        if not parse_mode_provided and parse_mode is None:
            parse_mode = TelegramConfig().parse_mode

        if "health_chat" in tg:
            raise ConfigError("telegram.health_chat is no longer supported; use telegram.admin")

        health_cooldown = tg.get("health_cooldown_seconds")
        if health_cooldown is not None:
            try:
                health_cooldown = int(health_cooldown)
            except (TypeError, ValueError) as exc:
                raise ConfigError("telegram.health_cooldown_seconds must be an integer") from exc

        if health_cooldown is None:
            health_cooldown = TelegramConfig().health_cooldown_seconds

        rate_limits = tg.get("rate_limits") or {}
        public_rate_limit = TelegramConfig().public_rate_limit_seconds
        if isinstance(rate_limits, dict) and "public" in rate_limits:
            public_rate_limit = _parse_rate_limit(rate_limits.get("public"))
        elif rate_limits not in ({}, None):
            raise ConfigError("telegram.rate_limits must be a mapping")

        return TelegramConfig(
            bot_token=bot_token,
            chats=chats,
            admin=admin,
            public=public,
            default=default,
            parse_mode=parse_mode,
            health_cooldown_seconds=health_cooldown,
            public_rate_limit_seconds=public_rate_limit,
        )

    # Legacy format: telegram_bot_token, telegram_chat_id
    bot_token = raw.get("telegram_bot_token")
    chat_id = raw.get("telegram_chat_id")

    if bot_token:
        bot_token = str(bot_token).strip()
    if chat_id:
        chat_id = str(chat_id).strip()
        # Validate legacy chat_id is numeric too
        if not _is_chat_id(chat_id):
            raise ConfigError(f"telegram_chat_id must be numeric, got: '{chat_id}'")

    if bot_token or chat_id:
        # Migrate to canonical form
        chats = {"default": chat_id} if chat_id else {}
        default = ["default"] if chat_id else []
        admin = ["default"] if chat_id else []
        return TelegramConfig(
            bot_token=bot_token,
            chats=chats,
            admin=admin,
            default=default,
        )

    return TelegramConfig()


def _parse_guardrails(raw: dict) -> "GuardrailsConfig":
    from brawny.config.models import GuardrailsConfig

    if "guardrails" in raw and isinstance(raw["guardrails"], dict):
        guardrails = raw["guardrails"]
        lint_paths = guardrails.get("lint_paths", [])
        if lint_paths is None:
            lint_paths = []
        if isinstance(lint_paths, str):
            lint_paths = [lint_paths]
        lint_paths = [str(path).strip() for path in lint_paths if str(path).strip()]
        return GuardrailsConfig(lint_paths=lint_paths)
    return GuardrailsConfig()


def _parse_debug(raw: dict) -> "DebugConfig":
    from brawny.config.models import DebugConfig

    if "debug" in raw and isinstance(raw["debug"], dict):
        debug = raw["debug"]
        allow_console = debug.get("allow_console", False)
        if not isinstance(allow_console, bool):
            raise ConfigError("debug.allow_console must be a boolean")
        enable_null_lease_reclaim = debug.get("enable_null_lease_reclaim", False)
        if not isinstance(enable_null_lease_reclaim, bool):
            raise ConfigError("debug.enable_null_lease_reclaim must be a boolean")
        return DebugConfig(
            allow_console=allow_console,
            enable_null_lease_reclaim=enable_null_lease_reclaim,
        )
    return DebugConfig()


def _parse_intent_cooldown(raw: dict) -> "IntentCooldownConfig":
    from brawny.config.models import IntentCooldownConfig

    if "intent_cooldown" in raw and isinstance(raw["intent_cooldown"], dict):
        cfg = raw["intent_cooldown"]
        enabled = cfg.get("enabled", True)
        default_seconds = cfg.get("default_seconds", IntentCooldownConfig().default_seconds)
        max_seconds = cfg.get("max_seconds", IntentCooldownConfig().max_seconds)
        prune_older_than_days = cfg.get(
            "prune_older_than_days", IntentCooldownConfig().prune_older_than_days
        )
        if not isinstance(enabled, bool):
            raise ConfigError("intent_cooldown.enabled must be a boolean")
        return IntentCooldownConfig(
            enabled=enabled,
            default_seconds=int(default_seconds),
            max_seconds=int(max_seconds),
            prune_older_than_days=int(prune_older_than_days),
        )
    return IntentCooldownConfig()


def _parse_http(raw: dict) -> "HttpConfig":
    """Parse HTTP config, handling canonical http: block."""
    from brawny.http import HttpConfig

    if "http" in raw and isinstance(raw["http"], dict):
        cfg = raw["http"]
        allowed_domains = cfg.get("allowed_domains", [])
        if isinstance(allowed_domains, str):
            allowed_domains = [allowed_domains]
        if not isinstance(allowed_domains, list):
            raise ConfigError("http.allowed_domains must be a list of domains")
        allowed_domains = [str(d).strip() for d in allowed_domains if str(d).strip()]

        connect_timeout_seconds = cfg.get("connect_timeout_seconds")
        read_timeout_seconds = cfg.get("read_timeout_seconds")
        max_retries = cfg.get("max_retries")
        backoff_base_seconds = cfg.get("backoff_base_seconds")

        if connect_timeout_seconds is None:
            connect_timeout_seconds = HttpConfig().connect_timeout_seconds
        if read_timeout_seconds is None:
            read_timeout_seconds = HttpConfig().read_timeout_seconds
        if max_retries is None:
            max_retries = HttpConfig().max_retries
        if backoff_base_seconds is None:
            backoff_base_seconds = HttpConfig().backoff_base_seconds
        try:
            connect_timeout_seconds = float(connect_timeout_seconds)
        except (TypeError, ValueError) as exc:
            raise ConfigError("http.connect_timeout_seconds must be a number") from exc
        try:
            read_timeout_seconds = float(read_timeout_seconds)
        except (TypeError, ValueError) as exc:
            raise ConfigError("http.read_timeout_seconds must be a number") from exc
        try:
            max_retries = int(max_retries)
        except (TypeError, ValueError) as exc:
            raise ConfigError("http.max_retries must be an integer") from exc
        try:
            backoff_base_seconds = float(backoff_base_seconds)
        except (TypeError, ValueError) as exc:
            raise ConfigError("http.backoff_base_seconds must be a number") from exc

        return HttpConfig(
            allowed_domains=allowed_domains,
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            max_retries=max_retries,
            backoff_base_seconds=backoff_base_seconds,
        )

    return HttpConfig()




def _interpolate_env_vars(
    value: object,
    missing: list[str] | None = None,
    path: str = "",
) -> object:
    """Recursively interpolate ${VAR}, ${VAR:-default}, and ${{VAR}} patterns in config values.

    Supports:
      - ${VAR_NAME} / ${{VAR_NAME}} - replaced with env var value, empty string if not set
      - ${VAR_NAME:-default} / ${{VAR_NAME:-default}} - replaced with env var value, or default if not set

    Args:
        value: Config value (string, list, dict, or primitive)

    Returns:
        Value with environment variables interpolated
    """
    if isinstance(value, str):
        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default_val = match.group(2)  # None if no default specified
            env_val = os.environ.get(var_name)
            if env_val is not None:
                return env_val
            if default_val is not None:
                return default_val
            if missing is not None:
                location = path or "<root>"
                missing.append(f"{var_name} (at {location})")
            return ""  # Return empty string for unset vars without default

        result = ENV_VAR_PATTERN.sub(replacer, value)
        # If the entire string was a variable that resolved to empty, return None
        # This allows filtering out empty RPC endpoints
        if result == "" and ENV_VAR_PATTERN.search(value):
            return None
        return result

    elif isinstance(value, list):
        interpolated = [
            _interpolate_env_vars(item, missing, f"{path}[{idx}]")
            for idx, item in enumerate(value)
        ]
        # Filter out None values (unset env vars) and empty strings from lists
        return [v for v in interpolated if v is not None and v != ""]

    elif isinstance(value, dict):
        return {
            k: _interpolate_env_vars(v, missing, f"{path}.{k}" if path else str(k))
            for k, v in value.items()
        }

    else:
        return value


def _get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """Get environment variable with BRAWNY_ prefix."""
    full_key = f"BRAWNY_{key}"
    value = os.environ.get(full_key, default)
    if required and not value:
        raise ConfigError(f"Required environment variable {full_key} is not set")
    return value


def _env_is_set(key: str) -> bool:
    return f"BRAWNY_{key}" in os.environ


def _fail_removed_env_vars() -> None:
    removed = [key for key in _REMOVED_ENV_KEYS if _env_is_set(key)]
    if removed:
        raise ConfigError(
            "Removed config options detected in environment: "
            f"{sorted(removed)}. These options no longer exist."
        )


def _get_env_list(key: str, default: list[str] | None = None) -> list[str]:
    """Get comma-separated list from environment variable."""
    value = _get_env(key)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def _get_env_int(key: str, default: int) -> int:
    """Get integer from environment variable."""
    value = _get_env(key)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"BRAWNY_{key} must be an integer, got: {value}")


def _get_env_float(key: str, default: float) -> float:
    """Get float from environment variable."""
    value = _get_env(key)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        raise ConfigError(f"BRAWNY_{key} must be a number, got: {value}")


def _parse_env_int(key: str) -> int:
    value = _get_env(key)
    if value is None:
        raise ConfigError(f"Missing env override BRAWNY_{key}")
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"BRAWNY_{key} must be an integer, got: {value}")


def _parse_env_bool(key: str) -> bool:
    value = _get_env(key)
    if value is None:
        raise ConfigError(f"Missing env override BRAWNY_{key}")
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"BRAWNY_{key} must be a boolean, got: {value}")


def _parse_env_float(key: str) -> float:
    value = _get_env(key)
    if value is None:
        raise ConfigError(f"Missing env override BRAWNY_{key}")
    try:
        return float(value)
    except ValueError:
        raise ConfigError(f"BRAWNY_{key} must be a number, got: {value}")


_ADVANCED_ENV_MAPPING: dict[str, tuple[str, Callable[[str], object]]] = {
    "POLL_INTERVAL_SECONDS": ("poll_interval_seconds", _parse_env_float),
    "REORG_DEPTH": ("reorg_depth", _parse_env_int),
    "FINALITY_CONFIRMATIONS": ("finality_confirmations", _parse_env_int),
    "DEFAULT_DEADLINE_SECONDS": ("default_deadline_seconds", _parse_env_int),
    "STUCK_TX_SECONDS": ("stuck_tx_seconds", _parse_env_int),
    "MAX_REPLACEMENT_ATTEMPTS": ("max_replacement_attempts", _parse_env_int),
    "GAS_LIMIT_MULTIPLIER": ("gas_limit_multiplier", _parse_env_float),
    "DEFAULT_PRIORITY_FEE_GWEI": ("default_priority_fee_gwei", _parse_env_float),
    "MAX_FEE_CAP_GWEI": ("max_fee_cap_gwei", _parse_env_float),
    "FEE_BUMP_PERCENT": ("fee_bump_percent", _parse_env_int),
    "RPC_TIMEOUT_SECONDS": ("rpc_timeout_seconds", _parse_env_float),
    "RPC_MAX_RETRIES": ("rpc_max_retries", _parse_env_int),
}


def _get_advanced_env_overrides() -> dict[str, object]:
    overrides: dict[str, object] = {}
    for env_key, (field_name, parser) in _ADVANCED_ENV_MAPPING.items():
        if _env_is_set(env_key):
            overrides[field_name] = parser(env_key)
    return overrides


def _get_advanced_env_overrides_with_keys() -> tuple[dict[str, object], list[str]]:
    overrides: dict[str, object] = {}
    overridden: list[str] = []
    for env_key, (field_name, parser) in _ADVANCED_ENV_MAPPING.items():
        if _env_is_set(env_key):
            overrides[field_name] = parser(env_key)
            overridden.append(f"advanced.{field_name}")
    return overrides, overridden


def from_env() -> "Config":
    """Load configuration from environment variables."""
    from brawny.config.models import (
        AdvancedConfig,
        Config,
        GuardrailsConfig,
        RPCDefaults,
        RPCGroupConfig,
    )
    from brawny.config.validation import canonicalize_endpoint, dedupe_preserve_order, InvalidEndpointError

    _fail_removed_env_vars()

    # Get required values
    database_url = _get_env("DATABASE_URL", required=True)
    if database_url is None:
        raise ConfigError("BRAWNY_DATABASE_URL is required")

    rpc_endpoints = _get_env_list("RPC_ENDPOINTS")
    if not rpc_endpoints:
        raise ConfigError("BRAWNY_RPC_ENDPOINTS is required (comma-separated list)")

    endpoints: list[str] = []
    for i, endpoint in enumerate(rpc_endpoints):
        try:
            endpoints.append(canonicalize_endpoint(endpoint))
        except InvalidEndpointError as e:
            raise ConfigError(f"rpc_endpoints[{i}]: {e}") from e
    endpoints = dedupe_preserve_order(endpoints)

    default_read_group = _get_env("RPC_DEFAULT_READ_GROUP") or "primary"
    default_broadcast_group = _get_env("RPC_DEFAULT_BROADCAST_GROUP") or default_read_group
    if default_broadcast_group != default_read_group:
        raise ConfigError(
            "RPC_DEFAULT_BROADCAST_GROUP must match RPC_DEFAULT_READ_GROUP when using "
            "RPC_ENDPOINTS (single group mode)."
        )

    chain_id = _get_env_int("CHAIN_ID", 1)
    production = _parse_env_bool("PRODUCTION") if _env_is_set("PRODUCTION") else False

    # Parse keystore type
    keystore_type_str = _get_env("KEYSTORE_TYPE", "file")
    try:
        keystore_type = KeystoreType(keystore_type_str)
    except ValueError:
        raise ConfigError(
            f"Invalid keystore type: {keystore_type_str}. "
            f"Must be one of: {', '.join(kt.value for kt in KeystoreType)}"
        )

    advanced_kwargs = _get_advanced_env_overrides()


    # Parse telegram config from env (legacy format)
    telegram_config = _parse_telegram({
        "telegram_bot_token": _get_env("TELEGRAM_BOT_TOKEN"),
        "telegram_chat_id": _get_env("TELEGRAM_CHAT_ID"),
    })
    guardrails_config = _parse_guardrails({
        "guardrails": {
            "lint_paths": _get_env_list("GUARDRAILS_LINT_PATHS"),
        }
    })
    http_allowed = _get_env("HTTP_ALLOWED_DOMAINS")
    http_config = _parse_http({
        "http": {
            "allowed_domains": [d.strip() for d in http_allowed.split(",")] if http_allowed else [],
            "connect_timeout_seconds": _get_env("HTTP_CONNECT_TIMEOUT_SECONDS"),
            "read_timeout_seconds": _get_env("HTTP_READ_TIMEOUT_SECONDS"),
            "max_retries": _get_env("HTTP_MAX_RETRIES"),
        }
    })

    config = Config(
        database_url=database_url,
        rpc_endpoints=endpoints,
        rpc_groups={default_read_group: RPCGroupConfig(endpoints=endpoints)},
        rpc_defaults=RPCDefaults(read=default_read_group, broadcast=default_broadcast_group),
        chain_id=chain_id,
        worker_count=_get_env_int("WORKER_COUNT", 1),
        production=production,
        advanced=AdvancedConfig(**advanced_kwargs) if advanced_kwargs else None,
        telegram=telegram_config,
        guardrails=guardrails_config,
        http=http_config,
        intent_cooldown=IntentCooldownConfig(),
        keystore_type=keystore_type,
        keystore_path=_get_env("KEYSTORE_PATH", "~/.brawny/keys") or "~/.brawny/keys",
    )

    config.validate()
    return config


def from_yaml(path: str) -> "Config":
    """Load configuration from a YAML file.

    Supports environment variable interpolation using ${VAR}, ${{VAR}}, or ${VAR:-default} syntax.
    For example:
        rpc:
          groups:
            primary:
              endpoints:
                - ${RPC_1}
                - ${RPC_2:-http://localhost:8545}
                - ${{RPC_3}}
          defaults:
            read: primary
            broadcast: primary

    Empty/unset variables in lists are automatically filtered out.
    """
    from brawny.config.models import (
        AdvancedConfig,
        Config,
        IntentCooldownConfig,
        RPCDefaults,
        RPCGroupConfig,
    )
    from brawny.config.validation import (
        canonicalize_endpoint,
        dedupe_preserve_order,
        InvalidEndpointError,
        validate_no_removed_fields,
    )

    if yaml is None:
        raise ConfigError("PyYAML is required for YAML config support.")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    except (OSError, UnicodeError, yaml.YAMLError) as e:
        raise ConfigError(f"Failed to read config file {path}: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a mapping at the top level.")

    # Interpolate environment variables in all config values
    missing: list[str] = []
    data = _interpolate_env_vars(data, missing)
    if not isinstance(data, dict):
        raise ConfigError("Config interpolation failed.")
    if missing:
        missing_list = ", ".join(sorted(set(missing)))
        raise ConfigError(
            f"Config interpolation failed. Missing environment variables: {missing_list}"
        )

    validate_no_removed_fields(data)

    guardrails_data: dict[str, object] = {}
    if "guardrails" in data:
        guardrails_value = data.pop("guardrails")
        if guardrails_value is None:
            guardrails_value = {}
        if not isinstance(guardrails_value, dict):
            raise ConfigError("guardrails must be a mapping")
        guardrails_data = dict(guardrails_value)

    debug_data: dict[str, object] = {}
    if "debug" in data:
        debug_value = data.pop("debug")
        if debug_value is None:
            debug_value = {}
        if not isinstance(debug_value, dict):
            raise ConfigError("debug must be a mapping")
        debug_data = dict(debug_value)

    advanced_data: dict[str, object] = {}
    if "advanced" in data:
        advanced_value = data.pop("advanced")
        if advanced_value is None:
            advanced_value = {}
        if not isinstance(advanced_value, dict):
            raise ConfigError("advanced must be a mapping")
        advanced_data = dict(advanced_value)

    rpc_data = data.pop("rpc", None)
    rpc_groups_data: dict[str, object] = {}
    rpc_defaults_data: dict[str, object] = {}

    if rpc_data is not None:
        if not isinstance(rpc_data, dict):
            raise ConfigError("rpc must be a mapping")
        if "rpc_groups" in data or "rpc_defaults" in data:
            raise ConfigError("Use rpc.groups and rpc.defaults; remove rpc_groups/rpc_defaults.")
        rpc_groups_data = rpc_data.get("groups", {}) or {}
        rpc_defaults_data = rpc_data.get("defaults", {}) or {}
        if not isinstance(rpc_groups_data, dict):
            raise ConfigError("rpc.groups must be a mapping")
        if not isinstance(rpc_defaults_data, dict):
            raise ConfigError("rpc.defaults must be a mapping")
    else:
        rpc_groups_data = data.pop("rpc_groups", {}) or {}
        rpc_defaults_data = data.pop("rpc_defaults", {}) or {}
    rpc_groups: dict[str, RPCGroupConfig] = {}

    if rpc_groups_data:
        for name, group_data in rpc_groups_data.items():
            if not isinstance(group_data, dict):
                raise ConfigError(f"rpc_groups.{name} must be a mapping")

            endpoints_raw = group_data.get("endpoints", [])
            if not isinstance(endpoints_raw, list):
                raise ConfigError(f"rpc_groups.{name}.endpoints must be a list")

            # Strip → canonicalize → dedupe (once, here)
            # InvalidEndpointError from canonicalize → ConfigError with context
            endpoints = []
            for i, ep in enumerate(endpoints_raw):
                if not isinstance(ep, str):
                    raise ConfigError(f"rpc_groups.{name}.endpoints[{i}] must be string")
                # Skip empty strings (from unset env vars)
                if not ep.strip():
                    continue
                try:
                    canonical = canonicalize_endpoint(ep)
                    endpoints.append(canonical)
                except InvalidEndpointError as e:
                    raise ConfigError(f"rpc_groups.{name}.endpoints[{i}]: {e}") from e

            original_count = len(endpoints)
            endpoints = dedupe_preserve_order(endpoints)
            if len(endpoints) != original_count:
                # Log warning about deduplication (will be logged at config load time)
                import logging
                logging.getLogger(__name__).warning(
                    f"rpc_groups.{name}: removed {original_count - len(endpoints)} "
                    f"duplicate endpoint(s) after canonicalization"
                )

            rpc_groups[name] = RPCGroupConfig(endpoints=endpoints)

    data["rpc_groups"] = rpc_groups

    rpc_defaults: RPCDefaults | None = None
    if rpc_defaults_data:
        read = rpc_defaults_data.get("read")
        broadcast = rpc_defaults_data.get("broadcast")
        if not read or not broadcast:
            raise ConfigError("rpc.defaults requires both read and broadcast")
        rpc_defaults = RPCDefaults(read=str(read), broadcast=str(broadcast))
    elif len(rpc_groups) == 1:
        only = next(iter(rpc_groups.keys()))
        rpc_defaults = RPCDefaults(read=only, broadcast=only)

    data["rpc_defaults"] = rpc_defaults

    if rpc_defaults and rpc_defaults.read in rpc_groups:
        data["rpc_endpoints"] = rpc_groups[rpc_defaults.read].endpoints
    else:
        data["rpc_endpoints"] = []

    if advanced_data:
        unknown = set(advanced_data.keys()) - _ADVANCED_FIELDS
        if unknown:
            raise ConfigError(f"Unknown advanced config fields: {sorted(unknown)}")
        data["advanced"] = AdvancedConfig(**advanced_data)
    if guardrails_data:
        data["guardrails"] = guardrails_data

    # Parse telegram config (handles both new and legacy formats)
    telegram_config = _parse_telegram(data)
    http_config = _parse_http(data)
    guardrails_config = _parse_guardrails(data)
    debug_config = _parse_debug(data)
    intent_cooldown_config = _parse_intent_cooldown(data)
    # Remove raw telegram fields - they've been canonicalized
    data.pop("telegram", None)
    data.pop("telegram_bot_token", None)
    data.pop("telegram_chat_id", None)
    data["telegram"] = telegram_config
    data.pop("http", None)
    data["http"] = http_config
    data.pop("guardrails", None)
    data["guardrails"] = guardrails_config
    data.pop("debug", None)
    data["debug"] = debug_config
    data.pop("intent_cooldown", None)
    data["intent_cooldown"] = intent_cooldown_config

    config = Config(**data)
    config.validate()
    return config


def apply_env_overrides(config: "Config") -> tuple["Config", list[str]]:
    """Apply environment overrides to the current config."""
    from brawny.config.models import (
        AdvancedConfig,
        Config,
        GuardrailsConfig,
        RPCDefaults,
        RPCGroupConfig,
        TelegramConfig,
    )
    from brawny.http import HttpConfig
    from brawny.config.validation import canonicalize_endpoint, dedupe_preserve_order, InvalidEndpointError

    _fail_removed_env_vars()

    overrides: dict[str, object] = {}
    advanced_overrides: dict[str, object] = {}
    guardrails_overrides: dict[str, object] = {}
    overridden: list[str] = []

    mapping = {
        "DATABASE_URL": ("database_url", _get_env),
        "CHAIN_ID": ("chain_id", _parse_env_int),
        "WORKER_COUNT": ("worker_count", _parse_env_int),
        "PRODUCTION": ("production", _parse_env_bool),
        "KEYSTORE_TYPE": ("keystore_type", _get_env),
        "KEYSTORE_PATH": ("keystore_path", _get_env),
    }

    for env_key, (field_name, parser) in mapping.items():
        if not _env_is_set(env_key):
            continue
        value = parser(env_key)
        if value is None:
            continue
        overrides[field_name] = value
        overridden.append(field_name)

    default_read_override = _get_env("RPC_DEFAULT_READ_GROUP") if _env_is_set("RPC_DEFAULT_READ_GROUP") else None
    default_broadcast_override = _get_env("RPC_DEFAULT_BROADCAST_GROUP") if _env_is_set("RPC_DEFAULT_BROADCAST_GROUP") else None
    if default_read_override or default_broadcast_override:
        read_group = default_read_override or config.rpc_defaults.read
        broadcast_group = default_broadcast_override or config.rpc_defaults.broadcast
        overrides["rpc_defaults"] = RPCDefaults(read=read_group, broadcast=broadcast_group)
        if default_read_override:
            overridden.append("rpc.defaults.read")
        if default_broadcast_override:
            overridden.append("rpc.defaults.broadcast")

    # Handle telegram env overrides (legacy format)
    telegram_token_override = _get_env("TELEGRAM_BOT_TOKEN") if _env_is_set("TELEGRAM_BOT_TOKEN") else None
    telegram_chat_override = _get_env("TELEGRAM_CHAT_ID") if _env_is_set("TELEGRAM_CHAT_ID") else None
    if telegram_token_override is not None or telegram_chat_override is not None:
        # Build new telegram config merging with existing
        base_telegram = config.telegram
        new_token = telegram_token_override.strip() if telegram_token_override else base_telegram.bot_token
        new_chats = dict(base_telegram.chats)
        new_default = list(base_telegram.default)
        new_admin = list(base_telegram.admin)
        new_public = list(base_telegram.public)

        if telegram_chat_override:
            chat_id = telegram_chat_override.strip()
            if not _is_chat_id(chat_id):
                raise ConfigError(f"BRAWNY_TELEGRAM_CHAT_ID must be numeric, got: '{chat_id}'")
            new_chats["default"] = chat_id
            if "default" not in new_default:
                new_default = ["default"] + new_default
            if not new_admin:
                new_admin = ["default"]

        overrides["telegram"] = TelegramConfig(
            bot_token=new_token,
            chats=new_chats,
            admin=new_admin,
            public=new_public,
            default=new_default,
            parse_mode=base_telegram.parse_mode,
            health_cooldown_seconds=base_telegram.health_cooldown_seconds,
            public_rate_limit_seconds=base_telegram.public_rate_limit_seconds,
        )
        if telegram_token_override is not None:
            overridden.append("telegram.bot_token")
        if telegram_chat_override is not None:
            overridden.append("telegram.chat_id")

    # Handle http env overrides
    if (
        _env_is_set("HTTP_ALLOWED_DOMAINS")
        or _env_is_set("HTTP_CONNECT_TIMEOUT_SECONDS")
        or _env_is_set("HTTP_READ_TIMEOUT_SECONDS")
        or _env_is_set("HTTP_MAX_RETRIES")
        or _env_is_set("HTTP_BACKOFF_BASE_SECONDS")
    ):
        base_http = config.http
        allowed_raw = _get_env("HTTP_ALLOWED_DOMAINS")
        allowed_domains = (
            [d.strip() for d in allowed_raw.split(",") if d.strip()] if allowed_raw is not None else base_http.allowed_domains
        )
        connect_timeout_seconds = (
            _parse_env_float("HTTP_CONNECT_TIMEOUT_SECONDS")
            if _env_is_set("HTTP_CONNECT_TIMEOUT_SECONDS")
            else base_http.connect_timeout_seconds
        )
        read_timeout_seconds = (
            _parse_env_float("HTTP_READ_TIMEOUT_SECONDS")
            if _env_is_set("HTTP_READ_TIMEOUT_SECONDS")
            else base_http.read_timeout_seconds
        )
        max_retries = (
            _parse_env_int("HTTP_MAX_RETRIES")
            if _env_is_set("HTTP_MAX_RETRIES")
            else base_http.max_retries
        )
        backoff_base_seconds = (
            _parse_env_float("HTTP_BACKOFF_BASE_SECONDS")
            if _env_is_set("HTTP_BACKOFF_BASE_SECONDS")
            else base_http.backoff_base_seconds
        )
        overrides["http"] = HttpConfig(
            allowed_domains=allowed_domains,
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            max_retries=max_retries,
            backoff_base_seconds=backoff_base_seconds,
        )
        if _env_is_set("HTTP_ALLOWED_DOMAINS"):
            overridden.append("http.allowed_domains")
        if _env_is_set("HTTP_CONNECT_TIMEOUT_SECONDS"):
            overridden.append("http.connect_timeout_seconds")
        if _env_is_set("HTTP_READ_TIMEOUT_SECONDS"):
            overridden.append("http.read_timeout_seconds")
    if _env_is_set("HTTP_MAX_RETRIES"):
        overridden.append("http.max_retries")
    if _env_is_set("HTTP_BACKOFF_BASE_SECONDS"):
        overridden.append("http.backoff_base_seconds")

    if _env_is_set("GUARDRAILS_LINT_PATHS"):
        guardrails_overrides["lint_paths"] = _get_env_list("GUARDRAILS_LINT_PATHS")
        overridden.append("guardrails.lint_paths")

    advanced_overrides, advanced_overridden = _get_advanced_env_overrides_with_keys()
    overridden.extend(advanced_overridden)

    rpc_endpoints_override: list[str] | None = None
    if _env_is_set("RPC_ENDPOINTS"):
        raw_endpoints = _get_env_list("RPC_ENDPOINTS")
        endpoints: list[str] = []
        for i, endpoint in enumerate(raw_endpoints):
            try:
                endpoints.append(canonicalize_endpoint(endpoint))
            except InvalidEndpointError as e:
                raise ConfigError(f"rpc_endpoints[{i}]: {e}") from e
        rpc_endpoints_override = dedupe_preserve_order(endpoints)

    if not overrides:
        return config, []

    if "keystore_type" in overrides:
        overrides["keystore_type"] = KeystoreType(str(overrides["keystore_type"]))

    if advanced_overrides:
        base_advanced = config.advanced or AdvancedConfig()
        overrides["advanced"] = replace(base_advanced, **advanced_overrides)
    if guardrails_overrides:
        base_guardrails = config.guardrails or GuardrailsConfig()
        overrides["guardrails"] = replace(base_guardrails, **guardrails_overrides)

    if rpc_endpoints_override is not None:
        defaults = overrides.get("rpc_defaults") or config.rpc_defaults
        read_group = defaults.read
        broadcast_group = defaults.broadcast
        if read_group != broadcast_group:
            raise ConfigError(
                "RPC_ENDPOINTS override requires rpc.defaults.read == rpc.defaults.broadcast"
            )
        overrides["rpc_endpoints"] = rpc_endpoints_override
        overrides["rpc_groups"] = {read_group: RPCGroupConfig(endpoints=rpc_endpoints_override)}
        overrides["rpc_defaults"] = RPCDefaults(read=read_group, broadcast=read_group)
        overridden.extend(["rpc_endpoints", "rpc_groups", "rpc.defaults.read", "rpc.defaults.broadcast"])

    if "rpc_defaults" in overrides:
        defaults = overrides["rpc_defaults"]
        if defaults.read in config.rpc_groups:
            overrides["rpc_endpoints"] = config.rpc_groups[defaults.read].endpoints

    return replace(config, **overrides), overridden
