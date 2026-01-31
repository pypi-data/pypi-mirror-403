"""Configuration models for brawny.

Defines dataclass models for all configuration sections.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from brawny.model.enums import KeystoreType
from brawny.http import HttpConfig

DEFAULT_BLOCK_HASH_HISTORY_SIZE = 256
DEFAULT_JOB_ERROR_BACKOFF_BLOCKS = 1
DEFAULT_INTENT_RETRY_BACKOFF_SECONDS = 5
DEFAULT_NONCE_RECONCILE_INTERVAL_SECONDS = 300
DEFAULT_STUCK_TX_BLOCKS = 50
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS = 30
DEFAULT_RPC_RETRY_BACKOFF_BASE = 1.0
DEFAULT_DB_CIRCUIT_BREAKER_FAILURES = 5
DEFAULT_DB_CIRCUIT_BREAKER_SECONDS = 30
DEFAULT_GAS_REFRESH_SECONDS = 15
DEFAULT_FALLBACK_GAS_LIMIT = 500_000
DEFAULT_ABI_CACHE_TTL_SECONDS = 86400 * 7
DEFAULT_NONCE_GAP_ALERT_SECONDS = 300
DEFAULT_MAX_EXECUTOR_RETRIES = 5
DEFAULT_FINALITY_CONFIRMATIONS = 12
DEFAULT_ALERTS_HEALTH_MAX_OLDEST_AGE_SECONDS = 120
DEFAULT_PUBLIC_ALERT_RATE_LIMIT_SECONDS = 60


@dataclass
class TelegramConfig:
    """Telegram alert configuration.

    Fields:
        bot_token: Bot token for API calls (None = disabled)
        chats: Named chat targets (address book)
        admin: System/lifecycle alert targets (required)
        public: Business/job alert targets (optional)
        default: Default targets for job alerts when job.alert_to not specified
        parse_mode: Default parse mode for telegram messages (None = disable formatting)
        health_cooldown_seconds: Deduplication window for health alerts
        public_rate_limit_seconds: Rate limit for public/job alerts
    """

    bot_token: str | None = None
    chats: dict[str, str] = field(default_factory=dict)  # name -> chat_id
    admin: list[str] = field(default_factory=list)  # chat names (required)
    public: list[str] = field(default_factory=list)  # chat names (optional)
    default: list[str] = field(default_factory=list)  # Always a list internally
    parse_mode: str | None = "Markdown"
    health_cooldown_seconds: int = 1800  # 30 minutes between identical alerts
    public_rate_limit_seconds: int = DEFAULT_PUBLIC_ALERT_RATE_LIMIT_SECONDS


@dataclass
class GuardrailsConfig:
    """Guardrail configuration for linting and runtime enforcement."""

    lint_paths: list[str] = field(default_factory=list)


@dataclass
class DebugConfig:
    """Debug-only settings (opt-in)."""

    allow_console: bool = False
    enable_null_lease_reclaim: bool = False


@dataclass
class IntentCooldownConfig:
    """Global intent cooldown configuration."""

    enabled: bool = True
    default_seconds: int = 300
    max_seconds: int = 3600
    prune_older_than_days: int = 30


@dataclass
class RPCGroupConfig:
    """A named collection of RPC endpoints."""

    endpoints: list[str] = field(default_factory=list)  # Canonicalized + deduped at parse time


@dataclass
class RPCDefaults:
    """Default RPC routing groups."""

    read: str
    broadcast: str


@dataclass
class AdvancedConfig:
    """
    Advanced options.

    RULE:
    - If this exceeds ~25 fields, something is wrong.
    - New options must justify why they are user-facing at all.
    - AdvancedConfig may only contain tuning parameters, not semantic switches.
      No feature flags or behavior-class booleans (e.g., enable_x/disable_y).
    """

    # Polling
    poll_interval_seconds: float = 1.0
    reorg_depth: int = 32
    finality_confirmations: int = DEFAULT_FINALITY_CONFIRMATIONS

    # Execution
    default_deadline_seconds: int = 3600
    stuck_tx_seconds: int = 300
    max_replacement_attempts: int = 5

    # Gas (gwei)
    gas_limit_multiplier: float = 1.2
    default_priority_fee_gwei: float = 0.01
    max_fee_cap_gwei: float | None = 500.0
    fee_bump_percent: int = 15

    # RPC
    rpc_timeout_seconds: float = 30.0
    rpc_max_retries: int = 3

    # Job logs
    log_retention_days: int = 7

    # Alerts
    alerts_health_max_oldest_age_seconds: int = DEFAULT_ALERTS_HEALTH_MAX_OLDEST_AGE_SECONDS


@dataclass
class Config:
    """Main configuration for brawny.

    NOTE: Direct construction does NOT validate. Use Config.from_yaml() or
    Config.from_env() for validated configuration, or call .validate() explicitly.
    """

    # Required fields (no defaults) must come first
    database_url: str
    rpc_endpoints: list[str]  # Derived from rpc.defaults.read; not user-facing

    # RPC Groups (for per-job read/broadcast routing)
    rpc_groups: dict[str, RPCGroupConfig]

    # Chain (required)
    chain_id: int

    # RPC defaults (required by validation)
    rpc_defaults: RPCDefaults | None = None

    # Execution
    worker_count: int = 1
    production: bool = False

    # Advanced (rarely changed)
    advanced: AdvancedConfig | None = None

    # Telegram (canonical form - parsed from telegram: or legacy fields)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)

    # Guardrails (lint hints for job code)
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)

    # Debug-only flags (disabled by default)
    debug: DebugConfig = field(default_factory=DebugConfig)

    # Intent cooldown (global defaults)
    intent_cooldown: IntentCooldownConfig = field(default_factory=IntentCooldownConfig)

    # HTTP (approved client for job code)
    http: HttpConfig = field(default_factory=HttpConfig)

    # Metrics
    metrics_port: int = 9091

    # Keystore (required)
    keystore_type: KeystoreType = KeystoreType.FILE
    keystore_path: str = "~/.brawny/keys"

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ConfigError: If validation fails
        """
        from brawny.config.validation import validate_config, validate_advanced_config

        validate_config(self)
        validate_advanced_config(self._advanced_or_default())

    @property
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        from brawny.config.parser import from_env as _from_env
        return _from_env()

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from a YAML file.

        Supports environment variable interpolation using ${VAR}, ${{VAR}}, or ${VAR:-default} syntax.
        """
        from brawny.config.parser import from_yaml as _from_yaml
        return _from_yaml(path)

    def apply_env_overrides(self) -> tuple["Config", list[str]]:
        """Apply environment overrides to the current config."""
        from brawny.config.parser import apply_env_overrides as _apply_env_overrides
        return _apply_env_overrides(self)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def redacted_dict(self) -> dict[str, object]:
        from urllib.parse import urlsplit, urlunsplit

        def _redact_url(value: str) -> str:
            split = urlsplit(value)
            netloc = split.netloc
            if "@" in netloc:
                netloc = "***@" + netloc.split("@", 1)[1]
            return urlunsplit((split.scheme, netloc, split.path, "", ""))

        data = self.to_dict()
        redacted: dict[str, object] = {}
        for key, value in data.items():
            if any(word in key.lower() for word in ("token", "secret", "key", "password")):
                redacted[key] = "***"
            elif key == "rpc_endpoints" and isinstance(value, list):
                redacted[key] = [_redact_url(str(v)) for v in value]
            elif key == "rpc_groups" and isinstance(value, dict):
                redacted_groups: dict[str, object] = {}
                for group_name, group_value in value.items():
                    if isinstance(group_value, dict):
                        endpoints = group_value.get("endpoints")
                        if isinstance(endpoints, list):
                            group_value = {
                                **group_value,
                                "endpoints": [_redact_url(str(v)) for v in endpoints],
                            }
                    redacted_groups[group_name] = group_value
                redacted[key] = redacted_groups
            elif key == "telegram" and isinstance(value, dict):
                # Redact bot_token within telegram config
                redacted[key] = {
                    **value,
                    "bot_token": "***" if value.get("bot_token") else None,
                }
            elif isinstance(value, str) and key.endswith("url"):
                redacted[key] = _redact_url(value)
            else:
                redacted[key] = value
        return redacted

    def _advanced_or_default(self) -> AdvancedConfig:
        return self.advanced or AdvancedConfig()

    def _derive_claim_timeout_seconds(self) -> int:
        deadline = self._advanced_or_default().default_deadline_seconds
        return max(60, int(min(300, deadline / 12)))

    @property
    def poll_interval_seconds(self) -> float:
        return self._advanced_or_default().poll_interval_seconds

    @property
    def reorg_depth(self) -> int:
        return self._advanced_or_default().reorg_depth

    @property
    def finality_confirmations(self) -> int:
        return self._advanced_or_default().finality_confirmations

    @property
    def default_deadline_seconds(self) -> int:
        return self._advanced_or_default().default_deadline_seconds

    @property
    def stuck_tx_seconds(self) -> int:
        return self._advanced_or_default().stuck_tx_seconds

    @property
    def max_replacement_attempts(self) -> int:
        return self._advanced_or_default().max_replacement_attempts

    @property
    def gas_limit_multiplier(self) -> float:
        return self._advanced_or_default().gas_limit_multiplier

    @property
    def default_priority_fee_gwei(self) -> float:
        return self._advanced_or_default().default_priority_fee_gwei

    @property
    def max_fee_cap_gwei(self) -> float | None:
        return self._advanced_or_default().max_fee_cap_gwei

    @property
    def fee_bump_percent(self) -> int:
        return self._advanced_or_default().fee_bump_percent

    @property
    def rpc_timeout_seconds(self) -> float:
        return self._advanced_or_default().rpc_timeout_seconds

    @property
    def rpc_max_retries(self) -> int:
        return self._advanced_or_default().rpc_max_retries

    @property
    def priority_fee(self) -> int:
        return int(self.default_priority_fee_gwei * 1_000_000_000)

    @property
    def max_fee(self) -> int | None:
        cap = self.max_fee_cap_gwei
        if cap is None:
            return None
        return int(cap * 1_000_000_000)

    @property
    def job_error_backoff_blocks(self) -> int:
        return DEFAULT_JOB_ERROR_BACKOFF_BLOCKS

    @property
    def block_hash_history_size(self) -> int:
        return DEFAULT_BLOCK_HASH_HISTORY_SIZE

    @property
    def deep_reorg_pause(self) -> bool:
        return False

    @property
    def claim_timeout_seconds(self) -> int:
        return self._derive_claim_timeout_seconds()

    @property
    def intent_retry_backoff_seconds(self) -> int:
        return DEFAULT_INTENT_RETRY_BACKOFF_SECONDS

    @property
    def max_executor_retries(self) -> int:
        return DEFAULT_MAX_EXECUTOR_RETRIES

    @property
    def nonce_reconcile_interval_seconds(self) -> int:
        return DEFAULT_NONCE_RECONCILE_INTERVAL_SECONDS

    @property
    def stuck_tx_blocks(self) -> int:
        return DEFAULT_STUCK_TX_BLOCKS

    @property
    def shutdown_timeout_seconds(self) -> int:
        return DEFAULT_SHUTDOWN_TIMEOUT_SECONDS

    @property
    def shutdown_grace_seconds(self) -> int:
        return DEFAULT_SHUTDOWN_TIMEOUT_SECONDS

    @property
    def rpc_retry_backoff_base(self) -> float:
        return DEFAULT_RPC_RETRY_BACKOFF_BASE

    @property
    def db_circuit_breaker_failures(self) -> int:
        return DEFAULT_DB_CIRCUIT_BREAKER_FAILURES

    @property
    def db_circuit_breaker_seconds(self) -> int:
        return DEFAULT_DB_CIRCUIT_BREAKER_SECONDS

    @property
    def gas_refresh_seconds(self) -> int:
        return DEFAULT_GAS_REFRESH_SECONDS

    @property
    def fallback_gas_limit(self) -> int:
        return DEFAULT_FALLBACK_GAS_LIMIT

    @property
    def abi_cache_ttl_seconds(self) -> int:
        return DEFAULT_ABI_CACHE_TTL_SECONDS

    @property
    def allow_unsafe_nonce_reset(self) -> bool:
        return False

    @property
    def nonce_gap_alert_seconds(self) -> int:
        return DEFAULT_NONCE_GAP_ALERT_SECONDS

    @property
    def log_retention_days(self) -> int:
        return self._advanced_or_default().log_retention_days
