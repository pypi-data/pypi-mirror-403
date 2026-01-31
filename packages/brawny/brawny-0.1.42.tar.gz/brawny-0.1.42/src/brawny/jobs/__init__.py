"""Job framework with base class, registry, and discovery."""

from brawny.jobs.base import Job, TxInfo, TxReceipt, BlockInfo
from brawny.jobs.registry import job, registry, get_registry, JobRegistry
from brawny.jobs.discovery import discover_jobs, discover_jobs_from_path, auto_discover_jobs
from brawny.jobs.job_validation import validate_job, validate_all_jobs

__all__ = [
    # Base classes
    "Job",
    "TxInfo",
    "TxReceipt",
    "BlockInfo",
    # Registry
    "job",
    "registry",
    "get_registry",
    "JobRegistry",
    # Discovery
    "discover_jobs",
    "discover_jobs_from_path",
    "auto_discover_jobs",
    # Validation
    "validate_job",
    "validate_all_jobs",
]
