"""Keystore implementations for transaction signing.

Provides secure key management with multiple backends:
- EnvKeystore: Load private keys from environment variables
- FileKeystore: Load from encrypted JSON keystore files

SECURITY: Private keys are NEVER logged, even at DEBUG level.
"""

from __future__ import annotations

import json
import os
import stat
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv
from web3 import Web3
from web3.types import TxParams

from brawny.logging import get_logger
from brawny.model.errors import KeystoreError
from brawny.model.startup import StartupMessage

# Load .env so keystore passwords are available in environment.
load_dotenv()

logger = get_logger(__name__)


def _normalize_addr(addr: str) -> str:
    """Normalize address to checksummed format.

    Handles addresses with or without 0x prefix.
    """
    if not addr.startswith("0x"):
        addr = "0x" + addr
    return Web3.to_checksum_address(addr)

if TYPE_CHECKING:
    from eth_account.datastructures import SignedTransaction


class Keystore(ABC):
    """Abstract keystore interface for signing transactions.

    Implementations must:
    - Never log or expose private key material
    - Be synchronous (no network calls during signing)
    - Return consistent addresses for the same key_id
    """

    @abstractmethod
    def get_address(self, key_id: str) -> str:
        """Return the checksum address for a key identifier.

        Args:
            key_id: Key identifier (address or alias)

        Returns:
            Checksum address

        Raises:
            KeystoreError: If key not found
        """
        ...

    @abstractmethod
    def sign_transaction(self, tx_dict: TxParams, key_id: str) -> SignedTransaction:
        """Sign a transaction.

        Must be synchronous and not make network calls.
        Must never log private key material.

        Args:
            tx_dict: Transaction parameters
            key_id: Key identifier (address or alias)

        Returns:
            Signed transaction

        Raises:
            KeystoreError: If signing fails
        """
        ...

    @abstractmethod
    def list_keys(self) -> list[str]:
        """Return list of signer addresses (checksummed, sorted, de-duplicated).

        Returns:
            Sorted list of unique checksummed Ethereum addresses.
        """
        ...

    def list_aliases(self) -> list[str]:
        """Return list of signer aliases/names (sorted).

        Default implementation returns empty list.
        Override in subclasses that support aliases.

        Returns:
            Sorted list of human-readable aliases, or empty if no aliases configured.
        """
        return []

    def list_keys_with_aliases(self) -> list[tuple[str, str | None]]:
        """Return list of (address, alias) tuples, sorted by address.

        Default implementation returns addresses with None alias.
        Override in subclasses that support aliases.

        Returns:
            List of tuples where each tuple is (checksummed_address, alias_or_none).
        """
        return [(addr, None) for addr in self.list_keys()]

    def has_key(self, key_id: str) -> bool:
        """Check if a key exists.

        Args:
            key_id: Key identifier to check

        Returns:
            True if key exists
        """
        try:
            self.get_address(key_id)
            return True
        except KeystoreError:
            return False

    def get_warnings(self) -> list[StartupMessage]:
        """Get startup warnings collected during initialization.

        Returns:
            List of startup warning messages
        """
        return []


class EnvKeystore(Keystore):
    """Load private keys from environment variables.

    Supports two formats:
    - BRAWNY_SIGNER_PRIVATE_KEY: Single signer
    - BRAWNY_SIGNER_{ADDRESS}_PRIVATE_KEY: Multiple signers by address

    Example:
        BRAWNY_SIGNER_PRIVATE_KEY=0x...
        BRAWNY_SIGNER_0x1234567890ABCDEF_PRIVATE_KEY=0x...
    """

    def __init__(self, allowed_signers: list[str] | None = None) -> None:
        """Initialize the keystore.

        Args:
            allowed_signers: Optional list of allowed signer addresses.
                            If None, all found signers are allowed.
        """
        self._accounts: dict[str, LocalAccount] = {}
        self._allowed_signers = (
            {Web3.to_checksum_address(s) for s in allowed_signers}
            if allowed_signers
            else None
        )
        self._load_keys()

    def _load_keys(self) -> None:
        """Load keys from environment variables."""
        # Check for single signer key
        single_key = os.environ.get("BRAWNY_SIGNER_PRIVATE_KEY")
        if single_key:
            self._add_key(single_key)

        # Check for address-specific keys
        for key, value in os.environ.items():
            if key.startswith("BRAWNY_SIGNER_") and key.endswith("_PRIVATE_KEY"):
                # Skip the generic key
                if key == "BRAWNY_SIGNER_PRIVATE_KEY":
                    continue
                self._add_key(value)

    def _add_key(self, private_key: str) -> None:
        """Add a key to the keystore."""
        try:
            # Normalize private key format
            if not private_key.startswith("0x"):
                private_key = f"0x{private_key}"

            account = Account.from_key(private_key)
            address = Web3.to_checksum_address(account.address)

            # Check against allowed signers
            if self._allowed_signers and address not in self._allowed_signers:
                return

            self._accounts[address] = account
        except (ValueError, TypeError) as e:
            # Don't expose the key in error messages
            raise KeystoreError(f"Failed to load private key: {type(e).__name__}")

    def get_address(self, key_id: str) -> str:
        """Get the checksum address for a key."""
        try:
            address = Web3.to_checksum_address(key_id)
        except ValueError:
            raise KeystoreError(f"Invalid key identifier: {key_id}")

        if address not in self._accounts:
            raise KeystoreError(f"Key not found: {address}")

        return address

    def sign_transaction(self, tx_dict: TxParams, key_id: str) -> SignedTransaction:
        """Sign a transaction with the specified key."""
        address = self.get_address(key_id)
        account = self._accounts[address]

        try:
            return account.sign_transaction(tx_dict)
        except (ValueError, TypeError) as e:
            # Don't expose key material in error
            raise KeystoreError(f"Signing failed: {type(e).__name__}: {e}")

    def list_keys(self) -> list[str]:
        """Return list of signer addresses (checksummed, sorted)."""
        return sorted(self._accounts.keys())


class FileKeystore(Keystore):
    """Load keys from encrypted JSON keystore files.

    Expects keystore files in the format produced by geth/web3:
    {
        "address": "...",
        "crypto": {...},
        "id": "...",
        "version": 3
    }

    Password resolution order:
    1. BRAWNY_KEYSTORE_PASSWORD_{NAME} (per-wallet)
    2. {name}.password file next to keystore
    3. BRAWNY_KEYSTORE_PASSWORD (global)
    4. BROWNIE_PASSWORD (only if brownie_password_fallback=True)
    """

    def __init__(
        self,
        keystore_path: str | Path,
        allowed_signers: list[str] | None = None,
        include_brownie: bool = False,
        brownie_password_fallback: bool = False,
    ) -> None:
        """Initialize the keystore.

        Args:
            keystore_path: Path to keystore directory or single file
            allowed_signers: Optional list of allowed signer addresses
            include_brownie: Also load accounts from ~/.brownie/accounts (read-only)
            brownie_password_fallback: Use BROWNIE_PASSWORD as password fallback
        """
        self._accounts: dict[str, LocalAccount] = {}
        self._name_to_address: dict[str, str] = {}
        self._warnings: list[StartupMessage] = []
        self._allowed_signers = (
            {Web3.to_checksum_address(s) for s in allowed_signers}
            if allowed_signers
            else None
        )
        self._keystore_path = Path(keystore_path).expanduser()
        self._include_brownie = include_brownie
        self._brownie_password_fallback = brownie_password_fallback
        self._brownie_path = Path("~/.brownie/accounts").expanduser()
        self._load_keys()

    def _load_keys(self) -> None:
        """Load keys from keystore files."""
        if not self._keystore_path.exists():
            # Create the directory if it doesn't exist (graceful handling)
            if self._keystore_path.suffix == "":  # It's a directory path
                self._keystore_path.mkdir(parents=True, exist_ok=True)
                if os.name == "posix":
                    os.chmod(self._keystore_path, 0o700)
            # If it's a file path that doesn't exist, that's an error
            elif not self._include_brownie:
                raise KeystoreError(f"Keystore path does not exist: {self._keystore_path}")

        if self._keystore_path.exists():
            self._load_from_path(self._keystore_path)

        # Also load from brownie if requested
        if self._include_brownie and self._brownie_path.exists():
            self._load_from_path(self._brownie_path, is_brownie=True)

        # Warn if no accounts loaded
        if not self._accounts:
            logger.warning(
                "keystore.empty",
                path=str(self._keystore_path),
            )

    def _load_from_path(self, path: Path, is_brownie: bool = False) -> None:
        """Load keys from a path (file or directory)."""
        if path.is_file():
            self._warn_insecure_path(path)
            name = path.stem
            self._load_keystore_file(path, wallet_name=name, is_brownie=is_brownie)
        else:
            self._warn_insecure_path(path)
            # Load all .json files in directory
            for file_path in path.glob("*.json"):
                try:
                    self._warn_insecure_path(file_path)
                    wallet_name = file_path.stem
                    self._load_keystore_file(file_path, wallet_name=wallet_name, is_brownie=is_brownie)
                except KeystoreError as e:
                    # Log the failure so users know WHY a keystore wasn't loaded
                    logger.warning(
                        "keystore.load_failed",
                        file=str(file_path),
                        wallet_name=wallet_name,
                        error=str(e),
                    )

    def _warn_insecure_path(self, path: Path) -> None:
        """Collect warning if keystore path permissions are too open."""
        if os.name != "posix":
            return
        try:
            mode = path.stat().st_mode
        except OSError:
            return

        insecure = mode & (stat.S_IRWXG | stat.S_IRWXO)
        if insecure:
            mode_str = oct(mode & 0o777)
            self._warnings.append(
                StartupMessage(
                    level="warning",
                    code="keystore.insecure_permissions",
                    message=f"Insecure permissions: {path.name} ({mode_str})",
                    fix=f"chmod 600 {path}",
                )
            )

    def _load_keystore_file(
        self, file_path: Path, wallet_name: str | None, is_brownie: bool = False
    ) -> None:
        """Load a single keystore file."""
        try:
            with open(file_path) as f:
                keystore_json = json.load(f)

            # Get password (brownie fallback only allowed for brownie sources or if explicitly enabled)
            use_brownie_fallback = is_brownie or self._brownie_password_fallback
            password = self._get_password(file_path, wallet_name, use_brownie_fallback)

            # Decrypt and load account
            private_key = Account.decrypt(keystore_json, password)
            account = Account.from_key(private_key)
            address = Web3.to_checksum_address(account.address)

            # Check against allowed signers
            if self._allowed_signers and address not in self._allowed_signers:
                return

            self._accounts[address] = account
            if wallet_name:
                if wallet_name in self._name_to_address:
                    existing = self._name_to_address[wallet_name]
                    if existing != address:
                        raise KeystoreError(
                            f"Duplicate wallet name '{wallet_name}' for different address"
                        )
                self._name_to_address[wallet_name] = address
        except KeystoreError:
            raise  # Re-raise with original message (e.g., "No password found...")
        except json.JSONDecodeError:
            raise KeystoreError(f"Invalid JSON in keystore file: {file_path}")
        except (ValueError, TypeError) as e:
            raise KeystoreError(f"Failed to load keystore: {type(e).__name__}")

    def _get_password(
        self,
        keystore_path: Path,
        wallet_name: str | None,
        use_brownie_fallback: bool = False,
    ) -> str:
        """Get password for a keystore file.

        Resolution order:
        1. BRAWNY_KEYSTORE_PASSWORD_{NAME} (per-wallet)
        2. {name}.password file next to keystore
        3. BRAWNY_KEYSTORE_PASSWORD (global)
        4. BROWNIE_PASSWORD (only if use_brownie_fallback=True)
        """
        if wallet_name:
            env_name = f"BRAWNY_KEYSTORE_PASSWORD_{wallet_name.upper()}"
            password = os.environ.get(env_name)
            if password:
                return password

            name_password_file = keystore_path.parent / f"{wallet_name}.password"
            if name_password_file.exists():
                return name_password_file.read_text().strip()

        # Check environment variable first
        password = os.environ.get("BRAWNY_KEYSTORE_PASSWORD")
        if password:
            return password

        # Check for .password file next to keystore
        password_file = keystore_path.with_suffix(".password")
        if password_file.exists():
            return password_file.read_text().strip()

        # Check for password file with same name
        password_file = keystore_path.parent / f"{keystore_path.stem}.password"
        if password_file.exists():
            return password_file.read_text().strip()

        # Brownie password fallback (only when explicitly allowed)
        if use_brownie_fallback:
            password = os.environ.get("BROWNIE_PASSWORD")
            if password:
                return password

        raise KeystoreError(
            f"No password found for {keystore_path}. "
            "Set BRAWNY_KEYSTORE_PASSWORD or create a .password file."
        )

    def get_address(self, key_id: str) -> str:
        """Get the checksum address for a key."""
        if key_id in self._name_to_address:
            return self._name_to_address[key_id]

        try:
            address = Web3.to_checksum_address(key_id)
        except ValueError:
            raise KeystoreError(f"Invalid key identifier: {key_id}")

        if address not in self._accounts:
            raise KeystoreError(f"Key not found: {address}")

        return address

    def sign_transaction(self, tx_dict: TxParams, key_id: str) -> SignedTransaction:
        """Sign a transaction with the specified key."""
        address = self.get_address(key_id)
        account = self._accounts[address]

        try:
            return account.sign_transaction(tx_dict)
        except (ValueError, TypeError) as e:
            raise KeystoreError(f"Signing failed: {type(e).__name__}: {e}")

    def list_keys(self) -> list[str]:
        """Return list of signer addresses (checksummed, sorted, de-duplicated).

        **Source of truth behavior:**
        - When _name_to_address mapping exists, it is the SOLE source of truth.
          The keystore directory is NOT scanned. This means addresses only in
          keystore files (without aliases) will NOT appear.
        - When _name_to_address is empty/None, addresses are extracted from
          the loaded accounts.

        Returns:
            Sorted list of unique checksummed Ethereum addresses.
        """
        if self._name_to_address:
            # Mapping is source of truth - normalize, de-dupe, and sort
            # (multiple aliases may map to same address)
            return sorted({_normalize_addr(a) for a in self._name_to_address.values()})

        # Return addresses from loaded accounts
        return sorted(self._accounts.keys())

    def list_aliases(self) -> list[str]:
        """Return list of signer aliases/names (sorted).

        Returns:
            Sorted list of human-readable aliases, or empty if no aliases configured.
        """
        if self._name_to_address:
            return sorted(self._name_to_address.keys())
        return []

    def list_keys_with_aliases(self) -> list[tuple[str, str | None]]:
        """Return list of (address, alias) tuples, sorted by address.

        Returns:
            List of tuples where each tuple is (checksummed_address, alias_or_none).
        """
        if self._name_to_address:
            pairs = [
                (_normalize_addr(addr), name)
                for name, addr in self._name_to_address.items()
            ]
            return sorted(pairs, key=lambda x: x[0])  # Sort by address

        # No aliases: return addresses with None alias
        return [(addr, None) for addr in self.list_keys()]

    def list_named_keys(self) -> dict[str, str]:
        """Return mapping of wallet name to address.

        DEPRECATED: Use list_aliases() or list_keys_with_aliases() instead.
        """
        return dict(self._name_to_address)

    def get_warnings(self) -> list[StartupMessage]:
        """Get startup warnings collected during initialization."""
        return self._warnings


def create_keystore(
    keystore_type: str,
    keystore_path: str | None = None,
    allowed_signers: list[str] | None = None,
    include_brownie: bool = False,
    brownie_password_fallback: bool = False,
) -> Keystore:
    """Factory function to create a keystore instance.

    Args:
        keystore_type: Type of keystore ('env', 'file')
        keystore_path: Path for file keystore
        allowed_signers: Optional list of allowed signer addresses
        include_brownie: Also load accounts from ~/.brownie/accounts (file keystore only)
        brownie_password_fallback: Use BROWNIE_PASSWORD as password fallback

    Returns:
        Keystore instance

    Raises:
        KeystoreError: If keystore creation fails
    """
    if keystore_type == "env":
        return EnvKeystore(allowed_signers=allowed_signers)
    elif keystore_type == "file":
        if not keystore_path:
            raise KeystoreError("keystore_path is required for file keystore")
        return FileKeystore(
            keystore_path,
            allowed_signers=allowed_signers,
            include_brownie=include_brownie,
            brownie_password_fallback=brownie_password_fallback,
        )
    else:
        raise KeystoreError(
            f"Unknown keystore type: {keystore_type}. "
            "Must be one of: env, file"
        )
