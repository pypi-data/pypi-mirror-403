"""Runner command."""

from __future__ import annotations

import os
import sys

import click


@click.command()
@click.option("--once", is_flag=True, help="Process once and exit")
@click.option("--workers", type=int, help="Worker count override")
@click.option("--dry-run", is_flag=True, help="Create intents but don't execute")
@click.option(
    "--jobs-module",
    "jobs_modules",
    multiple=True,
    help="Additional job module(s) to load",
)
@click.option("--config", "config_path", default="./config.yaml", help="Path to config.yaml")
@click.option(
    "--no-strict",
    is_flag=True,
    help="Don't exit on job validation errors (warn only)",
)
def start(
    once: bool,
    workers: int | None,
    dry_run: bool,
    jobs_modules: tuple[str, ...],
    config_path: str,
    no_strict: bool,
) -> None:
    """Start the brawny daemon (job runner and transaction executor)."""
    from brawny.config import Config
    from brawny.daemon import BrawnyDaemon, RuntimeOverrides
    from brawny.logging import LogFormat, get_logger, log_unexpected, set_runtime_logging, setup_logging
    from brawny.metrics import (
        PrometheusMetricsProvider,
        set_metrics_provider,
        start_metrics_server,
    )
    from brawny.model.enums import IntentStatus
    from brawny.scheduler.shutdown import ShutdownContext, ShutdownHandler

    if not config_path or not os.path.exists(config_path):
        click.echo(
            f"Config file is required for run and was not found: {config_path}",
            err=True,
        )
        sys.exit(1)

    config = Config.from_yaml(config_path)
    config, overrides_applied = config.apply_env_overrides()

    log_level = os.environ.get("BRAWNY_LOG_LEVEL", "INFO")
    # Start in startup mode (human-readable, warnings only)
    setup_logging(log_level, LogFormat.JSON, config.chain_id, mode="startup")

    click.echo(f"Config: {config_path}")
    metrics_bind = f"127.0.0.1:{config.metrics_port}"
    log = get_logger(__name__)

    try:
        provider = PrometheusMetricsProvider()
        set_metrics_provider(provider)
        start_metrics_server(metrics_bind, provider)
        click.echo(f"Metrics: http://{metrics_bind}/metrics")
    except (OSError, RuntimeError) as e:
        raise RuntimeError(f"Failed to start metrics server at {metrics_bind}") from e

    # Build runtime overrides
    runtime_overrides = RuntimeOverrides(
        dry_run=dry_run,
        once=once,
        worker_count=workers,
        strict_validation=not no_strict,
    )

    click.echo("Starting brawny runner...")
    click.echo(f"  Chain ID: {config.chain_id}")
    if config.rpc_groups:
        from brawny.config.routing import (
            resolve_default_broadcast_group,
            resolve_default_read_group,
        )

        read_group = resolve_default_read_group(config)
        broadcast_group = resolve_default_broadcast_group(config)
        click.echo(f"  RPC Default Read Group: {read_group}")
        click.echo(f"  RPC Default Broadcast Group: {broadcast_group}")
        click.echo(f"  RPC Read Endpoints: {len(config.rpc_groups[read_group].endpoints)}")
        click.echo(
            f"  RPC Broadcast Endpoints: {len(config.rpc_groups[broadcast_group].endpoints)}"
        )
    click.echo(f"  Workers: {workers or config.worker_count}")
    if dry_run:
        click.echo("  Mode: DRY RUN (no transactions)")
    if once:
        click.echo("  Mode: Single iteration")

    # Initialize daemon
    daemon = BrawnyDaemon(
        config,
        overrides=runtime_overrides,
        extra_modules=list(jobs_modules),
    )

    validation_errors, routing_errors, startup_messages = daemon.initialize()

    # Show signers
    if daemon.keystore:
        signers_with_aliases = daemon.keystore.list_keys_with_aliases()
        if signers_with_aliases:
            # Format: "alias (0x123...)" or just "0x123..." if no alias
            formatted = []
            for addr, alias in signers_with_aliases:
                if alias:
                    formatted.append(f"{alias} ({addr[:10]}...)")
                else:
                    formatted.append(addr[:10] + "...")
            click.echo(f"  Signers: {len(signers_with_aliases)} ({', '.join(formatted)})")

    # Show startup warnings/errors
    for msg in startup_messages:
        color = "yellow" if msg.level == "warning" else "red"
        symbol = "\u26a0" if msg.level == "warning" else "\u2717"
        text = f"  {symbol} {msg.message}"
        if msg.fix:
            text += click.style(f" \u2192 {msg.fix}", dim=True)
        click.echo(click.style(text, fg=color))

    # Report validation errors
    if validation_errors:
        click.echo("")
        click.echo(click.style("Job validation errors:", fg="red", bold=True))
        for job_id, errors in validation_errors.items():
            click.echo(f"  {job_id}:")
            for error in errors:
                click.echo(f"    - {error}")

        click.echo("")
        click.echo(click.style("Tip:", dim=True) + " Remove the @job decorator to hide incomplete jobs from discovery.")

        if runtime_overrides.strict_validation:
            click.echo("")
            click.echo(
                "Exiting due to validation errors. Use --no-strict to continue anyway.",
                err=True,
            )
            sys.exit(1)
        else:
            click.echo("")
            click.echo(
                click.style("Continuing despite validation errors (--no-strict)", fg="yellow"),
            )

    # Report routing errors
    if routing_errors:
        click.echo("")
        click.echo(click.style("Job routing configuration errors:", fg="red", bold=True))
        for error in routing_errors:
            click.echo(f"  - {error}")

        if runtime_overrides.strict_validation:
            click.echo("")
            click.echo(
                "Exiting due to routing errors. Use --no-strict to continue anyway.",
                err=True,
            )
            sys.exit(1)
        else:
            click.echo("")
            click.echo(
                click.style("Continuing despite routing errors (--no-strict)", fg="yellow"),
            )

    # Show discovered jobs
    jobs = daemon.jobs
    if not jobs:
        click.echo("  Jobs discovered: 0")
    else:
        click.echo(f"  Jobs discovered: {len(jobs)}")
        job_items = list(jobs.items())[:20]
        for job_id, job in job_items:
            click.echo(f"    - {job_id}: {job.name}")
        if len(jobs) > 20:
            click.echo(click.style(f"    ... and {len(jobs) - 20} more", dim=True))

    # Check for orphaned jobs
    db = daemon.db
    db_jobs = db.list_all_jobs()
    discovered_job_ids = set(jobs.keys())
    orphaned = [j for j in db_jobs if j.job_id not in discovered_job_ids and j.enabled]
    if orphaned:
        click.echo("")
        click.echo(
            click.style("Orphaned jobs", fg="yellow", bold=True)
            + click.style(" (in database but not discovered):", fg="yellow")
        )
        for j in orphaned:
            click.echo(click.style(f"    - {j.job_id}", fg="yellow"))
        click.echo(click.style("  These won't run. Check: --jobs-module or ./jobs/", dim=True))

    # Warn if no jobs registered
    if not jobs:
        broadcasted_intents = db.get_intents_by_status(
            IntentStatus.BROADCASTED.value, chain_id=config.chain_id
        )
        broadcasted_count = len(broadcasted_intents)

        click.echo("")
        if broadcasted_count > 0:
            click.echo(
                click.style(
                    f"No jobs registered but {broadcasted_count} broadcasted intent(s) found.",
                    fg="yellow",
                ),
            )
            click.echo(
                click.style("  Continuing to monitor broadcasted transactions.", dim=True),
            )
        else:
            modules = list(jobs_modules)
            if modules:
                click.echo(
                    click.style("No jobs registered.", fg="yellow")
                    + " Ensure --jobs-module values are correct and jobs use @job.",
                )
            else:
                click.echo(
                    click.style("No jobs registered.", fg="yellow")
                    + " Add jobs under ./jobs or use --jobs-module.",
                )

    click.echo("\n--- Starting brawny ---")

    # Switch to runtime logging (full structured JSON)
    set_runtime_logging()

    # Create shutdown handler
    nonce_manager = daemon._executor.nonce_manager if daemon._executor else None
    shutdown_handler = ShutdownHandler(config, db, daemon.rpc, nonce_manager=nonce_manager)
    shutdown_handler.register_callback(lambda: daemon.stop(timeout=5.0))

    try:
        with ShutdownContext(shutdown_handler):
            if once:
                daemon.run(blocking=True)
                click.echo("Single iteration complete.")
            else:
                click.echo("Polling for new blocks... (Ctrl+C to stop)")
                try:
                    daemon.run(blocking=True)
                except KeyboardInterrupt:
                    click.echo("\nShutdown requested...")
    except Exception as exc:
        # BUG re-raise unexpected CLI runner failures.
        if not getattr(exc, "_logged_unexpected", False):
            log_unexpected(log, "cli.run_failed", error=str(exc)[:200], config_path=config_path)
        raise

    click.echo("Shutdown complete.")


def register(main) -> None:
    main.add_command(start)
