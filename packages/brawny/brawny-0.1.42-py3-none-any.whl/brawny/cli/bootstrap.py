"""CLI bootstrap utilities."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from .env in the current directory."""
    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
    else:
        load_dotenv()


def configure_bytecode_cache() -> None:
    """
    Prevent __pycache__ from being created in the user's project by redirecting
    pyc writes to a centralized cache directory.

    Must run before importing/loading user job modules.
    """
    # Always disable bytecode writes to avoid __pycache__ in project jobs.
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True

    # If user already set a prefix, respect it.
    if os.environ.get("PYTHONPYCACHEPREFIX"):
        return

    cache_dir = Path.home() / ".cache" / "brawny" / "pycache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PYTHONPYCACHEPREFIX"] = str(cache_dir)
    sys.pycache_prefix = str(cache_dir)
