"""Maintenance commands."""

from __future__ import annotations

import click

from brawny.cli.helpers import get_config, get_db


@click.command()
def reconcile() -> None:
    """Run recovery reconciliation."""
    from brawny.config import get_config
    from brawny.db import create_database
    from brawny._rpc.clients import ReadClient
    from brawny.recovery.runner import run_periodic_recovery
    from brawny.tx.nonce import NonceManager

    click.echo("Running recovery reconciliation...")

    config = get_config()
    db = create_database(
        config.database_url,
        circuit_breaker_failures=config.db_circuit_breaker_failures,
        circuit_breaker_seconds=config.db_circuit_breaker_seconds,
        production=config.production,
    )
    db.connect()

    try:
        rpc = ReadClient.from_config(config)
        nonce_manager = NonceManager(db, rpc, config.chain_id)
        run_periodic_recovery(
            db,
            config,
            nonce_manager,
            actor="cli",
            source="maintenance_reconcile",
        )
        click.echo("Recovery reconciliation complete.")

    finally:
        db.close()


@click.command()
@click.option("--older-than", default="30d", help="Delete intents older than (e.g., 30d)")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def cleanup(older_than: str, config_path: str | None) -> None:
    """Clean up old data."""
    if older_than.endswith("d"):
        days = int(older_than[:-1])
    else:
        days = int(older_than)

    db = get_db(config_path)
    try:
        deleted = db.cleanup_old_intents(days)
        click.echo(f"Deleted {deleted} old intents.")
    finally:
        db.close()

@click.command("audit-intents")
@click.option("--max-age-seconds", type=int, default=None, help="Max age for broadcasted intents")
@click.option("--limit", default=100, help="Limit results")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def audit_intents(max_age_seconds: int | None, limit: int, config_path: str | None) -> None:
    """Audit intent state invariants and report inconsistencies."""
    from brawny.config import Config
    from brawny.metrics import INTENT_STATE_INCONSISTENT, get_metrics

    if config_path:
        config = Config.from_yaml(config_path)
        config, _ = config.apply_env_overrides()
    else:
        from brawny.config import get_config

        config = get_config()

    db = get_db(config_path)
    try:
        age_seconds = max_age_seconds or config.claim_timeout_seconds
        issues = db.list_intent_inconsistencies(
            max_age_seconds=age_seconds,
            limit=limit,
            chain_id=config.chain_id,
        )
        if not issues:
            click.echo("No intent inconsistencies found.")
            return

        click.echo("\nIntent inconsistencies:")
        click.echo("-" * 90)
        click.echo(f"{'Intent ID':<38} {'Status':<12} {'Reason':<30}")
        click.echo("-" * 90)
        counts: dict[str, int] = {}
        for issue in issues:
            intent_id = str(issue["intent_id"])[:36]
            status = issue.get("status", "")
            reason = issue.get("reason", "")
            counts[reason] = counts.get(reason, 0) + 1
            click.echo(f"{intent_id:<38} {status:<12} {reason:<30}")

        metrics = get_metrics()
        for reason, count in counts.items():
            metrics.counter(INTENT_STATE_INCONSISTENT).inc(
                count,
                chain_id=config.chain_id,
                reason=reason,
            )

        click.echo(f"\n(Showing {len(issues)} of {limit} max)")
    finally:
        db.close()


@click.command("repair-claims")
@click.option("--older-than", type=int, default=10, help="Minutes threshold")
@click.option("--execute", is_flag=True, help="Actually perform repair (dry-run by default)")
@click.option("--limit", type=int, default=100, help="Max intents to repair")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def repair_claims(
    older_than: int,
    execute: bool,
    limit: int,
    config_path: str | None,
) -> None:
    """Release stuck CLAIMED intents with zero attempts."""
    config = get_config(config_path)
    db = get_db(config_path)
    try:
        query = """
            SELECT i.intent_id, i.job_id, i.claimed_at
            FROM tx_intents i
            WHERE i.chain_id = ?
              AND i.status = 'claimed'
              AND (i.claimed_at IS NULL OR datetime(i.claimed_at) < datetime('now', ? || ' minutes'))
              AND NOT EXISTS (SELECT 1 FROM tx_attempts a WHERE a.intent_id = i.intent_id)
            ORDER BY (i.claimed_at IS NOT NULL), i.claimed_at ASC
            LIMIT ?
        """
        stuck = db.execute_returning(query, (config.chain_id, -older_than, limit))

        if not stuck:
            click.echo("No stuck claims found matching criteria.")
            return

        click.echo(f"Found {len(stuck)} stuck claims (no attempts):")
        for row in stuck[:10]:
            click.echo(
                f"  - {row['intent_id']} (job={row['job_id']}, claimed={row['claimed_at']})"
            )
        if len(stuck) > 10:
            click.echo(f"  ... and {len(stuck) - 10} more")

        if not execute:
            click.echo("\nDry-run mode. Use --execute to repair.")
            return

        repaired = 0
        for row in stuck:
            if db.release_intent_claim(row["intent_id"]):
                repaired += 1

        click.echo(f"\nRepaired {repaired}/{len(stuck)} intents.")
    finally:
        db.close()


def register(main) -> None:
    main.add_command(reconcile)
    main.add_command(cleanup)
    main.add_command(audit_intents)
    main.add_command(repair_claims)
