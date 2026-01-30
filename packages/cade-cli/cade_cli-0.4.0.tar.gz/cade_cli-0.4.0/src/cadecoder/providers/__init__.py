"""Provider package for LLM integrations.

This package provides a clean, unified interface for different LLM providers
with automatic registration and easy access.
"""

from cadecoder.core.config import get_config
from cadecoder.core.logging import log
from cadecoder.providers.anthropic import AnthropicProvider
from cadecoder.providers.base import (
    Provider,
    ProviderError,
    ProviderRegistry,
    ProviderRequest,
    ProviderResponse,
    ProviderType,
    StreamEvent,
    provider_registry,
)
from cadecoder.providers.ollama import OllamaProvider
from cadecoder.providers.openai import OpenAIProvider


def get_provider_for_model(model: str) -> Provider | None:
    """Get the appropriate provider for a given model name.

    Auto-detects provider based on model name prefix:
    - claude-* -> Anthropic
    - gpt-*, o1-*, o3-*, o4-* -> OpenAI
    - Unknown models -> OpenAI (assume OpenAI-compatible API)

    Args:
        model: Model identifier (e.g., "claude-opus-4-5-20251101", "gpt-5.2", "llama3:70b")

    Returns:
        The appropriate provider, or None if not available
    """
    model_lower = model.lower()

    # Claude models -> Anthropic
    if model_lower.startswith("claude"):
        provider = provider_registry.get(ProviderType.ANTHROPIC)
        if provider:
            return provider
        log.warning(f"Model '{model}' requires Anthropic but ANTHROPIC_API_KEY not set")
        return None

    # OpenAI models OR unknown models -> OpenAI (assume OpenAI-compatible API)
    provider = provider_registry.get(ProviderType.OPENAI)
    if provider:
        return provider

    log.warning(f"No provider available for model '{model}'")
    return None


def initialize_providers() -> None:
    """Initialize and register available providers.

    Reads configuration from environment variables and config file.
    Preference: env var > config file > default
    """
    import os

    config = get_config()
    model_settings = config.model_settings

    # Register OpenAI if configured (env vars take precedence over config)
    openai_api_key = os.environ.get("OPENAI_API_KEY") or model_settings.api_key
    openai_base_url = os.environ.get("OPENAI_BASE_URL") or model_settings.host

    if openai_api_key:
        try:
            openai_provider = OpenAIProvider(api_key=openai_api_key, base_url=openai_base_url)
            provider_registry.register(openai_provider)
            log.info("Registered OpenAI provider")
        except Exception as e:
            log.warning(f"Failed to register OpenAI provider: {e}")

    # Register Anthropic if configured
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            anthropic_provider = AnthropicProvider()
            provider_registry.register(anthropic_provider)
            log.info("Registered Anthropic provider")
        except Exception as e:
            log.warning(f"Failed to register Anthropic provider: {e}")

    # Register Ollama if configured
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL")
    if ollama_base_url:
        try:
            ollama_provider = OllamaProvider(base_url=ollama_base_url)
            provider_registry.register(ollama_provider)
            log.info(f"Registered Ollama provider at {ollama_base_url}")
        except Exception as e:
            log.warning(f"Failed to register Ollama provider: {e}")

    # Set default based on DEFAULT_AI_MODEL
    from cadecoder.core.constants import DEFAULT_AI_MODEL

    default_provider = get_provider_for_model(DEFAULT_AI_MODEL)
    if default_provider:
        provider_registry.set_default(default_provider.provider_type)
        log.info(
            f"Default provider set to {default_provider.provider_type.value} for model {DEFAULT_AI_MODEL}"
        )


# Auto-initialize on import
initialize_providers()


__all__ = [
    # Base classes
    "Provider",
    "ProviderError",
    "ProviderRegistry",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderType",
    "StreamEvent",
    "provider_registry",
    # Providers
    "AnthropicProvider",
    "OllamaProvider",
    "OpenAIProvider",
    # Functions
    "initialize_providers",
    "get_provider_for_model",
]
