"""Accounts management commands (brownie-compatible)."""

from __future__ import annotations

import json
import os
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path

import click

# Default paths
DEFAULT_BRAWNY_ACCOUNTS_PATH = "~/.brawny/accounts"
DEFAULT_BROWNIE_ACCOUNTS_PATH = "~/.brownie/accounts"


def get_accounts_path() -> Path:
    """Get the brawny accounts path from env or default."""
    path_str = os.environ.get("BRAWNY_ACCOUNTS_PATH", DEFAULT_BRAWNY_ACCOUNTS_PATH)
    return Path(path_str).expanduser()


def get_brownie_accounts_path() -> Path:
    """Get the brownie accounts path."""
    return Path(DEFAULT_BROWNIE_ACCOUNTS_PATH).expanduser()


def check_dir_permissions(path: Path) -> tuple[bool, str | None]:
    """Check if directory has secure permissions.

    Returns:
        (is_secure, error_message)
    """
    if os.name != "posix":
        return True, None

    if not path.exists():
        return True, None

    try:
        mode = path.stat().st_mode
    except OSError:
        return True, None

    # Check if group or world readable/writable
    insecure = mode & (stat.S_IRWXG | stat.S_IRWXO)
    if insecure:
        return False, f"Directory {path} has insecure permissions ({oct(mode & 0o777)}). Use --fix-perms to fix."

    return True, None


def fix_permissions(path: Path) -> None:
    """Fix directory and file permissions to be secure."""
    if os.name != "posix":
        return

    if path.is_dir():
        os.chmod(path, 0o700)
        for child in path.iterdir():
            fix_permissions(child)
    elif path.is_file():
        os.chmod(path, 0o600)


def get_address_from_keystore(file_path: Path) -> str | None:
    """Extract address from a keystore file."""
    try:
        with open(file_path) as f:
            data = json.load(f)
        addr = data.get("address", "")
        if addr and not addr.startswith("0x"):
            addr = f"0x{addr}"
        return addr.lower() if addr else None
    except (json.JSONDecodeError, OSError):
        return None


def list_keystore_files(path: Path) -> list[tuple[str, Path, str | None]]:
    """List keystore files in a directory.

    Returns:
        List of (name, path, address) tuples
    """
    if not path.exists():
        return []

    results = []
    for file_path in sorted(path.glob("*.json")):
        name = file_path.stem
        address = get_address_from_keystore(file_path)
        results.append((name, file_path, address))

    return results


@click.group()
def accounts() -> None:
    """Manage accounts (brownie-compatible keystore)."""
    pass


@accounts.command("list")
@click.option(
    "--include-brownie",
    is_flag=True,
    help="Also show accounts from ~/.brownie/accounts (read-only)",
)
@click.option(
    "--path",
    "accounts_path",
    default=None,
    help=f"Path to accounts directory (default: $BRAWNY_ACCOUNTS_PATH or {DEFAULT_BRAWNY_ACCOUNTS_PATH})",
)
def accounts_list(include_brownie: bool, accounts_path: str | None) -> None:
    """List available accounts."""
    brawny_path = Path(accounts_path).expanduser() if accounts_path else get_accounts_path()
    brownie_path = get_brownie_accounts_path()

    brawny_accounts = list_keystore_files(brawny_path)
    brownie_accounts = list_keystore_files(brownie_path) if include_brownie else []

    # First-run prompt: if brawny is empty but brownie has accounts
    if not brawny_accounts and not include_brownie and brownie_path.exists():
        brownie_count = len(list_keystore_files(brownie_path))
        if brownie_count > 0:
            click.echo()
            click.echo(click.style(f"Found {brownie_count} Brownie account(s) in {brownie_path}", dim=True))
            if click.confirm("Import Brownie accounts into Brawny?", default=False):
                # Re-invoke with import
                ctx = click.get_current_context()
                ctx.invoke(accounts_import, from_source="brownie", all_accounts=True)
                # Refresh list
                brawny_accounts = list_keystore_files(brawny_path)
            else:
                click.echo(click.style("Tip: Use --include-brownie to view without importing", dim=True))
                click.echo()

    has_any = False

    # Show brawny accounts
    if brawny_accounts:
        has_any = True
        click.echo()
        click.echo(click.style(str(brawny_path), dim=True))
        for name, _, address in brawny_accounts:
            addr_display = address or "unknown"
            click.echo(f"  {click.style(name, fg='cyan')}  {click.style(addr_display, dim=True)}")

    # Show brownie accounts (read-only)
    if brownie_accounts:
        has_any = True
        # Collect brawny addresses for duplicate detection
        brawny_addresses = {addr for _, _, addr in brawny_accounts if addr}

        click.echo()
        click.echo(click.style(f"{brownie_path} (read-only)", dim=True))
        for name, _, address in brownie_accounts:
            addr_display = address or "unknown"
            # Mark if already in brawny
            suffix = ""
            if address and address in brawny_addresses:
                suffix = click.style(" (also in brawny)", dim=True)
            click.echo(f"  {click.style(name, fg='yellow')}  {click.style(addr_display, dim=True)}{suffix}")

    if has_any:
        click.echo()
    else:
        click.echo()
        click.echo(click.style("No accounts found.", dim=True))
        click.echo(f"  Import a key: brawny accounts import --private-key 0x...")
        if brownie_path.exists():
            click.echo(f"  From Brownie: brawny accounts import --from brownie --all")
        click.echo()


@accounts.command("import")
@click.option(
    "--from",
    "from_source",
    type=click.Choice(["brownie"]),
    default=None,
    help="Import from external source (brownie)",
)
@click.option(
    "--all",
    "all_accounts",
    is_flag=True,
    help="Import all accounts from source",
)
@click.option(
    "--link",
    "link_mode",
    is_flag=True,
    help="Create symlinks instead of copies (unix only)",
)
@click.option(
    "--copy",
    "copy_mode",
    is_flag=True,
    help="Create physical copies (default on Windows)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing files",
)
@click.option(
    "--rename",
    "auto_rename",
    is_flag=True,
    help="Auto-rename on conflict (e.g., name_1.json)",
)
@click.option(
    "--fix-perms",
    "fix_perms",
    is_flag=True,
    help="Fix directory permissions if insecure",
)
@click.option(
    "--name",
    "wallet_name",
    default=None,
    help="Wallet name (for --private-key import)",
)
@click.option(
    "--private-key",
    "private_key",
    default=None,
    help="Private key to import (hex)",
)
@click.option(
    "--password",
    "password_value",
    default=None,
    help="Keystore password (avoid in shell history)",
)
@click.option(
    "--password-env",
    "password_env",
    default="BRAWNY_KEYSTORE_PASSWORD",
    help="Environment variable for password",
)
@click.option(
    "--path",
    "out_path",
    default=None,
    help=f"Output directory (default: $BRAWNY_ACCOUNTS_PATH or {DEFAULT_BRAWNY_ACCOUNTS_PATH})",
)
@click.argument("names", nargs=-1)
def accounts_import(
    from_source: str | None,
    all_accounts: bool,
    link_mode: bool,
    copy_mode: bool,
    overwrite: bool,
    auto_rename: bool,
    fix_perms: bool,
    wallet_name: str | None,
    private_key: str | None,
    password_value: str | None,
    password_env: str,
    out_path: str | None,
    names: tuple[str, ...],
) -> None:
    """Import accounts from various sources.

    Examples:

      # Import a private key
      brawny accounts import --private-key 0x... --name worker

      # Import all Brownie accounts (symlinks)
      brawny accounts import --from brownie --all --link

      # Import specific Brownie accounts (copies)
      brawny accounts import --from brownie hot_wallet personal_bot

      # List available Brownie accounts
      brawny accounts import --from brownie
    """
    dest_path = Path(out_path).expanduser() if out_path else get_accounts_path()

    # Check destination permissions
    is_secure, perm_error = check_dir_permissions(dest_path)
    if not is_secure:
        if fix_perms:
            click.echo(f"Fixing permissions on {dest_path}...")
            fix_permissions(dest_path)
        else:
            raise click.ClickException(perm_error or "Insecure permissions")

    # Branch: import from brownie
    if from_source == "brownie":
        _import_from_brownie(
            dest_path=dest_path,
            names=names,
            all_accounts=all_accounts,
            link_mode=link_mode,
            copy_mode=copy_mode,
            overwrite=overwrite,
            auto_rename=auto_rename,
            fix_perms=fix_perms,
        )
        return

    # Branch: import private key
    if private_key:
        _import_private_key(
            dest_path=dest_path,
            private_key=private_key,
            wallet_name=wallet_name,
            password_value=password_value,
            password_env=password_env,
            overwrite=overwrite,
        )
        return

    # No valid import source
    raise click.ClickException(
        "Specify --private-key or --from brownie. "
        "Use 'brawny accounts import --help' for usage."
    )


def _import_from_brownie(
    dest_path: Path,
    names: tuple[str, ...],
    all_accounts: bool,
    link_mode: bool,
    copy_mode: bool,
    overwrite: bool,
    auto_rename: bool,
    fix_perms: bool,
) -> None:
    """Import accounts from Brownie."""
    brownie_path = get_brownie_accounts_path()

    if not brownie_path.exists():
        raise click.ClickException(f"Brownie accounts directory not found: {brownie_path}")

    available = list_keystore_files(brownie_path)
    if not available:
        raise click.ClickException(f"No accounts found in {brownie_path}")

    # If no names and not --all, list available
    if not names and not all_accounts:
        click.echo()
        click.echo(f"Available Brownie accounts ({brownie_path}):")
        click.echo()
        for name, _, address in available:
            addr_display = address or "unknown"
            click.echo(f"  {click.style(name, fg='yellow')}  {click.style(addr_display, dim=True)}")
        click.echo()
        click.echo("Import with:")
        click.echo(f"  brawny accounts import --from brownie --all        # all accounts")
        click.echo(f"  brawny accounts import --from brownie NAME [NAME]  # specific accounts")
        click.echo()
        return

    # Determine which accounts to import
    if all_accounts:
        to_import = available
    else:
        name_set = set(names)
        to_import = [(n, p, a) for n, p, a in available if n in name_set]
        missing = name_set - {n for n, _, _ in to_import}
        if missing:
            raise click.ClickException(f"Accounts not found in Brownie: {', '.join(sorted(missing))}")

    # Determine mode: link vs copy
    use_symlinks = link_mode
    if copy_mode:
        use_symlinks = False
    elif not link_mode and not copy_mode:
        # Default: symlinks on unix, copy on windows
        use_symlinks = os.name == "posix"

    # Ensure destination exists with secure permissions
    dest_path.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(dest_path, 0o700)

    # Check for existing accounts (by name and address)
    existing = list_keystore_files(dest_path)
    existing_names = {n for n, _, _ in existing}
    existing_addresses = {a for _, _, a in existing if a}

    imported = 0
    skipped = 0

    for name, src_path, address in to_import:
        dest_file = dest_path / f"{name}.json"

        # Check for collision by address
        if address and address in existing_addresses and not overwrite:
            existing_name = next((n for n, _, a in existing if a == address), None)
            click.echo(click.style(f"  skip: {name} (address already exists as '{existing_name}')", fg="yellow"))
            skipped += 1
            continue

        # Check for collision by name
        if name in existing_names and not overwrite:
            if auto_rename:
                # Find unique name
                counter = 1
                while f"{name}_{counter}" in existing_names:
                    counter += 1
                new_name = f"{name}_{counter}"
                dest_file = dest_path / f"{new_name}.json"
                existing_names.add(new_name)
                click.echo(click.style(f"  rename: {name} -> {new_name}", dim=True))
            else:
                click.echo(click.style(f"  skip: {name} (already exists, use --overwrite or --rename)", fg="yellow"))
                skipped += 1
                continue

        # Remove existing if overwriting
        if dest_file.exists() or dest_file.is_symlink():
            dest_file.unlink()

        # Create link or copy
        if use_symlinks:
            dest_file.symlink_to(src_path.resolve())
            click.echo(click.style(f"  link: {name}", fg="green"))
        else:
            shutil.copy2(src_path, dest_file)
            # Secure the copy
            if os.name == "posix":
                os.chmod(dest_file, 0o600)
            click.echo(click.style(f"  copy: {name}", fg="green"))

        existing_names.add(name)
        if address:
            existing_addresses.add(address)
        imported += 1

    click.echo()
    if imported > 0:
        mode_str = "linked" if use_symlinks else "copied"
        click.echo(f"Imported {imported} account(s) ({mode_str}) to {dest_path}")
    if skipped > 0:
        click.echo(click.style(f"Skipped {skipped} account(s)", dim=True))


def _import_private_key(
    dest_path: Path,
    private_key: str,
    wallet_name: str | None,
    password_value: str | None,
    password_env: str,
    overwrite: bool,
) -> None:
    """Import a private key into an encrypted keystore file."""
    from eth_account import Account
    from web3 import Web3

    # Get password
    password = password_value or os.environ.get(password_env)
    if password is None:
        password = click.prompt(
            "Keystore password",
            hide_input=True,
            confirmation_prompt=True,
        )

    # Parse private key
    if not private_key.startswith("0x"):
        private_key = f"0x{private_key}"

    try:
        account = Account.from_key(private_key)
    except ValueError as e:
        raise click.ClickException(f"Invalid private key: {e}")

    address = Web3.to_checksum_address(account.address)

    # Check for duplicate address
    existing = list_keystore_files(dest_path)
    for name, _, addr in existing:
        if addr and addr.lower() == address.lower():
            if not overwrite:
                raise click.ClickException(
                    f"Address {address} already exists as '{name}'. Use --overwrite to replace."
                )
            # Remove existing
            (dest_path / f"{name}.json").unlink()
            break

    # Encrypt
    keystore_data = Account.encrypt(account.key, password)

    # Ensure destination exists
    dest_path.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(dest_path, 0o700)

    # Determine filename
    if wallet_name:
        filename = f"{wallet_name}.json"
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S.%fZ")
        filename = f"UTC--{timestamp}--{address[2:].lower()}.json"

    file_path = dest_path / filename
    if file_path.exists() and not overwrite:
        raise click.ClickException(f"File already exists: {file_path}. Use --overwrite to replace.")

    # Write with secure permissions
    file_path.write_text(json.dumps(keystore_data, indent=2))
    if os.name == "posix":
        os.chmod(file_path, 0o600)

    click.echo(f"Keystore created: {file_path}")
    click.echo(f"Address: {address}")


@accounts.command("new")
@click.option(
    "--name",
    "wallet_name",
    required=True,
    help="Wallet name",
)
@click.option(
    "--password",
    "password_value",
    default=None,
    help="Keystore password (avoid in shell history)",
)
@click.option(
    "--password-env",
    "password_env",
    default="BRAWNY_KEYSTORE_PASSWORD",
    help="Environment variable for password",
)
@click.option(
    "--path",
    "out_path",
    default=None,
    help=f"Output directory (default: $BRAWNY_ACCOUNTS_PATH or {DEFAULT_BRAWNY_ACCOUNTS_PATH})",
)
def accounts_new(
    wallet_name: str,
    password_value: str | None,
    password_env: str,
    out_path: str | None,
) -> None:
    """Generate a new account."""
    from eth_account import Account
    from web3 import Web3

    dest_path = Path(out_path).expanduser() if out_path else get_accounts_path()

    # Get password
    password = password_value or os.environ.get(password_env)
    if password is None:
        password = click.prompt(
            "Keystore password",
            hide_input=True,
            confirmation_prompt=True,
        )

    # Generate new account
    account = Account.create()
    address = Web3.to_checksum_address(account.address)

    # Encrypt
    keystore_data = Account.encrypt(account.key, password)

    # Ensure destination exists
    dest_path.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(dest_path, 0o700)

    file_path = dest_path / f"{wallet_name}.json"
    if file_path.exists():
        raise click.ClickException(f"File already exists: {file_path}")

    # Write with secure permissions
    file_path.write_text(json.dumps(keystore_data, indent=2))
    if os.name == "posix":
        os.chmod(file_path, 0o600)

    click.echo(f"New account created: {file_path}")
    click.echo(f"Address: {address}")
    click.echo()
    click.echo(click.style("IMPORTANT: Back up your keystore file and remember your password!", fg="yellow"))


@accounts.command("delete")
@click.argument("name")
@click.option(
    "--path",
    "accounts_path",
    default=None,
    help=f"Accounts directory (default: $BRAWNY_ACCOUNTS_PATH or {DEFAULT_BRAWNY_ACCOUNTS_PATH})",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def accounts_delete(name: str, accounts_path: str | None, force: bool) -> None:
    """Delete an account."""
    path = Path(accounts_path).expanduser() if accounts_path else get_accounts_path()
    file_path = path / f"{name}.json"

    if not file_path.exists() and not file_path.is_symlink():
        raise click.ClickException(f"Account not found: {name}")

    # Get address for confirmation
    address = get_address_from_keystore(file_path) if file_path.exists() else None

    if not force:
        msg = f"Delete account '{name}'"
        if address:
            msg += f" ({address})"
        msg += "?"
        if not click.confirm(msg, default=False):
            click.echo("Cancelled.")
            return

    file_path.unlink()
    click.echo(f"Deleted: {name}")


def register(main) -> None:
    """Register accounts command with main CLI."""
    main.add_command(accounts)
