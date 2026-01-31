"""RPC client management — shared by TxExecutor and JobRunner.

This module provides caching for read RPC clients by group.
Broadcast clients are created per-call from endpoint snapshots (see broadcast.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brawny._rpc.client import ReadClient, BroadcastClient

if TYPE_CHECKING:
    from brawny.config import Config



class RPCClients:
    """Manages RPC clients for read operations.

    Caches read clients by group. Broadcast clients are created per-call
    from endpoint snapshots (see broadcast.py).

    Example:
        clients = RPCClients(config)

        # Get cached read client for a group
        public_rpc = clients.get_read_client("public")
        private_rpc = clients.get_read_client("private")

        # Same group = same cached client
        assert clients.get_read_client("public") is public_rpc
    """

    def __init__(self, config: "Config") -> None:
        """Initialize RPC clients manager.

        Args:
            config: Application configuration
        """
        self._config = config
        self._read_clients: dict[str, ReadClient] = {}

    def get_read_client(self, group_name: str) -> ReadClient:
        """Get (cached) read client for a group.

        If the group's client hasn't been created yet, creates it.
        Subsequent calls return the same cached instance.

        Args:
            group_name: Name of the RPC group (e.g., "public", "private")

        Returns:
            ReadClient configured for the group's endpoints

        Raises:
            ValueError: If group not found in config.rpc_groups
        """
        if group_name not in self._read_clients:
            from brawny._rpc.retry_policy import fast_read_policy

            if group_name not in self._config.rpc_groups:
                raise ValueError(f"RPC group '{group_name}' not found")

            group = self._config.rpc_groups[group_name]
            self._read_clients[group_name] = ReadClient(
                endpoints=group.endpoints,
                timeout_seconds=self._config.rpc_timeout_seconds,
                max_retries=self._config.rpc_max_retries,
                retry_backoff_base=self._config.rpc_retry_backoff_base,
                retry_policy=fast_read_policy(self._config),
                chain_id=self._config.chain_id,
                log_init=False,  # Daemon already logged main RPC init
            )

        return self._read_clients[group_name]

    def get_default_client(self) -> ReadClient:
        """Get the default read client.

        Uses rpc.defaults.read for the default client.

        Returns:
            ReadClient for the default group

        Raises:
            ValueError: If default group cannot be resolved
        """
        from brawny.config.routing import resolve_default_read_group

        return self.get_read_client(resolve_default_read_group(self._config))

    def clear_cache(self) -> None:
        """Clear all cached clients.

        Useful for testing or when config changes require new clients.
        """
        self._read_clients.clear()
