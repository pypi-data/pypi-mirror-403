"""BrawnyDaemon - Main daemon orchestrator.

Provides the core daemon class that manages all components and threads.
"""

from __future__ import annotations

import asyncio
import itertools
import os
import socket
import threading
import time
from threading import Event, Lock, Thread
from typing import TYPE_CHECKING, Any, Callable

from brawny.alerts.contracts import ContractSystem
from brawny.alerts.health import health_alert
from brawny.alerts.routing import resolve_targets, validate_targets
from brawny.alerts.send import AlertService, create_send_health, set_alert_service
from brawny.async_runtime import clear_loop, register_loop, run_sync
from brawny.automation import AutomationState
from brawny.daemon.context import DaemonContext, DaemonState, RuntimeOverrides
from brawny.daemon.loops import run_monitor, run_worker
from brawny.daemon.supervisor import WorkerSupervisor
from brawny.db import create_database
from brawny.db.migrate import Migrator, verify_critical_schema
from brawny.jobs.discovery import (
    JobDiscoveryFailed,
    JobLoadError,
    auto_discover_jobs,
    discover_jobs,
)
from brawny.jobs.job_validation import validate_all_jobs
from brawny.jobs.registry import get_registry
from brawny.keystore import create_keystore
from brawny.lifecycle import LifecycleDispatcher
from brawny.logging import get_logger
from brawny.metrics import ACTIVE_WORKERS, get_metrics
from brawny.model.startup import StartupMessage
from brawny.model.types import BlockInfo
from brawny._rpc.clients import ReadClient
from brawny.scheduler.poller import BlockPoller
from brawny.scheduler.reorg import ReorgDetector
from brawny.scheduler.runner import JobRunner
from brawny.recovery.runner import run_startup_recovery
from brawny.startup import reconcile_broadcasted_intents
from brawny.tx.executor import TxExecutor
from brawny.tx.monitor import TxMonitor
from brawny.tx.nonce import NonceManager
from brawny.tx.replacement import TxReplacer
from brawny.runtime_controls import RuntimeControls
from brawny.validation import validate_job_routing
from brawny.telegram import TelegramBot

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.config.models import TelegramConfig
    from brawny.db.base import Database
    from brawny.jobs.base import Job
    from brawny.keystore import Keystore


class BrawnyDaemon:
    """Main daemon orchestrator.

    Manages all components, threads, and lifecycle for the brawny daemon.
    """

    def __init__(
        self,
        config: "Config",
        overrides: RuntimeOverrides | None = None,
        extra_modules: list[str] | None = None,
    ) -> None:
        """Initialize the daemon.

        Args:
            config: Application configuration
            overrides: Runtime overrides for dry_run, once, worker_count, etc.
            extra_modules: Additional job modules to discover
        """
        self.config = config
        self.overrides = overrides or RuntimeOverrides()
        self._extra_modules = extra_modules or []
        self._log = get_logger(__name__)

        # Components (initialized in start())
        self._db: Database | None = None
        self._rpc: ReadClient | None = None
        self._keystore: Keystore | None = None
        self._contract_system: ContractSystem | None = None
        self._lifecycle: LifecycleDispatcher | None = None
        self._executor: TxExecutor | None = None
        self._monitor: TxMonitor | None = None
        self._replacer: TxReplacer | None = None
        self._controls: RuntimeControls | None = None
        self._automation: AutomationState | None = None
        self._job_runner: JobRunner | None = None
        self._reorg_detector: ReorgDetector | None = None
        self._poller: BlockPoller | None = None

        # Jobs
        self._jobs: dict[str, Job] = {}

        # Telegram (cached instance)
        self._telegram_bot: TelegramBot | None = None

        # Health alerting (initialized in initialize())
        self._health_send_fn: Callable[..., None] | None = None
        self._admin_chat_ids: list[str] | None = None
        self._health_cooldown: int = 1800

        # Threading
        self._stop = Event()
        self._wakeup_hint = Event()
        self._worker_threads: list[Thread] = []
        self._monitor_thread: Thread | None = None
        self._monitor_stop = Event()

        # Worker supervision (fail-fast on worker thread failures)
        self._supervisor = WorkerSupervisor(fail_fast=True)

        # Inflight tracking
        self._inflight_lock = Lock()
        self._inflight_count = 0
        self._inflight_zero = Event()
        self._inflight_zero.set()

        # Claim token generation
        self._claim_counter = itertools.count(1)
        self._hostname = socket.gethostname()
        self._pid = os.getpid()

        # Async event loop (owned by daemon, used by runner for async job.check())
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self._loop_thread: Thread | None = None
        self._loop_started = Event()
        self._loop_thread_id: int | None = None
        self._alert_service: AlertService | None = None

    @property
    def db(self) -> "Database":
        """Get database connection."""
        if self._db is None:
            raise RuntimeError("Daemon not started")
        return self._db

    @property
    def rpc(self) -> ReadClient:
        """Get RPC manager."""
        if self._rpc is None:
            raise RuntimeError("Daemon not started")
        return self._rpc

    @property
    def jobs(self) -> dict[str, "Job"]:
        """Get discovered jobs."""
        return self._jobs

    @property
    def keystore(self) -> "Keystore | None":
        """Get keystore (None in dry_run mode)."""
        return self._keystore

    def _check_schema(self) -> None:
        """Verify critical DB schema columns exist. Hard-fail if not."""
        if self._db is None:
            raise RuntimeError("Database not initialized")

        try:
            verify_critical_schema(self._db)
        except Exception as exc:
            # BUG re-raise on schema validation failures.
            error_msg = str(exc)
            self._log.critical(
                "schema.validation_failed",
                error=error_msg,
                table="critical_schema",
                exc_info=True,
            )
            health_alert(
                component="brawny.startup.schema",
                chain_id=self.config.chain_id,
                error=error_msg,
                level="critical",
                action="See error for remediation",
                db_dialect=self._db.dialect,
                force_send=True,
                send_fn=self._health_send_fn,
                admin_chat_ids=self._admin_chat_ids,
            )
            raise SystemExit(f"DB schema mismatch: {error_msg}") from exc

    def _start_async_loop(self) -> None:
        if self._loop_thread and self._loop_thread.is_alive():
            return

        def _run_loop() -> None:
            asyncio.set_event_loop(self._loop)
            self._loop_thread_id = threading.get_ident()
            register_loop(self._loop, self._loop_thread_id)
            self._loop_started.set()
            self._loop.run_forever()
            self._loop.close()

        self._loop_started.clear()
        self._loop_thread = Thread(target=_run_loop, name="brawny-async-loop", daemon=True)
        self._loop_thread.start()
        self._loop_started.wait(timeout=5.0)
        if not self._loop_started.is_set():
            raise RuntimeError("Async loop failed to start")

    def _stop_async_loop(self) -> None:
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread:
            self._loop_thread.join(timeout=5.0)
        clear_loop()

    def _make_claim_token(self, worker_id: int) -> str:
        """Generate a unique claim token for a worker."""
        return f"{self._hostname}:{self._pid}:{worker_id}:{next(self._claim_counter)}"

    def _make_claimed_by(self, worker_id: int) -> str:
        """Generate a stable claimed_by identifier for a worker."""
        return f"{self._hostname}:{self._pid}:{worker_id}"

    def _inflight_start(self) -> None:
        """Mark an inflight operation starting."""
        with self._inflight_lock:
            self._inflight_count += 1
            self._inflight_zero.clear()

    def _inflight_done(self) -> None:
        """Mark an inflight operation complete."""
        with self._inflight_lock:
            self._inflight_count = max(0, self._inflight_count - 1)
            if self._inflight_count == 0:
                self._inflight_zero.set()

    def _on_intent_created(self, intent_id: str) -> None:
        """Callback when intent is created."""
        self._wakeup_hint.set()

    @staticmethod
    def _ingest_is_meaningful(block_result: "BlockResult") -> bool:
        return block_result.jobs_triggered > 0 or block_result.intents_created > 0

    def _process_block(self, block: BlockInfo) -> None:
        """Process a single block."""
        if self._job_runner is None:
            raise RuntimeError("Job runner not initialized")
        if self._automation and not self._automation.enabled():
            enabled, reason, disabled_at = self._automation.status()
            self._log.debug(
                "block.ingest.skipped",
                block_number=block.block_number,
                reason=reason,
                disabled_at=disabled_at.isoformat() if disabled_at else None,
            )
            return

        self._log.debug(
            "block.ingest.start",
            block_number=block.block_number,
        )

        block_result = self._job_runner.process_block(block)

        meaningful = self._ingest_is_meaningful(block_result)
        log_fields = {
            "block_number": block.block_number,
            "jobs_checked": block_result.jobs_checked,
            "jobs_triggered": block_result.jobs_triggered,
            "intents_created": block_result.intents_created,
        }
        if meaningful:
            log_fields["meaningful"] = True
            if block_result.jobs_triggered > 0:
                log_fields["reason"] = "jobs_triggered"
            elif block_result.intents_created > 0:
                log_fields["reason"] = "intents_created"

        log_fn = self._log.info if meaningful else self._log.debug
        log_fn(
            "block.ingest.done",
            **log_fields,
        )

    def _discover_jobs(self) -> list[JobLoadError]:
        """Discover and register jobs based on config.

        Returns:
            List of JobLoadError for any modules that failed to load.
        """
        registry = get_registry()
        registry.clear()  # Start fresh to prevent partial state leakage

        if self._extra_modules:
            discovered, errors = discover_jobs(self._extra_modules)
        else:
            discovered, errors = auto_discover_jobs()

        # Log discovery summary
        self._log.info(
            "job.discovery.complete",
            jobs_loaded=len(discovered),
            jobs_failed=len(errors),
        )

        if errors:
            registry.clear()  # Don't leave partial state
            return errors

        self._jobs = {job.job_id: job for job in registry.get_all()}
        return []

    def _validate_jobs(self) -> tuple[dict[str, list[str]], list[str]]:
        """Validate discovered jobs.

        Returns:
            Tuple of (validation_errors, routing_errors)
        """
        validation_errors: dict[str, list[str]] = {}
        routing_errors: list[str] = []

        if self._jobs:
            keystore = self._keystore if not self.overrides.dry_run else None
            validation_errors = validate_all_jobs(self._jobs, keystore=keystore)
            routing_errors = validate_job_routing(self.config, self._jobs)

        return validation_errors, routing_errors

    def _validate_telegram_config(self) -> list[str]:
        """Validate telegram configuration and routing.

        Returns:
            List of validation errors (empty if valid)
        """
        tg = self.config.telegram
        errors: list[str] = []

        # Check if any routing is configured (use truthiness, not is not None)
        has_routing = (
            bool(tg.default)
            or bool(tg.public)
            or any(getattr(j, "_alert_to", None) for j in self._jobs.values())
        )

        # Validate all name references
        valid_names = set(tg.chats.keys())

        # Validate admin targets (names only)
        invalid = validate_targets(tg.admin, valid_names, allow_ids=False)
        for name in invalid:
            errors.append(f"telegram.admin references unknown chat '{name}'")

        # Validate public targets (names only)
        invalid = validate_targets(tg.public, valid_names, allow_ids=False)
        for name in invalid:
            errors.append(f"telegram.public references unknown chat '{name}'")

        # Validate default targets (names only)
        invalid = validate_targets(tg.default, valid_names, allow_ids=False)
        for name in invalid:
            errors.append(f"telegram.default references unknown chat '{name}'")

        # Validate each job's alert_to target
        for job_id, job in self._jobs.items():
            target = getattr(job, "_alert_to", None)
            if target is None:
                continue

            invalid = validate_targets(target, valid_names, allow_ids=False)
            for name in invalid:
                errors.append(
                    f"Job '{job_id}' references unknown telegram chat '{name}'. "
                    f"Valid names: {sorted(valid_names)}"
                )
        if errors:
            for err in errors:
                self._log.error("telegram.routing.invalid", error=err)
        return errors

    def _warn_loose_telegram_chat_ids(self) -> list["StartupMessage"]:
        """Warn if telegram targets resolve to non-numeric chat IDs.

        This is intentionally loose and only runs once at startup.
        """
        tg = self.config.telegram
        warnings: list[StartupMessage] = []
        if tg is None:
            return warnings

        def _normalize_targets(value: object) -> list[str]:
            if value is None:
                return []
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]
            return []

        def _is_intlike(value: str) -> bool:
            v = value.strip()
            if v.startswith("-"):
                v = v[1:]
            return v.isdigit()

        targets: list[str] = []
        targets.extend(_normalize_targets(tg.admin))
        targets.extend(_normalize_targets(tg.public))
        targets.extend(_normalize_targets(tg.default))
        for job in self._jobs.values():
            target = getattr(job, "_alert_to", None)
            targets.extend(_normalize_targets(target))

        for target in targets:
            resolved = tg.chats.get(target, target)
            if not _is_intlike(str(resolved)):
                warnings.append(
                    StartupMessage(
                        level="warning",
                        code="telegram.chat_id_format",
                        message=(
                            f"Telegram target '{target}' resolves to non-numeric chat id "
                            f"'{resolved}'."
                        ),
                        fix="Use numeric chat IDs (e.g. -1001234567890).",
                    )
                )

        return warnings

        # Warn about configuration issues (non-fatal)
        if has_routing and not tg.bot_token:
            self._log.warning(
                "telegram.bot_token_missing",
                message="Jobs use alert_to= or telegram.default is set, but bot_token is missing",
            )
        elif (
            tg.bot_token
            and not tg.default
            and not tg.public
            and not any(getattr(j, "_alert_to", None) for j in self._jobs.values())
        ):
            self._log.warning(
                "telegram.no_default_targets",
                message="bot_token set but no public/default targets and no jobs use alert_to=",
            )

        return []

    def _reconcile_startup(self) -> None:
        """Reconcile state on startup."""
        if self._db is None:
            raise RuntimeError("Database not initialized")
        nonce_manager = (
            self._executor.nonce_manager
            if self._executor
            else NonceManager(self._db, self._rpc, self.config.chain_id)
        )
        run_startup_recovery(
            self._db,
            self.config,
            nonce_manager,
            actor="daemon",
            source="startup_recovery",
        )

    def _reconcile_broadcasted_intents_startup(self) -> None:
        """Reconcile broadcasted intents using live-path monitoring."""
        if self._monitor is None:
            return
        reconcile_broadcasted_intents(
            self._db,
            self._monitor,
            self.config.chain_id,
            self._log,
        )

    def _start_workers(self) -> None:
        """Start worker threads with supervision."""
        if self.overrides.dry_run:
            return

        worker_count = (
            self.overrides.worker_count
            if self.overrides.worker_count is not None
            else self.config.worker_count
        )

        ctx = DaemonContext(
            config=self.config,
            log=self._log,
            db=self._db,
            rpc=self._rpc,
            executor=self._executor,
            monitor=self._monitor,
            replacer=self._replacer,
            nonce_manager=self._executor.nonce_manager if self._executor else None,
            controls=self._controls,
            automation=self._automation,
            chain_id=self.config.chain_id,
            health_send_fn=self._health_send_fn,
            admin_chat_ids=self._admin_chat_ids,
            health_cooldown=self._health_cooldown,
        )
        state = DaemonState(
            make_claim_token=self._make_claim_token,
            make_claimed_by=self._make_claimed_by,
            inflight_inc=self._inflight_start,
            inflight_dec=self._inflight_done,
        )

        # Register workers with supervisor
        for i in range(worker_count):
            self._supervisor.add(
                f"tx_worker_{i}",
                lambda worker_id=i: run_worker(
                    worker_id, self._stop, self._wakeup_hint, ctx, state, self.overrides.dry_run
                ),
            )

        # Register monitor as supervised worker
        self._supervisor.add(
            "tx_monitor",
            lambda: run_monitor(self._monitor_stop, ctx, self._worker_threads),
        )

        # Start all supervised workers
        self._supervisor.start_all()

        # Track worker threads for backward compatibility (used in monitor and shutdown)
        # The supervisor owns the actual threads, but we need references for metrics
        with self._supervisor._lock:
            for name, worker_state in self._supervisor._workers.items():
                if name.startswith("tx_worker_") and worker_state.thread:
                    self._worker_threads.append(worker_state.thread)
                elif name == "tx_monitor" and worker_state.thread:
                    self._monitor_thread = worker_state.thread

        # Start supervisor watcher - signals daemon stop when supervisor triggers shutdown
        def _watch_supervisor() -> None:
            self._supervisor.wait_for_shutdown()
            if not self._stop.is_set():
                self._log.critical(
                    "daemon.supervisor_shutdown",
                    reason=self._supervisor.fatal_reason(),
                )
                self._stop.set()
                self._wakeup_hint.set()
                if self._poller:
                    self._poller.stop(timeout=0.1)

        watcher = Thread(target=_watch_supervisor, name="supervisor-watcher", daemon=True)
        watcher.start()

        # Initial gauge
        metrics = get_metrics()
        metrics.gauge(ACTIVE_WORKERS).set(
            len(self._worker_threads),
            chain_id=self.config.chain_id,
        )

    def _shutdown(self) -> None:
        """Shutdown the daemon gracefully."""
        self._log.info("daemon.shutdown.start")

        # Signal stop
        self._stop.set()
        self._wakeup_hint.set()
        self._monitor_stop.set()

        # Wait for inflight
        if not self._inflight_zero.is_set():
            self._log.info(
                "shutdown.await_inflight",
                inflight=self._inflight_count,
                grace_seconds=self.config.shutdown_grace_seconds,
            )
        start_wait = time.time()
        self._inflight_zero.wait(timeout=self.config.shutdown_grace_seconds)
        wait_elapsed = time.time() - start_wait
        remaining = max(0.0, self.config.shutdown_grace_seconds - wait_elapsed)

        # Join workers
        for t in self._worker_threads:
            t.join(timeout=remaining)

        # Join monitor
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)

        # Log any threads still alive
        alive = [t for t in self._worker_threads if t.is_alive()]
        if alive:
            self._log.warning("shutdown.threads_still_alive", count=len(alive))

        # Close HTTP clients to avoid leaked connections
        # Keep calls qualified to avoid name collision (both modules export close_http_client)
        from brawny.alerts import abi_resolver
        from brawny.telegram import close_http_client as close_telegram_http_client

        if self._alert_service is not None:
            run_sync(self._alert_service.stop(flush_timeout=self.config.shutdown_grace_seconds))
            set_alert_service(None)
        abi_resolver.close_http_client()
        close_telegram_http_client()
        if self._job_runner is not None:
            self._job_runner.close()
        if self._lifecycle is not None:
            self._lifecycle.close()

        self._stop_async_loop()

        self._log.info("daemon.shutdown.complete")

    def initialize(
        self,
    ) -> tuple[dict[str, list[str]], list[str], list["StartupMessage"]]:
        """Initialize all components.

        Returns:
            Tuple of (validation_errors, routing_errors, startup_messages) for jobs
        """
        startup_messages: list[StartupMessage] = []

        # Database
        self._db = create_database(
            self.config.database_url,
            circuit_breaker_failures=self.config.db_circuit_breaker_failures,
            circuit_breaker_seconds=self.config.db_circuit_breaker_seconds,
            production=self.config.production,
        )
        self._db.connect()
        self._controls = RuntimeControls(self._db)
        self._automation = AutomationState(self.config.chain_id, self._log)

        # Migrations
        migrator = Migrator(self._db)
        pending = migrator.pending()
        if pending:
            self._log.info("migrations.applying", count=len(pending))
            migrator.migrate()

        # RPC
        self._rpc = ReadClient.from_config(self.config)

        self._log.info(
            "startup.finality_policy",
            chain_id=self.config.chain_id,
            finality_confirmations=self.config.finality_confirmations,
            read_only=True,
        )

        # Keystore (only in live mode)
        if not self.overrides.dry_run:
            self._keystore = create_keystore(
                self.config.keystore_type,
                keystore_path=self.config.keystore_path,
                allowed_signers=[],
            )
            # Make keystore available for signer_address() helper
            from brawny.api import _set_keystore
            _set_keystore(self._keystore)

            # Collect keystore warnings
            startup_messages.extend(self._keystore.get_warnings())

        # Discover jobs
        load_errors = self._discover_jobs()
        if load_errors:
            for err in load_errors:
                self._log.error(
                    "job.module_load_failed",
                    path=err.path,
                    message=err.message,
                    traceback=err.traceback,
                )
            raise JobDiscoveryFailed(load_errors)

        # Sanity check: don't run with zero jobs
        if not self._jobs:
            raise RuntimeError("No jobs discovered - check your jobs directory")

        validation_errors, routing_errors = self._validate_jobs()

        # Validate telegram routing (fails hard on unknown names)
        telegram_errors = self._validate_telegram_config()
        if telegram_errors:
            from brawny.model.errors import ConfigError
            raise ConfigError(
                f"Invalid telegram routing: {len(telegram_errors)} error(s)\n"
                + "\n".join(f"  - {e}" for e in telegram_errors)
            )
        startup_messages.extend(self._warn_loose_telegram_chat_ids())

        # Cache TelegramBot instance (if configured)
        if self.config.telegram.bot_token:
            self._telegram_bot = TelegramBot(
                token=self.config.telegram.bot_token,
                default_parse_mode=self.config.telegram.parse_mode or "Markdown",
            )

        # Initialize health alerting (admin lane only)
        tg = self.config.telegram
        if tg:
            self._admin_chat_ids = resolve_targets(tg.admin, tg.chats, [])
            if self._telegram_bot:
                self._health_send_fn = create_send_health(self._telegram_bot)
            self._health_cooldown = tg.health_cooldown_seconds

        from brawny.alerts import send as alerts_send
        self._alert_service = AlertService(
            maxsize=alerts_send.ALERT_QUEUE_MAXSIZE,
            max_attempts=alerts_send.ALERT_SEND_MAX_ATTEMPTS,
            backoff_base_seconds=alerts_send.ALERT_SEND_BACKOFF_BASE_SECONDS,
            backoff_max_seconds=alerts_send.ALERT_SEND_BACKOFF_MAX_SECONDS,
            health_max_oldest_age_seconds=self.config._advanced_or_default().alerts_health_max_oldest_age_seconds,
        )
        set_alert_service(self._alert_service)

        # Validate schema (after health is set up so we can alert on failure)
        self._check_schema()

        # Contract system
        self._contract_system = ContractSystem(self._rpc, self.config)

        # Lifecycle
        self._lifecycle = LifecycleDispatcher(
            self._db,
            self._rpc,
            self.config,
            self._jobs,
            contract_system=self._contract_system,
            telegram_bot=self._telegram_bot,
        )

        # TX execution components (only in live mode)
        if self._keystore:
            self._executor = TxExecutor(
                self._db, self._rpc, self._keystore, self.config,
                lifecycle=self._lifecycle,
                jobs=self._jobs,
            )
            self._monitor = TxMonitor(
                self._db, self._rpc, self._executor.nonce_manager, self.config,
                lifecycle=self._lifecycle
            )
            self._replacer = TxReplacer(
                self._db, self._rpc, self._keystore, self._executor.nonce_manager, self.config,
                lifecycle=self._lifecycle,
                controls=self._controls,
            )

        # Job runner
        self._job_runner = JobRunner(
            self._db,
            self._rpc,
            self.config,
            self._jobs,
            lifecycle=self._lifecycle,
            contract_system=self._contract_system,
            loop=self._loop,
            controls=self._controls,
            health_send_fn=self._health_send_fn,
            admin_chat_ids=self._admin_chat_ids,
            health_cooldown=self._health_cooldown,
        )
        self._job_runner._on_intent_created = self._on_intent_created

        # Reorg detector
        self._reorg_detector = ReorgDetector(
            db=self._db,
            rpc=self._rpc,
            chain_id=self.config.chain_id,
            reorg_depth=self.config.reorg_depth,
            block_hash_history_size=self.config.block_hash_history_size,
            finality_confirmations=self.config.finality_confirmations,
            lifecycle=self._lifecycle,
            health_send_fn=self._health_send_fn,
            admin_chat_ids=self._admin_chat_ids,
            health_cooldown=self._health_cooldown,
        )

        # Block poller
        self._poller = BlockPoller(
            self._db, self._rpc, self.config, self._process_block,
            reorg_detector=self._reorg_detector,
            health_send_fn=self._health_send_fn,
            admin_chat_ids=self._admin_chat_ids,
            health_cooldown=self._health_cooldown,
            automation=self._automation,
        )

        # Register jobs in database
        for job_id, job in self._jobs.items():
            self._db.upsert_job(job_id, job.name, job.check_interval_blocks)

        return validation_errors, routing_errors, startup_messages

    def run(self, blocking: bool = True) -> int:
        """Run the daemon. Returns exit code (0=clean, 1=failure).

        Caller should: sys.exit(daemon.run())

        Args:
            blocking: If True, block until shutdown. If False, return immediately.

        Returns:
            Exit code: 0 for clean shutdown, 1 for worker failure
        """
        if self._poller is None:
            raise RuntimeError("Daemon not initialized")

        # Start async loop and services
        self._start_async_loop()
        if self._alert_service is not None:
            run_sync(self._alert_service.start())

        # Startup reconciliation
        self._reconcile_startup()
        self._reconcile_broadcasted_intents_startup()

        # Warm gas cache before workers start (eliminates cold-start race)
        try:
            run_sync(asyncio.wait_for(self._rpc.gas_quote(), timeout=5.0))
            self._log.debug("startup.gas_cache_warmed")
        except Exception as e:
            # RECOVERABLE gas cache warm failures fall back to lazy fills.
            self._log.error("startup.gas_cache_warm_failed", error=str(e), exc_info=True)

        # Start workers
        self._start_workers()

        try:
            if self.overrides.once:
                # Single iteration mode
                self._poller._poll_once()
            else:
                # Normal polling mode
                try:
                    self._poller.start(blocking=blocking)
                except KeyboardInterrupt:
                    self._log.info("daemon.keyboard_interrupt")
        except Exception as exc:
            # BUG re-raise unexpected daemon run failures.
            self._log.error("daemon.run_failed", error=str(exc)[:200], exc_info=True)
            setattr(exc, "_logged_unexpected", True)
            raise
        finally:
            self._shutdown()

        # Return non-zero exit code if supervisor triggered shutdown due to worker failure
        if self._supervisor.fatal_reason():
            return 1
        return 0

    def health_check(self) -> dict[str, Any]:
        """Return daemon health status.

        Uses all_healthy() as primary health indicator. This ensures:
        - fail_fast=True + worker fails → shutdown_requested()=True → healthy=False
        - fail_fast=False + worker fails → all_healthy()=False → healthy=False

        Either way, health checks report unhealthy when workers fail.
        """
        worker_snapshot = self._supervisor.snapshot()
        workers_ok = self._supervisor.all_healthy()

        from brawny.alerts import send as alerts_send
        alert_health = alerts_send.get_alert_worker_health()
        alerts_ok = bool(alert_health.get("healthy", True))

        return {
            "healthy": workers_ok and alerts_ok and not self._supervisor.shutdown_requested(),
            "workers": worker_snapshot,
            "fatal_reason": self._supervisor.fatal_reason(),
            "alerts": alert_health,
        }

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the daemon.

        Signals all components to stop. Called from shutdown handler.

        Args:
            timeout: Timeout for stopping the poller
        """
        # Signal workers and monitor to stop
        self._stop.set()
        self._wakeup_hint.set()
        self._monitor_stop.set()

        if self._poller:
            self._poller.stop(timeout=timeout)
