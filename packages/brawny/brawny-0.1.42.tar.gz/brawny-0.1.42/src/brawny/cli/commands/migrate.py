"""Database migration commands."""

from __future__ import annotations

import click

from brawny.cli.helpers import get_db


@click.command()
@click.option("--status", is_flag=True, help="Show migration status only")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def migrate(status: bool, config_path: str | None) -> None:
    """Run database migrations."""
    from brawny.db.migrate import Migrator, verify_critical_schema

    db = get_db(config_path)
    try:
        migrator = Migrator(db)

        if status:
            migrations = migrator.status()
            if not migrations:
                click.echo("No migrations found.")
                return

            click.echo("\nMigration Status:")
            click.echo("-" * 60)
            for m in migrations:
                status_icon = "[x]" if m["applied"] else "[ ]"
                applied = f" ({m['applied_at']})" if m["applied_at"] else ""
                click.echo(f"  {status_icon} {m['version']} - {m['filename']}{applied}")
            click.echo()
        else:
            pending = migrator.pending()
            if not pending:
                verify_critical_schema(db)
                click.echo("No pending migrations.")
                return

            click.echo(f"Running {len(pending)} migration(s)...")
            applied = migrator.migrate()
            for m in applied:
                click.echo(f"  Applied: {m.version} - {m.filename}")
            verify_critical_schema(db)
            click.echo(f"\nSuccessfully applied {len(applied)} migration(s).")
    finally:
        db.close()


def register(main) -> None:
    main.add_command(migrate)
