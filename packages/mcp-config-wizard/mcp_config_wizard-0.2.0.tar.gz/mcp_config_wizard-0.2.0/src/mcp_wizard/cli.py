"""CLI entry point for MCP Config Wizard."""

from __future__ import annotations

import sys


def main() -> int:
    """Main entry point for the CLI."""
    try:
        from .wizard import run_wizard

        run_wizard()
        return 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


def version() -> None:
    """Print version information."""
    from . import __app_name__, __version__

    print(f"{__app_name__} {__version__}")


if __name__ == "__main__":
    sys.exit(main())
