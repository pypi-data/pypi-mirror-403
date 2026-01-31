"""MCP Config Wizard - Easily configure MCP servers through a beautiful interactive CLI."""

__version__ = "0.1.0"
__app_name__ = "mcp-config-wizard"

from .cli import main

__all__ = ["main", "__version__", "__app_name__"]
