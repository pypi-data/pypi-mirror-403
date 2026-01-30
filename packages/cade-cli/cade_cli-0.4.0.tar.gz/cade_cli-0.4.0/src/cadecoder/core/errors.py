"""Custom error types for CadeCoder.

This module defines a comprehensive exception hierarchy for the application.
All custom exceptions inherit from CadeCoderError, allowing for consistent
error handling throughout the codebase.
"""


class CadeCoderError(Exception):
    """Base class for all CadeCoder-specific errors.

    All custom exceptions should inherit from this class to enable
    consistent error handling and filtering.
    """

    pass


class FileSystemError(CadeCoderError):
    """Raised for general file system operations errors."""

    pass


class FileOpsError(CadeCoderError):
    """Raised for errors during file operations like diffing or patching."""

    pass


class ConfigError(CadeCoderError):
    """Raised for configuration loading, validation, or saving errors."""

    pass


class AuthError(CadeCoderError):
    """Raised for authentication or API key related errors."""

    pass


class StorageError(CadeCoderError):
    """Raised for errors during storage operations."""

    pass


def get_provider_config_help() -> str:
    """Return help text for configuring an AI provider."""
    return """
No AI provider configured.

Options:
  Remote LLM:
    export OPENAI_API_KEY="your-key"
      or
    export ANTHROPIC_API_KEY="your-key"

  Local LLM:
    export OPENAI_BASE_URL="<endpoint>"
    export OPENAI_API_KEY="local"

    Or just: --endpoint <url> --model <model>
""".strip()
