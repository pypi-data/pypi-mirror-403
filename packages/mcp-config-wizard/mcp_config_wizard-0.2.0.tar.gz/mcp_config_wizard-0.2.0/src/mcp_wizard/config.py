"""Configuration file discovery and management for MCP clients with global/project scope support."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import platformdirs


class MCPScope(Enum):
    """Enumeration of MCP configuration scopes."""
    GLOBAL = "global"      # User-level, applies everywhere
    PROJECT = "project"    # Project-level, applies to specific directory


@dataclass
class MCPConfigPath:
    """Represents a configuration path with its scope."""
    path: Path
    scope: MCPScope
    description: str = ""


@dataclass
class MCPClient:
    """Represents an MCP client with its configuration paths."""

    name: str
    display_name: str
    config_paths: list[MCPConfigPath] = field(default_factory=list)
    workspace_config: str | None = None  # Relative path for workspace configs
    config_format: str = "json"  # "json" or "yaml"
    config_key: str = "mcpServers"  # Key for MCP servers in config
    category: str = "Other"  # Category for grouping (e.g., "AI", "Cloud", "Communication")
    emoji: str = "📟"  # Emoji icon for the client
    description: str = ""  # Description of the client

    def get_config_path(self, scope: MCPScope | None = None) -> MCPConfigPath | None:
        """Get the first existing config path, optionally filtered by scope."""
        paths = [p for p in self.config_paths if scope is None or p.scope == scope]
        for config_path in paths:
            if config_path.path.exists():
                return config_path
        return paths[0] if paths else None

    def get_all_paths(self, scope: MCPScope | None = None) -> list[MCPConfigPath]:
        """Get all config paths, optionally filtered by scope."""
        if scope is None:
            return self.config_paths
        return [p for p in self.config_paths if p.scope == scope]

    def exists(self) -> bool:
        """Check if any config file exists."""
        return any(p.path.exists() for p in self.config_paths)


# ============================================================================
# CLIENT PATH FUNCTIONS - Each client with their global and project scopes
# ============================================================================

def get_claude_desktop_config_paths() -> list[MCPConfigPath]:
    """Claude Desktop configuration paths.
    
    Claude Desktop only supports global configuration (no project-level).
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "Claude" / "claude_desktop_config.json",
                scope=MCPScope.GLOBAL,
                description="Global user config"
            ))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            paths.append(MCPConfigPath(
                path=Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
                scope=MCPScope.GLOBAL,
                description="Global user config"
            ))
        else:  # Linux
            paths.append(MCPConfigPath(
                path=Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
                scope=MCPScope.GLOBAL,
                description="Global user config"
            ))
    return paths


def get_cursor_config_paths() -> list[MCPConfigPath]:
    """Cursor MCP configuration paths.
    
    Cursor inherits VS Code structure:
    - Global: settings.json
    - Project: .cursor/mcp.json
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "Cursor" / "User" / "settings.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".cursor" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level config"
            ))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            paths.append(MCPConfigPath(
                path=Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "settings.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".cursor" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level config"
            ))
        else:  # Linux
            paths.append(MCPConfigPath(
                path=Path.home() / ".config" / "Cursor" / "User" / "settings.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".cursor" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level config"
            ))
    return paths


def get_windsurf_config_paths() -> list[MCPConfigPath]:
    """Windsurf MCP configuration paths.
    
    Windsurf is built on Codeium infrastructure:
    - Global: ~/.codeium/mcp_config.json
    - Project: .windsurf/mcp.json (fallback)
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".codeium" / "mcp_config.json",
        scope=MCPScope.GLOBAL,
        description="Global Codeium config"
    ))
    paths.append(MCPConfigPath(
        path=Path.cwd() / ".windsurf" / "mcp.json",
        scope=MCPScope.PROJECT,
        description="Workspace-level config"
    ))
    return paths


def get_vscode_config_paths() -> list[MCPConfigPath]:
    """VS Code MCP configuration paths.
    
    VS Code stores MCP servers in mcp.json with 'servers' key:
    - Global: User settings folder
    - Project: .vscode/mcp.json (workspace)
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "Code" / "User" / "mcp.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".vscode" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level settings"
            ))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            paths.append(MCPConfigPath(
                path=Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".vscode" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level settings"
            ))
        else:  # Linux
            paths.append(MCPConfigPath(
                path=Path.home() / ".config" / "Code" / "User" / "mcp.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".vscode" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level settings"
            ))
    return paths


def get_lm_studio_config_paths() -> list[MCPConfigPath]:
    """LM Studio configuration paths.
    
    LM Studio only supports global configuration.
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "LM Studio" / "mcp.json",
                scope=MCPScope.GLOBAL,
                description="Global user config"
            ))
    else:  # macOS and Linux
        paths.append(MCPConfigPath(
            path=Path.home() / ".lmstudio" / "mcp.json",
            scope=MCPScope.GLOBAL,
            description="Global user config"
        ))
    return paths


def get_zed_config_paths() -> list[MCPConfigPath]:
    """Zed editor configuration paths.
    
    Zed stores MCP config in settings.json under context_servers field:
    - Windows: APPDATA\\Zed\\settings.json
    - macOS: ~/Library/Application Support/Zed/settings.json
    - Linux: ~/.config/zed/settings.json
    
    Note: Zed uses a single settings.json file per platform (no project-level).
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "Zed" / "settings.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            paths.append(MCPConfigPath(
                path=Path.home() / "Library" / "Application Support" / "Zed" / "settings.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
        else:  # Linux
            paths.append(MCPConfigPath(
                path=Path.home() / ".config" / "zed" / "settings.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
    return paths


def get_warp_config_paths() -> list[MCPConfigPath]:
    """Warp terminal configuration paths (macOS only)."""
    paths = []
    if os.name == "posix" and "darwin" in os.uname().sysname.lower():
        paths.append(MCPConfigPath(
            path=Path.home() / "Library" / "Application Support" / "dev.warp.Warp-Stable" / "mcp_servers.json",
            scope=MCPScope.GLOBAL,
            description="Global Warp config"
        ))
    return paths


def get_claude_code_config_paths() -> list[MCPConfigPath]:
    """Claude Code CLI configuration paths.
    
    Claude Code stores MCP servers in:
    - Global: ~/.claude.json (mcpServers field) - applies to all projects
    - Project: .mcp.json (mcpServers field) - applies to current project
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".claude.json",
        scope=MCPScope.GLOBAL,
        description="User-level config, applies everywhere"
    ))
    paths.append(MCPConfigPath(
        path=Path.cwd() / ".mcp.json",
        scope=MCPScope.PROJECT,
        description="Project-level config, checked into VCS"
    ))
    return paths


def get_goose_config_paths() -> list[MCPConfigPath]:
    """Goose (Block) configuration paths.
    
    Goose uses YAML configuration:
    - Global: ~/.config/goose/config.yaml
    - Project: .goose/config.yaml
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "goose" / "config.yaml",
                scope=MCPScope.GLOBAL,
                description="Global user config"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".goose" / "config.yaml",
                scope=MCPScope.PROJECT,
                description="Project-level config"
            ))
    else:
        paths.append(MCPConfigPath(
            path=Path.home() / ".config" / "goose" / "config.yaml",
            scope=MCPScope.GLOBAL,
            description="Global user config"
        ))
        paths.append(MCPConfigPath(
            path=Path.cwd() / ".goose" / "config.yaml",
            scope=MCPScope.PROJECT,
            description="Project-level config"
        ))
    return paths


def get_gemini_cli_config_paths() -> list[MCPConfigPath]:
    """Gemini CLI configuration paths.
    
    Gemini CLI stores MCP servers in:
    - Global: ~/.gemini/settings.json (mcpServers field) - applies to all projects
    - Project: .gemini/settings.json (mcpServers field) - applies to current project
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".gemini" / "settings.json",
        scope=MCPScope.GLOBAL,
        description="User-level config, applies everywhere"
    ))
    paths.append(MCPConfigPath(
        path=Path.cwd() / ".gemini" / "settings.json",
        scope=MCPScope.PROJECT,
        description="Project-level config, checked into VCS"
    ))
    return paths


def get_amazon_q_config_paths() -> list[MCPConfigPath]:
    """Amazon Q CLI configuration paths.
    
    Amazon Q only supports global configuration.
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".aws" / "amazonq" / "mcp.json",
        scope=MCPScope.GLOBAL,
        description="Global user config"
    ))
    return paths


def get_codex_config_paths() -> list[MCPConfigPath]:
    """OpenAI Codex CLI configuration paths.
    
    Codex only supports global configuration.
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".codex" / "config.json",
        scope=MCPScope.GLOBAL,
        description="Global user config"
    ))
    return paths


def get_opencode_config_paths() -> list[MCPConfigPath]:
    """OpenCode CLI configuration paths.
    
    OpenCode only supports global configuration.
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".opencode" / "config.json",
        scope=MCPScope.GLOBAL,
        description="Global user config"
    ))
    return paths


def get_amp_config_paths() -> list[MCPConfigPath]:
    """Amp (Sourcegraph) configuration paths.
    
    Amp uses VS Code mcp.json format:
    - Global: VS Code user settings
    - Project: .vscode/mcp.json
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "Code" / "User" / "mcp.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".vscode" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level settings"
            ))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            paths.append(MCPConfigPath(
                path=Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".vscode" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level settings"
            ))
        else:  # Linux
            paths.append(MCPConfigPath(
                path=Path.home() / ".config" / "Code" / "User" / "mcp.json",
                scope=MCPScope.GLOBAL,
                description="Global user settings"
            ))
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".vscode" / "mcp.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level settings"
            ))
    return paths


def get_cline_config_paths() -> list[MCPConfigPath]:
    """Cline (VS Code extension) configuration paths.
    
    Cline stores config in VS Code globalStorage - global only.
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "cline_mcp_settings.json",
                scope=MCPScope.GLOBAL,
                description="Global extension config"
            ))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            paths.append(MCPConfigPath(
                path=Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "cline_mcp_settings.json",
                scope=MCPScope.GLOBAL,
                description="Global extension config"
            ))
        else:  # Linux
            paths.append(MCPConfigPath(
                path=Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "cline_mcp_settings.json",
                scope=MCPScope.GLOBAL,
                description="Global extension config"
            ))
    return paths


def get_roo_code_config_paths() -> list[MCPConfigPath]:
    """Roo Code (VS Code extension) configuration paths.
    
    Roo Code stores config in VS Code globalStorage - global only.
    """
    paths = []
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(MCPConfigPath(
                path=Path(appdata) / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "mcp_settings.json",
                scope=MCPScope.GLOBAL,
                description="Global extension config"
            ))
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            paths.append(MCPConfigPath(
                path=Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "mcp_settings.json",
                scope=MCPScope.GLOBAL,
                description="Global extension config"
            ))
        else:  # Linux
            paths.append(MCPConfigPath(
                path=Path.home() / ".config" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "mcp_settings.json",
                scope=MCPScope.GLOBAL,
                description="Global extension config"
            ))
    return paths


def get_continue_config_paths() -> list[MCPConfigPath]:
    """Continue configuration paths.
    
    Continue uses YAML format:
    - Global: ~/.continue/config.yaml
    - Project: .continue/mcpServers/
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".continue" / "config.yaml",
        scope=MCPScope.GLOBAL,
        description="Global user config"
    ))
    paths.append(MCPConfigPath(
        path=Path.cwd() / ".continue" / "mcpServers",
        scope=MCPScope.PROJECT,
        description="Project-level config directory"
    ))
    return paths


def get_jetbrains_config_paths() -> list[MCPConfigPath]:
    """JetBrains (AI Assistant/Junie) configuration paths.
    
    JetBrains supports:
    - Global: ~/.junie/mcp.json
    - Project: .junie/mcp/
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".junie" / "mcp.json",
        scope=MCPScope.GLOBAL,
        description="Global user config"
    ))
    paths.append(MCPConfigPath(
        path=Path.cwd() / ".junie" / "mcp",
        scope=MCPScope.PROJECT,
        description="Project-level config directory"
    ))
    return paths


def get_antigravity_config_paths() -> list[MCPConfigPath]:
    """Google Antigravity configuration paths.
    
    Google Antigravity stores MCP config in:
    - Global: ~/.gemini/antigravity/mcp_config.json
    - Project: .gemini/antigravity/mcp_config.json
    """
    paths = []
    paths.append(MCPConfigPath(
        path=Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
        scope=MCPScope.GLOBAL,
        description="User-level config"
    ))
    paths.append(MCPConfigPath(
        path=Path.cwd() / ".gemini" / "antigravity" / "mcp_config.json",
        scope=MCPScope.PROJECT,
        description="Project-level config"
    ))
    return paths


def get_supported_clients() -> list[MCPClient]:
    """Get all supported MCP clients with their configuration paths."""
    return [
        # Desktop IDEs
        MCPClient(
            name="claude_desktop",
            display_name="Claude Desktop",
            config_paths=get_claude_desktop_config_paths(),
            category="🤖 AI & Coding",
            emoji="🤖",
            description="Official Claude desktop application by Anthropic",
        ),
        MCPClient(
            name="cursor",
            display_name="Cursor",
            config_paths=get_cursor_config_paths(),
            category="🤖 AI & Coding",
            emoji="⚡",
            description="AI-first code editor with built-in intelligence",
        ),
        MCPClient(
            name="windsurf",
            display_name="Windsurf",
            config_paths=get_windsurf_config_paths(),
            category="🤖 AI & Coding",
            emoji="💨",
            description="Ultra-fast code editor with Codeium AI",
        ),
        MCPClient(
            name="vscode",
            display_name="VS Code",
            config_paths=get_vscode_config_paths(),
            config_key="servers",
            category="📝 Editors & IDEs",
            emoji="💻",
            description="Visual Studio Code with extensions support",
        ),
        MCPClient(
            name="lm_studio",
            display_name="LM Studio",
            config_paths=get_lm_studio_config_paths(),
            category="🤖 AI & Coding",
            emoji="🧠",
            description="Run local language models with ease",
        ),
        MCPClient(
            name="zed",
            display_name="Zed Editor",
            config_paths=get_zed_config_paths(),
            config_key="context_servers",
            category="📝 Editors & IDEs",
            emoji="⚡",
            description="High-performance collaborative code editor",
        ),
        MCPClient(
            name="warp",
            display_name="Warp Terminal",
            config_paths=get_warp_config_paths(),
            category="⌨️  Terminals & CLIs",
            emoji="⌨️",
            description="AI-powered terminal with modern UI",
        ),
        # CLI Tools
        MCPClient(
            name="claude_code",
            display_name="Claude Code",
            config_paths=get_claude_code_config_paths(),
            category="🤖 AI & Coding",
            emoji="💬",
            description="Command-line interface for Claude",
        ),
        MCPClient(
            name="goose",
            display_name="Goose",
            config_paths=get_goose_config_paths(),
            config_format="yaml",
            config_key="extensions",
            category="🤖 AI & Coding",
            emoji="🪶",
            description="AI assistant for automating development tasks",
        ),
        MCPClient(
            name="gemini_cli",
            display_name="Gemini CLI",
            config_paths=get_gemini_cli_config_paths(),
            category="🤖 AI & Coding",
            emoji="✨",
            description="Google's Gemini AI command-line interface",
        ),
        MCPClient(
            name="amazon_q",
            display_name="Amazon Q CLI",
            config_paths=get_amazon_q_config_paths(),
            category="🤖 AI & Coding",
            emoji="🔶",
            description="AWS's generative AI assistant",
        ),
        MCPClient(
            name="codex",
            display_name="Codex CLI",
            config_paths=get_codex_config_paths(),
            category="🤖 AI & Coding",
            emoji="🔮",
            description="OpenAI's code generation API",
        ),
        MCPClient(
            name="opencode",
            display_name="OpenCode",
            config_paths=get_opencode_config_paths(),
            category="🤖 AI & Coding",
            emoji="🎯",
            description="Open-source code generation tool",
        ),
        # VS Code Extensions
        MCPClient(
            name="cline",
            display_name="Cline",
            config_paths=get_cline_config_paths(),
            category="📝 Editors & IDEs",
            emoji="📦",
            description="Autonomous AI agent for VS Code",
        ),
        MCPClient(
            name="roo_code",
            display_name="Roo Code",
            config_paths=get_roo_code_config_paths(),
            category="🤖 AI & Coding",
            emoji="🦘",
            description="Code AI assistant with advanced reasoning",
        ),
        MCPClient(
            name="continue",
            display_name="Continue",
            config_paths=get_continue_config_paths(),
            category="🤖 AI & Coding",
            emoji="⏸️",
            description="Open-source AI code completion plugin",
        ),
        MCPClient(
            name="antigravity",
            display_name="Antigravity IDE",
            config_paths=get_antigravity_config_paths(),
            category="💻 Low-Code/No-Code",
            emoji="🪐",
            description="AI-powered visual development platform",
        ),
    ]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_clients_by_category() -> dict[str, list[MCPClient]]:
    """Organize clients into categories."""
    clients = get_supported_clients()
    categorized: dict[str, list[MCPClient]] = {}
    
    for client in clients:
        if client.category not in categorized:
            categorized[client.category] = []
        categorized[client.category].append(client)
    
    # Sort by category display order
    category_order = [
        "🤖 AI & Coding",
        "📝 Editors & IDEs",
        "⌨️  Terminals & CLIs",
        "💻 Low-Code/No-Code",
    ]
    
    sorted_categories = {}
    for cat in category_order:
        if cat in categorized:
            sorted_categories[cat] = categorized[cat]
    
    # Add any remaining categories not in the order
    for cat in sorted(categorized.keys()):
        if cat not in sorted_categories:
            sorted_categories[cat] = categorized[cat]
    
    return sorted_categories


def detect_installed_clients() -> list[MCPClient]:
    """Detect which MCP clients are installed (have config directories)."""
    installed = []
    for client in get_supported_clients():
        if client.name == "custom":
            installed.append(client)
        elif client.config_paths:
            for config_path in client.config_paths:
                if config_path.path.parent.exists():
                    installed.append(client)
                    break
    return installed


def read_config(path: Path) -> dict[str, Any]:
    """Read and parse an MCP configuration file.
    
    Supports both 'servers' (VS Code MCP format) and 'mcpServers' (Claude Desktop format).
    """
    if not path.exists():
        return {"servers": {}}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"servers": {}}
            
            if path.suffix in [".yaml", ".yml"]:
                try:
                    import yaml
                    data = yaml.safe_load(content) or {}
                except ImportError:
                    data = json.loads(content)
            else:
                data = json.loads(content)
            
            # Support both 'servers' and 'mcpServers' keys
            if "servers" not in data and "mcpServers" not in data:
                data["servers"] = {}
            
            return data
    except (json.JSONDecodeError, Exception):
        return {"servers": {}}


def write_config(path: Path, config: dict[str, Any], backup: bool = True) -> None:
    """Write an MCP configuration file with optional backup."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if backup and path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f".{timestamp}.backup{path.suffix}")
        shutil.copy2(path, backup_path)

    if path.suffix in [".yaml", ".yml"]:
        try:
            import yaml
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        except ImportError:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)


def get_servers(config: dict[str, Any]) -> dict[str, Any]:
    """Get the MCP servers from a configuration.
    
    Supports both 'servers' (VS Code MCP format) and 'mcpServers' (Claude Desktop format).
    Returns servers from either key, preferring 'servers' if both exist.
    """
    # Prefer 'servers' key (VS Code MCP standard), fall back to 'mcpServers'
    return config.get("servers", config.get("mcpServers", {}))


def add_server(
    config: dict[str, Any], name: str, server_config: dict[str, Any]
) -> dict[str, Any]:
    """Add a server to the configuration.
    
    Uses 'servers' key by default (VS Code MCP standard), but preserves
    existing key if 'mcpServers' is already in use.
    """
    # If config already has mcpServers, preserve it; otherwise use servers
    if "mcpServers" in config:
        config["mcpServers"][name] = server_config
    else:
        if "servers" not in config:
            config["servers"] = {}
        config["servers"][name] = server_config
    return config


def remove_server(config: dict[str, Any], name: str) -> dict[str, Any]:
    """Remove a server from the configuration.
    
    Handles both 'servers' and 'mcpServers' keys.
    """
    # Try both key formats
    if "servers" in config and name in config["servers"]:
        del config["servers"][name]
    elif "mcpServers" in config and name in config["mcpServers"]:
        del config["mcpServers"][name]
    return config


def get_current_directory_config() -> Path:
    """Get a config path in the current working directory."""
    return Path.cwd() / "mcp_servers.json"
