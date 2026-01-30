"""Tool manager module - handles MCP tools (both built-in local and external)."""

from cadecoder.tools.manager.base import (
    JsonToolSchema,
    ToolAuthorizationRequired,
    ToolManager,
)
from cadecoder.tools.manager.composite import CompositeToolManager
from cadecoder.tools.manager.config import (
    MCPAuthType,
    MCPOAuthTokens,
    MCPServerConfig,
    MCPServerStore,
    MCPTransportType,
)
from cadecoder.tools.manager.mcp import MCPOAuthHandler, MCPToolManager

__all__ = [
    # Base
    "ToolManager",
    "ToolAuthorizationRequired",
    "JsonToolSchema",
    # Managers
    "MCPToolManager",
    "CompositeToolManager",
    # MCP
    "MCPOAuthHandler",
    "MCPServerConfig",
    "MCPServerStore",
    "MCPAuthType",
    "MCPOAuthTokens",
    "MCPTransportType",
]
