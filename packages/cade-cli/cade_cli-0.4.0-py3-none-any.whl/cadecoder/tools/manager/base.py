"""Base tool manager interface and shared types."""

from abc import ABC, abstractmethod
from typing import Any

# Type aliases
JsonToolSchema = dict[str, Any]


class ToolAuthorizationRequired(Exception):
    """Exception raised when a tool requires user authorization."""

    def __init__(self, tool_name: str, authorization_url: str | None = None):
        self.tool_name = tool_name
        self.authorization_url = authorization_url

        if authorization_url:
            message = (
                f"Authorization required for '{tool_name}'.\n\n"
                f"Please authorize by clicking this link:\n{authorization_url}\n\n"
                f"After authorizing, let me know and I'll retry the operation."
            )
        else:
            message = (
                f"Authorization required for '{tool_name}'.\n\n"
                f"Please authorize this tool in your Arcade account."
            )

        super().__init__(message)


class ToolManager(ABC):
    """Base interface for tool management.

    All tool managers (local, arcade, MCP) must implement this interface.
    """

    @abstractmethod
    async def get_tools(self) -> list[dict[str, Any]]:
        """Get all available tools as JSON schemas.

        Returns:
            List of tool schemas in OpenAI function format.
        """
        pass

    @abstractmethod
    async def execute(self, name: str, inputs: dict[str, Any]) -> Any:
        """Execute a tool by name with inputs.

        Args:
            name: The tool name to execute.
            inputs: Dictionary of input parameters.

        Returns:
            The result of the tool execution.
        """
        pass
