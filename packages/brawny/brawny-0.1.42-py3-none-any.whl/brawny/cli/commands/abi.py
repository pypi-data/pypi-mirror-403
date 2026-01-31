"""ABI cache commands.

Uses global ABI cache at ~/.brawny/abi_cache.db.
"""

from __future__ import annotations

import json
import sys

import click

from brawny.db.global_cache import GlobalABICache


@click.group()
def abi() -> None:
    """Manage ABI cache (stored in ~/.brawny/abi_cache.db)."""
    pass


@abi.command("show")
@click.argument("address")
@click.option("--chain-id", type=int, default=1, help="Chain ID (default: 1)")
def abi_show(address: str, chain_id: int) -> None:
    """Show cached ABI for address."""
    cache = GlobalABICache()
    cached = cache.get_cached_abi(chain_id, address)
    if not cached:
        click.echo(f"No cached ABI for {address} on chain {chain_id}.")
        return

    click.echo(f"\nCached ABI for {address}")
    click.echo("-" * 60)
    click.echo(f"  Chain ID: {cached.chain_id}")
    click.echo(f"  Source: {cached.source}")
    click.echo(f"  Resolved: {cached.resolved_at}")
    click.echo("\n  ABI Preview:")

    try:
        abi_data = json.loads(cached.abi_json)
        for item in abi_data[:10]:
            if item.get("type") == "function":
                name = item.get("name", "?")
                inputs = ", ".join(i.get("type", "?") for i in item.get("inputs", []))
                click.echo(f"    - {name}({inputs})")
        if len(abi_data) > 10:
            click.echo(f"    ... and {len(abi_data) - 10} more")
    except json.JSONDecodeError:
        click.echo("    (Invalid JSON)")
    click.echo()


@abi.command("set")
@click.argument("address")
@click.option("--file", "abi_file", required=True, help="ABI JSON file")
@click.option("--chain-id", type=int, default=1, help="Chain ID (default: 1)")
def abi_set(address: str, abi_file: str, chain_id: int) -> None:
    """Set cached ABI from file."""
    from pathlib import Path

    path = Path(abi_file)
    if not path.exists():
        click.echo(f"File not found: {abi_file}", err=True)
        sys.exit(1)

    abi_json = path.read_text()

    try:
        json.loads(abi_json)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    cache = GlobalABICache()
    cache.set_cached_abi(chain_id, address, abi_json, "manual")
    click.echo(f"ABI cached for {address} on chain {chain_id}.")


@abi.command("clear")
@click.argument("address")
@click.option("--chain-id", type=int, default=1, help="Chain ID (default: 1)")
def abi_clear(address: str, chain_id: int) -> None:
    """Clear cached ABI for address."""
    cache = GlobalABICache()
    if cache.clear_cached_abi(chain_id, address):
        click.echo(f"ABI cache cleared for {address}.")
    else:
        click.echo(f"No cached ABI found for {address}.")


def register(main) -> None:
    main.add_command(abi)
