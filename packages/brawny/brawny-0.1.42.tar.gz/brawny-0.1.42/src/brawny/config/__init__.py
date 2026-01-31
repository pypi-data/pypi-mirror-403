"""Configuration management for brawny.

All configuration is validated at startup. Invalid config prevents startup with clear error messages.
Environment variables use the BRAWNY_ prefix.
"""

from __future__ import annotations

import os

from brawny.config.models import (
    AdvancedConfig,
    Config,
    IntentCooldownConfig,
    RPCDefaults,
    RPCGroupConfig,
)
from brawny.config.validation import (
    InvalidEndpointError,
    canonicalize_endpoint,
    canonicalize_endpoints,
    dedupe_preserve_order,
    validate_config,
)
from brawny.model.errors import ConfigError

__all__ = [
    # Models
    "Config",
    "AdvancedConfig",
    "IntentCooldownConfig",
    "RPCDefaults",
    "RPCGroupConfig",
    # Validation
    "InvalidEndpointError",
    "canonicalize_endpoint",
    "canonicalize_endpoints",
    "dedupe_preserve_order",
    "validate_config",
    # Errors
    "ConfigError",
    # Global instance
    "get_config",
    "set_config",
    "reset_config",
]


# Global configuration instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    Loads from environment on first access.
    """
    global _config
    if _config is None:
        default_path = os.path.join(os.getcwd(), "config.yaml")
        if os.path.exists(default_path):
            config = Config.from_yaml(default_path)
            _config, _ = config.apply_env_overrides()
        else:
            _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance.

    Useful for testing or programmatic configuration.
    """
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration instance.

    Forces reload from environment on next access.
    """
    global _config
    _config = None
