"""Job validation for brawny.

Provides structural validation for job instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brawny.jobs.base import Job
    from brawny.keystore import Keystore


def _is_valid_address(address: str) -> bool:
    """Check if a string looks like a valid Ethereum address.

    Args:
        address: String to validate

    Returns:
        True if valid address format
    """
    if not isinstance(address, str):
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False


def validate_job(job: "Job", keystore: "Keystore | None" = None) -> list[str]:
    """Validate job structure and configuration.

    Checks:
    - Required attributes (job_id, name)
    - Required methods (check)
    - check_interval_blocks is positive
    - Signer exists in keystore (if configured and keystore provided)

    Does NOT:
    - Call check() or build_intent()
    - Make RPC calls
    - Validate runtime behavior

    Args:
        job: Job instance to validate
        keystore: Optional keystore for signer validation

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []

    # Required attributes
    job_id = getattr(job, "job_id", None)
    if not job_id:
        errors.append("missing job_id attribute")

    name = getattr(job, "name", None)
    if not name:
        errors.append("missing name attribute")

    # Required methods
    if not callable(getattr(job, "check", None)):
        errors.append("missing check() method")

    # check_interval_blocks should be positive
    interval = getattr(job, "check_interval_blocks", 1)
    if not isinstance(interval, int) or interval < 1:
        errors.append(f"check_interval_blocks must be positive integer, got {interval}")

    # Signer validation (if keystore available)
    signer = getattr(job, "_signer_name", None)
    if signer and keystore:
        if not keystore.has_key(signer):
            # Show aliases if available (what user can type), else addresses
            available = keystore.list_aliases() or keystore.list_keys()
            if available:
                errors.append(f"signer '{signer}' not found in keystore (available: {', '.join(available)})")
            else:
                errors.append(f"signer '{signer}' not found (keystore is empty)")

    return errors


def validate_all_jobs(
    jobs: dict[str, "Job"],
    keystore: "Keystore | None" = None,
) -> dict[str, list[str]]:
    """Validate all jobs and return errors by job_id.

    Args:
        jobs: Dict of job_id -> Job instance
        keystore: Optional keystore for signer validation

    Returns:
        Dict of job_id -> list of errors (only jobs with errors included)
    """
    all_errors: dict[str, list[str]] = {}

    for job_id, job in jobs.items():
        errors = validate_job(job, keystore)
        if errors:
            all_errors[job_id] = errors

    return all_errors
