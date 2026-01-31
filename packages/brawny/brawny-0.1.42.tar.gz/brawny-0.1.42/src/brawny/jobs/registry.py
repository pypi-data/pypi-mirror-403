"""Job registry for brawny.

Provides job registration and the @job decorator.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable, TypeVar, overload

from brawny.logging import get_logger


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _humanize_class_name(name: str) -> str:
    """Convert CamelCase to human-readable."""
    return re.sub('([a-z])([A-Z])', r'\1 \2', name)


if TYPE_CHECKING:
    from brawny.jobs.base import Job

T = TypeVar("T", bound="Job")

logger = get_logger(__name__)


class JobRegistry:
    """Registry for managing job instances.

    Jobs can be registered via:
    - @brawny.job decorator
    - Explicit registry.register(job) call
    - Module discovery via config
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._job_classes: dict[str, type[Job]] = {}

    def register(self, job_or_class: Job | type[Job]) -> Job | type[Job]:
        """Register a job instance or class.

        Typically called internally by @job decorator. Can also be called directly:
            registry.register(MyJob())

        Args:
            job_or_class: Job instance or class to register

        Returns:
            The registered job/class (for decorator usage)

        Raises:
            ValueError: If duplicate job_id
        """
        if isinstance(job_or_class, type):
            job_class = job_or_class
            job = job_class()
        else:
            job = job_or_class
            job_class = type(job)

        # Auto-derive job_id and name if not explicitly set
        if not getattr(job, "job_id", None):
            job.job_id = _camel_to_snake(job_class.__name__)
        if not getattr(job, "name", None):
            job.name = _humanize_class_name(job_class.__name__)

        job_id = job.job_id

        if job_id in self._jobs:
            existing = self._jobs[job_id]
            raise ValueError(f"Duplicate job_id '{job_id}': already registered by {type(existing).__name__}")

        self._jobs[job_id] = job
        self._job_classes[job_id] = job_class
        logger.debug("job.registry.registered", job_id=job_id, job_class=job_class.__name__)

        return job_or_class

    def unregister(self, job_id: str) -> bool:
        """Unregister a job by ID.

        Args:
            job_id: Job ID to unregister

        Returns:
            True if job was unregistered, False if not found
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            del self._job_classes[job_id]
            logger.debug("job.registry.unregistered", job_id=job_id)
            return True
        return False

    def get(self, job_id: str) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: Job ID to retrieve

        Returns:
            Job instance or None if not found
        """
        return self._jobs.get(job_id)

    def get_all(self) -> list[Job]:
        """Get all registered jobs ordered by job_id.

        Returns:
            List of job instances
        """
        return [self._jobs[jid] for jid in sorted(self._jobs.keys())]

    def list_job_ids(self) -> list[str]:
        """List all registered job IDs.

        Returns:
            List of job IDs
        """
        return sorted(self._jobs.keys())

    def __len__(self) -> int:
        """Return number of registered jobs."""
        return len(self._jobs)

    def __contains__(self, job_id: str) -> bool:
        """Check if a job ID is registered."""
        return job_id in self._jobs

    def __iter__(self):
        """Iterate over registered jobs in job_id order."""
        return iter(self.get_all())

    def clear(self) -> None:
        """Clear all registered jobs."""
        self._jobs.clear()
        self._job_classes.clear()


# Global registry instance
registry = JobRegistry()


def get_registry() -> JobRegistry:
    """Return the global job registry."""
    return registry


@overload
def job(cls: type[T]) -> type[T]: ...


@overload
def job(
    cls: None = None,
    *,
    job_id: str | None = None,
    rpc_group: str | None = None,
    read_group: str | None = None,
    broadcast_group: str | None = None,
    signer: str | None = None,
    alert_to: str | list[str] | None = None,
) -> Callable[[type[T]], type[T]]: ...


def job(
    cls: type[T] | None = None,
    *,
    job_id: str | None = None,
    rpc_group: str | None = None,
    read_group: str | None = None,
    broadcast_group: str | None = None,
    signer: str | None = None,
    alert_to: str | list[str] | None = None,
) -> type[T] | Callable[[type[T]], type[T]]:
    """Register a job class with optional RPC routing configuration.

    Works with or without parentheses:
        @job                    # Simple registration (defaults)
        @job()                  # Same as above
        @job(job_id="my_job")   # Custom job ID
        @job(signer="hot1", rpc_group="private")  # Full config
        @job(alert_to="dev")    # Send alerts to "dev" chat

    Args:
        cls: The job class (auto-passed when used without parentheses)
        job_id: Job identifier (defaults to snake_case of class name, or cls.job_id if set)
        rpc_group: RPC group for both read and broadcast routing
        read_group: RPC group for read operations (default: resolved at runtime)
        broadcast_group: RPC group for broadcasts (default: resolved at runtime)
        signer: Signer key name from config (required for tx jobs)
        alert_to: Telegram chat name(s) for alerts (overrides config.telegram.default).
                  Can be a single name or list of names. Names must be defined in config.

    Raises:
        TypeError: If decorator is misused (e.g., @job("string"))
        ValueError: If job_id is already registered
    """
    def _validate_str(name: str, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise TypeError(f"{name} must be a non-empty string")

    def _configure_and_register(job_cls: type[T]) -> type[T]:
        if not isinstance(job_cls, type):
            raise TypeError("@job must decorate a class")

        # Resolve job_id: explicit param > class attr > derive from name
        if job_id is not None:
            _validate_str("job_id", job_id)
            resolved_job_id = job_id
        else:
            existing = getattr(job_cls, "job_id", None)
            if isinstance(existing, str) and existing.strip():
                resolved_job_id = existing
            else:
                resolved_job_id = _camel_to_snake(job_cls.__name__)

        # Validate routing config
        if rpc_group is not None and (read_group is not None or broadcast_group is not None):
            raise TypeError("rpc_group cannot be combined with read_group/broadcast_group")

        if rpc_group is not None:
            _validate_str("rpc_group", rpc_group)
            resolved_read_group = rpc_group
            resolved_broadcast_group = rpc_group
        else:
            resolved_read_group = read_group
            resolved_broadcast_group = broadcast_group
            if resolved_read_group is not None:
                _validate_str("read_group", resolved_read_group)
            if resolved_broadcast_group is not None:
                _validate_str("broadcast_group", resolved_broadcast_group)

        if signer is not None:
            _validate_str("signer", signer)

        # Check for duplicate registration
        if resolved_job_id in registry._jobs:
            raise ValueError(f"Job '{resolved_job_id}' already registered")

        # Normalize alert_to to list | None (dedupe while preserving order)
        # Empty list [] or whitespace normalizes to None, not []
        resolved_alert_to: list[str] | None = None
        if alert_to is not None:
            if isinstance(alert_to, str):
                resolved_alert_to = [alert_to.strip()] if alert_to.strip() else None
            else:
                # Dedupe while preserving order
                seen: set[str] = set()
                deduped: list[str] = []
                for n in alert_to:
                    if n and n.strip():
                        stripped = n.strip()
                        if stripped not in seen:
                            seen.add(stripped)
                            deduped.append(stripped)
                resolved_alert_to = deduped if deduped else None

        # Attach config to class
        job_cls.job_id = resolved_job_id  # type: ignore[attr-defined]
        job_cls._read_group = resolved_read_group  # type: ignore[attr-defined]
        job_cls._broadcast_group = resolved_broadcast_group  # type: ignore[attr-defined]
        job_cls._signer_name = signer  # type: ignore[attr-defined]
        job_cls._alert_to = resolved_alert_to  # type: ignore[attr-defined]

        # Auto-derive name if not set
        if not getattr(job_cls, "name", None):
            job_cls.name = _humanize_class_name(job_cls.__name__)  # type: ignore[attr-defined]

        registry.register(job_cls)
        return job_cls

    # Detect usage: @job vs @job(...)
    if cls is not None:
        return _configure_and_register(cls)
    return _configure_and_register
