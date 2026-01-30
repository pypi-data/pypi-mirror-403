"""Orchestrator for task execution."""

import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field

from cadecoder.ai.prompts import AGENT_SYSTEM_PROMPT, get_environment_context
from cadecoder.core.config import get_config
from cadecoder.core.constants import (
    DEFAULT_TEMPERATURE,
    MAX_EXECUTION_ITERATIONS,
)
from cadecoder.core.errors import get_provider_config_help
from cadecoder.core.logging import log
from cadecoder.core.types import ExecutionEventType, extract_tool_output_content
from cadecoder.execution.context_window import (
    CompactionStrategy,
    ContextWindowManager,
    create_context_manager,
)
from cadecoder.execution.parallel import AsyncToolExecutor
from cadecoder.providers import get_provider_for_model
from cadecoder.providers.base import (
    Provider,
    ProviderRequest,
    provider_registry,
)
from cadecoder.tools.manager import (
    CompositeToolManager,
    ToolAuthorizationRequired,
    ToolManager,
)


def create_orchestrator(
    provider: Provider | None = None,
    tool_manager: ToolManager | None = None,
    default_model: str | None = None,
    context_manager: ContextWindowManager | None = None,
    local_only: bool = False,
) -> "Orchestrator":
    """Factory function to create an orchestrator with sensible defaults.

    Args:
        provider: LLM provider (uses default if not specified)
        tool_manager: Tool manager (creates CompositeToolManager if not specified)
        default_model: Default model to use
        context_manager: Context window manager (created if not specified)
        local_only: If True, skip remote tools (use only local tools)

    Returns:
        Configured Orchestrator instance
    """
    if tool_manager is None:
        tool_manager = CompositeToolManager(local_only=local_only)

    return Orchestrator(
        provider=provider,
        tool_manager=tool_manager,
        default_model=default_model,
        context_manager=context_manager,
    )


# --- Execution Models ---


class ExecutionMode:
    """Execution mode constants."""

    STREAMING = "streaming"


class ExecutionContext(BaseModel):
    """Context for task execution."""

    task: str
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    mode: str = ExecutionMode.STREAMING
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionEvent(BaseModel):
    """Event emitted during execution."""

    type: str
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Result of task execution."""

    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_results: list[dict[str, Any]] | None = None
    mode: str = ExecutionMode.STREAMING
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContinuationDecision(BaseModel):
    """Decision about whether to continue execution."""

    should_continue: bool = False
    reason: str = ""
    needs_user_input: bool = False


class Orchestrator:
    """Orchestrator for task execution.

    This orchestrator:
    - Executes tasks in streaming mode with iterative execution
    - Manages tool execution with parallel support
    - Handles both execute() and stream() interfaces
    - Manages context window with automatic compaction
    """

    def __init__(
        self,
        provider: Provider | None = None,
        tool_manager: ToolManager | None = None,
        default_model: str | None = None,
        context_manager: ContextWindowManager | None = None,
    ):
        """Initialize orchestrator.

        Args:
            provider: LLM provider instance
            tool_manager: Tool manager for executing tools
            default_model: Default model to use
            context_manager: Context window manager (created if not provided)
        """
        self.default_model = default_model or get_config().settings.default_model

        # Select provider based on model name if not explicitly provided
        if provider is not None:
            self.provider = provider
        else:
            self.provider = get_provider_for_model(self.default_model)
            if not self.provider:
                # Fallback to default if model-based selection fails
                self.provider = provider_registry.get_default()

        if not self.provider:
            raise ValueError(get_provider_config_help())

        self.tool_manager = tool_manager
        self._tools_cache: list[dict[str, Any]] | None = None
        self._tools_description_cache: str | None = None

        # Context window management
        self.context_manager = context_manager or create_context_manager(model=self.default_model)

        # Async tool executor
        self._async_executor = None
        if self.tool_manager:
            self._async_executor = AsyncToolExecutor(self.tool_manager)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute a task in streaming mode."""
        context.mode = ExecutionMode.STREAMING

        log.info(f"Executing task with mode: {context.mode}")

        result_content = ""
        tool_calls = []
        final_metadata: dict[str, Any] = {}

        async for event in self.stream(context):
            if event.type == ExecutionEventType.CONTENT:
                result_content += event.content or ""
            elif event.type == ExecutionEventType.TOOL_CALL:
                tool_calls.append(event.metadata.get("tool_call", {}))
            elif event.type == ExecutionEventType.COMPLETE:
                final_metadata = event.metadata

        return ExecutionResult(
            content=result_content,
            tool_calls=tool_calls if tool_calls else None,
            tool_results=None,
            mode=ExecutionMode.STREAMING,
            metadata={"streamed": True, **final_metadata},
        )

    async def stream(self, context: ExecutionContext) -> AsyncIterator[ExecutionEvent]:
        """Stream execution events."""
        context.mode = ExecutionMode.STREAMING

        # Load tools
        tools = await self._load_tools()

        # Build messages
        messages = self._build_messages(context)

        # Clear tool outputs for new execution
        self.context_manager.clear_tool_outputs()

        iteration = 0
        should_continue = True

        while should_continue and iteration < MAX_EXECUTION_ITERATIONS:
            iteration += 1
            log.info(f"Execution iteration {iteration}")

            # Check context window status before each turn
            context_status = self.context_manager.check_context_status(messages)
            log.debug(
                f"Context status: {context_status['token_count']:,} tokens "
                f"({context_status['percentage_used']}% used)"
            )

            # Compact context if needed
            if context_status["needs_compaction"]:
                log.warning(
                    f"Context window near limit ({context_status['percentage_used']}%), "
                    "compacting..."
                )
                yield ExecutionEvent(
                    type=ExecutionEventType.CONTEXT_COMPACTION,
                    metadata={
                        "before_tokens": context_status["token_count"],
                        "strategy": CompactionStrategy.KEEP_RECENT.value,
                    },
                )

                messages, backup = self.context_manager.compact_context(
                    messages,
                    strategy=CompactionStrategy.KEEP_RECENT,
                )

                new_status = self.context_manager.check_context_status(messages)
                log.info(
                    f"Context compacted: {context_status['token_count']:,} -> "
                    f"{new_status['token_count']:,} tokens"
                )
                yield ExecutionEvent(
                    type=ExecutionEventType.CONTEXT_COMPACTION,
                    metadata={
                        "after_tokens": new_status["token_count"],
                        "backup_timestamp": backup.timestamp.isoformat(),
                    },
                )

            # Build provider request
            request = ProviderRequest(
                messages=messages,
                model=self.default_model,
                tools=tools if tools else None,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=None,
                tool_choice="auto",
                system_prompt=None,
                stream=True,
            )

            # Stream from provider
            accumulated_content = ""
            tool_calls: list[dict[str, Any]] = []

            async for stream_event in self.provider.stream(request):
                if stream_event.content:
                    accumulated_content += stream_event.content
                    yield ExecutionEvent(
                        type=ExecutionEventType.CONTENT,
                        content=stream_event.content,
                    )

                # Handle tool call events from provider
                if stream_event.type == ExecutionEventType.TOOL_CALL.value:
                    tool_call = stream_event.metadata.get("tool_call")
                    if tool_call:
                        tool_calls.append(tool_call)
                        yield ExecutionEvent(
                            type=ExecutionEventType.TOOL_CALL,
                            metadata={"tool_call": tool_call},
                        )

            # If we have tool calls, execute them
            if tool_calls:
                yield ExecutionEvent(
                    type=ExecutionEventType.TOOL_EXECUTION_START,
                    metadata={"tool_count": len(tool_calls)},
                )

                tool_results = await self._execute_tool_calls(tool_calls)

                for tc, result in zip(tool_calls, tool_results):
                    tool_name = result.get("name", "unknown")
                    tool_content = result.get("content", "")
                    tool_status = result.get("status", "success")
                    tool_call_id = tc.get("id", "")

                    # Track tool output in context manager
                    self.context_manager.add_tool_output(
                        tool_name=tool_name,
                        output=tool_content,
                        tool_call_id=tool_call_id,
                    )

                    yield ExecutionEvent(
                        type=ExecutionEventType.TOOL_RESULT,
                        content=tool_content,
                        metadata={
                            "tool_name": tool_name,
                            "tool_call_id": tool_call_id,
                            "status": tool_status,
                        },
                    )

                # Add assistant message with tool calls
                messages.append(
                    {
                        "role": "assistant",
                        "content": accumulated_content if accumulated_content else None,
                        "tool_calls": tool_calls,
                    }
                )

                # Add tool results as messages
                tool_results_for_event = []
                for tc, result in zip(tool_calls, tool_results):
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id", ""),
                            "content": result.get("content", ""),
                        }
                    )
                    tool_results_for_event.append(
                        {
                            "tool_call_id": tc.get("id", ""),
                            "tool_name": result.get("name", "unknown"),
                            "content": result.get("content", ""),
                        }
                    )

                # Signal turn end so session can save messages
                yield ExecutionEvent(
                    type=ExecutionEventType.ASSISTANT_TURN_END,
                    content=accumulated_content,
                    metadata={
                        "tool_calls": tool_calls,
                        "tool_results": tool_results_for_event,
                    },
                )

                # Check if we should continue
                decision = self._decide_continuation(accumulated_content, tool_results)
                should_continue = decision.should_continue and not decision.needs_user_input
            else:
                # No tool calls, check if we should continue
                decision = self._decide_continuation(accumulated_content, [])
                should_continue = decision.should_continue and not decision.needs_user_input

                if accumulated_content:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": accumulated_content,
                        }
                    )

                    # Signal turn end for non-tool responses
                    yield ExecutionEvent(
                        type=ExecutionEventType.ASSISTANT_TURN_END,
                        content=accumulated_content,
                        metadata={"tool_calls": [], "tool_results": []},
                    )

        yield ExecutionEvent(
            type=ExecutionEventType.COMPLETE,
            metadata={"iterations": iteration},
        )

    async def _load_tools(self) -> list[dict[str, Any]]:
        """Load available tools."""
        if not self.tool_manager:
            return []

        if self._tools_cache is None:
            self._tools_cache = await self.tool_manager.get_tools()

        return self._tools_cache

    async def _execute_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute tool calls and return results."""
        if not self.tool_manager:
            return []

        if self._async_executor:
            log.info(f"Using parallel executor for {len(tool_calls)} tool calls")
            results = await self._async_executor.execute_tools(tool_calls, preserve_order=True)

            formatted_results: list[dict[str, Any]] = []
            for result in results:
                result_dict: dict[str, Any] = {
                    "name": result.name,
                    "content": result.content,
                    "status": result.status,
                }
                if result.authorization_url:
                    result_dict["authorization_url"] = result.authorization_url
                formatted_results.append(result_dict)
            return formatted_results

        # Fallback to sequential execution
        log.info(f"Using sequential execution for {len(tool_calls)} tool calls")
        sequential_results: list[dict[str, Any]] = []

        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            name = function.get("name", "unknown")

            try:
                args = json.loads(function.get("arguments", "{}"))
                result_content = await self.tool_manager.execute(name, args)
                actual_content = extract_tool_output_content(result_content)

                sequential_results.append(
                    {
                        "name": name,
                        "content": str(actual_content),
                        "status": "success",
                    }
                )

            except Exception as e:
                auth_url = None
                if isinstance(e, ToolAuthorizationRequired):
                    auth_url = e.authorization_url
                    log.error(f"Authorization required for tool {name}")
                else:
                    log.error(f"Tool execution failed for {name}: {e}")

                error_dict: dict[str, Any] = {
                    "name": name,
                    "content": str(e),
                    "status": "error",
                }
                if auth_url:
                    error_dict["authorization_url"] = auth_url

                sequential_results.append(error_dict)

        return sequential_results

    def _decide_continuation(
        self, content: str, tool_results: list[dict[str, Any]]
    ) -> ContinuationDecision:
        """Decide whether to continue execution."""
        # Check for explicit signals
        content_lower = content.lower() if content else ""

        if "[task_complete]" in content_lower or "task complete" in content_lower:
            return ContinuationDecision(
                should_continue=False,
                reason="Task marked as complete",
            )

        if "[need_user_input]" in content_lower or "need user input" in content_lower:
            return ContinuationDecision(
                should_continue=False,
                reason="Needs user input",
                needs_user_input=True,
            )

        if "[continue]" in content_lower:
            return ContinuationDecision(
                should_continue=True,
                reason="Explicit continue signal",
            )

        # If there were tool calls with results, continue
        if tool_results:
            return ContinuationDecision(
                should_continue=True,
                reason="Tool results available",
            )

        # Default: don't continue
        return ContinuationDecision(
            should_continue=False,
            reason="No continuation signal",
        )

    def _build_messages(self, context: ExecutionContext) -> list[dict[str, Any]]:
        """Build messages for the provider.

        Constructs the full message list including:
        - System prompt with environment context and tools list
        - Conversation history
        - Current task as user message
        """
        messages: list[dict[str, Any]] = []

        # Check if we need to add a system prompt
        has_system_message = any(
            msg.get("role") == "system" for msg in context.conversation_history
        )

        if not has_system_message:
            # Build tools list
            tools_list = "(No tools available)"
            if self._tools_description_cache:
                tools_list = self._tools_description_cache
            elif self.tool_manager:
                tools_list = "(Tools available - use tools to see list)"

            # Build environment context
            try:
                env_context = get_environment_context()
            except Exception as e:
                log.warning(f"Failed to get environment context: {e}")
                env_context = "(Environment context unavailable)"

            # Replace placeholders in system prompt
            system_content = AGENT_SYSTEM_PROMPT.replace(
                "{_TOOLS_BULLET_LIST}", tools_list
            ).replace("{_ENVIRONMENT_CONTEXT}", env_context)

            messages.append(
                {
                    "role": "system",
                    "content": system_content,
                }
            )

        # Add conversation history
        messages.extend(context.conversation_history)

        # Add the current task
        messages.append(
            {
                "role": "user",
                "content": context.task,
            }
        )

        return messages

    def get_context_status(self, conversation_history: list[dict[str, Any]]) -> dict[str, Any]:
        """Get current context window status.

        Args:
            conversation_history: Current conversation messages

        Returns:
            Dict with token_count, percentage_used, needs_compaction, etc.
        """
        return self.context_manager.check_context_status(conversation_history)

    def get_tool_outputs_summary(self) -> dict[str, Any]:
        """Get summary of collected tool outputs.

        Returns:
            Dict with total_outputs, unique_tools, total_size_chars, estimated_tokens
        """
        return self.context_manager.get_tool_outputs_summary()

    def get_all_tool_outputs(self) -> list[dict[str, Any]]:
        """Get all collected tool outputs.

        Returns:
            List of all tool output records
        """
        return self.context_manager.tool_outputs.get_all_outputs()

    def get_final_tool_outputs(self) -> dict[str, str]:
        """Get only the final output for each tool.

        Returns:
            Dict mapping tool_name to final output
        """
        return self.context_manager.tool_outputs.get_final_outputs()

    def compact_context(
        self,
        messages: list[dict[str, Any]],
        strategy: CompactionStrategy = CompactionStrategy.KEEP_RECENT,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Manually compact context.

        Args:
            messages: Current messages to compact
            strategy: Compaction strategy to use

        Returns:
            Tuple of (compacted_messages, backup_info)
        """
        compacted, backup = self.context_manager.compact_context(messages, strategy)
        return compacted, {
            "timestamp": backup.timestamp.isoformat(),
            "original_token_count": backup.token_count,
            "new_token_count": self.context_manager.estimate_tokens(compacted),
            "messages_before": len(messages),
            "messages_after": len(compacted),
        }
