"""CLI entry group for brawny."""

from __future__ import annotations

import click

from brawny.cli.bootstrap import configure_bytecode_cache, load_env

load_env()
configure_bytecode_cache()


@click.group()
@click.version_option(version="0.1.0", prog_name="brawny")
def main() -> None:
    """brawny: Block-driven Ethereum job/transaction execution framework."""
    pass
