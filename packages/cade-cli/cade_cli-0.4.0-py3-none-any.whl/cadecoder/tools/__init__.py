"""Tools module for AI agent capabilities.

This module provides:
- Unified MCP tool management (both built-in local and external servers)
- Local built-in tools (filesystem, shell, search, git) served via stdio MCP
- MCP server configuration and OAuth support

Architecture:
    tools/
    ├── manager/           # Tool management system
    │   ├── base.py       # ToolManager ABC
    │   ├── mcp.py        # MCPToolManager (stdio & HTTP transports)
    │   ├── composite.py  # CompositeToolManager (unified MCP)
    │   └── config.py     # MCP server configuration
    └── local/             # Built-in local tools (served via stdio MCP)
        ├── filesystem.py # File operations
        ├── shell.py      # Shell/bash execution
        ├── search.py     # Grep/ripgrep search
        └── git.py        # Git operations
"""

from cadecoder.tools.manager import (
    CompositeToolManager,
    MCPAuthType,
    MCPOAuthHandler,
    MCPOAuthTokens,
    MCPServerConfig,
    MCPServerStore,
    MCPToolManager,
    MCPTransportType,
    ToolAuthorizationRequired,
    ToolManager,
)

__all__ = [
    # Managers
    "ToolManager",
    "MCPToolManager",
    "CompositeToolManager",
    # MCP
    "MCPOAuthHandler",
    "MCPServerConfig",
    "MCPServerStore",
    "MCPAuthType",
    "MCPOAuthTokens",
    "MCPTransportType",
    # Exceptions
    "ToolAuthorizationRequired",
]
