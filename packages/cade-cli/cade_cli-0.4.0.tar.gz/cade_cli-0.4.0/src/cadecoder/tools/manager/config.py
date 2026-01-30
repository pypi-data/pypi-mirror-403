"""MCP server configuration and storage."""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from cadecoder.core.config import get_config
from cadecoder.core.logging import log


class MCPAuthType(str, Enum):
    """Authentication types for MCP servers."""

    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH = "oauth"


class MCPTransportType(str, Enum):
    """Transport types for MCP servers."""

    HTTP = "http"
    STDIO = "stdio"


@dataclass
class MCPOAuthTokens:
    """OAuth tokens for an MCP server."""

    access_token: str
    token_type: str = "Bearer"
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scope: str | None = None

    def is_expired(self) -> bool:
        """Check if access token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPOAuthTokens":
        """Create from dictionary."""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            scope=data.get("scope"),
        )


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""

    name: str
    url: str
    transport: MCPTransportType = MCPTransportType.HTTP
    auth_type: MCPAuthType = MCPAuthType.NONE
    auth_value: str | None = None
    enabled: bool = True
    last_connected: datetime | None = None
    tool_count: int = 0
    # Stdio-specific fields
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    # OAuth fields
    oauth_tokens: MCPOAuthTokens | None = None
    oauth_authorization_server: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None
    oauth_scopes: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "transport": self.transport.value,
            "auth_type": self.auth_type.value,
            "auth_value": self.auth_value,
            "enabled": self.enabled,
            "last_connected": (self.last_connected.isoformat() if self.last_connected else None),
            "tool_count": self.tool_count,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "oauth_tokens": self.oauth_tokens.to_dict() if self.oauth_tokens else None,
            "oauth_authorization_server": self.oauth_authorization_server,
            "oauth_client_id": self.oauth_client_id,
            "oauth_client_secret": self.oauth_client_secret,
            "oauth_scopes": self.oauth_scopes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary."""
        last_connected = None
        if data.get("last_connected"):
            last_connected = datetime.fromisoformat(data["last_connected"])

        oauth_tokens = None
        if data.get("oauth_tokens"):
            oauth_tokens = MCPOAuthTokens.from_dict(data["oauth_tokens"])

        return cls(
            name=data["name"],
            url=data["url"],
            transport=MCPTransportType(data.get("transport", "http")),
            auth_type=MCPAuthType(data.get("auth_type", "none")),
            auth_value=data.get("auth_value"),
            enabled=data.get("enabled", True),
            last_connected=last_connected,
            tool_count=data.get("tool_count", 0),
            command=data.get("command"),
            args=data.get("args"),
            env=data.get("env"),
            oauth_tokens=oauth_tokens,
            oauth_authorization_server=data.get("oauth_authorization_server"),
            oauth_client_id=data.get("oauth_client_id"),
            oauth_client_secret=data.get("oauth_client_secret"),
            oauth_scopes=data.get("oauth_scopes"),
        )


class MCPServerStore:
    """Persistent storage for MCP server configurations."""

    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is None:
            config_dir = Path(get_config().app_dir)
        self.config_dir = config_dir
        self.config_file = config_dir / "mcp_servers.json"
        self._servers: dict[str, MCPServerConfig] = {}
        self._load()

    def _load(self) -> None:
        """Load servers from disk."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, encoding="utf-8") as f:
                data = json.load(f)

            for server_data in data.get("servers", []):
                server = MCPServerConfig.from_dict(server_data)
                self._servers[server.name] = server

            log.debug(f"Loaded {len(self._servers)} MCP server configs")
        except Exception as e:
            log.warning(f"Failed to load MCP server configs: {e}")

    def _save(self) -> None:
        """Save servers to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        try:
            data = {
                "servers": [s.to_dict() for s in self._servers.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.warning(f"Failed to save MCP server configs: {e}")

    def add(self, server: MCPServerConfig) -> None:
        """Add or update a server configuration."""
        self._servers[server.name] = server
        self._save()

    def remove(self, name: str) -> bool:
        """Remove a server configuration."""
        if name in self._servers:
            del self._servers[name]
            self._save()
            return True
        return False

    def get(self, name: str) -> MCPServerConfig | None:
        """Get a server configuration by name."""
        return self._servers.get(name)

    def list_all(self) -> list[MCPServerConfig]:
        """List all server configurations."""
        return list(self._servers.values())

    def list_enabled(self) -> list[MCPServerConfig]:
        """List enabled server configurations."""
        return [s for s in self._servers.values() if s.enabled]

    def update_status(self, name: str, connected: bool, tool_count: int = 0) -> None:
        """Update server connection status."""
        if name in self._servers:
            if connected:
                self._servers[name].last_connected = datetime.now()
                self._servers[name].tool_count = tool_count
            self._save()
