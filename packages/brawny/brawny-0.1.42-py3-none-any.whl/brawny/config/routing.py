"""RPC group routing helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.jobs.base import Job


def resolve_default_read_group(config: "Config") -> str:
    """Resolve the default read RPC group."""
    if not config.rpc_groups:
        raise ValueError("rpc_groups not configured; set rpc.groups and rpc.defaults")
    if not config.rpc_defaults:
        raise ValueError("rpc.defaults not configured; set rpc.defaults.read")
    return config.rpc_defaults.read


def resolve_default_broadcast_group(config: "Config") -> str:
    """Resolve the default broadcast RPC group."""
    if not config.rpc_groups:
        raise ValueError("rpc_groups not configured; set rpc.groups and rpc.defaults")
    if not config.rpc_defaults:
        raise ValueError("rpc.defaults not configured; set rpc.defaults.broadcast")
    return config.rpc_defaults.broadcast


def resolve_job_groups(config: "Config", job: "Job") -> tuple[str, str]:
    """Resolve read/broadcast groups for a job.

    Returns:
        (read_group, broadcast_group)
    """
    read_group = getattr(job, "_read_group", None)
    broadcast_group = getattr(job, "_broadcast_group", None)

    if not config.rpc_groups:
        raise ValueError("rpc_groups not configured; set rpc.groups and rpc.defaults")

    if read_group is None:
        read_group = resolve_default_read_group(config)
    if broadcast_group is None:
        broadcast_group = resolve_default_broadcast_group(config)

    if read_group not in config.rpc_groups:
        raise ValueError(f"read_group '{read_group}' not found in rpc_groups")
    if broadcast_group not in config.rpc_groups:
        raise ValueError(f"broadcast_group '{broadcast_group}' not found in rpc_groups")

    return read_group, broadcast_group
