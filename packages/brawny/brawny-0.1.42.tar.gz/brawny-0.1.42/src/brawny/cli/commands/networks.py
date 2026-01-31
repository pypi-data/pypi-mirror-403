"""Network management CLI commands (Brownie-compatible).

Usage:
    brawny networks list
    brawny networks add <type> <id> <settings...>
    brawny networks delete <id>

These commands manage ~/.brawny/network-config.yaml (Brownie-compatible format).
This is separate from the project-level config.yaml networks section.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click
import yaml


def _get_config_path() -> Path:
    """Get user network config path."""
    return Path.home() / ".brawny" / "network-config.yaml"


def _load_config() -> dict[str, Any]:
    """Load user network config."""
    path = _get_config_path()
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {"live": [], "development": []}


def _save_config(config: dict[str, Any]) -> None:
    """Save user network config."""
    path = _get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


@click.group("networks")
def networks_cli() -> None:
    """Manage Brownie-compatible network configurations.

    These networks are stored in ~/.brawny/network-config.yaml and used
    by `network.connect()` in scripts and console.
    """
    pass


def _redact_api_keys(url: str) -> str:
    """Redact API keys from URLs for safe display.

    Matches common patterns:
    - /v2/abc123... → /v2/abc1...
    - /v3/abc123... → /v3/abc1...
    - ?apikey=... → ?apikey=...
    """
    import re
    # Redact Alchemy/Infura-style path keys (show first 4 chars)
    url = re.sub(r"(/v[23]/)([a-zA-Z0-9_-]{4})([a-zA-Z0-9_-]+)", r"\1\2...", url)
    # Redact query param API keys
    url = re.sub(r"([\?&]api[_-]?key=)([a-zA-Z0-9_-]{4})([a-zA-Z0-9_-]+)", r"\1\2...", url, flags=re.I)
    return url


@networks_cli.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed info (redacts API keys)")
def list_networks(verbose: bool) -> None:
    """List available networks."""
    from brawny.networks.config import load_networks

    networks = load_networks()

    live = [(n.id, n) for n in networks.values() if not n.is_development]
    dev = [(n.id, n) for n in networks.values() if n.is_development]

    click.echo("\nLive Networks:")
    if not live:
        click.echo("  (none configured)")
    for net_id, net in sorted(live):
        if verbose:
            # Redact API keys in displayed hosts for security
            redacted_hosts = [_redact_api_keys(h) for h in net.hosts[:2]]
            hosts_str = ", ".join(redacted_hosts)
            if len(net.hosts) > 2:
                hosts_str += f" (+{len(net.hosts) - 2} more)"
            click.echo(f"  {net_id}: chainid={net.chainid} hosts=[{hosts_str}]")
        else:
            click.echo(f"  - {net_id} (chainid: {net.chainid})")

    click.echo("\nDevelopment Networks:")
    for net_id, net in sorted(dev):
        fork_info = " (fork)" if net.is_fork else ""
        if verbose:
            click.echo(f"  {net_id}: cmd={net.cmd} port={net.cmd_settings.get('port', 8545)}{fork_info}")
        else:
            click.echo(f"  - {net_id}{fork_info}")


@networks_cli.command("add")
@click.argument("network_type", type=click.Choice(["live", "development"]))
@click.argument("network_id")
@click.argument("settings", nargs=-1)
def add_network(network_type: str, network_id: str, settings: tuple[str, ...]) -> None:
    """Add a new network to ~/.brawny/network-config.yaml.

    Examples:

        brawny networks add live mainnet-custom host=https://... chainid=1

        # Multiple hosts for failover (RPC pool):
        brawny networks add live mainnet host=https://eth.llamarpc.com host=https://eth-mainnet.g.alchemy.com/v2/KEY chainid=1

        brawny networks add development my-fork cmd=anvil port=9545 fork=mainnet
    """
    from brawny.networks.config import load_networks

    # Check if network ID already exists
    existing = load_networks()
    if network_id in existing:
        raise click.ClickException(
            f"Network '{network_id}' already exists. "
            f"Delete it first with: brawny networks delete {network_id}"
        )

    config = _load_config()

    # Parse key=value settings - collect repeated keys as lists
    params: dict[str, Any] = {}
    multi_keys: dict[str, list[str]] = {}  # For repeated keys like host=...

    for s in settings:
        if "=" not in s:
            raise click.ClickException(f"Invalid: {s}. Use key=value format.")
        key, value_str = s.split("=", 1)

        # Special handling for 'host' - can be repeated for multi-host
        if key == "host":
            multi_keys.setdefault("host", []).append(value_str)
            continue

        # Parse integers and floats for other keys
        value: Any = value_str
        try:
            value = int(value_str)
        except ValueError:
            try:
                value = float(value_str)
            except ValueError:
                pass
        params[key] = value

    # Convert multi-host to single or list as needed
    if "host" in multi_keys:
        hosts = multi_keys["host"]
        params["host"] = hosts if len(hosts) > 1 else hosts[0]

    if network_type == "live":
        if "host" not in params:
            raise click.ClickException("Live networks require 'host'")
        if "chainid" not in params:
            raise click.ClickException("Live networks require 'chainid'")

        # Ensure live section exists with at least one group
        if "live" not in config or not config["live"]:
            config["live"] = [{"name": "Custom", "networks": []}]

        # Find Custom group or use first group
        group = config["live"][0]
        for g in config["live"]:
            if g.get("name") == "Custom":
                group = g
                break

        net_config = {"id": network_id, **params}
        group.setdefault("networks", []).append(net_config)

    else:  # development
        if "cmd" not in params:
            raise click.ClickException("Development networks require 'cmd'")

        # Separate cmd_settings from top-level params
        cmd_keys = {"port", "fork", "fork_block", "accounts", "balance", "chain_id", "mnemonic", "block_time"}
        cmd_settings = {k: params.pop(k) for k in list(params.keys()) if k in cmd_keys}

        net_config: dict[str, Any] = {
            "id": network_id,
            "host": params.pop("host", "http://127.0.0.1"),
            "cmd": params.pop("cmd"),
            **params,
        }
        if cmd_settings:
            net_config["cmd_settings"] = cmd_settings

        config.setdefault("development", []).append(net_config)

    _save_config(config)
    click.echo(f"Added {network_type} network: {network_id}")


@networks_cli.command("delete")
@click.argument("network_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def delete_network(network_id: str, force: bool) -> None:
    """Delete a network from user config."""
    # Don't allow deleting built-in defaults
    builtin = {"development", "mainnet-fork"}
    if network_id in builtin:
        raise click.ClickException(
            f"Cannot delete built-in network '{network_id}'. "
            "You can override it by adding a network with the same ID."
        )

    config = _load_config()
    found = False

    # Check live networks
    for group in config.get("live", []):
        networks = group.get("networks", [])
        for i, net in enumerate(networks):
            if net["id"] == network_id:
                if not force:
                    click.confirm(f"Delete '{network_id}'?", abort=True)
                networks.pop(i)
                found = True
                break
        if found:
            break

    # Check development networks
    if not found:
        dev = config.get("development", [])
        for i, net in enumerate(dev):
            if net["id"] == network_id:
                if not force:
                    click.confirm(f"Delete '{network_id}'?", abort=True)
                dev.pop(i)
                found = True
                break

    if not found:
        raise click.ClickException(f"Network '{network_id}' not found in user config")

    _save_config(config)
    click.echo(f"Deleted: {network_id}")


def register(main) -> None:
    """Register networks command with main CLI."""
    main.add_command(networks_cli)
