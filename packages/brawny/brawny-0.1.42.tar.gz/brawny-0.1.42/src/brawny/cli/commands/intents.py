"""Transaction intent commands."""

from __future__ import annotations

import sys

import click

from brawny.cli.helpers import get_db


@click.group()
def intents() -> None:
    """Manage transaction intents."""
    pass


@intents.command("list")
@click.option("--status", help="Filter by status")
@click.option("--job", help="Filter by job ID")
@click.option("--limit", default=50, help="Limit results")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def intents_list(status: str | None, job: str | None, limit: int, config_path: str | None) -> None:
    """List transaction intents."""
    db = get_db(config_path)
    try:
        intents_data = db.list_intents_filtered(status=status, job_id=job, limit=limit)
        if not intents_data:
            click.echo("No intents found.")
            return

        click.echo("\nTransaction Intents:")
        click.echo("-" * 120)
        click.echo(f"{'Intent ID':<38} {'Job':<20} {'Status':<12} {'Created':<20} {'Retry After':<20}")
        click.echo("-" * 120)
        for intent in intents_data:
            intent_id = str(intent["intent_id"])[:36]
            job_id = intent["job_id"][:18]
            created = str(intent["created_at"])[:19]
            retry_after = str(intent.get("retry_after") or "")[:19]
            click.echo(f"{intent_id:<38} {job_id:<20} {intent['status']:<12} {created:<20} {retry_after:<20}")
        click.echo(f"\n(Showing {len(intents_data)} of {limit} max)")
    finally:
        db.close()


@intents.command("show")
@click.argument("intent_id")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def intents_show(intent_id: str, config_path: str | None) -> None:
    """Show intent details."""
    from uuid import UUID

    db = get_db(config_path)
    try:
        intent = db.get_intent(UUID(intent_id))
        if not intent:
            click.echo(f"Intent '{intent_id}' not found.", err=True)
            sys.exit(1)

        click.echo(f"\nIntent: {intent.intent_id}")
        click.echo("-" * 60)
        click.echo(f"  Job ID: {intent.job_id}")
        click.echo(f"  Chain ID: {intent.chain_id}")
        click.echo(f"  Status: {intent.status.value}")
        click.echo(f"  Signer: {intent.signer_address}")
        click.echo(f"  To: {intent.to_address}")
        click.echo(f"  Value: {intent.value_wei} wei")
        click.echo(f"  Idempotency Key: {intent.idempotency_key}")
        click.echo(f"  Min Confirmations: {intent.min_confirmations}")
        if intent.deadline_ts:
            click.echo(f"  Deadline: {intent.deadline_ts}")
        if intent.retry_after:
            click.echo(f"  Retry After: {intent.retry_after}")
        if intent.retry_count > 0:
            click.echo(f"  Retry Count: {intent.retry_count}")
        if intent.claim_token:
            click.echo(f"  Claim Token: {intent.claim_token}")
        click.echo(f"  Created: {intent.created_at}")
        click.echo(f"  Updated: {intent.updated_at}")

        attempts = db.get_attempts_for_intent(intent.intent_id)
        if attempts:
            click.echo(f"\n  Attempts ({len(attempts)}):")
            for att in attempts:
                status = att.status.value
                tx_hash = att.tx_hash[:20] + "..." if att.tx_hash else "N/A"
                click.echo(f"    - {att.attempt_id}: {status} (tx: {tx_hash})")
        click.echo()
    finally:
        db.close()


@intents.command("cancel")
@click.argument("intent_id")
@click.option("--force", is_flag=True, help="Force cancel even if in-flight")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def intents_cancel(intent_id: str, force: bool, config_path: str | None) -> None:
    """Cancel an intent."""
    from uuid import UUID

    db = get_db(config_path)
    try:
        intent = db.get_intent(UUID(intent_id))
        if not intent:
            click.echo(f"Intent '{intent_id}' not found.", err=True)
            sys.exit(1)

        if intent.status.value == "terminal":
            terminal = intent.terminal_reason or "halted"
            click.echo(f"Intent is already terminal ({terminal}).", err=True)
            sys.exit(1)

        if intent.status.value in ("broadcasted",) and not force:
            click.echo(
                f"Intent is {intent.status.value}. Use --force to cancel in-flight intents.",
                err=True,
            )
            sys.exit(1)

        if db.abandon_intent(UUID(intent_id)):
            click.echo(f"Intent '{intent_id}' cancelled.")
        else:
            click.echo("Failed to cancel intent.", err=True)
            sys.exit(1)
    finally:
        db.close()


def register(main) -> None:
    main.add_command(intents)
