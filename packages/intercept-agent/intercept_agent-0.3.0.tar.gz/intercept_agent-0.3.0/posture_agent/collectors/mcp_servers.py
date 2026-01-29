"""MCP servers collector - discovers configured MCP servers for AI tools."""

import json
from pathlib import Path
from typing import Any

from posture_agent.collectors.base import BaseCollector, CollectorResult


# MCP config file locations by tool
# These are relative to home directory
MCP_CONFIG_PATHS = [
    ("claude", ".claude/mcp.json"),
    ("cursor", ".cursor/mcp.json"),
    ("vscode", ".vscode/mcp.json"),
    ("continue", ".continue/config.json"),
    ("generic", "mcp.json"),
]

# Platform-specific config paths (absolute paths relative to home)
# macOS uses ~/Library/Application Support/ for app configs
MCP_CONFIG_PATHS_MACOS = [
    ("claude-desktop", "Library/Application Support/Claude/claude_desktop_config.json"),
    ("cursor-desktop", "Library/Application Support/Cursor/User/globalStorage/cursor.mcp/mcp.json"),
]

# Keywords indicating credential-related environment variables
CREDENTIAL_KEYWORDS = {"key", "token", "secret", "password", "api", "auth", "credential"}

# Keywords indicating shell execution
SHELL_COMMANDS = {"bash", "sh", "zsh", "cmd", "powershell", "pwsh"}

# Keywords indicating filesystem access
FILESYSTEM_KEYWORDS = {"file", "fs", "path", "directory", "folder", "read", "write"}


def detect_risk_indicators(server: dict[str, Any]) -> list[str]:
    """Detect potential risk indicators for an MCP server configuration."""
    risks: list[str] = []

    command = (server.get("command") or "").lower()
    args = server.get("args") or []
    args_str = " ".join(str(a) for a in args).lower()
    env = server.get("env") or {}
    url = (server.get("url") or "").lower()
    transport = (server.get("transport") or "stdio").lower()

    # Check for shell execution
    if any(shell in command for shell in SHELL_COMMANDS):
        risks.append("shell")

    # Check for credential env vars
    env_keys_lower = [k.lower() for k in env.keys()]
    if any(kw in key for key in env_keys_lower for kw in CREDENTIAL_KEYWORDS):
        risks.append("credentials")

    # Check for network access
    if transport in ("sse", "http", "streamable-http"):
        risks.append("network")
    if url and ("http://" in url or "https://" in url):
        risks.append("network")

    # Check for filesystem access indicators
    combined = f"{command} {args_str}"
    if any(kw in combined for kw in FILESYSTEM_KEYWORDS):
        risks.append("filesystem")
    # Also check if any args look like file paths
    if any("/" in str(a) or "\\" in str(a) for a in args):
        risks.append("filesystem")

    return list(set(risks))  # Dedupe


def parse_mcp_config(config_path: Path, tool: str) -> list[dict[str, Any]]:
    """Parse an MCP config file and extract server definitions."""
    servers: list[dict[str, Any]] = []

    try:
        content = config_path.read_text()
        data = json.loads(content)
    except (OSError, json.JSONDecodeError):
        return servers

    # Handle different config formats
    servers_data: dict[str, Any] = {}

    if tool == "continue":
        # Continue uses a different structure: {"mcpServers": {...}}
        servers_data = data.get("mcpServers", {})
    else:
        # Claude, Cursor, VS Code use: {"mcpServers": {...}}
        servers_data = data.get("mcpServers", {})

    for name, server_config in servers_data.items():
        if not isinstance(server_config, dict):
            continue

        # Determine transport type
        transport = "stdio"  # default
        if "url" in server_config:
            transport = server_config.get("transport", "sse")
        elif "command" in server_config:
            transport = "stdio"

        server_entry = {
            "name": name,
            "tool": tool,
            "config_path": str(config_path),
            "transport": transport,
            "command": server_config.get("command"),
            "args": server_config.get("args"),
            "url": server_config.get("url"),
            "env_keys": list((server_config.get("env") or {}).keys()),
            "risk_indicators": detect_risk_indicators(server_config),
        }
        servers.append(server_entry)

    return servers


class MCPServersCollector(BaseCollector):
    """Collects MCP (Model Context Protocol) server configurations."""

    name = "mcp_servers"

    async def collect(self) -> CollectorResult:
        import platform

        errors: list[str] = []
        all_servers: list[dict[str, Any]] = []

        home = Path.home()

        # Check standard config paths
        for tool, relative_path in MCP_CONFIG_PATHS:
            config_path = home / relative_path
            try:
                if config_path.exists():
                    servers = parse_mcp_config(config_path, tool)
                    all_servers.extend(servers)
            except Exception as e:
                errors.append(f"{tool} ({relative_path}): {e}")

        # Check macOS-specific paths
        if platform.system() == "Darwin":
            for tool, relative_path in MCP_CONFIG_PATHS_MACOS:
                config_path = home / relative_path
                try:
                    if config_path.exists():
                        servers = parse_mcp_config(config_path, tool)
                        all_servers.extend(servers)
                except Exception as e:
                    errors.append(f"{tool} ({relative_path}): {e}")

        return CollectorResult(
            collector=self.name,
            data=all_servers,
            errors=errors,
        )
