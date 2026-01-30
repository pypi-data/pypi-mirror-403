"""Composite tool manager using unified MCP architecture."""

import json
from pathlib import Path
from typing import Any

from cadecoder.core.logging import log
from cadecoder.tools.manager.base import ToolManager
from cadecoder.tools.manager.config import (
    MCPAuthType,
    MCPServerConfig,
    MCPServerStore,
    MCPTransportType,
)
from cadecoder.tools.manager.mcp import MCPToolManager


class CompositeToolManager(ToolManager):
    """Manages tools from MCP servers (both built-in local and external)."""

    def __init__(self, enable_mcp: bool = True, local_only: bool = False):
        self._tool_source_map: dict[str, str] = {}
        self._mcp_tool_to_manager: dict[str, tuple[MCPToolManager, str]] = {}
        self._tool_schemas: dict[str, dict[str, Any]] = {}
        self._mcp_managers: list[MCPToolManager] = []
        self._enable_mcp = enable_mcp
        self._local_only = local_only
        self._tools_loaded = False  # Track whether get_tools() has been called

        # Create built-in local tools MCP server (always enabled)
        local_mcp_config = self._create_local_tools_config()
        local_mcp_manager = MCPToolManager(local_mcp_config)
        self._mcp_managers.append(local_mcp_manager)
        self._local_mcp_manager = local_mcp_manager

        # Load user-configured MCP servers (skip if local_only mode)
        if local_only:
            log.info("Local-only mode: external MCP servers disabled")
        elif enable_mcp:
            self._mcp_store = MCPServerStore()
            for server_config in self._mcp_store.list_enabled():
                mcp_manager = MCPToolManager(server_config, self._mcp_store)
                self._mcp_managers.append(mcp_manager)

    def _create_local_tools_config(self) -> MCPServerConfig:
        """Create MCP config for built-in local tools via stdio."""
        import cadecoder.tools.local

        local_tools_dir = Path(cadecoder.tools.local.__file__).parent

        return MCPServerConfig(
            name="__builtin_local__",
            url="uv",
            transport=MCPTransportType.STDIO,
            command="uv",
            args=[
                "run",
                "--with",
                "arcade-mcp-server",
                "python",
                "-m",
                "arcade_mcp_server",
                "stdio",
                "--cwd",
                str(local_tools_dir),
            ],
            enabled=True,
            auth_type=MCPAuthType.NONE,
        )

    def _normalize_local_tool_name(self, arcade_name: str) -> str:
        """Convert arcade-mcp-server tool name back to original format.

        arcade-mcp-server transforms names like:
        - bash_tool -> ArcadeMCP_LocalBash
        - list_files_tool -> ArcadeMCP_LocalListfiles
        """
        if not arcade_name.startswith("ArcadeMCP_Local"):
            return arcade_name

        # Remove prefix
        name = arcade_name.replace("ArcadeMCP_Local", "").lower()

        # Map known tools back to original names
        name_map = {
            "bash": "bash_tool",
            "executecommand": "execute_command_tool",
            "listfiles": "list_files_tool",
            "readfile": "read_file_tool",
            "writefile": "write_file_tool",
            "editfile": "edit_file_tool",
            "editfileinsert": "edit_file_insert_tool",
            "searchcode": "search_code_tool",
            "grep": "grep_tool",
            "ripgrep": "ripgrep_tool",
            "gitstatus": "git_status_tool",
            "gitdiff": "git_diff_tool",
            "gitlog": "git_log_tool",
            "gitbranch": "git_branch_tool",
        }

        return name_map.get(name, arcade_name)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get all available tools from MCP sources."""
        all_tools = []
        local_count = 0
        mcp_count = 0

        for mcp_manager in self._mcp_managers:
            try:
                mcp_tools = await mcp_manager.get_tools()

                # Determine if this is the built-in local tools server
                is_builtin = mcp_manager.config.name == "__builtin_local__"

                for tool in mcp_tools:
                    arcade_name = tool.get("function", {}).get("name", "unknown")

                    # Normalize local tool names back to original format
                    if is_builtin:
                        tool_name = self._normalize_local_tool_name(arcade_name)
                        # Update the tool schema with normalized name
                        tool["function"]["name"] = tool_name
                        # Keep mapping from normalized name to arcade name for execution
                        self._tool_source_map[tool_name] = "local"
                        self._mcp_tool_to_manager[tool_name] = (mcp_manager, arcade_name)
                        local_count += 1
                    else:
                        tool_name = arcade_name
                        self._tool_source_map[tool_name] = "mcp"
                        self._mcp_tool_to_manager[tool_name] = (mcp_manager, arcade_name)
                        mcp_count += 1

                    # Cache tool schema for error enrichment
                    self._tool_schemas[tool_name] = tool

                    all_tools.append(tool)

                # Update server status for external MCP servers
                if not is_builtin and self._enable_mcp and hasattr(self, "_mcp_store"):
                    self._mcp_store.update_status(mcp_manager.config.name, True, len(mcp_tools))

                log.info(
                    f"Loaded {len(mcp_tools)} tools from "
                    f"{'built-in local' if is_builtin else 'MCP'} server '{mcp_manager.config.name}'"
                )

            except Exception as e:
                log.error(f"Failed to load tools from MCP '{mcp_manager.config.name}': {e}")

        # Summary
        log.info(f"Total tools: {len(all_tools)} (Built-in: {local_count}, MCP: {mcp_count})")
        self._tools_loaded = True
        return all_tools

    def _get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """Get the schema for a tool by name.

        Args:
            tool_name: Name of the tool.

        Returns:
            The tool's schema dict, or None if not found.
        """
        return self._tool_schemas.get(tool_name)

    def _enrich_error(self, name: str, error: Exception, inputs: dict[str, Any]) -> str:
        """Create enriched error message with tool schema.

        Args:
            name: Tool name that was called.
            error: The exception that occurred.
            inputs: The inputs that were passed to the tool.

        Returns:
            Enriched error message with the tool's input schema.
        """
        error_str = str(error)
        schema = self._get_tool_schema(name)

        if schema:
            params = schema.get("function", {}).get("parameters", {})
            params_json = json.dumps(params, indent=2)
            return f"Error calling tool '{name}': {error_str}. Tool input schema is: {params_json}"

        return f"Tool '{name}' does not exist: {error_str}"

    async def execute(self, name: str, inputs: dict[str, Any]) -> Any:
        """Execute a tool by routing to the appropriate MCP manager."""
        # Ensure tools have been loaded before execution
        if not self._tools_loaded:
            log.warning("Tools not loaded before execute() was called. Loading now...")
            await self.get_tools()

        manager_info = self._mcp_tool_to_manager.get(name)
        if not manager_info:
            # Provide helpful diagnostic information
            available_tools = list(self._mcp_tool_to_manager.keys())[:10]
            raise Exception(
                f"Tool '{name}' not found in tool mappings. "
                f"Available tools (first 10): {available_tools}. "
                f"Total mappings: {len(self._mcp_tool_to_manager)}"
            )

        mcp_manager, arcade_name = manager_info
        source = self._tool_source_map.get(name, "unknown")
        log.debug(f"Executing {source} tool: {name} (arcade name: {arcade_name})")

        # Use the arcade name for execution (what the server expects)
        try:
            return await mcp_manager.execute(arcade_name, inputs)
        except Exception as e:
            # Enrich tool execution errors with schema information
            # This helps the LLM understand what went wrong and fix parameter issues
            error_str = str(e).lower()

            # Check if this looks like a parameter-related error
            is_param_error = any(
                keyword in error_str
                for keyword in [
                    "required",
                    "missing",
                    "argument",
                    "parameter",
                    "type",
                    "expected",
                    "invalid",
                    "schema",
                    "validation",
                ]
            )

            if is_param_error:
                enriched_error = self._enrich_error(name, e, inputs)
                raise Exception(enriched_error) from e

            # Re-raise other errors as-is
            raise

    def is_interactive_tool(self, name: str) -> bool:
        """Determine whether a tool is interactive (bash_tool)."""
        # Interactive tools are bash-like tools that need terminal access
        return name in ("bash_tool", "execute_command_tool")

    def get_tool_source(self, name: str) -> str | None:
        """Get the source type for a tool."""
        return self._tool_source_map.get(name)

    def get_all_tool_info(self) -> list[dict[str, Any]]:
        """Get info about all tools including their source."""
        tool_info = []
        for name, source in self._tool_source_map.items():
            info: dict[str, Any] = {"name": name, "source": source}
            if name in self._mcp_tool_to_manager:
                manager, arcade_name = self._mcp_tool_to_manager[name]
                info["server"] = manager.config.name
                info["transport"] = manager.config.transport.value
                if arcade_name != name:
                    info["arcade_name"] = arcade_name
            tool_info.append(info)
        return tool_info

    async def close(self) -> None:
        """Close all MCP connections."""
        for mcp_manager in self._mcp_managers:
            await mcp_manager.close()
