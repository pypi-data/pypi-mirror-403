#!/usr/bin/env python3
"""Configure MCP clients to connect to optix-mcp-server.

This script handles configuration for:
- Claude Code (~/.claude.json)
- Codex CLI (~/.codex/config.toml)
- Cursor (~/.cursor/mcp.json)

Usage:
    python configure_mcp_client.py --client claude --python-path /path/to/python --server-path /path/to/server.py
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Python 3.11+ has tomllib built-in
try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore

# For writing TOML, we'll use a simple approach
# since tomllib is read-only


def backup_file(file_path: Path, max_backups: int = 3) -> Optional[Path]:
    """Create a backup of a file before modifying it.

    Args:
        file_path: Path to the file to backup
        max_backups: Maximum number of backups to keep

    Returns:
        Path to the backup file, or None if original doesn't exist
    """
    if not file_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".backup.{timestamp}")

    shutil.copy2(file_path, backup_path)

    # Clean up old backups
    backup_pattern = f"{file_path.name}.backup.*"
    backups = sorted(file_path.parent.glob(backup_pattern), reverse=True)
    for old_backup in backups[max_backups:]:
        old_backup.unlink()

    return backup_path


def configure_claude_code(python_path: str, server_path: str) -> bool:
    """Configure Claude Code to use optix-mcp-server.

    Updates ~/.claude.json with the server configuration.

    Args:
        python_path: Path to Python interpreter
        server_path: Path to server.py

    Returns:
        True if successful
    """
    config_path = Path.home() / ".claude.json"

    # Load existing config or create new
    if config_path.exists():
        backup_file(config_path)
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in {config_path}", file=sys.stderr)
                return False
    else:
        config = {}

    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Add optix server configuration
    config["mcpServers"]["optix"] = {
        "type": "stdio",
        "command": python_path,
        "args": [server_path],
        "env": {}
    }

    # Write updated config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Updated {config_path}")
    return True


def configure_codex_cli(python_path: str, server_path: str) -> bool:
    """Configure Codex CLI to use optix-mcp-server.

    Updates ~/.codex/config.toml with the server configuration.

    Args:
        python_path: Path to Python interpreter
        server_path: Path to server.py

    Returns:
        True if successful
    """
    config_dir = Path.home() / ".codex"
    config_path = config_dir / "config.toml"

    # Ensure directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    # Read existing config
    existing_content = ""
    if config_path.exists():
        backup_file(config_path)
        with open(config_path, "r") as f:
            existing_content = f.read()

    # Check if optix server already configured
    if "[mcp_servers.optix]" in existing_content:
        # Update existing configuration
        lines = existing_content.split("\n")
        new_lines = []
        skip_until_next_section = False

        for line in lines:
            if line.strip() == "[mcp_servers.optix]":
                skip_until_next_section = True
                continue
            if skip_until_next_section:
                if line.strip().startswith("["):
                    skip_until_next_section = False
                else:
                    continue
            new_lines.append(line)

        existing_content = "\n".join(new_lines)

    # Add optix configuration
    optix_config = f'''
[mcp_servers.optix]
command = "{python_path}"
args = ["{server_path}"]
enabled = true
'''

    # Append to existing content
    new_content = existing_content.rstrip() + "\n" + optix_config

    with open(config_path, "w") as f:
        f.write(new_content)

    print(f"Updated {config_path}")
    return True


def configure_cursor(python_path: str, server_path: str) -> bool:
    """Configure Cursor to use optix-mcp-server.

    Updates ~/.cursor/mcp.json with the server configuration.

    Args:
        python_path: Path to Python interpreter
        server_path: Path to server.py

    Returns:
        True if successful
    """
    config_dir = Path.home() / ".cursor"
    config_path = config_dir / "mcp.json"

    # Ensure directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    # Load existing config or create new
    if config_path.exists():
        backup_file(config_path)
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in {config_path}", file=sys.stderr)
                return False
    else:
        config = {}

    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Add optix server configuration
    config["mcpServers"]["optix"] = {
        "command": python_path,
        "args": [server_path],
        "env": {}
    }

    # Write updated config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Updated {config_path}")
    return True


def configure_api_keys(env_file: Path) -> bool:
    """Interactive API key configuration flow.

    Args:
        env_file: Path to .env file

    Returns:
        True if successful
    """
    print("\n=== API Key Configuration ===")
    print("Configure API keys for AI providers (press Enter to skip)\n")

    providers = {
        "OPENROUTER_API_KEY": "OpenRouter",
        "GEMINI_API_KEY": "Google Gemini",
        "OPENAI_API_KEY": "OpenAI",
    }

    # Load existing env file if present
    existing_vars: dict[str, str] = {}
    if env_file.exists():
        backup_file(env_file)
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    existing_vars[key.strip()] = value.strip()

    # Prompt for each provider
    for env_var, provider_name in providers.items():
        current = existing_vars.get(env_var, "")
        if current:
            prompt = f"{provider_name} API Key (current: ***{current[-4:]}): "
        else:
            prompt = f"{provider_name} API Key: "

        value = input(prompt).strip()
        if value:
            existing_vars[env_var] = value
        elif not current:
            # Keep empty if no existing value
            pass

    # Write updated .env file
    env_content = """# optix-mcp-server Configuration

# Server Configuration
SERVER_NAME=optix-mcp-server
LOG_LEVEL=INFO
TRANSPORT=stdio

# Tool Configuration
DISABLED_TOOLS=

# API Keys
"""

    for env_var in providers:
        value = existing_vars.get(env_var, "")
        if value:
            env_content += f"{env_var}={value}\n"
        else:
            env_content += f"# {env_var}=\n"

    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"\nUpdated {env_file}")
    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Configure MCP clients for optix-mcp-server"
    )
    parser.add_argument(
        "--client",
        choices=["claude", "codex", "cursor"],
        help="MCP client to configure"
    )
    parser.add_argument(
        "--python-path",
        help="Path to Python interpreter"
    )
    parser.add_argument(
        "--server-path",
        help="Path to server.py"
    )
    parser.add_argument(
        "--configure-api-keys",
        action="store_true",
        help="Configure API keys interactively"
    )
    parser.add_argument(
        "--env-file",
        help="Path to .env file (for API key configuration)"
    )

    args = parser.parse_args()

    # API key configuration mode
    if args.configure_api_keys:
        if not args.env_file:
            print("Error: --env-file required for API key configuration", file=sys.stderr)
            return 1
        return 0 if configure_api_keys(Path(args.env_file)) else 1

    # Client configuration mode
    if not args.client:
        print("Error: --client is required", file=sys.stderr)
        return 1

    if not args.python_path or not args.server_path:
        print("Error: --python-path and --server-path are required", file=sys.stderr)
        return 1

    # Validate paths
    if not os.path.isfile(args.python_path):
        print(f"Error: Python path does not exist: {args.python_path}", file=sys.stderr)
        return 1

    if not os.path.isfile(args.server_path):
        print(f"Error: Server path does not exist: {args.server_path}", file=sys.stderr)
        return 1

    # Configure the specified client
    success = False
    if args.client == "claude":
        success = configure_claude_code(args.python_path, args.server_path)
    elif args.client == "codex":
        success = configure_codex_cli(args.python_path, args.server_path)
    elif args.client == "cursor":
        success = configure_cursor(args.python_path, args.server_path)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
