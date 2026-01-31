"""Job discovery for brawny.

Provides module and path-based job discovery mechanisms.
"""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

from brawny.logging import get_logger, log_unexpected

logger = get_logger(__name__)


@dataclass(frozen=True)
class JobLoadError:
    """Represents a failure to load a job module."""

    path: str
    message: str  # str(e) for quick scanning
    traceback: str  # full traceback for debugging


class JobDiscoveryFailed(Exception):
    """Raised when one or more job modules fail to load."""

    def __init__(self, errors: list[JobLoadError]) -> None:
        self.errors = errors
        super().__init__(f"Failed to load {len(errors)} job module(s)")


def _import_module_tree(module_path: str) -> list[JobLoadError]:
    """Import a module and all submodules if it's a package.

    Returns:
        List of JobLoadError for any modules that failed to load.
    """
    load_errors: list[JobLoadError] = []

    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        # RECOVERABLE job module load failures should not crash discovery.
        load_errors.append(
            JobLoadError(
                path=module_path,
                message=str(e),
                traceback=traceback.format_exc(),
            )
        )
        log_unexpected(
            logger,
            "job.module_load_failed",
            module=module_path,
            error=str(e),
            error_type=type(e).__name__,
        )
        return load_errors

    # If it's a package, walk submodules recursively.
    if hasattr(module, "__path__"):
        for _, name, _ in pkgutil.walk_packages(module.__path__, module.__name__ + "."):
            if name.split(".")[-1].startswith("_"):
                continue
            try:
                importlib.import_module(name)
            except Exception as e:
                # RECOVERABLE job submodule load failures should not crash discovery.
                load_errors.append(
                    JobLoadError(
                        path=name,
                        message=str(e),
                        traceback=traceback.format_exc(),
                    )
                )
                log_unexpected(
                    logger,
                    "job.module_load_failed",
                    module=name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

    return load_errors


def discover_jobs(module_paths: list[str]) -> tuple[list[str], list[JobLoadError]]:
    """Discover and import job modules.

    Imports the specified modules to trigger @job decorators.

    Args:
        module_paths: List of Python module paths to import

    Returns:
        Tuple of (discovered job IDs, list of JobLoadError for failed modules)
    """
    # Lazy import to avoid circular dependency
    from brawny.jobs.registry import get_registry

    registry = get_registry()
    discovered: list[str] = []
    load_errors: list[JobLoadError] = []

    for module_path in module_paths:
        # Record jobs before import
        before = set(registry.list_job_ids())

        # Import module and any submodules (package tree)
        errors = _import_module_tree(module_path)
        load_errors.extend(errors)

        # Find newly registered jobs
        after = set(registry.list_job_ids())
        new_jobs = after - before

        for job_id in new_jobs:
            discovered.append(job_id)

    return discovered, load_errors


def discover_jobs_from_path(jobs_dir: str | Path) -> tuple[list[str], list[JobLoadError]]:
    """Discover jobs by scanning a directory for Python files.

    Recursively finds all .py files and imports them to trigger @job.
    Does NOT require __init__.py files in subdirectories.

    Args:
        jobs_dir: Path to jobs directory

    Returns:
        Tuple of (discovered job IDs, list of JobLoadError for failed modules)
    """
    # Lazy import to avoid circular dependency
    from brawny.jobs.registry import get_registry

    registry = get_registry()
    jobs_path = Path(jobs_dir).resolve()
    load_errors: list[JobLoadError] = []

    if not jobs_path.is_dir():
        logger.error("job.discovery.not_a_directory", path=str(jobs_path))
        return [], []

    discovered: list[str] = []
    before = set(registry.list_job_ids())

    # Find all .py files recursively
    for py_file in jobs_path.rglob("*.py"):
        # Skip private files and __init__.py
        if py_file.name.startswith("_"):
            continue

        # Skip examples directory (reference code, not to be registered)
        if "examples" in py_file.parts:
            continue

        try:
            # Create a unique module name based on path
            rel_path = py_file.relative_to(jobs_path)
            module_name = f"_jobs_.{rel_path.with_suffix('').as_posix().replace('/', '.')}"

            # Import the file directly
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

        except Exception as e:
            # RECOVERABLE individual job file load failures should not crash discovery.
            load_errors.append(
                JobLoadError(
                    path=str(py_file),
                    message=str(e),
                    traceback=traceback.format_exc(),
                )
            )
            log_unexpected(
                logger,
                "job.module_load_failed",
                file=str(py_file),
                error=str(e),
                error_type=type(e).__name__,
            )

    # Find newly registered jobs
    after = set(registry.list_job_ids())
    new_jobs = after - before

    for job_id in sorted(new_jobs):
        discovered.append(job_id)

    return discovered, load_errors


def auto_discover_jobs() -> tuple[list[str], list[JobLoadError]]:
    """Auto-discover jobs from conventional locations.

    Checks in order:
    1. ./jobs/ directory
    2. ./src/*/jobs/ directories

    This enables zero-config job discovery for projects that follow conventions.

    Returns:
        Tuple of (discovered job IDs, list of JobLoadError for failed modules)
    """
    discovered: list[str] = []
    load_errors: list[JobLoadError] = []
    cwd = Path.cwd()

    # Check ./jobs/
    jobs_dir = cwd / "jobs"
    if jobs_dir.is_dir():
        jobs, errors = discover_jobs_from_path(jobs_dir)
        discovered.extend(jobs)
        load_errors.extend(errors)

    # Check ./src/*/jobs/ (setuptools convention)
    if not discovered:
        src_dir = cwd / "src"
        if src_dir.is_dir():
            for pkg_dir in src_dir.iterdir():
                if pkg_dir.is_dir() and not pkg_dir.name.startswith("_"):
                    pkg_jobs = pkg_dir / "jobs"
                    if pkg_jobs.is_dir():
                        jobs, errors = discover_jobs_from_path(pkg_jobs)
                        discovered.extend(jobs)
                        load_errors.extend(errors)

    return discovered, load_errors
