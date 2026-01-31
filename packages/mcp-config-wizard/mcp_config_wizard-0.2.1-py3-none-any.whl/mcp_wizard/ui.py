"""Rich UI components for MCP Config Wizard."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

console = Console()


def print_banner() -> None:
    """Print the welcome banner with enhanced modern styling."""
    banner_text = Text()
    banner_text.append("🧙✨ ", style="bold")
    banner_text.append("MCP Config Wizard", style="bold bright_cyan")
    banner_text.append(" ✨🧙\n\n", style="bold")
    banner_text.append("Beautifully configure MCP servers • Dual-scope support • 20+ clients\n", style="dim white")
    banner_text.append("Global & Project-level • Auto-publishing • Beautiful Interactive CLI", style="dim bright_cyan")
    
    panel = Panel(
        Align.center(banner_text),
        border_style="bright_cyan",
        padding=(1, 3),
        expand=False,
    )
    console.print(panel)
    console.print()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_server_table(servers: dict[str, Any]) -> None:
    """Print a table of configured servers."""
    if not servers:
        print_warning("No MCP servers configured.")
        return

    table = Table(
        title="Configured MCP Servers",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )

    table.add_column("Name", style="green", no_wrap=True)
    table.add_column("Transport", style="yellow")
    table.add_column("Details", style="dim")

    for name, config in servers.items():
        transport = get_transport_type(config)
        details = get_server_details(config)
        table.add_row(name, transport, details)

    console.print(table)


def get_transport_type(config: dict[str, Any]) -> str:
    """Determine the transport type from server config."""
    if "url" in config:
        return "http/sse"
    elif "command" in config:
        return "stdio"
    return "unknown"


def get_server_details(config: dict[str, Any]) -> str:
    """Get a brief description of server config."""
    if "url" in config:
        return config["url"][:50] + "..." if len(config.get("url", "")) > 50 else config.get("url", "")
    elif "command" in config:
        cmd = config.get("command", "")
        args = config.get("args", [])
        if args:
            # Show command and first meaningful arg
            arg_str = " ".join(args[:2])
            if len(arg_str) > 40:
                arg_str = arg_str[:40] + "..."
            return f"{cmd} {arg_str}"
        return cmd
    return ""


def print_server_details(name: str, config: dict[str, Any]) -> None:
    """Print detailed information about a server."""
    console.print(f"\n[bold cyan]Server:[/bold cyan] {name}")
    console.print(f"[bold]Transport:[/bold] {get_transport_type(config)}")

    if "command" in config:
        console.print(f"[bold]Command:[/bold] {config['command']}")
        if "args" in config:
            console.print(f"[bold]Args:[/bold] {' '.join(config['args'])}")
        if "env" in config:
            console.print("[bold]Environment:[/bold]")
            for key, value in config["env"].items():
                # Mask sensitive values
                masked = mask_sensitive(key, value)
                console.print(f"  {key}={masked}")

    if "url" in config:
        console.print(f"[bold]URL:[/bold] {config['url']}")
        if "headers" in config:
            console.print("[bold]Headers:[/bold]")
            for key, value in config["headers"].items():
                masked = mask_sensitive(key, value)
                console.print(f"  {key}: {masked}")


def mask_sensitive(key: str, value: str) -> str:
    """Mask sensitive values like API keys."""
    sensitive_keywords = ["key", "token", "secret", "password", "auth", "credential"]
    key_lower = key.lower()

    if any(kw in key_lower for kw in sensitive_keywords):
        if len(value) > 8:
            return value[:4] + "*" * (len(value) - 8) + value[-4:]
        return "*" * len(value)
    return value


def print_config_preview(config: dict[str, Any]) -> None:
    """Print a preview of the configuration to be saved."""
    import json

    console.print("\n[bold cyan]Configuration Preview:[/bold cyan]")
    console.print_json(json.dumps(config, indent=2))


def print_divider() -> None:
    """Print a visual divider."""
    console.print("─" * 50, style="dim")


def confirm_action(message: str) -> None:
    """Print a confirmation message before action."""
    console.print(f"\n[bold]{message}[/bold]")
