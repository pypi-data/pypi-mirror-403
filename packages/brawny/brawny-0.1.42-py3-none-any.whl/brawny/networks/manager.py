"""Network connection management.

Provides Brownie-compatible network.connect()/disconnect() API.
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from brawny.networks.config import NetworkConfig, load_networks
from brawny._rpc.errors import RPCError

if TYPE_CHECKING:
    from brawny._rpc.clients import ReadClient


def _get_pidfile_dir() -> Path:
    """Get directory for PID files."""
    path = Path.home() / ".brawny" / "pids"
    path.mkdir(parents=True, exist_ok=True)
    return path


class NetworkManager:
    """Manages network connections with Brownie-compatible API.

    Usage:
        from brawny import network

        network.connect("mainnet")
        print(network.show_active())  # "mainnet"
        print(network.chain_id)       # 1
        network.disconnect()

    Dev network lifecycle:
        - PID files stored in ~/.brawny/pids/{network_id}.json
        - Processes cleaned up on disconnect() or atexit
        - Handles already-dead processes gracefully
    """

    def __init__(self) -> None:
        self._networks: dict[str, NetworkConfig] | None = None
        self._active: NetworkConfig | None = None
        self._rpc: ReadClient | None = None
        self._rpc_process: subprocess.Popen | None = None
        self._rpc_process_network_id: str | None = None  # Track which network we started
        self._chain_id: int | None = None  # Cached after first lookup

        # Register cleanup on exit (handles normal exit, not SIGKILL)
        atexit.register(self._cleanup)

        # Handle SIGTERM gracefully (e.g., from container orchestration)
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_cleanup)

    def _signal_cleanup(self, signum: int, frame: object) -> None:
        """Handle SIGTERM by cleaning up and re-raising."""
        self._cleanup()
        # Re-raise to allow normal signal handling
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    def _cleanup(self) -> None:
        """Kill RPC process on exit. Safe to call multiple times."""
        if self._rpc_process is None:
            return

        # Check if still running (poll() returns None if running)
        if self._rpc_process.poll() is None:
            self._rpc_process.terminate()
            try:
                self._rpc_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._rpc_process.kill()
                self._rpc_process.wait(timeout=1)

        # Clean up PID file
        if self._rpc_process_network_id:
            self._remove_pidfile(self._rpc_process_network_id)
            self._rpc_process_network_id = None

        self._rpc_process = None

    def _write_pidfile(self, network_id: str, pid: int, port: int) -> None:
        """Write PID file for debugging."""
        pidfile = _get_pidfile_dir() / f"{network_id}.json"
        pidfile.write_text(json.dumps({"pid": pid, "port": port, "network_id": network_id}))

    def _remove_pidfile(self, network_id: str) -> None:
        """Remove PID file."""
        pidfile = _get_pidfile_dir() / f"{network_id}.json"
        pidfile.unlink(missing_ok=True)

    def _ensure_networks(self) -> dict[str, NetworkConfig]:
        """Lazily load networks."""
        if self._networks is None:
            self._networks = load_networks()
        return self._networks

    @property
    def is_connected(self) -> bool:
        """Check if connected to a network."""
        return self._active is not None and self._rpc is not None

    @property
    def chain_id(self) -> int | None:
        """Get current chain ID (cached)."""
        if not self.is_connected or self._rpc is None:
            return None
        if self._chain_id is None:
            self._chain_id = self._rpc.get_chain_id()
        return self._chain_id

    def show_active(self) -> str | None:
        """Get ID of currently active network."""
        return self._active.id if self._active else None

    def connect(
        self,
        network_id: str | None = None,
        launch_rpc: bool = True,
    ) -> None:
        """Connect to a network.

        Args:
            network_id: Network ID to connect to. Priority:
                       1. Explicit argument
                       2. BRAWNY_NETWORK env var
                       3. "development" default
            launch_rpc: If True, launch RPC process for development networks

        Raises:
            ConnectionError: If already connected
            KeyError: If network_id not found
        """
        if self.is_connected:
            raise ConnectionError(
                f"Already connected to '{self._active.id}'. "
                "Call network.disconnect() first."
            )

        networks = self._ensure_networks()

        # Priority: explicit arg > env var > default
        network_id = network_id or os.environ.get("BRAWNY_NETWORK") or "development"

        if network_id not in networks:
            available = ", ".join(sorted(networks.keys()))
            raise KeyError(f"Network '{network_id}' not found. Available: {available}")

        config = networks[network_id]

        # Resolve fork reference at connect time
        self._resolve_fork(config, networks)

        # Get endpoints (list) - read client handles failover automatically
        endpoints = config.get_endpoints()

        # Launch RPC for development networks
        if config.is_development and launch_rpc:
            local_url = config.get_host_with_port()
            try:
                self._launch_rpc(config)
                self._wait_for_rpc(local_url, timeout=config.timeout)
            except BaseException:
                # Clean up on failure
                if self._rpc_process:
                    self._rpc_process.terminate()
                    self._rpc_process = None
                raise
            # Dev networks only use local endpoint
            endpoints = [local_url]

        # Create read client with full configuration (preserves brawny's advantages)
        from brawny._rpc.clients import ReadClient
        from brawny._rpc.retry_policy import policy_from_values

        self._rpc = ReadClient(
            endpoints=endpoints,
            timeout_seconds=float(config.timeout),
            max_retries=config.max_retries,
            retry_backoff_base=config.retry_backoff_base,
            retry_policy=policy_from_values(
                "FAST_READ",
                max_attempts=config.max_retries,
                base_backoff_seconds=config.retry_backoff_base,
            ),
            chain_id=config.chainid,
        )
        self._active = config
        self._chain_id = None  # Reset cache

        # Verify connection and cache chain_id
        try:
            self._chain_id = self._rpc.get_chain_id()
        except (RPCError, OSError, ValueError) as e:
            self._cleanup_on_failure()
            raise ConnectionError(f"Failed to connect to {network_id}: {e}")

        # Update config chainid if not set
        if config.chainid is None:
            config.chainid = self._chain_id

    def _cleanup_on_failure(self) -> None:
        """Clean up state after connection failure."""
        if self._rpc_process:
            self._rpc_process.terminate()
            self._rpc_process = None
        self._rpc = None
        self._active = None
        self._chain_id = None

    def _resolve_fork(
        self,
        config: NetworkConfig,
        networks: dict[str, NetworkConfig],
    ) -> None:
        """Resolve fork reference to actual URL at connect time.

        Only inherits chain_id/explorer/multicall2 from forked network if not
        explicitly set on the dev config. This allows intentional overrides
        (e.g., testing with a different chain_id).
        """
        fork_ref = config.cmd_settings.get("fork")
        if not fork_ref:
            return

        # If fork is a network ID, resolve to URL (uses first endpoint from list)
        if fork_ref in networks:
            live = networks[fork_ref]
            endpoints = live.get_endpoints()
            config.cmd_settings["fork"] = endpoints[0] if endpoints else fork_ref

            # Only inherit properties if not explicitly set on dev config
            if config.chainid is None:
                config.chainid = live.chainid
            if config.explorer is None:
                config.explorer = live.explorer
            if config.multicall2 is None:
                config.multicall2 = live.multicall2

            # Set chain_id in cmd_settings for Anvil (only if not already set)
            if "chain_id" not in config.cmd_settings and config.chainid:
                config.cmd_settings["chain_id"] = config.chainid

    def disconnect(self, kill_rpc: bool = True) -> None:
        """Disconnect from the current network.

        Args:
            kill_rpc: If True (default), terminate any RPC process we started.
                     Safe to call even if process already died.
        """
        if not self._active:
            raise ConnectionError("Not connected to any network")

        if kill_rpc and self._rpc_process:
            # Safe termination - handles already-dead processes
            if self._rpc_process.poll() is None:
                self._rpc_process.terminate()
                try:
                    self._rpc_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._rpc_process.kill()
                    self._rpc_process.wait(timeout=1)

            # Clean up PID file
            if self._rpc_process_network_id:
                self._remove_pidfile(self._rpc_process_network_id)
                self._rpc_process_network_id = None

            self._rpc_process = None

        self._rpc = None
        self._active = None
        self._chain_id = None

    def _launch_rpc(self, config: NetworkConfig) -> None:
        """Launch RPC process for development network.

        Writes PID file to ~/.brawny/pids/{network_id}.json for debugging.
        """
        import socket

        if config.cmd is None:
            raise RuntimeError(f"Network '{config.id}' has no cmd configured")

        # Check if port is available
        port = config.cmd_settings.get("port", 8545)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(
                    f"Port {port} already in use. "
                    f"Use a different port in cmd_settings or stop the existing process."
                )

        # Check if command exists
        cmd_name = config.cmd.split()[0]
        if not shutil.which(cmd_name):
            raise RuntimeError(f"RPC command '{cmd_name}' not found. Install it first.")

        # Build command as list (avoids shell=True security issues)
        cmd_parts = self._build_rpc_command(config)

        # Platform-specific process group handling
        kwargs: dict[str, object] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if sys.platform != "win32":
            kwargs["start_new_session"] = True  # Unix: create new process group

        self._rpc_process = subprocess.Popen(cmd_parts, **kwargs)
        self._rpc_process_network_id = config.id

        # Write PID file for debugging
        self._write_pidfile(config.id, self._rpc_process.pid, port)

    def _build_rpc_command(self, config: NetworkConfig) -> list[str]:
        """Build command list for RPC process."""
        if config.cmd is None:
            raise RuntimeError(f"Network '{config.id}' has no cmd configured")

        # Split base command (handles "npx hardhat node" etc.)
        cmd_parts = config.cmd.split()
        settings = config.cmd_settings

        if "anvil" in config.cmd.lower():
            if "port" in settings:
                cmd_parts.extend(["--port", str(settings["port"])])
            if "fork" in settings:
                # Use _expand_env_var for consistency with config loading
                from brawny.networks.config import _expand_env_var
                fork_url = _expand_env_var(str(settings["fork"]), network_id=config.id)
                if fork_url:
                    cmd_parts.extend(["--fork-url", fork_url])
            if "fork_block" in settings:
                cmd_parts.extend(["--fork-block-number", str(settings["fork_block"])])
            if "accounts" in settings:
                cmd_parts.extend(["--accounts", str(settings["accounts"])])
            if "balance" in settings:
                cmd_parts.extend(["--balance", str(settings["balance"])])
            if "chain_id" in settings:
                cmd_parts.extend(["--chain-id", str(settings["chain_id"])])

        elif "ganache" in config.cmd.lower():
            if "port" in settings:
                cmd_parts.extend(["--port", str(settings["port"])])
            if "fork" in settings:
                from brawny.networks.config import _expand_env_var
                fork_url = _expand_env_var(str(settings["fork"]), network_id=config.id)
                if fork_url:
                    cmd_parts.extend(["--fork", fork_url])
            if "accounts" in settings:
                cmd_parts.extend(["--accounts", str(settings["accounts"])])
            if "chain_id" in settings:
                cmd_parts.extend(["--chainId", str(settings["chain_id"])])

        return cmd_parts

    def _wait_for_rpc(self, host: str, timeout: int = 30) -> None:
        """Wait for RPC to become responsive.

        Uses httpx for consistency with existing console.py implementation.
        """
        import httpx

        start = time.time()
        while time.time() - start < timeout:
            # Check if process died
            if self._rpc_process and self._rpc_process.poll() is not None:
                raise RuntimeError("RPC process exited unexpectedly")

            try:
                resp = httpx.post(
                    host,
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_blockNumber",
                        "params": [],
                        "id": 1,
                    },
                    timeout=2.0,
                )
                if resp.status_code == 200:
                    return
            except httpx.RequestError:
                pass
            time.sleep(0.3)

        raise TimeoutError(f"RPC at {host} not responding after {timeout}s")

    def list_networks(self) -> dict[str, list[str]]:
        """List all available networks grouped by type."""
        networks = self._ensure_networks()
        return {
            "live": [n.id for n in networks.values() if not n.is_development],
            "development": [n.id for n in networks.values() if n.is_development],
        }

    @property
    def rpc(self) -> ReadClient | None:
        """Get underlying read client."""
        return self._rpc


# Global singleton
_manager: NetworkManager | None = None


def _get_manager() -> NetworkManager:
    """Get or create network manager singleton."""
    global _manager
    if _manager is None:
        _manager = NetworkManager()
    return _manager


__all__ = ["NetworkManager", "_get_manager"]
