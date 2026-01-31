"""Daemon context and state for brawny.

Provides DaemonContext (shared component references) and DaemonState (loop callbacks).
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import Logger
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.db.base import Database
    from brawny._rpc.clients import ReadClient
    from brawny.tx.executor import TxExecutor
    from brawny.tx.monitor import TxMonitor
    from brawny.tx.replacement import TxReplacer
    from brawny.tx.nonce import NonceManager
    from brawny.runtime_controls import RuntimeControls
    from brawny.automation import AutomationState


@dataclass
class DaemonContext:
    """Shared context for daemon loops.

    Contains references to all components needed by worker and monitor loops.
    """

    config: "Config"
    log: Logger
    db: "Database"
    rpc: "ReadClient"
    executor: "TxExecutor | None"
    monitor: "TxMonitor | None"
    replacer: "TxReplacer | None"
    nonce_manager: "NonceManager | None"
    chain_id: int
    controls: "RuntimeControls | None" = None
    automation: "AutomationState | None" = None

    # Health alerts (optional - None means disabled)
    health_send_fn: Callable[..., None] | None = None
    admin_chat_ids: list[str] | None = None
    health_cooldown: int = 1800


@dataclass
class DaemonState:
    """State callbacks for daemon loops.

    Provides callbacks to track inflight operations and generate claim tokens.
    Keeps loops decoupled from daemon internals.
    """

    make_claim_token: Callable[[int], str]
    make_claimed_by: Callable[[int], str]
    inflight_inc: Callable[[], None]
    inflight_dec: Callable[[], None]


@dataclass
class RuntimeOverrides:
    """Runtime overrides for daemon configuration.

    Allows CLI and programmatic callers to override config values.
    """

    dry_run: bool = False
    once: bool = False
    worker_count: int | None = None
    strict_validation: bool = True
