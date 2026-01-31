"""Agent configuration definitions."""

import platform
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ConfigFormat(Enum):
    """Configuration file format."""
    JSON = "json"
    TOML = "toml"


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    label: str
    config_format: ConfigFormat
    global_path: str
    local_path: str
    key_path: str
    server_config: dict[str, Any] = field(default_factory=dict)

    def get_config_path(self, scope: str) -> Path:
        """Get the config file path based on scope."""
        if scope == "global":
            path = self.global_path
        else:
            path = self.local_path

        path = path.replace("~", str(Path.home()))
        return Path(path)


def _get_vscode_global_path() -> str:
    """Get platform-specific VS Code config path."""
    system = platform.system()
    if system == "Darwin":
        return "~/Library/Application Support/Code/User/mcp.json"
    elif system == "Windows":
        return "%APPDATA%/Code/User/mcp.json"
    else:
        return "~/.config/Code/User/mcp.json"


def _make_optix_server_config(agent_type: str) -> dict[str, Any]:
    """Generate the optix server configuration for an agent."""
    base_args = ["--from", "optix-mcp-server", "optix"]

    if agent_type == "claude":
        return {
            "type": "stdio",
            "command": "uvx",
            "args": base_args,
            "env": {},
        }
    elif agent_type == "cursor":
        return {
            "command": "uvx",
            "args": base_args,
            "env": {},
        }
    elif agent_type == "codex":
        return {
            "command": "uvx",
            "args": base_args,
            "enabled": True,
            "env": {},
        }
    elif agent_type == "vscode":
        return {
            "type": "stdio",
            "command": "uvx",
            "args": base_args,
            "env": {},
        }
    elif agent_type == "opencode":
        return {
            "type": "local",
            "command": ["uvx", "--from", "optix-mcp-server", "optix"],
            "enabled": True,
            "env": {},
        }
    else:
        return {
            "command": "uvx",
            "args": base_args,
        }


AGENTS: dict[str, AgentConfig] = {
    "claude": AgentConfig(
        name="claude",
        label="Claude Code",
        config_format=ConfigFormat.JSON,
        global_path="~/.claude.json",
        local_path=".mcp.json",
        key_path="mcpServers",
        server_config=_make_optix_server_config("claude"),
    ),
    "cursor": AgentConfig(
        name="cursor",
        label="Cursor",
        config_format=ConfigFormat.JSON,
        global_path="~/.cursor/mcp.json",
        local_path=".cursor/mcp.json",
        key_path="mcpServers",
        server_config=_make_optix_server_config("cursor"),
    ),
    "codex": AgentConfig(
        name="codex",
        label="Codex CLI",
        config_format=ConfigFormat.TOML,
        global_path="~/.codex/config.toml",
        local_path=".codex/config.toml",
        key_path="mcp_servers",
        server_config=_make_optix_server_config("codex"),
    ),
    "vscode": AgentConfig(
        name="vscode",
        label="VS Code (Copilot)",
        config_format=ConfigFormat.JSON,
        global_path=_get_vscode_global_path(),
        local_path=".vscode/mcp.json",
        key_path="servers",
        server_config=_make_optix_server_config("vscode"),
    ),
    "opencode": AgentConfig(
        name="opencode",
        label="OpenCode",
        config_format=ConfigFormat.JSON,
        global_path="~/.config/opencode/opencode.json",
        local_path="opencode.json",
        key_path="mcp",
        server_config=_make_optix_server_config("opencode"),
    ),
}


def get_agent(name: str) -> AgentConfig | None:
    """Get agent configuration by name."""
    return AGENTS.get(name.lower())


def get_all_agents() -> list[AgentConfig]:
    """Get all agent configurations."""
    return list(AGENTS.values())


def get_agent_names() -> list[str]:
    """Get all agent names."""
    return list(AGENTS.keys())
