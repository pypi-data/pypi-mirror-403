"""Project initialization command."""

from __future__ import annotations

from pathlib import Path

import click

from brawny.cli.helpers import (
    _check_directory_empty,
    _write_agents,
    _print_success,
    _validate_project_name,
    _write_config,
    _write_env_example,
    _write_examples,
    _write_gitignore,
    _write_monitoring,
    _write_pyproject,
)


@click.command()
@click.argument("project_name", required=False, default=None)
@click.option("--force", "-f", is_flag=True, help="Initialize even if directory is not empty")
def init(project_name: str | None, force: bool) -> None:
    """Initialize a new brawny project in the current directory.

    PROJECT_NAME defaults to the current directory name if not provided.

    Examples:

        brawny init              # Use current directory name

        brawny init my_keeper    # Use 'my_keeper' as project name

        brawny init -f           # Force init in non-empty directory
    """
    project_dir = Path.cwd()

    if project_name is None:
        project_name = project_dir.name

    _validate_project_name(project_name)  # Validates name is usable

    if not force:
        _check_directory_empty(project_dir)

    try:
        # Normalize project name to valid Python package name
        package_name = project_name.lower().replace("-", "_").replace(" ", "_")

        # Create package_name, jobs, interfaces, and data structure
        package_dir = project_dir / package_name
        jobs_dir = project_dir / "jobs"
        interfaces_dir = project_dir / "interfaces"
        data_dir = project_dir / "data"
        package_dir.mkdir(parents=True, exist_ok=True)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        interfaces_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        (package_dir / "__init__.py").touch()
        (jobs_dir / "__init__.py").write_text(
            '"""Job definitions - auto-discovered from ./jobs."""\n'
        )

        _write_pyproject(project_dir, project_name, package_name)
        _write_config(project_dir, package_name)
        _write_env_example(project_dir)
        _write_agents(project_dir)
        _write_gitignore(project_dir)
        _write_examples(jobs_dir / "_examples.py")
        _write_monitoring(project_dir)

    except click.ClickException:
        raise
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc

    _print_success(project_name, package_name)


def register(main) -> None:
    main.add_command(init)
