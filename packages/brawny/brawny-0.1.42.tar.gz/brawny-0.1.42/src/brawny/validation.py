"""Startup validation — static checks only.

This module provides validation functions for job routing configuration.
These are run at startup to catch misconfigurations early.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brawny.config.routing import resolve_job_groups

if TYPE_CHECKING:
    from brawny.config import Config
    from brawny.jobs.base import Job


def validate_job_routing(
    config: "Config",
    job_classes: dict[str, "Job"],
) -> list[str]:
    """Validate job routing configuration. Returns list of errors.

    Checks:
    - Validate read_group/broadcast_group exist in rpc_groups

    Note: Signer validation is handled separately by validate_job() in registry.py
    which checks against the actual keystore (not config.signers).

    Does NOT:
    - Make RPC calls (no probes)
    - Validate runtime behavior

    Args:
        config: Application configuration
        job_classes: Dict of job_id -> Job instance

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []

    for job_id, job_cls in job_classes.items():
        try:
            resolve_job_groups(config, job_cls)
        except ValueError as exc:
            errors.append(f"Job '{job_id}': {exc}")

    return errors


def validate_startup(config: "Config", job_classes: dict[str, "Job"]) -> None:
    """Validate at startup. Raises on error.

    This function should be called during application startup after
    config and jobs are loaded.

    Args:
        config: Application configuration
        job_classes: Dict of job_id -> Job instance

    Raises:
        ValueError: If validation fails with list of errors
    """
    errors = validate_job_routing(config, job_classes)
    if errors:
        raise ValueError(
            "Startup validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
