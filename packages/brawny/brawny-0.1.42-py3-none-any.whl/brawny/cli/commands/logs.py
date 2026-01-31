"""Job logs commands."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import click


@click.group()
def logs() -> None:
    """View and manage job logs."""
    pass


@logs.command("list")
@click.option("--job", "job_id", help="Filter by job ID")
@click.option("--latest", is_flag=True, help="Show only latest per job")
@click.option("--limit", default=20, help="Max entries to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def list_logs(
    job_id: str | None,
    latest: bool,
    limit: int,
    as_json: bool,
    config_path: str | None,
) -> None:
    """List job logs."""
    from brawny.cli.helpers import suppress_logging

    suppress_logging()

    from brawny.cli.helpers import get_config, get_db_readonly
    from brawny.db.ops import logs as log_ops

    config = get_config(config_path)
    db = get_db_readonly(config_path)

    if latest:
        entries = log_ops.list_latest_logs(db, config.chain_id)
    elif job_id:
        entries = log_ops.list_logs(db, config.chain_id, job_id, limit)
    else:
        entries = log_ops.list_all_logs(db, config.chain_id, limit)

    if not entries:
        click.echo("No logs found.")
        return

    if as_json:
        click.echo(json.dumps(entries, default=str, indent=2))
        return

    for entry in entries:
        ts = entry["ts"]
        if isinstance(ts, datetime):
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
        level = entry["level"]
        level_color = "yellow" if level == "warn" else ("red" if level == "error" else None)
        level_str = click.style(f"({level})", fg=level_color) if level_color else f"({level})"
        click.echo(f"[{ts}] {entry['job_id']} {level_str}: {entry['fields']}")


@logs.command("cleanup")
@click.option("--older-than", default=7, type=int, help="Delete logs older than N days")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def cleanup_logs(older_than: int, config_path: str | None) -> None:
    """Delete old job logs."""
    from brawny.cli.helpers import suppress_logging

    suppress_logging()

    from brawny.cli.helpers import get_config, get_db
    from brawny.db.ops import logs as log_ops

    config = get_config(config_path)
    db = get_db(config_path)
    cutoff = datetime.utcnow() - timedelta(days=older_than)
    deleted = log_ops.delete_old_logs(db, config.chain_id, cutoff)
    click.echo(f"Deleted {deleted} logs older than {older_than} days.")


def register(main: click.Group) -> None:
    """Register logs commands."""
    main.add_command(logs)
