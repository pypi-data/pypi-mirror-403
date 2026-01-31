"""Script execution command (brownie-compatible).

Usage:
    brawny run scripts/harvest.py
    brawny run scripts/harvest.py main --arg1 value1
    brawny run scripts/deploy.py --fork
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import click

from brawny.logging import get_logger

log = get_logger(__name__)


@click.command("run")
@click.argument("script_path", type=click.Path(exists=True))
@click.argument("function", default="main")
@click.argument("args", nargs=-1)
@click.option("--config", "config_path", default="./config.yaml", help="Path to config.yaml")
@click.option("--fork", is_flag=True, help="Fork network with Anvil")
@click.option("--fork-block", type=int, help="Fork at specific block")
@click.option("--port", default=8545, type=int, help="Port for Anvil fork")
@click.option("--interactive", "-i", is_flag=True, help="Drop into console after script")
def run(
    script_path: str,
    function: str,
    args: tuple[str, ...],
    config_path: str,
    fork: bool,
    fork_block: int | None,
    port: int,
    interactive: bool,
):
    """Run a Python script with brawny context (brownie-compatible).

    Scripts have access to:

      accounts   - Signing accounts from keystore

      Contract() - Contract interaction

      chain      - Block information

      history    - Transaction history

      Wei()      - Unit conversion

      web3, rpc  - Direct RPC access

    Example:

        brawny run scripts/harvest.py

        brawny run scripts/deploy.py deploy --fork

        brawny run scripts/debug.py --interactive
    """
    from brawny.alerts.contracts import ContractSystem
    from brawny.config import Config
    from brawny.keystore import create_keystore
    from brawny._rpc.clients import BroadcastClient
    from brawny.accounts import _init_accounts
    from brawny.history import _init_history
    from brawny.chain import _init_chain
    from brawny.script_tx import _init_broadcaster
    from brawny.api import _set_fallback_rpc
    from brawny._context import _job_ctx
    from brawny.model.types import JobContext, BlockInfo
    from brawny.logging import setup_logging

    # Setup logging
    setup_logging(log_level="INFO")

    if not os.path.exists(config_path):
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    config = Config.from_yaml(config_path)
    config, _ = config.apply_env_overrides()

    from brawny.config.routing import resolve_default_read_group

    default_group = resolve_default_read_group(config)
    rpc_endpoints = config.rpc_groups[default_group].endpoints
    chain_id = config.chain_id

    if not rpc_endpoints:
        click.echo("No RPC endpoints configured", err=True)
        sys.exit(1)

    if fork:
        # Start Anvil fork
        from brawny.cli.commands.console import _start_anvil_fork
        local_url = _start_anvil_fork(rpc_endpoints[0], chain_id, port, block=fork_block)
        rpc_endpoints = [local_url]
        click.echo(f"Started Anvil fork at {local_url}")

    # Create broadcast client
    from brawny._rpc.retry_policy import broadcast_policy

    rpc = BroadcastClient(
        endpoints=rpc_endpoints,
        timeout_seconds=config.rpc_timeout_seconds,
        max_retries=config.rpc_max_retries,
        retry_backoff_base=config.rpc_retry_backoff_base,
        retry_policy=broadcast_policy(config),
    )
    _set_fallback_rpc(rpc)

    # Create keystore for signing
    keystore = create_keystore(
        config.keystore_type,
        keystore_path=config.keystore_path,
        allowed_signers=[],
    )

    # Create contract system
    contract_system = ContractSystem(rpc, config)

    # Initialize script singletons
    _init_accounts()
    _init_history()
    _init_chain(rpc, chain_id)
    _init_broadcaster(rpc, keystore, chain_id)

    # Set up job context for Contract() to work
    block_data = rpc.get_block("latest")
    block = BlockInfo(
        chain_id=chain_id,
        block_number=block_data["number"],
        block_hash=block_data["hash"],
        timestamp=block_data["timestamp"],
        base_fee=block_data.get("baseFeePerGas", 0),
    )
    ctx = JobContext(
        block=block,
        rpc=rpc,
        logger=log,
        contract_system=contract_system,
        hook_name="script",
    )
    _job_ctx.set(ctx)

    # Load and run script
    script_file = Path(script_path).resolve()
    sys.path.insert(0, str(script_file.parent))

    try:
        # Load module
        spec = importlib.util.spec_from_file_location("__script__", script_file)
        if spec is None or spec.loader is None:
            raise click.ClickException(f"Cannot load script: {script_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["__script__"] = module
        spec.loader.exec_module(module)

        # Find and call function
        if not hasattr(module, function):
            available = [n for n in dir(module) if not n.startswith("_") and callable(getattr(module, n))]
            raise click.ClickException(
                f"Function '{function}' not found in {script_path}. "
                f"Available: {', '.join(available)}"
            )

        func = getattr(module, function)

        # Parse args (simple key=value style)
        kwargs = {}
        positional = []
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                kwargs[key] = value
            else:
                positional.append(arg)

        # Execute
        log.info("script.run", script=script_path, function=function)
        result = func(*positional, **kwargs)

        if result is not None:
            click.echo(f"Result: {result}")

        log.info("script.complete")

        # Interactive mode: drop into console with script namespace
        if interactive:
            click.echo("\nDropping into interactive console (script namespace available)...")
            try:
                from brawny.cli.commands.console import _start_repl
                # Make script module's namespace available
                namespace = {name: getattr(module, name) for name in dir(module) if not name.startswith("_")}
                _start_repl(namespace)
            except ImportError:
                click.echo("Interactive mode requires prompt_toolkit. Install with: pip install prompt_toolkit", err=True)

    finally:
        sys.path.remove(str(script_file.parent))
        if "__script__" in sys.modules:
            del sys.modules["__script__"]


def register(main) -> None:
    """Register run command with main CLI (brownie-compatible script runner)."""
    main.add_command(run)
