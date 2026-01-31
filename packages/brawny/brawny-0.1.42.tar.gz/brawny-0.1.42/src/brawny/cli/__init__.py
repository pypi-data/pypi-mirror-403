"""CLI entrypoint for brawny."""

from __future__ import annotations

from brawny.cli.app import main
from brawny.cli.commands import register_all


register_all(main)


__all__ = ["main"]


if __name__ == "__main__":
    main()
