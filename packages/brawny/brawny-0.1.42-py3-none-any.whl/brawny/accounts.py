"""Brownie-compatible accounts management.

Storage: ~/.brownie/accounts/*.json (Brownie compatibility)
Format: Ethereum Keystore JSON v3 (Web3 Secret Storage)

Usage:
    from brawny import accounts

    # Load by name (prompts for password if needed)
    acct = accounts.load("my_wallet")

    # Add new account (returns GeneratedAccount, includes mnemonic if generated)
    gen = accounts.add()  # Generates new key
    acct = gen.account
    gen = accounts.add("0x...")  # From private key
    acct = gen.account

    # Save to keystore
    acct.save("my_wallet")

    # From mnemonic
    acct = accounts.from_mnemonic("word1 word2 ...")

    # Index access (loaded accounts)
    accounts[0]

    # List available (not yet loaded)
    accounts.list()  # Returns ["wallet1", "wallet2", ...]
"""

from __future__ import annotations

import getpass
import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterator

from eth_account import Account as EthAccount
from eth_account.hdaccount import generate_mnemonic

if TYPE_CHECKING:
    from brawny.jobs.base import TxReceipt

_accounts: "Accounts | None" = None
_hdwallet_enabled = False


def _ensure_hdwallet_enabled() -> None:
    global _hdwallet_enabled
    if _hdwallet_enabled:
        return
    EthAccount.enable_unaudited_hdwallet_features()
    _hdwallet_enabled = True


def _get_accounts_dir() -> Path:
    """Get accounts directory (Brownie-compatible default)."""
    # User override
    if env_dir := os.environ.get("ETHJ_ACCOUNTS_DIR"):
        return Path(env_dir).expanduser()

    # Default: Brownie location for compatibility
    brownie_dir = Path.home() / ".brownie" / "accounts"
    if brownie_dir.exists():
        return brownie_dir

    # Fallback: brawny location
    brawny_dir = Path.home() / ".brawny" / "accounts"
    brawny_dir.mkdir(parents=True, exist_ok=True)
    return brawny_dir


def _get_password(name: str, password: str | None = None) -> str:
    """Resolve password for account.

    Priority:
    1. Explicit password argument
    2. Environment variable ETHJ_PASSWORD_<NAME>
    3. Interactive prompt (if TTY)
    4. Error
    """
    if password is not None:
        return password

    # Environment variable
    env_key = f"ETHJ_PASSWORD_{name.upper()}"
    if env_pass := os.environ.get(env_key):
        return env_pass

    # Interactive prompt
    if sys.stdin.isatty():
        return getpass.getpass(f"Enter password for '{name}': ")

    raise ValueError(
        f"No password for '{name}'. Set {env_key} or provide password argument."
    )


class Account:
    """Represents a signing account.

    Brownie-compatible interface for transaction signing.
    """

    def __init__(
        self,
        address: str,
        private_key: bytes | None = None,
        alias: str | None = None,
    ) -> None:
        self._address = address
        self._private_key = private_key  # Only set after unlock/add
        self._alias = alias

    @property
    def address(self) -> str:
        """Checksummed address."""
        return self._address

    @property
    def alias(self) -> str | None:
        """Keystore alias (e.g., 'worker', 'deployer')."""
        return self._alias

    @property
    def private_key(self) -> str:
        """Private key as hex string."""
        if self._private_key is None:
            raise ValueError(f"Account {self._address} is locked")
        return "0x" + self._private_key.hex()

    def balance(self) -> int:
        """Get account balance in wei."""
        from brawny.api import rpc
        return rpc.get_balance(self._address)

    def save(
        self,
        filename: str,
        password: str | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Save account to keystore file.

        Args:
            filename: Name for keystore file (without .json extension)
            password: Encryption password (prompts if not provided)
            overwrite: Allow overwriting existing file

        Returns:
            Path to saved keystore file

        Raises:
            FileExistsError: If file exists and overwrite=False
        """
        if self._private_key is None:
            raise ValueError("Cannot save locked account")

        accounts_dir = _get_accounts_dir()
        filepath = accounts_dir / f"{filename}.json"

        if filepath.exists() and not overwrite:
            raise FileExistsError(f"Account '{filename}' already exists. Use overwrite=True.")

        # Get password
        if password is None:
            if sys.stdin.isatty():
                password = getpass.getpass(f"Enter password for '{filename}': ")
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    raise ValueError("Passwords do not match")
            else:
                raise ValueError("Password required for non-interactive save")

        # Encrypt with standard Ethereum keystore format
        keystore = EthAccount.encrypt(self._private_key, password)

        # Write file
        accounts_dir.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(keystore, f, indent=2)

        self._alias = filename
        return filepath

    def transfer(
        self,
        to: str,
        amount: int | str,
        gas_limit: int | None = None,
        gas_price: int | None = None,
        max_fee_per_gas: int | None = None,
        max_priority_fee_per_gas: int | None = None,
        data: str | None = None,
    ) -> "TxReceipt":
        """Send ETH to an address."""
        from brawny.api import Wei
        from brawny.script_tx import _get_broadcaster

        if isinstance(amount, str):
            amount = Wei(amount)

        return _get_broadcaster().transfer(
            sender=self._address,
            to=to,
            value=amount,
            gas_limit=gas_limit,
            gas_price=gas_price,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            data=data,
            private_key=self._private_key,
        )

    def sign_transaction(self, tx: dict) -> Any:
        """Sign a transaction dict."""
        if self._private_key is None:
            raise ValueError(f"Account {self._address} is locked")
        return EthAccount.sign_transaction(tx, self._private_key)

    def sign_message(self, message: str | bytes) -> Any:
        """Sign a message."""
        from eth_account.messages import encode_defunct

        if self._private_key is None:
            raise ValueError(f"Account {self._address} is locked")

        if isinstance(message, str):
            message = message.encode()

        signable = encode_defunct(primitive=message)
        return EthAccount.sign_message(signable, self._private_key)

    def __repr__(self) -> str:
        if self._alias:
            return f"<Account '{self._alias}' {self._address}>"
        return f"<Account {self._address}>"

    def __str__(self) -> str:
        return self._address

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Account):
            return self._address.lower() == other._address.lower()
        if isinstance(other, str):
            return self._address.lower() == other.lower()
        return False

    def __hash__(self) -> int:
        return hash(self._address.lower())


@dataclass(frozen=True)
class GeneratedAccount:
    account: Account
    mnemonic: str | None = None


class Accounts:
    """Container for available signing accounts.

    Brownie-compatible interface:
        accounts[0]                 # By index (loaded accounts)
        accounts.load("wallet")     # Load from keystore
        accounts.add("0x...")       # Add from private key
        accounts.add()              # Generate new account
        accounts.from_mnemonic(...) # From BIP39 mnemonic
        accounts.list()             # List available keystores
        for acc in accounts: ...    # Iteration (loaded only)
        len(accounts)               # Count (loaded only)
    """

    def __init__(self) -> None:
        self._loaded: list[Account] = []
        self._by_address: dict[str, Account] = {}
        self._by_alias: dict[str, Account] = {}
        self.default: Account | None = None

    def _register(self, account: Account) -> Account:
        """Register account in container."""
        self._loaded.append(account)
        self._by_address[account.address.lower()] = account
        if account.alias:
            self._by_alias[account.alias.lower()] = account
        return account

    def list(self) -> list[str]:
        """List available keystore names (not yet loaded).

        Returns:
            List of keystore names (without .json extension)
        """
        accounts_dir = _get_accounts_dir()
        if not accounts_dir.exists():
            return []
        return [f.stem for f in accounts_dir.glob("*.json")]

    def load(
        self,
        filename: str,
        password: str | None = None,
    ) -> Account:
        """Load account from keystore file.

        Args:
            filename: Keystore name (without .json)
            password: Decryption password (prompts if not provided)

        Returns:
            Unlocked Account instance

        Raises:
            FileNotFoundError: If keystore doesn't exist
            ValueError: If password is wrong
        """
        # Check if already loaded
        if filename.lower() in self._by_alias:
            return self._by_alias[filename.lower()]

        # Find keystore file
        accounts_dir = _get_accounts_dir()
        filepath = accounts_dir / f"{filename}.json"

        if not filepath.exists():
            # Also check Brownie dir if we're using brawny dir
            brownie_path = Path.home() / ".brownie" / "accounts" / f"{filename}.json"
            if brownie_path.exists():
                filepath = brownie_path
            else:
                raise FileNotFoundError(f"Keystore '{filename}' not found")

        # Load and decrypt
        with open(filepath) as f:
            keystore = json.load(f)

        password = _get_password(filename, password)

        try:
            private_key = EthAccount.decrypt(keystore, password)
        except ValueError as e:
            raise ValueError(f"Wrong password for '{filename}'") from e

        # Create account
        eth_acct = EthAccount.from_key(private_key)
        account = Account(
            address=eth_acct.address,
            private_key=private_key,
            alias=filename,
        )

        return self._register(account)

    def add(self, private_key: str | bytes | None = None) -> GeneratedAccount:
        """Add account from private key or generate new one.

        Args:
            private_key: Optional private key (hex string or bytes).
                        If None, generates new account with mnemonic.

        Returns:
            GeneratedAccount with mnemonic if generated
        """
        if private_key is None:
            # Generate new account with mnemonic
            _ensure_hdwallet_enabled()
            mnemonic = generate_mnemonic(num_words=12, lang="english")
            eth_acct = EthAccount.from_mnemonic(mnemonic)
            account = Account(
                address=eth_acct.address,
                private_key=eth_acct.key,
            )
            return GeneratedAccount(account=self._register(account), mnemonic=mnemonic)
        else:
            # From provided key
            if isinstance(private_key, str):
                if not private_key.startswith("0x"):
                    private_key = "0x" + private_key
            eth_acct = EthAccount.from_key(private_key)
            account = Account(
                address=eth_acct.address,
                private_key=eth_acct.key,
            )
        return GeneratedAccount(account=self._register(account), mnemonic=None)

    def from_mnemonic(
        self,
        mnemonic: str,
        count: int = 1,
        offset: int = 0,
        passphrase: str = "",
    ) -> Account | list[Account]:
        """Generate account(s) from BIP39 mnemonic.

        Args:
            mnemonic: BIP39 mnemonic phrase
            count: Number of accounts to derive
            offset: Starting index
            passphrase: Optional BIP39 passphrase

        Returns:
            Single Account if count=1, else list of Accounts
        """
        results = []
        _ensure_hdwallet_enabled()
        for i in range(offset, offset + count):
            # Standard Ethereum derivation path
            path = f"m/44'/60'/0'/0/{i}"
            eth_acct = EthAccount.from_mnemonic(
                mnemonic,
                passphrase=passphrase,
                account_path=path,
            )
            account = Account(
                address=eth_acct.address,
                private_key=eth_acct.key,
            )
            results.append(self._register(account))

        return results[0] if count == 1 else results

    def at(self, address: str) -> Account:
        """Get loaded account by address.

        Args:
            address: Hex address (0x...)

        Returns:
            Account instance

        Raises:
            KeyError: If address not loaded
        """
        key = address.lower()
        if key not in self._by_address:
            raise KeyError(f"Account {address} not loaded")
        return self._by_address[key]

    def remove(self, account: Account | str) -> None:
        """Remove account from loaded list (does not delete keystore).

        Args:
            account: Account instance or address string
        """
        if isinstance(account, str):
            account = self.at(account)

        self._loaded.remove(account)
        self._by_address.pop(account.address.lower(), None)
        if account.alias:
            self._by_alias.pop(account.alias.lower(), None)

    def clear(self) -> None:
        """Remove all loaded accounts."""
        self._loaded.clear()
        self._by_address.clear()
        self._by_alias.clear()
        self.default = None

    def __getitem__(self, index: int) -> Account:
        """Get account by index."""
        return self._loaded[index]

    def __len__(self) -> int:
        return len(self._loaded)

    def __iter__(self) -> Iterator[Account]:
        return iter(self._loaded)

    def __contains__(self, item: str | Account) -> bool:
        if isinstance(item, Account):
            return item in self._loaded
        return item.lower() in self._by_address or item.lower() in self._by_alias

    def __repr__(self) -> str:
        available = len(self.list())
        loaded = len(self._loaded)
        return f"<Accounts [{loaded} loaded, {available} available]>"


def _init_accounts() -> None:
    """Initialize global accounts singleton."""
    global _accounts
    _accounts = Accounts()


def _get_accounts() -> Accounts:
    """Get accounts singleton, initializing if needed."""
    global _accounts
    if _accounts is None:
        _init_accounts()
    return _accounts


# Proxy for import-time access
class _AccountsProxy:
    """Proxy that delegates to accounts singleton."""

    def __getitem__(self, index: int) -> Account:
        return _get_accounts()[index]

    def __len__(self) -> int:
        return len(_get_accounts())

    def __iter__(self) -> Iterator[Account]:
        return iter(_get_accounts())

    def __contains__(self, item: str | Account) -> bool:
        return item in _get_accounts()

    def at(self, address: str) -> Account:
        return _get_accounts().at(address)

    def load(self, filename: str, password: str | None = None) -> Account:
        return _get_accounts().load(filename, password)

    def add(self, private_key: str | bytes | None = None) -> GeneratedAccount:
        return _get_accounts().add(private_key)

    def from_mnemonic(
        self,
        mnemonic: str,
        count: int = 1,
        offset: int = 0,
        passphrase: str = "",
    ) -> Account | list[Account]:
        return _get_accounts().from_mnemonic(mnemonic, count, offset, passphrase)

    def list(self) -> list[str]:
        return _get_accounts().list()

    def remove(self, account: Account | str) -> None:
        return _get_accounts().remove(account)

    def clear(self) -> None:
        _get_accounts().clear()

    @property
    def default(self) -> Account | None:
        return _get_accounts().default

    @default.setter
    def default(self, value: Account | None) -> None:
        _get_accounts().default = value

    def __repr__(self) -> str:
        return repr(_get_accounts())


# Global proxy instance
accounts = _AccountsProxy()
