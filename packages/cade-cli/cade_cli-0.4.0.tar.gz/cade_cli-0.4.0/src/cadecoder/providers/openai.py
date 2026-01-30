"""OpenAI provider adapter.

This module implements the Provider interface for OpenAI's API,
handling both standard completions and streaming responses.
"""

import os
from collections.abc import AsyncIterator
from typing import Any, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

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


class OpenAIProvider(Provider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (uses environment if not provided)
            base_url: Custom API endpoint URL (for OpenAI-compatible APIs)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")

        if not self.api_key:
            raise ProviderError("OpenAI API key not configured", ProviderType.OPENAI)

        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self._supported_models = [
            # GPT-5.x frontier models (current)
            "gpt-5.2",
            "gpt-5.1",
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-5.2-pro",
            "gpt-5-pro",
            # GPT-5 Codex models
            "gpt-5.2-codex",
            "gpt-5.1-codex",
            "gpt-5.1-codex-max",
            "gpt-5-codex",
            # GPT-4.1 models
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            # Reasoning models
            "o3",
            "o3-pro",
            "o3-mini",
            "o4-mini",
            # GPT-4o models (still available)
            "gpt-4o",
            "gpt-4o-mini",
            # Legacy models
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.OPENAI

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return self._supported_models

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Create a completion using OpenAI.

        Args:
            request: The request to process

        Returns:
            The provider's response

        Raises:
            ProviderError: If the request fails
        """
        try:
            # Build OpenAI request
            openai_request = self._build_openai_request(request)

            # Make API call
            response = await self.client.chat.completions.create(**openai_request)

            # Convert to unified response
            choice = response.choices[0]

            # Extract tool calls if present
            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]

            return ProviderResponse(
                content=choice.message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                model=response.model,
                provider=ProviderType.OPENAI,
            )

        except Exception as e:
            log.error(f"OpenAI completion failed: {e}")
            raise ProviderError(
                f"OpenAI completion failed: {str(e)}",
                provider=ProviderType.OPENAI,
                details={"error": str(e)},
            )

    async def stream(self, request: ProviderRequest) -> AsyncIterator[StreamEvent]:
        """Stream a completion from OpenAI.

        Args:
            request: The request to process

        Yields:
            Stream events as they arrive

        Raises:
            ProviderError: If the request fails
        """
        try:
            # Build OpenAI request with streaming
            openai_request = self._build_openai_request(request)
            openai_request["stream"] = True

            # Stream response
            stream = await self.client.chat.completions.create(**openai_request)

            # Track state for tool calls
            current_tool_calls: dict[int, dict[str, Any]] = {}

            async for chunk in stream:
                chunk = cast(ChatCompletionChunk, chunk)

                # Handle content delta
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamEvent(
                        type=ExecutionEventType.CONTENT.value,
                        content=chunk.choices[0].delta.content,
                    )

                # Handle tool calls
                if chunk.choices and chunk.choices[0].delta.tool_calls:
                    for tc_delta in chunk.choices[0].delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tc_delta.id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }

                        # Update tool call
                        if tc_delta.function:
                            if tc_delta.function.name:
                                current_tool_calls[idx]["function"]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                current_tool_calls[idx]["function"]["arguments"] += (
                                    tc_delta.function.arguments
                                )

                # Handle finish
                if chunk.choices and chunk.choices[0].finish_reason:
                    # Emit any pending tool calls
                    for tool_call in current_tool_calls.values():
                        yield StreamEvent(
                            type=ExecutionEventType.TOOL_CALL.value,
                            content=None,
                            metadata={"tool_call": tool_call},
                        )

                    # Emit completion event
                    yield StreamEvent(
                        type=ExecutionEventType.COMPLETE.value,
                        content=None,
                        metadata={
                            "finish_reason": chunk.choices[0].finish_reason,
                            "model": chunk.model,
                        },
                    )

        except Exception as e:
            log.error(f"OpenAI streaming failed: {e}")
            yield StreamEvent(
                type="error",
                content=str(e),
                metadata={"provider": ProviderType.OPENAI},
            )

    def _build_openai_request(self, request: ProviderRequest) -> dict[str, Any]:
        """Build OpenAI API request from unified request.

        Args:
            request: Unified request

        Returns:
            OpenAI API request dictionary
        """
        openai_request: dict[str, Any] = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
        }

        # Add optional parameters
        if request.max_tokens:
            openai_request["max_tokens"] = request.max_tokens

        if request.tools:
            openai_request["tools"] = request.tools
            log.info(f"OpenAI request includes {len(request.tools)} tools")
            # Log first few tool names for debugging
            tool_names = [t.get("function", {}).get("name", "unknown") for t in request.tools[:5]]
            log.debug(f"First few tools: {tool_names}")

        if request.tool_choice:
            openai_request["tool_choice"] = request.tool_choice

        # Add any provider-specific metadata
        if "openai" in request.metadata:
            openai_request.update(request.metadata["openai"])

        return openai_request

    def supports_feature(self, feature: str) -> bool:
        """Check if OpenAI supports a feature.

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
            "json_mode": True,
            "reasoning": False,  # Not yet
        }
        return supported_features.get(feature, False)
