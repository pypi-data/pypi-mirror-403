"""
brawny: Block-driven Ethereum job/transaction execution framework.

This package provides a robust, production-ready framework for scheduling
and executing Ethereum transactions based on block events.
"""

from brawny.jobs.base import Job
from brawny.jobs.registry import registry, job
from brawny.model.types import (
    BlockInfo,
    Trigger,
    TxAttempt,
    TxIntent,
    TxIntentSpec,
    to_wei,
)
from brawny.model.contexts import (
    BlockContext,
    CheckContext,
    BuildContext,
    AlertContext,
)
from brawny.model.events import DecodedEvent, find_event, events_by_name
from brawny.telegram import telegram, get_telegram, TelegramBot
from brawny.testing import job_context
from brawny.interfaces import interface

# Implicit context helpers (Flask-like pattern)
from brawny.api import (
    block,
    ctx,       # Get current phase context (CheckContext or BuildContext)
    trigger,
    intent,
    shorten,
    explorer_link,
    gas_ok,
    gas_quote,
    kv,        # Persistent KV store
    alert,     # Send alerts from job hooks
    rpc,       # RPC proxy (internal package renamed to _rpc to avoid collision)
    http,      # Approved HTTP client proxy
    get_address_from_alias,
    Contract,  # Brownie-style
    Wei,       # Brownie-style
    web3,      # Brownie-style
    multicall, # Brownie-style
)

# Brownie-style singletons for scripts
from brawny.accounts import accounts, Account
from brawny.history import history
from brawny.chain import chain
from brawny.networks import network

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Job",
    "job",
    "registry",
    "BlockInfo",
    "Trigger",
    "TxAttempt",
    "TxIntent",
    "TxIntentSpec",
    "to_wei",
    # Phase-specific contexts (OE7)
    "BlockContext",
    "CheckContext",
    "BuildContext",
    "AlertContext",
    # Events
    "DecodedEvent",
    "find_event",
    "events_by_name",
    # Implicit context helpers
    "block",
    "ctx",
    "trigger",
    "intent",
    "shorten",
    "explorer_link",
    "gas_ok",
    "gas_quote",
    "kv",
    "alert",
    "rpc",
    "http",
    "get_address_from_alias",
    # Brownie-style helpers
    "Contract",
    "Wei",
    "web3",
    "multicall",
    # Brownie-style singletons
    "accounts",
    "Account",
    "history",
    "chain",
    "network",
    # Telegram
    "telegram",
    "get_telegram",
    "TelegramBot",
    # Testing
    "job_context",
    "interface",
]
