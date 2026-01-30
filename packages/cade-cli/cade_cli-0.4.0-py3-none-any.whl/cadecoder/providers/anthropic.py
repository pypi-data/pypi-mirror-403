"""Anthropic provider adapter.

This module implements the Provider interface for Anthropic's Claude API,
handling both standard completions and streaming responses with automatic
tool schema conversion between OpenAI and Anthropic formats.
"""

import json
import os
from collections.abc import AsyncIterator
from typing import Any

from anthropic import Anthropic, AsyncAnthropic

from cadecoder.core.logging import log
from cadecoder.core.types import ExecutionEventType
from cadecoder.providers.base import (
    Provider,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
    ProviderType,
    StreamEvent,
)

# Fallback models used when API fetch fails
_FALLBACK_MODELS: list[str] = [
    # Claude 4.5 models (current)
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-5-20251101",
    # Aliases (point to latest snapshot)
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "claude-opus-4-5",
    # Legacy Claude 3.5 models
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
]

# Module-level cache for fetched models (shared across instances)
_models_cache: list[str] | None = None


class AnthropicProvider(Provider):
    """Anthropic Claude provider implementation.

    Handles automatic conversion between OpenAI-format tool schemas
    (used internally) and Anthropic's native tool format.

    Dynamically fetches available models from the Anthropic API
    and validates user-provided model strings against them.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (uses environment if not provided)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ProviderError("Anthropic API key not configured", ProviderType.ANTHROPIC)

        self.client = AsyncAnthropic(api_key=self.api_key)
        self._sync_client: Anthropic | None = None

    def _get_sync_client(self) -> Anthropic:
        """Get or create synchronous client for model fetching."""
        if self._sync_client is None:
            self._sync_client = Anthropic(api_key=self.api_key)
        return self._sync_client

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.ANTHROPIC

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models.

        Fetches from API on first access, caches result.
        Falls back to hardcoded list if API call fails.
        """
        global _models_cache
        if _models_cache is None:
            _models_cache = self._fetch_models_from_api()
        return _models_cache

    def _fetch_models_from_api(self) -> list[str]:
        """Fetch available models from Anthropic API.

        Returns:
            List of model IDs available from Anthropic.
        """
        try:
            client = self._get_sync_client()
            response = client.models.list()
            models = [model.id for model in response.data]
            if models:
                log.debug(f"Fetched {len(models)} models from Anthropic API")
                return models
            log.warning("Anthropic API returned empty model list, using fallback")
            return _FALLBACK_MODELS.copy()
        except Exception as e:
            log.warning(f"Failed to fetch models from Anthropic API: {e}, using fallback")
            return _FALLBACK_MODELS.copy()

    def is_valid_model(self, model: str) -> bool:
        """Check if a model string is valid.

        Args:
            model: Model identifier to validate.

        Returns:
            True if the model is in the supported models list.
        """
        return model in self.supported_models

    def validate_model(self, model: str) -> None:
        """Validate a model string and raise if invalid.

        Args:
            model: Model identifier to validate.

        Raises:
            ProviderError: If the model is not supported.
        """
        if not self.is_valid_model(model):
            available = ", ".join(self.supported_models[:5])
            raise ProviderError(
                f"Invalid model '{model}'. Available models include: {available}...",
                provider=ProviderType.ANTHROPIC,
                details={
                    "requested_model": model,
                    "available_models": self.supported_models,
                },
            )

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Create a completion using Anthropic.

        Args:
            request: The request to process

        Returns:
            The provider's response

        Raises:
            ProviderError: If the request fails
        """
        try:
            # Warn if model not in known list (don't block, API may accept it)
            if not self.is_valid_model(request.model):
                log.warning(
                    f"Model '{request.model}' not in known Anthropic models. "
                    "Request may fail if model is invalid."
                )

            anthropic_request = self._build_anthropic_request(request)
            response = await self.client.messages.create(**anthropic_request)

            # Extract content and tool calls from response
            content = self._extract_text_content(response.content)
            tool_calls = self._extract_tool_calls(response.content)

            # Map Anthropic stop reasons to unified format
            finish_reason = self._map_stop_reason(response.stop_reason)

            return ProviderResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                model=response.model,
                provider=ProviderType.ANTHROPIC,
            )

        except Exception as e:
            log.error(f"Anthropic completion failed: {e}")
            raise ProviderError(
                f"Anthropic completion failed: {str(e)}",
                provider=ProviderType.ANTHROPIC,
                details={"error": str(e)},
            )

    async def stream(self, request: ProviderRequest) -> AsyncIterator[StreamEvent]:
        """Stream a completion from Anthropic.

        Args:
            request: The request to process

        Yields:
            Stream events as they arrive

        Raises:
            ProviderError: If the request fails
        """
        try:
            # Warn if model not in known list (don't block, API may accept it)
            if not self.is_valid_model(request.model):
                log.warning(
                    f"Model '{request.model}' not in known Anthropic models. "
                    "Request may fail if model is invalid."
                )

            anthropic_request = self._build_anthropic_request(request)

            # Track tool call state during streaming
            current_tool_calls: dict[str, dict[str, Any]] = {}
            current_tool_input: dict[str, str] = {}

            async with self.client.messages.stream(**anthropic_request) as stream:
                async for event in stream:
                    # Handle text delta
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamEvent(
                                type=ExecutionEventType.CONTENT.value,
                                content=event.delta.text,
                            )
                        elif hasattr(event.delta, "partial_json"):
                            # Tool input JSON being streamed
                            if hasattr(event, "index"):
                                idx = str(event.index)
                                if idx not in current_tool_input:
                                    current_tool_input[idx] = ""
                                current_tool_input[idx] += event.delta.partial_json

                    # Handle content block start (tool use begins)
                    elif event.type == "content_block_start":
                        if hasattr(event.content_block, "type"):
                            if event.content_block.type == "tool_use":
                                idx = str(event.index)
                                current_tool_calls[idx] = {
                                    "id": event.content_block.id,
                                    "type": "function",
                                    "function": {
                                        "name": event.content_block.name,
                                        "arguments": "",
                                    },
                                }
                                current_tool_input[idx] = ""

                    # Handle content block stop (tool use complete)
                    elif event.type == "content_block_stop":
                        idx = str(event.index)
                        if idx in current_tool_calls:
                            # Finalize tool call with accumulated input
                            current_tool_calls[idx]["function"]["arguments"] = (
                                current_tool_input.get(idx, "{}")
                            )

                    # Handle message stop
                    elif event.type == "message_stop":
                        # Emit any pending tool calls
                        for tool_call in current_tool_calls.values():
                            yield StreamEvent(
                                type=ExecutionEventType.TOOL_CALL.value,
                                content=None,
                                metadata={"tool_call": tool_call},
                            )

                    # Handle message delta (contains stop reason)
                    elif event.type == "message_delta":
                        if hasattr(event, "delta") and hasattr(event.delta, "stop_reason"):
                            yield StreamEvent(
                                type=ExecutionEventType.COMPLETE.value,
                                content=None,
                                metadata={
                                    "finish_reason": self._map_stop_reason(event.delta.stop_reason),
                                    "model": request.model,
                                },
                            )

        except Exception as e:
            log.error(f"Anthropic streaming failed: {e}")
            yield StreamEvent(
                type="error",
                content=str(e),
                metadata={"provider": ProviderType.ANTHROPIC},
            )

    def _build_anthropic_request(self, request: ProviderRequest) -> dict[str, Any]:
        """Build Anthropic API request from unified request.

        Args:
            request: Unified request

        Returns:
            Anthropic API request dictionary
        """
        # Separate system message from conversation messages
        system_prompt, messages = self._convert_messages(request.messages)

        # Use provided system prompt override if available
        if request.system_prompt:
            system_prompt = request.system_prompt

        anthropic_request: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }

        # Add system prompt if present
        if system_prompt:
            anthropic_request["system"] = system_prompt

        # Always include temperature
        anthropic_request["temperature"] = request.temperature

        # Convert tools from OpenAI format to Anthropic format
        if request.tools:
            anthropic_request["tools"] = self._convert_tools_to_anthropic(request.tools)
            log.info(f"Anthropic request includes {len(request.tools)} tools")
            tool_names = [t.get("function", {}).get("name", "unknown") for t in request.tools[:5]]
            log.debug(f"First few tools: {tool_names}")

        # Handle tool choice
        if request.tool_choice:
            anthropic_request["tool_choice"] = self._convert_tool_choice(request.tool_choice)

        # Add any provider-specific metadata
        if "anthropic" in request.metadata:
            anthropic_request.update(request.metadata["anthropic"])

        return anthropic_request

    def _convert_messages(
        self, messages: list[dict[str, Any]]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert OpenAI-format messages to Anthropic format.

        Handles:
        - System messages (extracted separately)
        - Tool calls (converted to tool_use content blocks)
        - Tool results (converted to tool_result content blocks)

        Args:
            messages: Messages in OpenAI format

        Returns:
            Tuple of (system_prompt, anthropic_messages)
        """
        system_prompt: str | None = None
        anthropic_messages: list[dict[str, Any]] = []

        # Track tool results to merge into user messages
        pending_tool_results: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                # Accumulate system messages
                if system_prompt:
                    system_prompt += "\n\n" + (content or "")
                else:
                    system_prompt = content

            elif role == "user":
                # Include any pending tool results with user message
                if pending_tool_results:
                    user_content: list[dict[str, Any]] = pending_tool_results.copy()
                    pending_tool_results.clear()
                    if content:
                        user_content.append({"type": "text", "text": content})
                    anthropic_messages.append({"role": "user", "content": user_content})
                else:
                    anthropic_messages.append({"role": "user", "content": content or ""})

            elif role == "assistant":
                # Flush any pending tool results before assistant message
                # This handles multi-turn tool use where tool results precede next assistant
                if pending_tool_results:
                    anthropic_messages.append(
                        {"role": "user", "content": pending_tool_results.copy()}
                    )
                    pending_tool_results.clear()

                # Convert assistant message with potential tool calls
                assistant_content: list[dict[str, Any]] = []

                if content:
                    assistant_content.append({"type": "text", "text": content})

                # Convert tool calls to tool_use blocks
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    for tc in tool_calls:
                        tool_use = self._convert_tool_call_to_tool_use(tc)
                        assistant_content.append(tool_use)

                if assistant_content:
                    anthropic_messages.append({"role": "assistant", "content": assistant_content})

            elif role == "tool":
                # Convert tool message to tool_result block
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id", ""),
                    "content": content or "",
                }
                pending_tool_results.append(tool_result)

        # Handle any remaining tool results (add as final user message)
        if pending_tool_results:
            anthropic_messages.append({"role": "user", "content": pending_tool_results})

        return system_prompt, anthropic_messages

    def _convert_tools_to_anthropic(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-format tools to Anthropic format.

        Args:
            tools: Tools in OpenAI format

        Returns:
            Tools in Anthropic format
        """
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tool = {
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                }
                anthropic_tools.append(anthropic_tool)
        return anthropic_tools

    def _convert_tool_choice(self, tool_choice: str | dict[str, Any]) -> dict[str, Any]:
        """Convert OpenAI tool_choice to Anthropic format.

        Args:
            tool_choice: Tool choice in OpenAI format

        Returns:
            Tool choice in Anthropic format
        """
        if isinstance(tool_choice, str):
            if tool_choice == "auto":
                return {"type": "auto"}
            elif tool_choice == "none":
                return {"type": "none"}
            elif tool_choice == "required":
                return {"type": "any"}
        elif isinstance(tool_choice, dict):
            # Specific tool requested
            if tool_choice.get("type") == "function":
                return {
                    "type": "tool",
                    "name": tool_choice.get("function", {}).get("name", ""),
                }
        return {"type": "auto"}

    def _convert_tool_call_to_tool_use(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Convert OpenAI tool call to Anthropic tool_use block.

        Args:
            tool_call: Tool call in OpenAI format

        Returns:
            Tool use block in Anthropic format
        """
        func = tool_call.get("function", {})
        arguments = func.get("arguments", "{}")

        # Parse arguments JSON string to dict
        try:
            input_dict = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            input_dict = {}

        return {
            "type": "tool_use",
            "id": tool_call.get("id", ""),
            "name": func.get("name", ""),
            "input": input_dict,
        }

    def _extract_text_content(self, content_blocks: list[Any]) -> str | None:
        """Extract text content from Anthropic response content blocks.

        Args:
            content_blocks: List of content blocks from response

        Returns:
            Combined text content or None
        """
        text_parts = []
        for block in content_blocks:
            if hasattr(block, "type") and block.type == "text":
                text_parts.append(block.text)
        return "".join(text_parts) if text_parts else None

    def _extract_tool_calls(self, content_blocks: list[Any]) -> list[dict[str, Any]] | None:
        """Extract tool calls from Anthropic response content blocks.

        Converts Anthropic tool_use blocks to OpenAI tool call format
        for compatibility with the unified interface.

        Args:
            content_blocks: List of content blocks from response

        Returns:
            List of tool calls in OpenAI format or None
        """
        tool_calls = []
        for block in content_blocks:
            if hasattr(block, "type") and block.type == "tool_use":
                # Convert to OpenAI format for unified handling
                tool_call = {
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input) if block.input else "{}",
                    },
                }
                tool_calls.append(tool_call)
        return tool_calls if tool_calls else None

    def _map_stop_reason(self, stop_reason: str | None) -> str:
        """Map Anthropic stop reason to unified format.

        Args:
            stop_reason: Anthropic stop reason

        Returns:
            Unified stop reason string
        """
        mapping = {
            "end_turn": "stop",
            "stop_sequence": "stop",
            "tool_use": "tool_calls",
            "max_tokens": "length",
        }
        return mapping.get(stop_reason or "", "stop")

    def supports_feature(self, feature: str) -> bool:
        """Check if Anthropic supports a feature.

        Args:
            feature: Feature name

        Returns:
            True if supported
        """
        supported_features = {
            "streaming": True,
            "tools": True,
            "tool_choice": True,
            "vision": True,
            "json_mode": False,
            "reasoning": True,
        }
        return supported_features.get(feature, False)
