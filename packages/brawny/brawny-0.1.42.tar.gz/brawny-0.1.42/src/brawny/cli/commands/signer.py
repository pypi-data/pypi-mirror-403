"""Signer management commands."""

from __future__ import annotations

import click

from brawny.cli.helpers import get_db


def resolve_signer_address(db, chain_id: int, address_or_alias: str) -> str:
    """Resolve address or alias to address.

    Args:
        db: Database connection
        chain_id: Chain ID for lookup
        address_or_alias: Either a 0x address or an alias string

    Returns:
        Lowercase address

    Raises:
        click.ClickException: If alias not found
    """
    # If it looks like an address, use directly
    if address_or_alias.startswith("0x") and len(address_or_alias) == 42:
        return address_or_alias.lower()

    # Otherwise, look up alias in signers table
    signer = db.get_signer_by_alias(chain_id, address_or_alias)
    if signer is None:
        raise click.ClickException(f"Unknown signer alias: {address_or_alias}")
    return signer.signer_address


@click.group()
def signer() -> None:
    """Signer management commands."""
    pass


@signer.command("force-reset")
@click.argument("address_or_alias")
@click.option("--target-nonce", "-n", type=int, default=None,
              help="Explicit target nonce to reset to")
@click.option("--use-rpc-pending", is_flag=True,
              help="Use RPC pending nonce as target (required if --target-nonce not set)")
@click.option("--reason", "-r", default=None,
              help="Reason for reset (required for audit trail)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def force_reset(
    address_or_alias: str,
    target_nonce: int | None,
    use_rpc_pending: bool,
    reason: str | None,
    yes: bool,
    config_path: str | None,
) -> None:
    """Force reset nonce state for a signer. USE WITH CAUTION.

    ADDRESS_OR_ALIAS can be:
      - Full address: 0x1234567890abcdef1234567890abcdef12345678
      - Signer alias: hot-wallet-1

    You must specify either --target-nonce or --use-rpc-pending:

    \b
      brawny signer force-reset 0x... --target-nonce 42 --reason "stuck tx"
      brawny signer force-reset 0x... --use-rpc-pending --reason "gap recovery"

    This will:
    - Reset local next_nonce to the specified target
    - Release all reservations with nonce >= target
    - Clear gap tracking
    - Log an audit trail with source and reason

    WARNING: If any prior transactions later mine, you may have duplicate
    transactions or nonce conflicts.
    """
    from web3 import Web3

    from brawny.config import Config, get_config
    from brawny.db import create_database
    from brawny._rpc.clients import ReadClient
    from brawny.tx.nonce import NonceManager
    from brawny.model.enums import NonceStatus

    # Validate: must specify either --target-nonce or --use-rpc-pending
    if target_nonce is None and not use_rpc_pending:
        click.echo(click.style(
            "Error: Must specify either --target-nonce or --use-rpc-pending",
            fg="red", bold=True
        ))
        click.echo("\nExamples:")
        click.echo("  brawny signer force-reset 0x... --target-nonce 42 --reason 'stuck tx'")
        click.echo("  brawny signer force-reset 0x... --use-rpc-pending --reason 'gap recovery'")
        raise SystemExit(1)

    if target_nonce is not None and use_rpc_pending:
        click.echo(click.style(
            "Error: Cannot specify both --target-nonce and --use-rpc-pending",
            fg="red", bold=True
        ))
        raise SystemExit(1)

    # Prompt for reason in interactive mode if not provided
    if reason is None and not yes:
        reason = click.prompt("Reason for reset (for audit trail)", default="")
        if not reason:
            click.echo(click.style(
                "Warning: No reason provided. Continuing without audit reason.",
                fg="yellow"
            ))

    # Load config
    if config_path:
        config = Config.from_yaml(config_path)
        config, _ = config.apply_env_overrides()
    else:
        config = get_config()

    # Connect to database
        db = create_database(
            config.database_url,
            circuit_breaker_failures=config.db_circuit_breaker_failures,
            circuit_breaker_seconds=config.db_circuit_breaker_seconds,
            production=config.production,
        )
    db.connect()

    try:
        # Resolve address or alias
        address = resolve_signer_address(db, config.chain_id, address_or_alias)

        # Setup RPC and nonce manager
        rpc = ReadClient.from_config(config)
        nonce_manager = NonceManager(db, rpc, config.chain_id)

        # Get current state
        chain_pending = rpc.get_transaction_count(
            Web3.to_checksum_address(address), block_identifier="pending"
        )
        signer_state = db.get_signer_state(config.chain_id, address)
        reservations = db.get_reservations_for_signer(config.chain_id, address)

        # Determine effective target nonce
        effective_target = target_nonce if target_nonce is not None else chain_pending

        # Calculate affected reservations
        affected = [
            r for r in reservations
            if r.nonce >= effective_target and r.status in (NonceStatus.RESERVED, NonceStatus.IN_FLIGHT)
        ]

        # Display current state
        click.echo(f"\nSigner: {address}")
        if address_or_alias.lower() != address:
            click.echo(f"Alias: {address_or_alias}")
        click.echo(f"Current chain pending nonce: {chain_pending}")
        click.echo(f"Current local next_nonce: {signer_state.next_nonce if signer_state else 'N/A'}")
        click.echo(f"Target nonce: {effective_target}" + (" (from RPC)" if use_rpc_pending else " (explicit)"))
        click.echo(f"Reservations to release: {len(affected)}")

        if affected:
            click.echo("\nReservations that will be released:")
            for r in affected:
                click.echo(f"  - nonce {r.nonce}: {r.status.value} (intent: {r.intent_id})")

        click.echo("\n" + click.style(
            "WARNING: This may cause duplicate transactions if prior txs later mine!",
            fg="yellow", bold=True
        ))

        # Confirm if not --yes
        if not yes:
            if not click.confirm("\nProceed with force reset?"):
                click.echo("Aborted.")
                return

        # Execute force reset
        new_nonce = nonce_manager.force_reset(
            address,
            source="cli",
            reason=reason or "no reason provided",
            target_nonce=effective_target,
        )
        click.echo(click.style(
            f"\n✓ Reset complete. next_nonce now {new_nonce}",
            fg="green", bold=True
        ))

    finally:
        db.close()


@signer.command("status")
@click.argument("address_or_alias")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def status(address_or_alias: str, config_path: str | None) -> None:
    """Show nonce status for a signer.

    ADDRESS_OR_ALIAS can be:
      - Full address: 0x1234567890abcdef1234567890abcdef12345678
      - Signer alias: hot-wallet-1
    """
    from web3 import Web3

    from brawny.config import Config, get_config
    from brawny.db import create_database
    from brawny._rpc.clients import ReadClient
    from brawny.model.enums import NonceStatus

    # Load config
    if config_path:
        config = Config.from_yaml(config_path)
        config, _ = config.apply_env_overrides()
    else:
        config = get_config()

    # Connect to database
        db = create_database(
            config.database_url,
            circuit_breaker_failures=config.db_circuit_breaker_failures,
            circuit_breaker_seconds=config.db_circuit_breaker_seconds,
            production=config.production,
        )
    db.connect()

    try:
        # Resolve address or alias
        address = resolve_signer_address(db, config.chain_id, address_or_alias)

        # Setup RPC
        rpc = ReadClient.from_config(config)

        # Get current state
        chain_pending = rpc.get_transaction_count(
            Web3.to_checksum_address(address), block_identifier="pending"
        )
        chain_confirmed = rpc.get_transaction_count(
            Web3.to_checksum_address(address), block_identifier="latest"
        )
        signer_state = db.get_signer_state(config.chain_id, address)
        reservations = db.get_reservations_for_signer(config.chain_id, address)

        # Display status
        click.echo(f"\nSigner: {address}")
        if address_or_alias.lower() != address:
            click.echo(f"Alias: {address_or_alias}")

        click.echo(f"\nChain State:")
        click.echo(f"  Confirmed nonce (latest): {chain_confirmed}")
        click.echo(f"  Pending nonce: {chain_pending}")

        if signer_state:
            click.echo(f"\nLocal State:")
            click.echo(f"  next_nonce: {signer_state.next_nonce}")
            click.echo(f"  last_synced_chain_nonce: {signer_state.last_synced_chain_nonce}")
            if signer_state.quarantined_at:
                click.echo(
                    click.style(
                        f"  quarantined_at: {signer_state.quarantined_at}",
                        fg="red",
                    )
                )
                if signer_state.quarantine_reason:
                    click.echo(
                        click.style(
                            f"  quarantine_reason: {signer_state.quarantine_reason}",
                            fg="red",
                        )
                    )
            if signer_state.replacements_paused:
                click.echo(click.style("  replacements_paused: true", fg="yellow"))
            if signer_state.gap_started_at:
                click.echo(click.style(
                    f"  gap_started_at: {signer_state.gap_started_at} (BLOCKED)",
                    fg="red"
                ))
        else:
            click.echo(f"\nLocal State: Not initialized")

        # Check for gap
        active = [r for r in reservations if r.status not in (NonceStatus.RELEASED,)]
        if active:
            expected_next = min(r.nonce for r in active)
            if chain_pending < expected_next:
                gap = expected_next - chain_pending
                click.echo(click.style(
                    f"\n⚠️  NONCE GAP DETECTED: chain_pending ({chain_pending}) < expected ({expected_next}), gap={gap}",
                    fg="yellow", bold=True
                ))

        # Show reservations
        if reservations:
            click.echo(f"\nReservations ({len(reservations)} total):")
            for r in sorted(reservations, key=lambda x: x.nonce):
                status_color = {
                    NonceStatus.RESERVED: "yellow",
                    NonceStatus.IN_FLIGHT: "cyan",
                    NonceStatus.RELEASED: "green",
                    NonceStatus.ORPHANED: "red",
                }.get(r.status, "white")
                click.echo(f"  nonce {r.nonce}: " + click.style(r.status.value, fg=status_color) +
                          f" (intent: {str(r.intent_id)[:8] if r.intent_id else 'none'})")
        else:
            click.echo(f"\nNo reservations")

    finally:
        db.close()


@signer.command("quarantine")
@click.argument("address_or_alias")
@click.option("--reason", "-r", default=None, help="Reason for quarantine")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def quarantine(address_or_alias: str, reason: str | None, config_path: str | None) -> None:
    """Quarantine a signer (blocks nonce reservations and broadcasts)."""
    from brawny.cli.helpers import get_config, get_db

    config = get_config(config_path)
    db = get_db(config_path)
    try:
        address = resolve_signer_address(db, config.chain_id, address_or_alias)
        updated = db.set_signer_quarantined(
            config.chain_id,
            address,
            reason=reason,
            actor="cli",
            source="cli",
        )
        if updated:
            click.echo(f"Signer '{address}' quarantined.")
        else:
            click.echo(f"Signer '{address}' not found.", err=True)
    finally:
        db.close()


@signer.command("unquarantine")
@click.argument("address_or_alias")
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
def unquarantine(address_or_alias: str, config_path: str | None) -> None:
    """Clear signer quarantine."""
    from brawny.cli.helpers import get_config, get_db

    config = get_config(config_path)
    db = get_db(config_path)
    try:
        address = resolve_signer_address(db, config.chain_id, address_or_alias)
        updated = db.clear_signer_quarantined(
            config.chain_id,
            address,
            actor="cli",
            source="cli",
        )
        if updated:
            click.echo(f"Signer '{address}' unquarantined.")
        else:
            click.echo(f"Signer '{address}' not found.", err=True)
    finally:
        db.close()


def register(main) -> None:
    """Register signer commands with the main CLI."""
    main.add_command(signer)
