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
    
    VS Code supports:
    - Global: User settings
    - Project: Workspace settings (.vscode/mcp.json)
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
    - Global: ~/.config/zed/settings.json
    - Project: .zed/settings.json
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
            paths.append(MCPConfigPath(
                path=Path.cwd() / ".zed" / "settings.json",
                scope=MCPScope.PROJECT,
                description="Workspace-level settings"
            ))
    else:  # macOS and Linux
        paths.append(MCPConfigPath(
            path=Path.home() / ".config" / "zed" / "settings.json",
            scope=MCPScope.GLOBAL,
            description="Global user settings"
        ))
        paths.append(MCPConfigPath(
            path=Path.cwd() / ".zed" / "settings.json",
            scope=MCPScope.PROJECT,
            description="Workspace-level settings"
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
        # Desktop Apps
        MCPClient(
            name="claude_desktop",
            display_name="Claude Desktop",
            config_paths=get_claude_desktop_config_paths(),
        ),
        MCPClient(
            name="cursor",
            display_name="Cursor",
            config_paths=get_cursor_config_paths(),
        ),
        MCPClient(
            name="windsurf",
            display_name="Windsurf (Codeium)",
            config_paths=get_windsurf_config_paths(),
        ),
        MCPClient(
            name="vscode",
            display_name="VS Code (GitHub Copilot)",
            config_paths=get_vscode_config_paths(),
        ),
        MCPClient(
            name="lm_studio",
            display_name="LM Studio",
            config_paths=get_lm_studio_config_paths(),
        ),
        MCPClient(
            name="zed",
            display_name="Zed Editor",
            config_paths=get_zed_config_paths(),
            config_key="context_servers",  # Zed uses "context_servers" key
        ),
        MCPClient(
            name="warp",
            display_name="Warp Terminal",
            config_paths=get_warp_config_paths(),
        ),
        # CLI Tools
        MCPClient(
            name="claude_code",
            display_name="Claude Code (CLI)",
            config_paths=get_claude_code_config_paths(),
        ),
        MCPClient(
            name="goose",
            display_name="Goose (Block)",
            config_paths=get_goose_config_paths(),
            config_format="yaml",
            config_key="extensions",
        ),
        MCPClient(
            name="gemini_cli",
            display_name="Gemini CLI (Google)",
            config_paths=get_gemini_cli_config_paths(),
        ),
        MCPClient(
            name="amazon_q",
            display_name="Amazon Q CLI",
            config_paths=get_amazon_q_config_paths(),
        ),
        MCPClient(
            name="codex",
            display_name="Codex CLI (OpenAI)",
            config_paths=get_codex_config_paths(),
        ),
        MCPClient(
            name="opencode",
            display_name="OpenCode CLI",
            config_paths=get_opencode_config_paths(),
        ),
        # VS Code Extensions
        MCPClient(
            name="cline",
            display_name="Cline (VS Code)",
            config_paths=get_cline_config_paths(),
        ),
        MCPClient(
            name="roo_code",
            display_name="Roo Code (VS Code)",
            config_paths=get_roo_code_config_paths(),
        ),
        MCPClient(
            name="continue",
            display_name="Continue",
            config_paths=get_continue_config_paths(),
            config_format="yaml",
        ),
        MCPClient(
            name="amp",
            display_name="Amp (Sourcegraph)",
            config_paths=get_amp_config_paths(),
        ),
        # JetBrains
        MCPClient(
            name="jetbrains",
            display_name="JetBrains (Junie/AI Assistant)",
            config_paths=get_jetbrains_config_paths(),
        ),
        # Google
        MCPClient(
            name="antigravity",
            display_name="Google Antigravity",
            config_paths=get_antigravity_config_paths(),
        ),
        # Custom
        MCPClient(
            name="custom",
            display_name="Custom Location",
            config_paths=[],
        ),
    ]


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
    """Read and parse an MCP configuration file."""
    if not path.exists():
        return {"mcpServers": {}}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"mcpServers": {}}
            
            if path.suffix in [".yaml", ".yml"]:
                try:
                    import yaml
                    data = yaml.safe_load(content) or {}
                except ImportError:
                    data = json.loads(content)
            else:
                data = json.loads(content)
            
            if "mcpServers" not in data:
                data["mcpServers"] = {}
            return data
    except (json.JSONDecodeError, Exception):
        return {"mcpServers": {}}


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
    """Get the MCP servers from a configuration."""
    return config.get("mcpServers", {})


def add_server(
    config: dict[str, Any], name: str, server_config: dict[str, Any]
) -> dict[str, Any]:
    """Add a server to the configuration."""
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    config["mcpServers"][name] = server_config
    return config


def remove_server(config: dict[str, Any], name: str) -> dict[str, Any]:
    """Remove a server from the configuration."""
    if "mcpServers" in config and name in config["mcpServers"]:
        del config["mcpServers"][name]
    return config


def get_current_directory_config() -> Path:
    """Get a config path in the current working directory."""
    return Path.cwd() / "mcp_servers.json"
