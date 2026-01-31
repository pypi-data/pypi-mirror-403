"""Shared helpers for CLI commands."""

from __future__ import annotations

import json
import keyword
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import click


def suppress_logging() -> None:
    """Suppress all logging output for CLI commands.

    Must be called BEFORE importing any brawny modules that use logging.
    """
    # Suppress stdlib logging
    logging.disable(logging.CRITICAL)

    # Configure structlog to drop all messages
    import structlog

    structlog.configure(
        processors=[structlog.dev.ConsoleRenderer()],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,  # Don't cache so we can reconfigure later
    )


def get_config(config_path: str | None = None):
    """Get config, applying env overrides.

    Args:
        config_path: Path to config.yaml. If None, uses default lookup.
    """
    from brawny.config import Config
    from brawny.config import get_config as _get_config

    if config_path:
        config = Config.from_yaml(config_path)
        config, _ = config.apply_env_overrides()
    else:
        config = _get_config()

    return config


def get_db(config_path: str | None = None):
    """Get database connection from config.

    Args:
        config_path: Path to config.yaml. If None, uses get_config() default.
    """
    from brawny.db import create_database

    config = get_config(config_path)

    db = create_database(
        config.database_url,
        circuit_breaker_failures=config.db_circuit_breaker_failures,
        circuit_breaker_seconds=config.db_circuit_breaker_seconds,
        production=config.production,
    )
    db.connect()
    return db


def get_db_readonly(config_path: str | None = None):
    """Get read-only database connection from config.

    Args:
        config_path: Path to config.yaml. If None, uses get_config() default.
    """
    from brawny.db import create_database

    config = get_config(config_path)

    db = create_database(
        config.database_url,
        circuit_breaker_failures=config.db_circuit_breaker_failures,
        circuit_breaker_seconds=config.db_circuit_breaker_seconds,
        production=config.production,
        read_only=True,
    )
    db.connect()
    return db


def discover_jobs_for_cli(config, extra_modules: tuple[str, ...] = ()):
    """Discover jobs using same logic as brawny start.

    Priority: CLI modules > auto-discovery

    Note: Call suppress_logging() BEFORE this function if you want silent discovery.

    Args:
        config: Config instance
        extra_modules: Additional modules from CLI flags
    """
    from brawny.jobs.discovery import auto_discover_jobs, discover_jobs

    if extra_modules:
        discover_jobs(list(extra_modules))
    else:
        auto_discover_jobs()


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    click.echo(json.dumps(data, indent=2, default=str))


def _validate_project_name(name: str) -> str:
    """Validate and normalize project name."""
    if not name or not name.strip():
        raise click.ClickException("Project name cannot be empty")

    stripped = name.strip()
    if len(stripped) > 100:
        raise click.ClickException("Project name must be 100 characters or less")
    if not stripped[0].isalpha():
        raise click.ClickException("Project name must start with a letter")
    if not re.match(r"^[A-Za-z0-9_-]+$", stripped):
        raise click.ClickException(
            "Project name contains invalid characters. Use only letters, numbers, hyphens, and underscores."
        )

    package_name = stripped.lower().replace("-", "_")
    if keyword.iskeyword(package_name):
        raise click.ClickException(f"Project name '{name}' is a Python keyword")

    stdlib_names = getattr(sys, "stdlib_module_names", set())
    if package_name in stdlib_names:
        raise click.ClickException(
            f"Project name '{name}' conflicts with Python standard library"
        )

    return package_name


def _check_directory_empty(project_dir: Path) -> None:
    """Verify target directory is empty (or has only ignorable files)."""
    if not project_dir.exists():
        raise click.ClickException(f"Directory {project_dir} does not exist")

    if not project_dir.is_dir():
        raise click.ClickException(f"{project_dir} is not a directory")

    if not os.access(project_dir, os.W_OK):
        raise click.ClickException(f"Cannot write to {project_dir}: permission denied")

    ignorable = {
        ".git", ".gitignore", "README.md", "LICENSE", ".DS_Store",
        "venv", ".venv", "env", ".env",
        ".idea", ".vscode",
    }
    existing = set(p.name for p in project_dir.iterdir())
    non_ignorable = existing - ignorable

    if non_ignorable:
        raise click.ClickException(
            f"Directory is not empty. Found: {', '.join(sorted(non_ignorable))}\n"
            "Run 'brawny init' in an empty directory."
        )


def _write_file(path: Path, content: str) -> None:
    """Write content to file, creating parent directories if needed."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Failed to create {path}: {exc}") from exc


def _write_pyproject(project_dir: Path, project_name: str, package_name: str) -> None:
    from brawny.cli_templates import PYPROJECT_TEMPLATE

    content = PYPROJECT_TEMPLATE.format(
        project_name=project_name,
        package_name=package_name,
    )
    _write_file(project_dir / "pyproject.toml", content)


def _write_config(project_dir: Path, package_name: str) -> None:
    from brawny.cli_templates import CONFIG_TEMPLATE

    content = CONFIG_TEMPLATE.format(package_name=package_name)
    _write_file(project_dir / "config.yaml", content)


def _write_env_example(project_dir: Path) -> None:
    from brawny.cli_templates import ENV_EXAMPLE_TEMPLATE

    _write_file(project_dir / ".env.example", ENV_EXAMPLE_TEMPLATE)

def _write_agents(project_dir: Path) -> None:
    from brawny.cli_templates import AGENTS_TEMPLATE

    _write_file(project_dir / "AGENTS.md", AGENTS_TEMPLATE)


def _write_gitignore(project_dir: Path) -> None:
    from brawny.cli_templates import GITIGNORE_TEMPLATE

    _write_file(project_dir / ".gitignore", GITIGNORE_TEMPLATE)


def _write_jobs_init(jobs_dir: Path) -> None:
    from brawny.cli_templates import INIT_JOBS_TEMPLATE

    _write_file(jobs_dir / "__init__.py", INIT_JOBS_TEMPLATE)


def _write_examples(path: Path) -> None:
    from brawny.cli_templates import EXAMPLES_TEMPLATE

    _write_file(path, EXAMPLES_TEMPLATE)


def _write_monitoring(project_dir: Path) -> None:
    from brawny.cli_templates import (
        DOCKER_COMPOSE_MONITORING_TEMPLATE,
        PROMETHEUS_CONFIG_TEMPLATE,
        GRAFANA_DATASOURCE_TEMPLATE,
        GRAFANA_DASHBOARDS_PROVIDER_TEMPLATE,
        GRAFANA_DASHBOARD_TEMPLATE,
    )

    monitoring_dir = project_dir / "monitoring"
    _write_file(monitoring_dir / "docker-compose.yml", DOCKER_COMPOSE_MONITORING_TEMPLATE)
    _write_file(monitoring_dir / "prometheus.yml", PROMETHEUS_CONFIG_TEMPLATE)
    _write_file(
        monitoring_dir / "grafana" / "provisioning" / "datasources" / "datasource.yml",
        GRAFANA_DATASOURCE_TEMPLATE,
    )
    _write_file(
        monitoring_dir / "grafana" / "provisioning" / "dashboards" / "dashboards.yml",
        GRAFANA_DASHBOARDS_PROVIDER_TEMPLATE,
    )
    _write_file(
        monitoring_dir / "grafana" / "provisioning" / "dashboards" / "brawny-overview.json",
        GRAFANA_DASHBOARD_TEMPLATE,
    )


def _print_success(project_name: str, package_name: str) -> None:
    """Print success message with next steps."""
    click.echo()
    click.echo(click.style(f"Initialized {project_name}", fg="green", bold=True))
    click.echo()
    click.echo("Project structure:")
    click.echo("  .")
    click.echo("  ├── pyproject.toml")
    click.echo("  ├── config.yaml")
    click.echo("  ├── .env.example")
    click.echo("  ├── .gitignore")
    click.echo(f"  ├── {package_name}/")
    click.echo("  │   └── __init__.py")
    click.echo("  ├── jobs/")
    click.echo("  │   ├── __init__.py")
    click.echo("  │   └── _examples.py")
    click.echo("  ├── interfaces/")
    click.echo("  ├── data/              # SQLite database")
    click.echo("  └── monitoring/        # Prometheus + Grafana")
    click.echo()
    click.echo("Next steps:")
    click.echo(click.style("  pip install -e .", fg="cyan"))
    click.echo(click.style("  cp .env.example .env", fg="cyan"))
    click.echo("  # Edit .env with your RPC URL and signer keys")
    click.echo(click.style("  brawny run", fg="cyan"))
    click.echo()
    click.echo("To create your first job:")
    click.echo("  1. Copy a class from jobs/_examples.py")
    click.echo("  2. Create a new file in jobs/")
    click.echo("  3. Add @job decorator and customize")
