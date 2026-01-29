"""Setup utilities for COBOL MCP Server configuration."""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

SUPPORTED_IDES = [
    "cursor", "claude-code", "claude-desktop", "vscode", "windsurf", "amp",
    "zed", "cline", "continue", "roo-code"
]

CLI_BASED_IDES = ["amp", "claude-code"]


def find_mcp_config_path(ide: str) -> Path | None:
    system = platform.system()
    home = Path.home()

    if ide in CLI_BASED_IDES:
        return None

    config_paths: dict[str, dict[str, Path]] = {
        "cursor": {
            "Darwin": home / ".cursor" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp.json",
            "Linux": home / ".config" / "cursor" / "mcp.json",
        },
        "claude-desktop": {
            "Darwin": home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            "Windows": Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
            "Linux": home / ".config" / "claude" / "claude_desktop_config.json",
        },
        "vscode": {
            "Darwin": home / ".vscode" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "mcp.json",
            "Linux": home / ".config" / "Code" / "User" / "mcp.json",
        },
        "windsurf": {
            "Darwin": home / ".codeium" / "windsurf" / "mcp_config.json",
            "Windows": Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_config.json",
            "Linux": home / ".codeium" / "windsurf" / "mcp_config.json",
        },
        "zed": {
            "Darwin": home / ".config" / "zed" / "settings.json",
            "Windows": home / ".config" / "zed" / "settings.json",
            "Linux": home / ".config" / "zed" / "settings.json",
        },
        "cline": {
            "Darwin": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "Windows": Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
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
        return None

    return config_paths[ide].get(system, config_paths[ide].get("Linux"))


def backup_config(config_path: Path) -> Path | None:
    if config_path and config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        if backup_path.exists():
            import time
            backup_path = config_path.with_suffix(f".json.backup.{int(time.time())}")
        shutil.copy2(config_path, backup_path)
        return backup_path
    return None


def create_cobol_mcp_config(api_key: str) -> dict[str, Any]:
    return {
        "command": "uvx",
        "args": ["--refresh", "--from", "cobol-mcp-client", "cobol-mcp"],
        "env": {"COBOL_MCP_API_KEY": api_key}
    }


def update_mcp_config(config_path: Path, api_key: str, ide: str) -> bool:
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config: dict[str, Any] = {}
        if config_path.exists():
            try:
                content = config_path.read_text().strip()
                if content:
                    config = json.loads(content)
            except json.JSONDecodeError:
                pass

        cobol_config = create_cobol_mcp_config(api_key)

        if ide == "zed":
            config.setdefault("context_servers", {})["cobol"] = cobol_config
        elif ide == "continue":
            config.setdefault("experimental", {})
            servers = config["experimental"].get("modelContextProtocolServers", [])
            servers = [s for s in servers if s.get("name") != "cobol"]
            servers.append({"name": "cobol", **cobol_config})
            config["experimental"]["modelContextProtocolServers"] = servers
        else:
            config.setdefault("mcpServers", {})["cobol"] = cobol_config

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return True
    except (PermissionError, OSError):
        return False


def setup_amp(api_key: str) -> bool:
    amp_bin = shutil.which("amp")
    if not amp_bin:
        return False

    try:
        subprocess.run([amp_bin, "mcp", "remove", "cobol"],
                       capture_output=True)
        subprocess.run([
            amp_bin, "mcp", "add", "cobol",
            "-e", f"COBOL_MCP_API_KEY={api_key}",
            "--", "uvx", "--refresh", "--from", "cobol-mcp-client", "cobol-mcp"
        ], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_claude_code(api_key: str) -> bool:
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return False

    try:
        subprocess.run([claude_bin, "mcp", "remove", "cobol", "-s", "user"],
                       capture_output=True)
        subprocess.run([
            claude_bin, "mcp", "add", "cobol",
            "-s", "user",
            "-e", f"COBOL_MCP_API_KEY={api_key}",
            "--", "uvx", "--refresh", "--from", "cobol-mcp-client", "cobol-mcp"
        ], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_mcp_config(api_key: str, ide: str = "cursor", quiet: bool = False) -> bool:
    if ide == "amp":
        return setup_amp(api_key)

    if ide == "claude-code":
        return setup_claude_code(api_key)

    config_path = find_mcp_config_path(ide)
    if config_path is None:
        return False

    if not quiet:
        backup_path = backup_config(config_path)
        if backup_path:
            print(f"Backed up existing config to: {backup_path}")

    return update_mcp_config(config_path, api_key, ide)
