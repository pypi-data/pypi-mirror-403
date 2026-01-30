"""Core shared types, enums, and message definitions for the entire codebase.

This module consolidates:
- Type enums (Role, ToolCallType, ExecutionEventType)
- TypedDict definitions for messages and tool calls
- Pydantic models for message structures
- Type aliases for common patterns
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# ============================================================================
# Type Aliases
# ============================================================================

# Tool-related type aliases
ToolCallList = list[dict[str, Any]]
ToolResultTuple = tuple[str, str, str]  # (call_id, tool_name, content)
ToolResultList = list[ToolResultTuple]

# Message-related type aliases
MessageDict = dict[str, Any]
MessageList = list[MessageDict]
ConversationHistory = list[MessageDict]

# Resource tracking for parallel execution
ResourceSet = set[str]
ToolGroup = list[dict[str, Any]]
ToolGroups = list[ToolGroup]

# ============================================================================
# Enums
# ============================================================================


class Role(str, Enum):
    """Message role types."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class ToolCallType(str, Enum):
    """Tool call type."""

    FUNCTION = "function"


class ExecutionEventType(str, Enum):
    """Event types for execution flow.

    Values:
        CONTENT: Text content from agent
        TOOL_CALL: Tool call request
        TOOL_EXECUTION_START: Tool execution started
        TOOL_RESULT: Tool execution result
        ASSISTANT_TURN_END: Assistant turn complete (save messages now)
        WARNING: Warning message
        ERROR: Error message
        COMPLETE: Execution complete
        CONTEXT_COMPACTION: Context window was compacted
    """

    CONTENT = "content"
    TOOL_CALL = "tool_call"
    TOOL_EXECUTION_START = "tool_execution_start"
    TOOL_RESULT = "tool_result"
    ASSISTANT_TURN_END = "assistant_turn_end"
    WARNING = "warning"
    ERROR = "error"
    COMPLETE = "complete"
    CONTEXT_COMPACTION = "context_compaction"


# ============================================================================
# Constants
# ============================================================================

# Prefixes for context/system scaffolding that should be excluded from user content
CONTEXT_PREFIXES: tuple[str, ...] = ("[Context:", "[Git Init")


# ============================================================================
# TypedDict Definitions (for compatibility)
# ============================================================================


class ToolFunctionDict(TypedDict, total=False):
    """Tool function call structure."""

    name: str
    arguments: str


class ToolCallShape(TypedDict, total=False):
    """Tool call shape structure."""

    id: str
    tool_call_id: str
    type: str
    function: ToolFunctionDict


class BaseMessageDict(TypedDict, total=False):
    """Base message structure as TypedDict.

    Used for compatibility with existing dict-based code.
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None


class ToolCallDict(TypedDict):
    """Tool call structure as TypedDict."""

    id: str
    type: Literal["function"]
    function: dict[str, Any]


class AssistantMessageDict(BaseMessageDict):
    """Assistant message with optional tool calls."""

    tool_calls: list[ToolCallDict] | None
    structured_state_json: str | None


class ToolMessageDict(BaseMessageDict):
    """Tool response message."""

    tool_call_id: str
    name: str | None


class ConversationMessageDict(TypedDict, total=False):
    """Union type for all message types in conversations."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None
    tool_calls: list[ToolCallDict] | None
    tool_call_id: str | None
    name: str | None
    structured_state_json: str | None


# ============================================================================
# Pydantic Models
# ============================================================================


class ToolExecutionResult(BaseModel):
    """Result from executing a single tool.

    Attributes:
        tool_call_id: ID of the tool call
        name: Name of the tool that was executed
        content: Result content or error message
        status: Execution status (success or error)
        error: Error message if status is error
        authorization_url: Authorization URL if authorization is required
    """

    tool_call_id: str = Field(..., description="ID of the tool call")
    name: str = Field(..., description="Name of the tool that was executed")
    content: str = Field(..., description="Result content or error message")
    status: Literal["success", "error"] = Field(..., description="Execution status")
    error: str | None = Field(None, description="Error message if status is error")
    authorization_url: str | None = Field(
        None, description="Authorization URL if authorization is required"
    )


class SingleMessageExitReason(str, Enum):
    """Exit reasons for single message mode.

    Values:
        COMPLETED: Task completed successfully
        NEEDS_INPUT: Agent needs user input to continue
        NEEDS_AUTH: Tool requires authorization
        ERROR: Execution error occurred
    """

    COMPLETED = "completed"
    NEEDS_INPUT = "needs_input"
    NEEDS_AUTH = "needs_auth"
    ERROR = "error"


class SingleMessageResult(BaseModel):
    """Result from single message mode execution.

    Attributes:
        exit_reason: Why execution stopped
        content: Final accumulated content
        needs_interactive: Whether to transition to interactive mode
        authorization_url: URL if auth is required
        error_message: Error message if error occurred
    """

    exit_reason: SingleMessageExitReason
    content: str = ""
    needs_interactive: bool = False
    authorization_url: str | None = None
    error_message: str | None = None


# ============================================================================
# Utility Functions
# ============================================================================


def extract_tool_output_content(result: Any) -> str:
    """Extract content from tool execution result.

    Handles various result formats:
    - Objects with output.value attribute (Arcade response)
    - Dicts with 'output' key
    - Raw values (converted to string)

    Args:
        result: Raw tool execution result

    Returns:
        Extracted content as string
    """
    if hasattr(result, "output") and hasattr(result.output, "value"):
        return str(result.output.value)
    if isinstance(result, dict) and "output" in result:
        return str(result.get("output", result))
    return str(result)
