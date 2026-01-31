"""Brownie-compatible network module.

Usage:
    from brawny import network

    network.connect("mainnet")
    network.disconnect()
    network.show_active()
    network.is_connected
    network.chain_id

NOTE: This is the Brownie-compatible network module that reads from
~/.brawny/network-config.yaml. Project-level config.yaml network sections
are no longer supported.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brawny.networks.manager import _get_manager

if TYPE_CHECKING:
    from brawny._rpc.clients import ReadClient


class _NetworkProxy:
    """Proxy providing attribute access to NetworkManager singleton.

    Uses __getattr__ for cleaner forwarding of methods/properties.
    """

    def connect(self, network_id: str | None = None, launch_rpc: bool = True) -> None:
        """Connect to a network."""
        _get_manager().connect(network_id, launch_rpc)

    def disconnect(self, kill_rpc: bool = True) -> None:
        """Disconnect from current network."""
        _get_manager().disconnect(kill_rpc)

    def show_active(self) -> str | None:
        """Get ID of active network."""
        return _get_manager().show_active()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return _get_manager().is_connected

    @property
    def chain_id(self) -> int | None:
        """Get current chain ID."""
        return _get_manager().chain_id

    def list_networks(self) -> dict[str, list[str]]:
        """List all available networks."""
        return _get_manager().list_networks()

    @property
    def rpc(self) -> ReadClient | None:
        """Get underlying read client."""
        return _get_manager().rpc

    def rpc_required(self) -> ReadClient:
        """Get read client, raising error if not connected.

        Use this instead of checking `if network.rpc is None` everywhere.

        Raises:
            ConnectionError: If not connected to any network

        Example:
            rpc = network.rpc_required()  # Raises if not connected
            block = rpc.get_block_number()
        """
        rpc = _get_manager().rpc
        if rpc is None:
            raise ConnectionError(
                "Not connected to any network. "
                "Call network.connect() first."
            )
        return rpc

    def __repr__(self) -> str:
        active = self.show_active()
        if active:
            return f"<Network '{active}' (chain_id={self.chain_id})>"
        return "<Network (not connected)>"


network = _NetworkProxy()

# Also export config types for advanced usage
from brawny.networks.config import EnvVarExpansionError, NetworkConfig, load_networks

__all__ = ["network", "NetworkConfig", "load_networks", "EnvVarExpansionError"]
