"""Jobs management commands."""

from __future__ import annotations

import click

from brawny.logging import get_logger, log_unexpected

logger = get_logger(__name__)


@click.group()
def jobs() -> None:
    """Manage jobs."""
    pass


@jobs.command("list")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def jobs_list(config_path: str | None) -> None:
    """List all registered jobs.

    Shows jobs discovered from code, with status from database.
    """
    # Suppress logging FIRST before any brawny imports
    from brawny.cli.helpers import suppress_logging

    suppress_logging()

    from datetime import datetime

    from brawny.cli.helpers import discover_jobs_for_cli, get_config, get_db
    from brawny.jobs.registry import get_registry

    # Discover jobs from code (same logic as brawny start)
    config = get_config(config_path)
    discover_jobs_for_cli(config)

    registry = get_registry()
    code_jobs = {job.job_id: job for job in registry.get_all()}

    # Get DB status for discovered jobs
    db = get_db(config_path)
    try:
        db_jobs = {j.job_id: j for j in db.list_all_jobs()}

        if not code_jobs:
            click.echo(click.style("No jobs discovered.", dim=True))
            click.echo("  Check: ./jobs/ directory or use --jobs-module.")

            # Show orphaned jobs if any
            if db_jobs:
                click.echo()
                click.echo(click.style("Jobs in database (not discovered):", fg="yellow"))
                for job_id, job in sorted(db_jobs.items()):
                    status = "enabled" if job.enabled else "disabled"
                    click.echo(f"    - {job_id} ({status})")
            return

        click.echo()
        def _parse_drain_until(value):
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None

        now = datetime.utcnow()

        for job_id in sorted(code_jobs.keys()):
            job = code_jobs[job_id]
            db_job = db_jobs.get(job_id)

            # Get interval from code (authoritative)
            interval = str(job.check_interval_blocks)

            # Get enabled status from DB, default to True for new jobs
            enabled = db_job.enabled if db_job else True

            drain_until = _parse_drain_until(db_job.drain_until) if db_job else None
            draining = drain_until is not None and drain_until > now

            # Status indicator
            if draining:
                status = click.style("! draining", fg="yellow")
            elif enabled:
                status = click.style("✓ enabled ", fg="green")
            else:
                status = click.style("✗ disabled", fg="red")

            line = f"  {status}  {job_id}  {click.style(f'every {interval} blocks', dim=True)}"
            if draining:
                line += click.style(f" (until {drain_until.isoformat()})", dim=True)
            click.echo(line)

        click.echo()

        # Warn about orphaned jobs (in DB but not discovered)
        orphaned = set(db_jobs.keys()) - set(code_jobs.keys())
        if orphaned:
            click.echo(click.style(f"Warning: {len(orphaned)} job(s) in database but not discovered:", fg="yellow"))
            for job_id in sorted(orphaned):
                job = db_jobs[job_id]
                status = "enabled" if job.enabled else "disabled"
                click.echo(f"    - {job_id} ({status})")
            click.echo()
            click.echo("  To remove orphaned jobs from database:")
            click.echo(click.style("    brawny jobs remove <job_id>", fg="cyan"))
            click.echo()

    finally:
        db.close()


@jobs.command("validate")
@click.option(
    "--jobs-module",
    "jobs_modules",
    multiple=True,
    help="Additional job module(s) to load",
)
@click.option("--config", "config_path", default="./config.yaml", help="Path to config.yaml")
def jobs_validate(jobs_modules: tuple[str, ...], config_path: str) -> None:
    """Validate job definitions including signer configuration."""
    import os
    import sys

    from brawny.config import Config
    from brawny.jobs.registry import get_registry
    from brawny.jobs.discovery import auto_discover_jobs, discover_jobs
    from brawny.jobs.job_validation import validate_all_jobs
    from brawny.keystore import create_keystore

    if not config_path or not os.path.exists(config_path):
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    config = Config.from_yaml(config_path)
    config, _ = config.apply_env_overrides()
    registry = get_registry()
    registry.clear()

    modules = list(jobs_modules)
    if modules:
        discover_jobs(modules)
    else:
        auto_discover_jobs()
    all_jobs = registry.get_all()

    if not all_jobs:
        click.echo("No jobs discovered.", err=True)
        click.echo("  Add jobs under ./jobs or use --jobs-module", err=True)
        sys.exit(1)

    # Try to load keystore for signer validation
    keystore = None
    try:
        keystore = create_keystore(
            config.keystore_type,
            keystore_path=config.keystore_path,
            allowed_signers=[],
        )
    except Exception as e:
        # RECOVERABLE keystore load failures skip signer validation.
        log_unexpected(logger, "jobs.keystore_load_failed", error=str(e)[:200])
        click.echo(click.style(f"Warning: Could not load keystore ({e})", fg="yellow"))
        click.echo("  Signer validation will be skipped.")
        click.echo()

    click.echo(f"Validating {len(all_jobs)} job(s)...")
    click.echo("-" * 50)

    errors = validate_all_jobs({job.job_id: job for job in all_jobs}, keystore=keystore)

    passed = 0
    failed = 0
    for job in all_jobs:
        job_id = job.job_id
        if job_id in errors:
            click.echo(click.style(f"  ✗ {job_id}", fg="red"))
            for error in errors[job_id]:
                click.echo(f"      - {error}")
            failed += 1
        else:
            click.echo(click.style(f"  ✓ {job_id}", fg="green"))
            passed += 1

    click.echo("-" * 50)
    if failed > 0:
        click.echo(click.style(f"{passed} passed, {failed} failed", fg="red"))
        click.echo()
        click.echo(click.style("Tip:", dim=True) + " Remove the @job decorator to hide incomplete jobs from discovery.")
        sys.exit(1)
    else:
        click.echo(click.style(f"{passed} passed", fg="green"))


@jobs.command("enable")
@click.argument("job_id")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def jobs_enable(job_id: str, config_path: str | None) -> None:
    """Enable a job."""
    from brawny.cli.helpers import get_db

    db = get_db(config_path)
    try:
        updated = db.set_job_enabled(job_id, True)
        if updated:
            click.echo(f"Job '{job_id}' enabled.")
        else:
            click.echo(f"Job '{job_id}' not found.", err=True)
    finally:
        db.close()


@jobs.command("disable")
@click.argument("job_id")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def jobs_disable(job_id: str, config_path: str | None) -> None:
    """Disable a job."""
    from brawny.cli.helpers import get_db

    db = get_db(config_path)
    try:
        updated = db.set_job_enabled(job_id, False)
        if updated:
            click.echo(f"Job '{job_id}' disabled.")
        else:
            click.echo(f"Job '{job_id}' not found.", err=True)
    finally:
        db.close()


@jobs.command("drain")
@click.argument("job_id")
@click.option(
    "--ttl-seconds",
    type=int,
    default=3600,
    show_default=True,
    help="Drain duration in seconds (ignored if --until is set)",
)
@click.option(
    "--until",
    "until_iso",
    default=None,
    help="Drain until ISO timestamp (e.g. 2025-01-01T00:00:00)",
)
@click.option("--reason", "-r", default=None, help="Reason for drain")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def jobs_drain(
    job_id: str,
    ttl_seconds: int,
    until_iso: str | None,
    reason: str | None,
    config_path: str | None,
) -> None:
    """Drain a job (pause new intents) until a timestamp."""
    from datetime import datetime, timedelta

    from brawny.cli.helpers import get_db

    if until_iso:
        try:
            drain_until = datetime.fromisoformat(until_iso)
        except ValueError:
            click.echo("Invalid --until format, expected ISO timestamp.", err=True)
            raise SystemExit(1)
    else:
        drain_until = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    db = get_db(config_path)
    try:
        updated = db.set_job_drain(
            job_id,
            drain_until=drain_until,
            reason=reason,
            actor="cli",
            source="cli",
        )
        if updated:
            click.echo(
                f"Job '{job_id}' drained until {drain_until.isoformat()}."
            )
        else:
            click.echo(f"Job '{job_id}' not found.", err=True)
    finally:
        db.close()


@jobs.command("undrain")
@click.argument("job_id")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def jobs_undrain(job_id: str, config_path: str | None) -> None:
    """Clear job drain."""
    from brawny.cli.helpers import get_db

    db = get_db(config_path)
    try:
        updated = db.clear_job_drain(job_id, actor="cli", source="cli")
        if updated:
            click.echo(f"Job '{job_id}' undrained.")
        else:
            click.echo(f"Job '{job_id}' not found.", err=True)
    finally:
        db.close()


@jobs.command("remove")
@click.argument("job_id")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def jobs_remove(job_id: str, config_path: str | None, force: bool) -> None:
    """Remove a job from the database.

    Use this to clean up orphaned jobs (jobs in database but not discovered from code).
    """
    from brawny.cli.helpers import get_db

    db = get_db(config_path)
    try:
        # Check if job exists
        job = db.get_job(job_id)
        if not job:
            click.echo(f"Job '{job_id}' not found in database.", err=True)
            return

        # Confirm unless --force
        if not force:
            click.echo(f"This will remove job '{job_id}' and its key-value data from the database.")
            if not click.confirm("Continue?"):
                click.echo("Cancelled.")
                return

        deleted = db.delete_job(job_id)
        if deleted:
            click.echo(f"Job '{job_id}' removed.")
        else:
            click.echo(f"Failed to remove job '{job_id}'.", err=True)
    finally:
        db.close()


@jobs.command("status")
@click.argument("job_id")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def jobs_status(job_id: str, config_path: str | None) -> None:
    """Show status for a job."""
    from brawny.cli.helpers import get_db

    db = get_db(config_path)
    try:
        job = db.get_job(job_id)
        if not job:
            click.echo(f"Job '{job_id}' not found.", err=True)
            return
        click.echo(f"\nJob: {job.job_id}")
        click.echo("-" * 40)
        click.echo(f"  Name: {job.job_name}")
        click.echo(f"  Enabled: {job.enabled}")
        click.echo(f"  Check Interval: {job.check_interval_blocks} blocks")
        click.echo(f"  Last Checked Block: {job.last_checked_block_number or 'Never'}")
        click.echo(f"  Last Triggered Block: {job.last_triggered_block_number or 'Never'}")
        click.echo(f"  Created: {job.created_at}")
        click.echo(f"  Updated: {job.updated_at}")
        click.echo()
    finally:
        db.close()


@jobs.command("run")
@click.argument("job_id")
@click.option("--at-block", type=int, help="Run check/build against this block")
@click.option("--dry-run", is_flag=True, help="Run check only (skip build_intent)")
@click.option(
    "--jobs-module",
    "jobs_modules",
    multiple=True,
    help="Additional job module(s) to load",
)
@click.option("--config", "config_path", default="./config.yaml", help="Path to config.yaml")
def jobs_run(
    job_id: str,
    at_block: int | None,
    dry_run: bool,
    jobs_modules: tuple[str, ...],
    config_path: str,
) -> None:
    """Run check/build for a single job without sending transactions.

    Developer utility for testing jobs locally.
    """
    # Import the implementation from job_dev
    from brawny.cli.commands.job_dev import job_run as _job_run_impl
    # Use Click's context to invoke the command
    ctx = click.get_current_context()
    ctx.invoke(
        _job_run_impl,
        job_id=job_id,
        at_block=at_block,
        dry_run=dry_run,
        jobs_modules=jobs_modules,
        config_path=config_path,
    )


def register(main) -> None:
    main.add_command(jobs)
