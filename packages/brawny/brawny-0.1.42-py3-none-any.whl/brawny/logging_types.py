"""Logging-specific enums.

Kept separate to avoid circular imports during logger setup.
"""

from enum import Enum


class LogFormat(str, Enum):
    """Log output format."""

    JSON = "json"
    TEXT = "text"
