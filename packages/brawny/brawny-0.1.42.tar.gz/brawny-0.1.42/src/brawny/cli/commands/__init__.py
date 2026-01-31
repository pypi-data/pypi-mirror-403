"""CLI command registration."""

from __future__ import annotations

from brawny.cli.commands.abi import register as register_abi
from brawny.cli.commands.contract import register as register_contract
from brawny.cli.commands.controls import register as register_controls
from brawny.cli.commands.health import register as register_health
from brawny.cli.commands.init_project import register as register_init
from brawny.cli.commands.intents import register as register_intents
from brawny.cli.commands.jobs import register as register_jobs
from brawny.cli.commands.logs import register as register_logs
from brawny.cli.commands.maintenance import register as register_maintenance
from brawny.cli.commands.migrate import register as register_migrate
from brawny.cli.commands.networks import register as register_networks
from brawny.cli.commands.run import register as register_start
from brawny.cli.commands.script import register as register_run
from brawny.cli.commands.accounts import register as register_accounts
from brawny.cli.commands.signer import register as register_signer


def register_all(main) -> None:
    register_migrate(main)
    register_start(main)  # brawny start (daemon)
    register_run(main)    # brawny run (scripts, brownie-compatible)
    register_init(main)
    register_jobs(main)   # includes jobs run
    register_intents(main)
    register_logs(main)   # brawny logs list/cleanup
    register_maintenance(main)
    register_health(main)
    register_abi(main)
    register_contract(main)
    register_accounts(main)
    register_networks(main)
    register_signer(main)  # brawny signer force-reset, status
    register_controls(main)
    # Console has optional dependency (prompt_toolkit) - import lazily
    try:
        from brawny.cli.commands.console import register as register_console
        register_console(main)
    except ImportError:
        pass  # prompt_toolkit not installed
