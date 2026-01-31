"""Startup diagnostic message types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class StartupMessage:
    """Startup diagnostic message for human-readable display.

    Used to collect warnings and errors during startup for display
    before the "--- Starting brawny ---" banner.
    """

    level: Literal["warning", "error"]
    code: str
    message: str
    fix: str | None = None  # Actionable fix suggestion
