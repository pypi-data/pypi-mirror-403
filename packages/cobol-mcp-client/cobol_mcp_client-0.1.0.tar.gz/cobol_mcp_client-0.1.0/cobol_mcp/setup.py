"""
Setup utilities for COBOL MCP Server configuration.
Automatically configures MCP settings for various IDEs.
"""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_API_URL = "https://cobol-mcp-backend.onrender.com"

SUPPORTED_IDES = [
    "cursor", "claude-desktop", "vscode", "windsurf", "amp", "zed",
    "cline", "continue", "roo-code"
]

CLI_BASED_IDES = ["amp"]


def find_mcp_config_path(ide: str) -> Path | None:
    """Find the MCP configuration file path based on OS and IDE."""
    system = platform.system()
    home = Path.home()

    if ide in CLI_BASED_IDES:
        return None

    config_paths: dict[str, dict[str, Path]] = {
        "cursor": {
            "Darwin": home / ".cursor" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Cursor" / "mcp.json",
            "Linux": home / ".config" / "cursor" / "mcp.json",
        },
        "claude-desktop": {
            "Darwin": home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Claude" / "claude_desktop_config.json",
            "Linux": home / ".config" / "claude" / "claude_desktop_config.json",
        },
        "vscode": {
            "Darwin": home / ".vscode" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Code" / "User" / "mcp.json",
            "Linux": home / ".config" / "Code" / "User" / "mcp.json",
        },
        "windsurf": {
            "Darwin": home / ".codeium" / "windsurf" / "mcp_config.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Windsurf" / "mcp_config.json",
            "Linux": home / ".codeium" / "windsurf" / "mcp_config.json",
        },
        "zed": {
            "Darwin": home / ".config" / "zed" / "settings.json",
            "Windows": home / ".config" / "zed" / "settings.json",
            "Linux": home / ".config" / "zed" / "settings.json",
        },
        "cline": {
            "Darwin": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "Linux": home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
        },
        "continue": {
            "Darwin": home / ".continue" / "config.json",
            "Windows": home / ".continue" / "config.json",
            "Linux": home / ".continue" / "config.json",
        },
        "roo-code": {
            "Darwin": home / ".roo-code" / "mcp.json",
            "Windows": home / ".roo-code" / "mcp.json",
            "Linux": home / ".roo-code" / "mcp.json",
        },
    }

    if ide not in config_paths:
        raise ValueError(f"Unsupported IDE: {ide}")

    ide_paths = config_paths[ide]
    return ide_paths.get(system, ide_paths.get("Linux"))


def backup_config(config_path: Path) -> Path | None:
    """Create a backup of existing configuration file."""
    if config_path and config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        if backup_path.exists():
            import time
            timestamp = int(time.time())
            backup_path = config_path.with_suffix(f".json.backup.{timestamp}")
        shutil.copy2(config_path, backup_path)
        return backup_path
    return None


def create_cobol_mcp_config(api_key: str) -> dict[str, Any]:
    """Create COBOL MCP server configuration."""
    return {
        "command": "uvx",
        "args": ["cobol-mcp-client"],
        "env": {
            "COBOL_MCP_API_KEY": api_key,
        }
    }


def update_mcp_config(config_path: Path, api_key: str, ide: str) -> bool:
    """Update MCP configuration file with COBOL MCP server."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config: dict[str, Any] = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        config = json.loads(content)
            except json.JSONDecodeError:
                print(f"⚠️  Existing config has invalid JSON, creating new one")

        cobol_config = create_cobol_mcp_config(api_key)

        if ide == "zed":
            if "context_servers" not in config:
                config["context_servers"] = {}
            config["context_servers"]["cobol"] = cobol_config
        elif ide == "continue":
            if "experimental" not in config:
                config["experimental"] = {}
            if "modelContextProtocolServers" not in config["experimental"]:
                config["experimental"]["modelContextProtocolServers"] = []
            servers = config["experimental"]["modelContextProtocolServers"]
            servers = [s for s in servers if s.get("name") != "cobol"]
            servers.append({"name": "cobol", **cobol_config})
            config["experimental"]["modelContextProtocolServers"] = servers
        else:
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            config["mcpServers"]["cobol"] = cobol_config

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return True

    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
        return False
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False


def check_cli_available(cli_name: str) -> bool:
    """Check if a CLI tool is available in PATH."""
    return shutil.which(cli_name) is not None


def setup_amp(api_key: str) -> bool:
    """Setup COBOL MCP Server for Amp."""
    if not check_cli_available("amp"):
        print("❌ Amp CLI ('amp') not found in PATH.")
        print("   Please install Amp from: https://ampcode.com")
        return False

    cmd = [
        "amp", "mcp", "add", "cobol",
        "-e", f"COBOL_MCP_API_KEY={api_key}",
        "--", "uvx", "cobol-mcp-client"
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed: {e}")
        if e.stderr:
            print(f"   {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ amp command not found")
        return False


def setup_mcp_config(api_key: str, ide: str = "cursor") -> bool:
    """
    Main setup function to configure COBOL MCP Server.

    Args:
        api_key: COBOL MCP API key
        ide: IDE to configure

    Returns:
        True if successful, False otherwise
    """
    if ide == "amp":
        success = setup_amp(api_key)
        if success:
            print("\n✅ Setup complete for Amp!")
            print("   Restart Amp to use the COBOL MCP server.")
        return success

    config_path = find_mcp_config_path(ide)

    if config_path is None:
        print(f"❌ Could not determine config path for {ide}")
        return False

    backup_path = backup_config(config_path)
    if backup_path:
        print(f"📦 Backed up existing config to: {backup_path}")

    if update_mcp_config(config_path, api_key, ide):
        print(f"\n✅ Setup complete!")
        print(f"📝 Configuration written to: {config_path}")
        print(f"\n💡 Restart {ide} to use the COBOL MCP server.")
        return True
    else:
        print(f"\n❌ Setup failed. Please check the error messages above.")
        if backup_path:
            print(f"   Your original config is safe at: {backup_path}")
        return False
