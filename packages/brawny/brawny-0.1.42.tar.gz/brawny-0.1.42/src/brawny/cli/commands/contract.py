"""Contract utility commands."""

from __future__ import annotations

import json
import os
import sys

import click

from brawny.cli.helpers import print_json


@click.group()
def contract() -> None:
    """Contract read utilities."""
    pass


@contract.command("call")
@click.option("--address", "address", required=True, help="Contract address")
@click.option("--fn", "fn_signature", required=True, help="Function signature")
@click.option("--args", "args", multiple=True, help="Function arguments as strings (repeatable)")
@click.option("--args-json", "args_json", default=None, help="Function arguments as JSON array (for typed values)")
@click.option("--abi", "abi_file", default=None, help="Optional ABI JSON file")
@click.option("--block", "block_number", type=int, default=None, help="Block number")
@click.option("--format", "fmt", default="json", help="Output format (json or text)")
@click.option("--config", "config_path", default="./config.yaml", help="Path to config.yaml")
def contract_call(
    address: str,
    fn_signature: str,
    args: tuple[str, ...],
    args_json: str | None,
    abi_file: str | None,
    block_number: int | None,
    fmt: str,
    config_path: str,
) -> None:
    """Call a view function and print decoded output with type.

    Arguments can be passed as strings with --args or as typed JSON with --args-json.

    Examples:

        brawny contract call --address 0x... --fn "balanceOf(address)" --args 0x...

        brawny contract call --address 0x... --fn "transfer(address,uint256)" --args-json '["0x...", 1000]'
    """
    from pathlib import Path

    from brawny.config import Config
    from brawny.alerts.contracts import ContractSystem
    from brawny.logging import LogFormat, get_logger, setup_logging
    from brawny._rpc.clients import ReadClient

    if not config_path or not os.path.exists(config_path):
        click.echo(
            f"Config file is required for contract call and was not found: {config_path}",
            err=True,
        )
        sys.exit(1)

    config = Config.from_yaml(config_path)
    config, overrides = config.apply_env_overrides()

    log_level = os.environ.get("BRAWNY_LOG_LEVEL", "INFO")
    setup_logging(log_level, LogFormat.JSON, config.chain_id)
    log = get_logger(__name__)
    log.info(
        "config.loaded",
        path=config_path,
        overrides=overrides,
        config=config.redacted_dict(),
    )

    rpc = ReadClient.from_config(config)
    # ContractSystem uses global ABI cache at ~/.brawny/abi_cache.db
    contract_system = ContractSystem(rpc, config)

    abi_data = None
    if abi_file:
        path = Path(abi_file)
        if not path.exists():
            click.echo(f"ABI file not found: {abi_file}", err=True)
            sys.exit(1)
        try:
            abi_data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            click.echo(f"Invalid ABI JSON: {e}", err=True)
            sys.exit(1)

    block_id = block_number if block_number is not None else rpc.get_block_number(timeout=5)

    handle = contract_system.handle(
        address=address,
        block_identifier=block_id,
        abi=abi_data,
    )

    caller = handle.fn(fn_signature)

    # Parse arguments - prefer args_json if provided
    if args_json:
        if args:
            click.echo("Cannot use both --args and --args-json", err=True)
            sys.exit(1)
        try:
            parsed_args = json.loads(args_json)
            if not isinstance(parsed_args, list):
                click.echo("--args-json must be a JSON array", err=True)
                sys.exit(1)
        except json.JSONDecodeError as e:
            click.echo(f"Invalid --args-json: {e}", err=True)
            sys.exit(1)
    else:
        parsed_args = list(args)

    value = caller.call(*parsed_args)

    if fmt == "text":
        click.echo(f"function: {fn_signature}")
        click.echo(f"block: {block_id}")
        click.echo(f"type: {type(value).__name__}")
        click.echo(f"value: {value}")
        return

    print_json(
        {
            "function": fn_signature,
            "block": block_id,
            "python_type": type(value).__name__,
            "value": value,
        }
    )


def register(main) -> None:
    main.add_command(contract)
