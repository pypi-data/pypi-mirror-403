"""Interactive wizard for configuring MCP servers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import questionary
from questionary import Choice, Style

from .config import (
    MCPClient,
    MCPScope,
    add_server,
    detect_installed_clients,
    get_current_directory_config,
    get_clients_by_category,
    get_servers,
    read_config,
    remove_server,
    write_config,
)
from .templates import ServerTemplate, get_all_templates, get_categories, get_template, get_templates_by_category
from .ui import (
    console,
    print_divider,
    print_error,
    print_info,
    print_server_details,
    print_server_table,
    print_success,
    print_warning,
)
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align

# Custom style for questionary
custom_style = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
        ("separator", "fg:gray"),
        ("instruction", "fg:gray"),
    ]
)


def _get_category_color(category: str) -> str:
    """Get a color for a category name."""
    colors = {
        "🤖 AI & Coding": "bright_cyan",
        "📝 Editors & IDEs": "bright_magenta",
        "⌨️ Terminals & CLIs": "bright_yellow",
        "💻 Low-Code/No-Code": "bright_green",
    }
    return colors.get(category, "bright_white")


def select_client() -> tuple[MCPClient, Path] | None:
    """Select an MCP client with beautiful categorized UI using modern styling."""
    clients = detect_installed_clients()

    if not clients:
        print_error("No MCP clients detected. Using custom location.")
        custom_path = questionary.path(
            "Enter config file path:",
            style=custom_style,
        ).ask()
        if not custom_path:
            return None
        return MCPClient(name="custom", display_name="Custom", config_paths=[]), Path(custom_path)

    # Display modern client categories
    console.print()  # Add spacing
    categorized_clients = get_clients_by_category()
    
    # Create a beautiful table showing available clients
    table = Table(
        title="[bold cyan]Available MCP Clients[/bold cyan]",
        border_style="bright_cyan",
        show_header=False,
        padding=(0, 1),
    )
    table.add_column("Status", width=2, style="dim")
    table.add_column("Client", style="bright_white")
    table.add_column("Description", style="dim white")
    
    for category, category_clients in categorized_clients.items():
        # Add category header
        table.add_row("", f"[bold {_get_category_color(category)}]{category}[/bold {_get_category_color(category)}]", "")
        
        for client in category_clients:
            status = "✓" if client.exists() else "◯"
            status_style = "green" if client.exists() else "dim"
            desc = client.description if hasattr(client, 'description') else ""
            table.add_row(f"[{status_style}]{status}[/{status_style}]", f"  {client.emoji} {client.display_name}", desc)
    
    # Add other options
    table.add_row("", "[bold bright_black]Other Options[/bold bright_black]", "")
    table.add_row("[cyan]→[/cyan]", "  🔧 Custom Configuration", "Specify custom config path")
    table.add_row("[cyan]→[/cyan]", "  📂 Current Directory", "Use local MCP config")
    
    console.print(table)
    console.print()  # Add spacing
    
    # Build choices for selection
    choices = [Choice(title="🔧 Custom Configuration", value="custom")]
    
    for category, category_clients in categorized_clients.items():
        for client in category_clients:
            installed_status = "✓" if client.exists() else "○"
            status_text = "" if client.exists() else " (not installed)"
            title = f"  {client.emoji} {client.display_name}{status_text}"
            choices.append(Choice(title=title, value=client))
    
    # Add special options
    choices.append(Choice(title="  📂 Current Directory", value="current_dir"))

    selected = questionary.select(
        "Choose a server template or custom:",
        choices=choices,
        style=custom_style,
    ).ask()

    if selected is None:
        return None

    if selected == "custom":
        custom_path = questionary.path(
            "Enter config file path:",
            style=custom_style,
            only_directories=False,
        ).ask()
        if not custom_path:
            return None
        return MCPClient(
            name="custom", 
            display_name="Custom Configuration", 
            config_paths=[]
        ), Path(custom_path)

    if selected == "current_dir":
        path = get_current_directory_config()
        return MCPClient(name="current", display_name="Current Directory", config_paths=[]), path

    if isinstance(selected, str):
        return None

    # For regular clients, ask about scope if multiple paths available
    scoped_paths = selected.get_all_paths()
    if len(scoped_paths) > 1:
        scope_choices = []
        for config_path in scoped_paths:
            scope_label = "🌍 Global (all projects)" if config_path.scope == MCPScope.GLOBAL else "📂 Project-level (this directory)"
            scope_choices.append(
                Choice(
                    title=f"{scope_label}\n    {config_path.path}",
                    value=config_path
                )
            )
        
        selected_scope = questionary.select(
            "Choose configuration scope:",
            choices=scope_choices,
            style=custom_style,
        ).ask()
        
        if selected_scope is None:
            return None
        
        config_path = selected_scope.path
    else:
        config_path = scoped_paths[0].path if scoped_paths else None
    
    if config_path is None:
        print_error("Could not determine config path.")
        return None

    return selected, config_path


def select_action() -> str | None:
    """Select an action to perform."""
    choices = [
        Choice(title="➕ Add a new server", value="add"),
        Choice(title="📋 List configured servers", value="list"),
        Choice(title="🔍 View server details", value="view"),
        Choice(title="❌ Remove a server", value="remove"),
        Choice(title="🚪 Exit", value="exit"),
    ]

    return questionary.select(
        "What would you like to do?",
        choices=choices,
        style=custom_style,
    ).ask()


def select_transport() -> str | None:
    """Select transport type for new server."""
    choices = [
        Choice(
            title="📟 STDIO - Local process (npx, uvx, python)",
            value="stdio",
        ),
        Choice(
            title="🌐 HTTP - Remote web endpoint",
            value="http",
        ),
        Choice(
            title="📡 SSE - Server-sent events",
            value="sse",
        ),
    ]

    return questionary.select(
        "Select transport type:",
        choices=choices,
        style=custom_style,
    ).ask()


def select_template_or_custom() -> ServerTemplate | str | None:
    """Select from templates or choose custom configuration."""
    templates = get_all_templates()
    categories = get_categories()

    choices = [
        Choice(title="🔧 Custom Configuration", value="custom"),
    ]

    # Category icons
    category_icons = {
        "development": "💻",
        "database": "🗄️",
        "memory": "🧠",
        "search": "🔍",
        "browser": "🌐",
        "cloud": "☁️",
        "communication": "💬",
        "productivity": "📋",
        "maps": "🗺️",
        "ai": "🤖",
        "utility": "🔧",
        "data": "📊",
        "security": "🔐",
    }
    
    category_names = {
        "development": "Development Tools",
        "database": "Databases",
        "memory": "Memory & Knowledge",
        "search": "Search & Web",
        "browser": "Browser Automation",
        "cloud": "Cloud & Infrastructure",
        "communication": "Communication",
        "productivity": "Productivity",
        "maps": "Maps & Location",
        "ai": "AI & Documentation",
        "utility": "Utilities",
        "data": "Data & Analytics",
        "security": "Security",
    }

    # Add templates grouped by category
    for category in categories:
        cat_templates = get_templates_by_category(category)
        if cat_templates:
            icon = category_icons.get(category, "📦")
            name = category_names.get(category, category.title())
            choices.append(Choice(title=f"─── {icon} {name} ───", value=None, disabled=""))
            for template in cat_templates:
                transport_icon = "🌐" if template.transport == "http" else "📟"
                choices.append(
                    Choice(
                        title=f"  {transport_icon} {template.display_name} — {template.description}",
                        value=template,
                    )
                )

    selected = questionary.select(
        "Choose a server template or custom:",
        choices=choices,
        style=custom_style,
    ).ask()

    return selected


def configure_stdio_server() -> dict[str, Any] | None:
    """Configure a STDIO transport server."""
    # Select command type
    command_choices = [
        Choice(title="npx -y @org/package", value="npx"),
        Choice(title="uvx package-name", value="uvx"),
        Choice(title="python -m module", value="python"),
        Choice(title="node script.js", value="node"),
        Choice(title="Custom command", value="custom"),
    ]

    command_type = questionary.select(
        "Select command type:",
        choices=command_choices,
        style=custom_style,
    ).ask()

    if command_type is None:
        return None

    config: dict[str, Any] = {}

    if command_type == "npx":
        config["command"] = "npx"
        package = questionary.text(
            "Enter package name (e.g., @modelcontextprotocol/server-filesystem):",
            style=custom_style,
            validate=lambda x: len(x) > 0 or "Package name is required",
        ).ask()
        if not package:
            return None

        args = ["-y", package]

        # Ask for additional arguments
        extra_args = questionary.text(
            "Additional arguments (space-separated, or leave empty):",
            style=custom_style,
        ).ask()
        if extra_args:
            args.extend(extra_args.split())

        config["args"] = args

    elif command_type == "uvx":
        config["command"] = "uvx"
        package = questionary.text(
            "Enter package name:",
            style=custom_style,
            validate=lambda x: len(x) > 0 or "Package name is required",
        ).ask()
        if not package:
            return None

        args = [package]

        extra_args = questionary.text(
            "Additional arguments (space-separated, or leave empty):",
            style=custom_style,
        ).ask()
        if extra_args:
            args.extend(extra_args.split())

        config["args"] = args

    elif command_type == "python":
        config["command"] = "python"
        module = questionary.text(
            "Enter module name:",
            style=custom_style,
            validate=lambda x: len(x) > 0 or "Module name is required",
        ).ask()
        if not module:
            return None

        args = ["-m", module]

        extra_args = questionary.text(
            "Additional arguments (space-separated, or leave empty):",
            style=custom_style,
        ).ask()
        if extra_args:
            args.extend(extra_args.split())

        config["args"] = args

    elif command_type == "node":
        config["command"] = "node"
        script = questionary.text(
            "Enter script path:",
            style=custom_style,
            validate=lambda x: len(x) > 0 or "Script path is required",
        ).ask()
        if not script:
            return None

        args = [script]

        extra_args = questionary.text(
            "Additional arguments (space-separated, or leave empty):",
            style=custom_style,
        ).ask()
        if extra_args:
            args.extend(extra_args.split())

        config["args"] = args

    else:  # custom
        command = questionary.text(
            "Enter command:",
            style=custom_style,
            validate=lambda x: len(x) > 0 or "Command is required",
        ).ask()
        if not command:
            return None

        config["command"] = command

        args_str = questionary.text(
            "Enter arguments (space-separated, or leave empty):",
            style=custom_style,
        ).ask()
        if args_str:
            config["args"] = args_str.split()

    # Environment variables
    if questionary.confirm(
        "Add environment variables?",
        default=False,
        style=custom_style,
    ).ask():
        config["env"] = {}
        while True:
            env_name = questionary.text(
                "Environment variable name (or leave empty to finish):",
                style=custom_style,
            ).ask()
            if not env_name:
                break

            env_value = questionary.password(
                f"Value for {env_name}:",
                style=custom_style,
            ).ask()
            if env_value:
                config["env"][env_name] = env_value

    return config


def configure_http_server() -> dict[str, Any] | None:
    """Configure an HTTP/SSE transport server."""
    url = questionary.text(
        "Enter server URL:",
        style=custom_style,
        validate=lambda x: x.startswith(("http://", "https://"))
        or "URL must start with http:// or https://",
    ).ask()

    if not url:
        return None

    config: dict[str, Any] = {"url": url}

    # Headers
    if questionary.confirm(
        "Add headers?",
        default=False,
        style=custom_style,
    ).ask():
        config["headers"] = {}
        while True:
            header_name = questionary.text(
                "Header name (or leave empty to finish):",
                style=custom_style,
            ).ask()
            if not header_name:
                break

            # Check if it's likely a sensitive header
            is_sensitive = any(
                kw in header_name.lower()
                for kw in ["key", "token", "auth", "secret", "password"]
            )

            if is_sensitive:
                header_value = questionary.password(
                    f"Value for {header_name}:",
                    style=custom_style,
                ).ask()
            else:
                header_value = questionary.text(
                    f"Value for {header_name}:",
                    style=custom_style,
                ).ask()

            if header_value:
                config["headers"][header_name] = header_value

    return config


def configure_from_template(template: ServerTemplate) -> tuple[str, dict[str, Any]] | None:
    """Configure a server from a template."""
    # Get server name
    default_name = template.name
    name = questionary.text(
        "Enter server name:",
        default=default_name,
        style=custom_style,
        validate=lambda x: len(x) > 0 or "Name is required",
    ).ask()

    if not name:
        return None

    # Start with template config
    config = template.config.copy()

    # Handle placeholders in args
    if "args" in config:
        new_args = []
        for arg in config["args"]:
            if arg.startswith("{") and arg.endswith("}"):
                placeholder = arg[1:-1]
                value = questionary.text(
                    f"Enter {placeholder}:",
                    style=custom_style,
                    validate=lambda x: len(x) > 0 or f"{placeholder} is required",
                ).ask()
                if not value:
                    return None
                new_args.append(value)
            else:
                new_args.append(arg)
        config["args"] = new_args

    # Prompt for required environment variables
    if template.env_vars:
        config["env"] = {}
        for env_var in template.env_vars:
            value = questionary.password(
                f"Enter {env_var}:",
                style=custom_style,
            ).ask()
            if value:
                config["env"][env_var] = value

    # Prompt for optional environment variables
    if template.optional_env_vars:
        if questionary.confirm(
            "Configure optional environment variables?",
            default=False,
            style=custom_style,
        ).ask():
            if "env" not in config:
                config["env"] = {}
            for env_var in template.optional_env_vars:
                value = questionary.text(
                    f"Enter {env_var} (optional):",
                    style=custom_style,
                ).ask()
                if value:
                    config["env"][env_var] = value

    # Prompt for required headers
    if template.headers:
        config["headers"] = {}
        for header in template.headers:
            value = questionary.password(
                f"Enter {header}:",
                style=custom_style,
            ).ask()
            if value:
                config["headers"][header] = value

    return name, config


def add_server_wizard(config_path: Path) -> bool:
    """Run the add server wizard."""
    # Read existing config
    config = read_config(config_path)

    # Select template or custom
    selection = select_template_or_custom()

    if selection is None:
        return False

    if isinstance(selection, ServerTemplate):
        # Configure from template
        result = configure_from_template(selection)
        if result is None:
            return False
        name, server_config = result
    else:
        # Custom configuration
        name = questionary.text(
            "Enter server name:",
            style=custom_style,
            validate=lambda x: len(x) > 0 or "Name is required",
        ).ask()

        if not name:
            return False

        # Check for existing server
        if name in get_servers(config):
            if not questionary.confirm(
                f"Server '{name}' already exists. Overwrite?",
                default=False,
                style=custom_style,
            ).ask():
                return False

        transport = select_transport()
        if transport is None:
            return False

        if transport == "stdio":
            server_config = configure_stdio_server()
        else:  # http or sse
            server_config = configure_http_server()

        if server_config is None:
            return False

    # Preview and confirm
    print_divider()
    console.print(f"\n[bold]Server Name:[/bold] {name}")
    print_server_details(name, server_config)

    if not questionary.confirm(
        "\nSave this configuration?",
        default=True,
        style=custom_style,
    ).ask():
        print_warning("Configuration not saved.")
        return False

    # Save
    config = add_server(config, name, server_config)
    write_config(config_path, config)
    print_success(f"Server '{name}' added to {config_path}")

    return True


def list_servers_wizard(config_path: Path) -> None:
    """List all configured servers."""
    config = read_config(config_path)
    servers = get_servers(config)

    print_info(f"Config file: {config_path}")
    print_server_table(servers)


def view_server_wizard(config_path: Path) -> None:
    """View details of a specific server."""
    config = read_config(config_path)
    servers = get_servers(config)

    if not servers:
        print_warning("No servers configured.")
        return

    choices = [Choice(title=name, value=name) for name in servers.keys()]
    selected = questionary.select(
        "Select server to view:",
        choices=choices,
        style=custom_style,
    ).ask()

    if selected:
        print_server_details(selected, servers[selected])


def remove_server_wizard(config_path: Path) -> bool:
    """Remove a server from configuration."""
    config = read_config(config_path)
    servers = get_servers(config)

    if not servers:
        print_warning("No servers configured.")
        return False

    choices = [Choice(title=name, value=name) for name in servers.keys()]
    selected = questionary.select(
        "Select server to remove:",
        choices=choices,
        style=custom_style,
    ).ask()

    if not selected:
        return False

    if not questionary.confirm(
        f"Remove server '{selected}'?",
        default=False,
        style=custom_style,
    ).ask():
        return False

    config = remove_server(config, selected)
    write_config(config_path, config)
    print_success(f"Server '{selected}' removed.")

    return True


def run_wizard() -> None:
    """Run the main wizard loop."""
    from .ui import print_banner

    print_banner()

    # Select client
    result = select_client()
    if result is None:
        print_info("Goodbye!")
        return

    client, config_path = result
    print_info(f"Configuring: {client.display_name}")
    print_info(f"Config path: {config_path}")
    print_divider()

    # Main action loop
    while True:
        action = select_action()

        if action is None or action == "exit":
            print_info("Goodbye!")
            break

        if action == "add":
            add_server_wizard(config_path)
        elif action == "list":
            list_servers_wizard(config_path)
        elif action == "view":
            view_server_wizard(config_path)
        elif action == "remove":
            remove_server_wizard(config_path)

        print_divider()
