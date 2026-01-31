"""Runtime controls commands."""

from __future__ import annotations

from datetime import datetime, timedelta

import click


@click.group()
def controls() -> None:
    """Manage runtime controls."""
    pass


@controls.command("list")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def controls_list(config_path: str | None) -> None:
    """List runtime controls."""
    from brawny.cli.helpers import get_db

    db = get_db(config_path)
    try:
        controls_list = db.list_runtime_controls()
        if not controls_list:
            click.echo("No runtime controls set.")
            return
        click.echo()
        for rc in controls_list:
            status = "active" if rc.active else "inactive"
            expires_at = rc.expires_at.isoformat() if rc.expires_at else "none"
            click.echo(
                f"  {rc.control}: {status}  expires_at={expires_at}  mode={rc.mode}"
            )
            if rc.reason:
                click.echo(f"    reason: {rc.reason}")
            if rc.actor:
                click.echo(f"    actor: {rc.actor}")
        click.echo()
    finally:
        db.close()


@controls.command("activate")
@click.argument("control")
@click.option(
    "--ttl-seconds",
    type=int,
    default=900,
    show_default=True,
    help="TTL in seconds (ignored if --forever)",
)
@click.option("--forever", is_flag=True, help="Set without expiration")
@click.option("--reason", "reason", default=None, help="Reason for activation")
@click.option("--actor", "actor", default="cli", help="Actor label for audit")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def controls_activate(
    control: str,
    ttl_seconds: int,
    forever: bool,
    reason: str | None,
    actor: str,
    config_path: str | None,
) -> None:
    """Activate a runtime control."""
    from brawny.cli.helpers import get_db

    expires_at = None
    if not forever:
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    db = get_db(config_path)
    try:
        db.set_runtime_control(
            control=control,
            active=True,
            expires_at=expires_at,
            reason=reason,
            actor=actor,
            mode="manual",
        )
        if expires_at:
            click.echo(f"Control '{control}' activated until {expires_at.isoformat()}.")
        else:
            click.echo(f"Control '{control}' activated with no expiration.")
    finally:
        db.close()


@controls.command("deactivate")
@click.argument("control")
@click.option("--reason", "reason", default=None, help="Reason for deactivation")
@click.option("--actor", "actor", default="cli", help="Actor label for audit")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def controls_deactivate(
    control: str,
    reason: str | None,
    actor: str,
    config_path: str | None,
) -> None:
    """Deactivate a runtime control."""
    from brawny.cli.helpers import get_db

    db = get_db(config_path)
    try:
        db.set_runtime_control(
            control=control,
            active=False,
            expires_at=None,
            reason=reason,
            actor=actor,
            mode="manual",
        )
        click.echo(f"Control '{control}' deactivated.")
    finally:
        db.close()


def register(main) -> None:
    """Register runtime controls commands."""
    main.add_command(controls)
