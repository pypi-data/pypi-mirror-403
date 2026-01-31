"""Network configuration loading (Brownie-compatible).

Loads from:
1. ~/.brawny/network-config.yaml (if exists)
2. Auto-copies ~/.brownie/network-config.yaml to ~/.brawny/ on first use
3. Built-in defaults

NOTE: This module provides Brownie-compatible ~/.brawny/network-config.yaml support.
Project-level config.yaml network sections are no longer supported.
They are in separate namespaces and serve different purposes.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Pattern to match ${VAR}, ${VAR:-default}, or $VAR forms (consistent with brawny.config)
_ENV_VAR_PATTERN = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}?")


class EnvVarExpansionError(ValueError):
    """Raised when an environment variable cannot be expanded."""

    def __init__(self, var_name: str, original_value: str, network_id: str | None = None):
        self.var_name = var_name
        self.original_value = original_value
        self.network_id = network_id
        network_ctx = f" in network '{network_id}'" if network_id else ""
        super().__init__(
            f"Environment variable '{var_name}' is not set{network_ctx}. "
            f"Original value: {original_value}"
        )


def _expand_env_var(value: str, *, network_id: str | None = None) -> str | None:
    """Expand environment variables in a string.

    Supports:
      - $VAR or ${VAR} - replaced with env var value
      - ${VAR:-default} - replaced with env var value, or default if not set

    Returns:
      - None if value is purely an env var that wasn't set (allows filtering)
      - Expanded string otherwise

    Raises:
      - EnvVarExpansionError if a var inside a larger string is unset (partial expansion)
        e.g., "https://alchemy.com/v2/$KEY" with KEY unset is an error, not a silent "/v2/"
    """
    unset_vars: list[str] = []

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_val = match.group(2)  # None if no default specified
        env_val = os.environ.get(var_name)
        if env_val is not None:
            return env_val
        if default_val is not None:
            return default_val
        # Track unset vars without defaults
        unset_vars.append(var_name)
        return ""

    result = _ENV_VAR_PATTERN.sub(replacer, value)

    # If the ENTIRE string was a single env var that wasn't set → return None (filterable)
    if result == "" and len(unset_vars) == 1 and value.strip() in (f"${unset_vars[0]}", f"${{{unset_vars[0]}}}"):
        return None

    # If ANY env var was unset inside a larger string → error (partial expansion is dangerous)
    if unset_vars:
        raise EnvVarExpansionError(unset_vars[0], value, network_id)

    return result


@dataclass
class NetworkConfig:
    """Configuration for a single network (Brownie-compatible format)."""

    id: str
    hosts: list[str]  # Flexible: accepts string or list in config, stored as list
    chainid: int | None = None
    name: str | None = None
    explorer: str | None = None
    multicall2: str | None = None  # Passed to Contract layer for batch calls
    timeout: int = 30

    # RPC settings (passed to ReadClient for production-grade handling)
    max_retries: int = 3
    retry_backoff_base: float = 1.0

    # Development network fields (None for live networks)
    cmd: str | None = None
    cmd_settings: dict[str, Any] = field(default_factory=dict)

    @property
    def is_development(self) -> bool:
        return self.cmd is not None

    @property
    def is_fork(self) -> bool:
        return self.cmd_settings.get("fork") is not None

    def get_endpoints(self) -> list[str]:
        """Get RPC endpoints with env var expansion.

        - Pure env var hosts (e.g., "$BACKUP_RPC") are filtered if unset
        - Partial expansion (e.g., "https://alchemy.com/v2/$KEY" with KEY unset) raises error

        Raises:
            EnvVarExpansionError: If a partial env var expansion would create invalid URL
            ValueError: If no valid endpoints remain after expansion
        """
        endpoints = []
        for host in self.hosts:
            expanded = _expand_env_var(host, network_id=self.id)
            if expanded:  # Skip None (pure env var that wasn't set)
                endpoints.append(expanded)

        if not endpoints:
            raise ValueError(
                f"Network '{self.id}' has no valid RPC endpoints after env var expansion. "
                f"Original hosts: {self.hosts}"
            )
        return endpoints

    def get_host_with_port(self) -> str:
        """Get first host URL with port for dev networks.

        Uses urllib.parse to correctly detect if port is already in URL.
        e.g., "http://127.0.0.1" needs port appended, "http://127.0.0.1:8545" doesn't.
        """
        from urllib.parse import urlparse

        endpoints = self.get_endpoints()
        host = endpoints[0]

        # Only append port for dev networks without explicit port
        if self.is_development:
            parsed = urlparse(host)
            if not parsed.port:  # No explicit port in URL
                port = self.cmd_settings.get("port", 8545)
                # Reconstruct URL with port
                host = f"{parsed.scheme}://{parsed.hostname}:{port}{parsed.path}"

        return host


def _get_config_path() -> Path | None:
    """Get network config file path. Auto-copies brownie config on first use."""
    brawny_config = Path.home() / ".brawny" / "network-config.yaml"

    if brawny_config.exists():
        return brawny_config

    # Auto-copy from brownie on first use
    brownie_config = Path.home() / ".brownie" / "network-config.yaml"
    if brownie_config.exists():
        brawny_config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(brownie_config, brawny_config)
        return brawny_config

    return None


def _parse_host(host_value: str | list | None, default: str = "") -> list[str]:
    """Parse host field - accepts string or list, returns list."""
    if host_value is None:
        return [default] if default else []
    if isinstance(host_value, str):
        return [host_value] if host_value else []
    return list(host_value)


def _parse_networks(data: dict) -> dict[str, NetworkConfig]:
    """Parse network config file."""
    networks: dict[str, NetworkConfig] = {}

    # Parse live networks
    for group in data.get("live", []):
        for net in group.get("networks", []):
            networks[net["id"]] = NetworkConfig(
                id=net["id"],
                hosts=_parse_host(net.get("host")),
                chainid=int(net["chainid"]) if "chainid" in net else None,
                name=net.get("name"),
                explorer=net.get("explorer"),
                multicall2=net.get("multicall2"),
                timeout=net.get("timeout", 30),
                max_retries=net.get("max_retries", 3),
                retry_backoff_base=net.get("retry_backoff_base", 1.0),
            )

    # Parse development networks (fork resolution happens at connect time)
    for net in data.get("development", []):
        networks[net["id"]] = NetworkConfig(
            id=net["id"],
            hosts=_parse_host(net.get("host"), default="http://127.0.0.1"),
            name=net.get("name"),
            timeout=net.get("timeout", 120),
            cmd=net.get("cmd"),
            cmd_settings=dict(net.get("cmd_settings", {})),
        )

    return networks


def load_networks() -> dict[str, NetworkConfig]:
    """Load all network configurations from Brownie-style config."""
    networks: dict[str, NetworkConfig] = {}

    # Load from config file
    config_path = _get_config_path()
    if config_path:
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
            networks = _parse_networks(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid network config at {config_path}: {e}")

    # Add built-in defaults (only if not already defined)
    _add_defaults(networks)

    return networks


def _add_defaults(networks: dict[str, NetworkConfig]) -> None:
    """Add built-in defaults if not already present."""
    if "development" not in networks:
        networks["development"] = NetworkConfig(
            id="development",
            name="Anvil (Local)",
            hosts=["http://127.0.0.1"],
            cmd="anvil",
            cmd_settings={"port": 8545, "accounts": 10},
        )

    if "mainnet-fork" not in networks:
        # Use env var for fork URL with public fallback
        # Users should set BRAWNY_FORK_RPC for reliable/fast forking
        fork_url = "${BRAWNY_FORK_RPC:-https://eth.llamarpc.com}"
        networks["mainnet-fork"] = NetworkConfig(
            id="mainnet-fork",
            name="Anvil (Mainnet Fork)",
            hosts=["http://127.0.0.1"],
            cmd="anvil",
            timeout=120,
            cmd_settings={
                "port": 8546,
                "fork": fork_url,  # Expanded at connect time
                "accounts": 10,
            },
        )
