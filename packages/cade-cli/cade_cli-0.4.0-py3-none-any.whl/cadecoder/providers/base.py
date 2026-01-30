"""Base provider interface for LLM integrations.

This module defines a clean, simple interface that all LLM providers
must implement, ensuring consistent behavior across different AI services.
Also includes provider-related utility functions.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from cadecoder.core.types import ConversationMessageDict


class ProviderType(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ARCADE = "arcade"
    LOCAL = "local"
    OLLAMA = "ollama"


class ProviderRequest(BaseModel):
    """Unified request format for all providers."""

    messages: list[ConversationMessageDict] = Field(..., description="Conversation messages")
    model: str = Field(..., description="Model to use")
    tools: list[dict[str, Any]] | None = Field(None, description="Available tools in OpenAI format")
    temperature: float = Field(0.7, description="Response randomness")
    max_tokens: int | None = Field(None, description="Maximum response tokens")
    stream: bool = Field(False, description="Whether to stream responses")

    # Optional parameters
    tool_choice: str | dict[str, Any] | None = Field(None, description="Tool selection preference")
    system_prompt: str | None = Field(None, description="System prompt override")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific metadata")


class ProviderResponse(BaseModel):
    """Unified response format from providers."""

    content: str | None = Field(None, description="Response content")
    tool_calls: list[dict[str, Any]] | None = Field(None, description="Tool calls requested")
    finish_reason: str = Field("stop", description="Why generation stopped")
    usage: dict[str, int] | None = Field(None, description="Token usage statistics")
    model: str | None = Field(None, description="Model that was used")
    provider: ProviderType | None = Field(None, description="Provider type")


class StreamEvent(BaseModel):
    """Streaming event from providers."""

    type: str = Field(..., description="Event type (see ExecutionEventType for allowed values)")
    content: str | None = Field(None, description="Content delta")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Event metadata")


class Provider(ABC):
    """Abstract base class for LLM providers.

    This defines the minimal interface that all providers must implement.
    Each provider adapter translates between this interface and the
    provider's native API.
    """

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        ...

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """Return list of supported model names."""
        ...

    @abstractmethod
    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Create a completion.

        Args:
            request: The request to process

        Returns:
            The provider's response

        Raises:
            ProviderError: If the request fails
        """
        ...

    @abstractmethod
    def stream(self, request: ProviderRequest) -> AsyncIterator[StreamEvent]:
        """Stream a completion.

        Args:
            request: The request to process

        Yields:
            Stream events as they arrive

        Raises:
            ProviderError: If the request fails
        """
        ...

    def supports_feature(self, feature: str) -> bool:
        """Check if provider supports a feature.

        Args:
            feature: Feature name (e.g., "tools", "streaming", "vision")

        Returns:
            True if supported
        """
        # Default implementation - override in subclasses
        return feature in ["streaming", "tools"]


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(
        self,
        message: str,
        provider: ProviderType | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.details = details or {}


class ProviderRegistry:
    """Registry for managing available providers."""

    def __init__(self):
        self._providers: dict[ProviderType, Provider] = {}
        self._default_provider: ProviderType | None = None

    def register(self, provider: Provider) -> None:
        """Register a provider.

        Args:
            provider: Provider instance to register
        """
        self._providers[provider.provider_type] = provider

    def get(self, provider_type: ProviderType) -> Provider | None:
        """Get a provider by type.

        Args:
            provider_type: Type of provider to get

        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(provider_type)

    def get_default(self) -> Provider | None:
        """Get the default provider.

        Returns:
            Default provider or None if not set
        """
        if self._default_provider:
            return self.get(self._default_provider)
        # Return first available provider
        return next(iter(self._providers.values())) if self._providers else None

    def set_default(self, provider_type: ProviderType) -> None:
        """Set the default provider.

        Args:
            provider_type: Provider type to use as default
        """
        if provider_type not in self._providers:
            raise ValueError(f"Provider {provider_type} not registered")
        self._default_provider = provider_type

    @property
    def available_providers(self) -> list[ProviderType]:
        """Get list of available provider types."""
        return list(self._providers.keys())


# Global registry instance
provider_registry = ProviderRegistry()


# ============================================================================
# Provider Utility Functions
# ============================================================================


def get_total_tokens(usage_source: Any) -> int:
    """Return total tokens from a provider response or usage mapping.

    Accepts either a provider response object (with optional ``usage`` field)
    or a raw usage dictionary/object. Prefers an explicit ``total_tokens`` when
    present; otherwise computes a total from known token fields.

    Known field sets:
    - OpenAI: ``prompt_tokens``, ``completion_tokens``, optional ``reasoning_tokens``
    - Anthropic: ``input_tokens``, ``output_tokens``
    - Generic: ``total_tokens``

    Args:
        usage_source: Provider response or usage mapping/object

    Returns:
        Total token count as an integer (0 if unavailable)
    """
    if usage_source is None:
        return 0

    # If a ProviderResponse-like object, extract its usage field first
    usage = getattr(usage_source, "usage", None)
    candidate = usage if usage is not None else usage_source

    # Handle dict-like usage
    if isinstance(candidate, dict):
        # Prefer explicit total_tokens
        if "total_tokens" in candidate and candidate["total_tokens"] is not None:
            try:
                return int(candidate.get("total_tokens", 0))
            except Exception:
                return 0

        # OpenAI-style fields
        prompt = candidate.get("prompt_tokens")
        completion = candidate.get("completion_tokens")
        reasoning = candidate.get("reasoning_tokens")
        if prompt is not None or completion is not None or reasoning is not None:
            try:
                total = int(prompt or 0) + int(completion or 0)
                # Only include reasoning if present and not already included
                # Some APIs may already include reasoning in completion; when in doubt,
                # prefer inclusion to avoid undercounting.
                total += int(reasoning or 0)
                return total
            except Exception:
                return 0

        # Anthropic-style fields
        input_tokens = candidate.get("input_tokens")
        output_tokens = candidate.get("output_tokens")
        if input_tokens is not None or output_tokens is not None:
            try:
                return int(input_tokens or 0) + int(output_tokens or 0)
            except Exception:
                return 0

        return 0

    # Handle object-style usage with attributes
    # Prefer explicit total_tokens
    if hasattr(candidate, "total_tokens"):
        try:
            return int(getattr(candidate, "total_tokens", 0) or 0)
        except Exception:
            return 0

    # OpenAI-style attributes
    has_prompt = hasattr(candidate, "prompt_tokens")
    has_completion = hasattr(candidate, "completion_tokens")
    has_reasoning = hasattr(candidate, "reasoning_tokens")
    if has_prompt or has_completion or has_reasoning:
        try:
            total = int(getattr(candidate, "prompt_tokens", 0) or 0) + int(
                getattr(candidate, "completion_tokens", 0) or 0
            )
            total += int(getattr(candidate, "reasoning_tokens", 0) or 0)
            return total
        except Exception:
            return 0

    # Anthropic-style attributes
    if hasattr(candidate, "input_tokens") or hasattr(candidate, "output_tokens"):
        try:
            return int(getattr(candidate, "input_tokens", 0) or 0) + int(
                getattr(candidate, "output_tokens", 0) or 0
            )
        except Exception:
            return 0

    return 0
