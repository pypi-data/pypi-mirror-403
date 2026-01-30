"""Ollama provider for local LLM inference with native tool calling support."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from cadecoder.core.logging import log
from cadecoder.providers.base import (
    Provider,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
    ProviderType,
    StreamEvent,
)


class OllamaProvider(Provider):
    """Provider for Ollama using native API with full tool calling support.

    Unlike OpenAI compatibility layer, this uses Ollama's native /api/chat endpoint
    which properly supports tool calling, thinking mode, and streaming.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama provider.

        Args:
            base_url: Base URL for Ollama server (default: http://localhost:11434)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        self._supported_models: list[str] = []  # Dynamic - determined by Ollama server
        log.info(f"Initialized Ollama provider with base_url={self.base_url}")

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.OLLAMA

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models (determined dynamically by Ollama)."""
        return self._supported_models

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert provider messages to Ollama format.

        Args:
            messages: Messages in provider format

        Returns:
            Messages in Ollama format
        """
        ollama_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            # Convert content blocks to text if needed
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif hasattr(block, "text"):
                        text_parts.append(block.text)
                content = "\n".join(text_parts)

            ollama_msg: dict[str, Any] = {
                "role": role,
                "content": content or "",
            }

            # Add tool calls if present
            if msg.get("tool_calls"):
                ollama_msg["tool_calls"] = msg["tool_calls"]

            # Add tool results
            if role == "tool":
                ollama_msg["tool_name"] = msg.get("tool_name")

            ollama_messages.append(ollama_msg)

        return ollama_messages

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Send a completion request to Ollama.

        Args:
            request: Provider request with model, messages, tools, etc.

        Returns:
            Provider response with content and tool calls

        Raises:
            ProviderError: If the request fails
        """
        try:
            payload: dict[str, Any] = {
                "model": request.model,
                "messages": self._convert_messages(request.messages),
                "stream": False,
            }

            # Add tools if present
            if request.tools:
                payload["tools"] = request.tools

            # Add optional parameters
            if request.max_tokens:
                payload["options"] = payload.get("options", {})
                payload["options"]["num_predict"] = request.max_tokens

            if request.temperature is not None:
                payload["options"] = payload.get("options", {})
                payload["options"]["temperature"] = request.temperature

            if request.system_prompt:
                # Prepend system message
                payload["messages"].insert(0, {"role": "system", "content": request.system_prompt})

            log.debug(
                f"Ollama request: model={request.model}, messages={len(payload['messages'])}, tools={len(request.tools) if request.tools else 0}"
            )

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            message = result.get("message", {})

            # Extract content (combine thinking and regular content)
            content_parts = []
            if message.get("thinking"):
                content_parts.append(f"[Thinking: {message['thinking']}]")
            if message.get("content"):
                content_parts.append(message["content"])
            content = "\n".join(content_parts) if content_parts else None

            # Extract tool calls
            tool_calls = None
            if message.get("tool_calls"):
                tool_calls = []
                for i, tool_call in enumerate(message["tool_calls"]):
                    func = tool_call.get("function", {})
                    # Parse arguments if they're a string
                    arguments = func.get("arguments", {})
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except Exception:
                            pass

                    tool_calls.append(
                        {
                            "id": tool_call.get("id", str(i)),
                            "type": "function",
                            "function": {
                                "name": func.get("name", ""),
                                "arguments": arguments,
                            },
                        }
                    )

            # Determine finish reason
            finish_reason = "stop"
            if tool_calls:
                finish_reason = "tool_calls"

            # Parse usage (Ollama may not provide accurate token counts)
            usage_data = result.get("usage", {})
            usage = {
                "prompt_tokens": usage_data.get("prompt_tokens", 0),
                "completion_tokens": usage_data.get("completion_tokens", 0),
                "total_tokens": usage_data.get("total_tokens", 0),
            }

            return ProviderResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
                usage=usage,
                model=request.model,
                provider=ProviderType.OLLAMA,
            )

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise ProviderError(
                f"Ollama request failed: {e.response.status_code} - {error_detail}",
                provider=ProviderType.OLLAMA,
                status_code=e.response.status_code,
            ) from e
        except Exception as e:
            raise ProviderError(
                f"Ollama request failed: {e}",
                provider=ProviderType.OLLAMA,
            ) from e

    async def stream(self, request: ProviderRequest) -> AsyncIterator[StreamEvent]:
        """Stream a completion from Ollama.

        Args:
            request: Provider request with model, messages, tools, etc.

        Yields:
            StreamEvent with incremental content and tool calls

        Raises:
            ProviderError: If the stream fails
        """
        try:
            payload: dict[str, Any] = {
                "model": request.model,
                "messages": self._convert_messages(request.messages),
                "stream": True,
            }

            # Add tools if present
            if request.tools:
                payload["tools"] = request.tools

            # Add optional parameters
            if request.max_tokens:
                payload["options"] = payload.get("options", {})
                payload["options"]["num_predict"] = request.max_tokens

            if request.temperature is not None:
                payload["options"] = payload.get("options", {})
                payload["options"]["temperature"] = request.temperature

            if request.system_prompt:
                payload["messages"].insert(0, {"role": "system", "content": request.system_prompt})

            log.debug(f"Ollama stream request: model={request.model}")

            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        chunk = json.loads(line)
                    except Exception:
                        continue

                    message = chunk.get("message", {})

                    # Yield thinking
                    if message.get("thinking"):
                        yield StreamEvent(
                            type="content_block_delta",
                            content=f"[Thinking: {message['thinking']}]",
                        )

                    # Yield text content
                    if message.get("content"):
                        yield StreamEvent(
                            type="content_block_delta",
                            content=message["content"],
                        )

                    # Yield tool calls
                    if message.get("tool_calls"):
                        for tool_call in message["tool_calls"]:
                            func = tool_call.get("function", {})
                            yield StreamEvent(
                                type="tool_use",
                                content=None,
                                metadata={
                                    "tool_name": func.get("name", ""),
                                    "tool_input": func.get("arguments", {}),
                                },
                            )

                    # Check if done
                    if chunk.get("done"):
                        break

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise ProviderError(
                f"Ollama stream failed: {e.response.status_code} - {error_detail}",
                provider=ProviderType.OLLAMA,
                status_code=e.response.status_code,
            ) from e
        except Exception as e:
            raise ProviderError(
                f"Ollama stream failed: {e}",
                provider=ProviderType.OLLAMA,
            ) from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
