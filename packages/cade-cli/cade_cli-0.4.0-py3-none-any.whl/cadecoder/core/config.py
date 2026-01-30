"""Configuration management for CadeCoder CLI.

Handles loading Arcade credentials (via arcade-core) and CadeCoder specific settings.
Credentials are shared with arcade-cli at ~/.arcade/credentials.yaml.
"""

import os
import threading
import tomllib
from functools import lru_cache
from pathlib import Path

import toml
import yaml
from arcade_core.auth_tokens import get_valid_access_token
from arcade_core.config_model import Config as ArcadeConfig
from arcade_core.constants import PROD_COORDINATOR_HOST
from pydantic import BaseModel, ConfigDict, Field

from cadecoder.core import constants
from cadecoder.core.errors import AuthError, ConfigError

# --- Constants ---

CADECODER_CONFIG_DIR_NAME = "cadecoder"
CADECODER_CONFIG_FILE_NAME = "cadecoder.toml"


# --- Pydantic Models for CadeCoder Settings ---


class ResponsesAPIConfig(BaseModel):
    """Configuration for Responses API."""

    model_config = ConfigDict(extra="ignore")
    enabled: bool = Field(default=True, description="Enable Responses API when available")
    streaming_enabled: bool = Field(
        default=True, description="Enable streaming responses by default"
    )


class ModelConfig(BaseModel):
    """Model configuration settings."""

    model_config = ConfigDict(extra="ignore")
    provider: str = Field(
        default="openai", description="AI provider name (openai, anthropic, etc.)"
    )
    model: str = Field(default=constants.DEFAULT_AI_MODEL, description="Model name")
    host: str | None = Field(
        default=None,
        description="Custom API host (for OpenAI-compatible APIs)",
    )
    api_key: str | None = Field(default=None, description="API key (overrides environment)")


class ToolConfig(BaseModel):
    """Tool configuration settings.

    Note: Tool filtering can be implemented at the MCP server level
    by enabling/disabling specific MCP servers in mcp_servers.json.
    """

    model_config = ConfigDict(extra="ignore")


class CadeCoderSettings(BaseModel):
    """Model for settings specific to cadecoder.toml."""

    model_config = ConfigDict(extra="ignore")
    default_model: str = constants.DEFAULT_AI_MODEL
    debug_mode: bool = Field(
        default=True,
        description="Enable debug mode for verbose logging and error details.",
    )
    use_responses_api: bool = Field(
        default=True, description="Use OpenAI Responses API when available"
    )
    responses_config: ResponsesAPIConfig = Field(
        default_factory=ResponsesAPIConfig,
        description="Responses API specific configuration",
    )
    model_settings: ModelConfig = Field(
        default_factory=ModelConfig, description="Model configuration"
    )
    tool_settings: ToolConfig = Field(default_factory=ToolConfig, description="Tool configuration")


# --- Helper Functions ---


def _get_cadecoder_config_path() -> Path:
    """Gets the path to the cadecoder specific config file."""
    home = Path.home()
    cadecoder_dir = home / ".cadecoder"
    return cadecoder_dir / CADECODER_CONFIG_FILE_NAME


@lru_cache(maxsize=1)
def _load_cadecoder_settings() -> CadeCoderSettings:
    """Loads the CadeCoder specific settings from cadecoder.toml.

    Creates a default file if it doesn't exist.
    Returns default settings if file is invalid or missing.
    """
    config_path = _get_cadecoder_config_path()

    if config_path.exists():
        try:
            with config_path.open("rb") as f:
                config_data = tomllib.load(f)
            return CadeCoderSettings.model_validate(config_data)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Error decoding TOML file '{config_path}': {e}. Using defaults.")
        except OSError as e:
            raise ConfigError(f"Error reading settings file '{config_path}': {e}. Using defaults.")
    else:
        default_settings = CadeCoderSettings()
        _save_cadecoder_settings(default_settings)
        return default_settings


def _save_cadecoder_settings(settings: CadeCoderSettings) -> None:
    """Save the CadeCoder specific settings to cadecoder.toml."""
    config_path = _get_cadecoder_config_path()
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = settings.model_dump(mode="python")
        with config_path.open("w", encoding="utf-8") as f:
            toml.dump(config_data, f)
    except (OSError, TypeError) as e:
        raise ConfigError(f"Error writing CadeCoder settings file '{config_path}': {e}") from e


def _load_arcade_config() -> ArcadeConfig | None:
    """Load arcade-core config if available."""
    try:
        return ArcadeConfig.load_from_file()
    except (FileNotFoundError, ValueError):
        return None


def _check_legacy_api_key() -> tuple[str, str] | None:
    """Check for legacy API key credentials (backward compatibility).

    Returns:
        Tuple of (api_key, email) if found, None otherwise.
    """
    creds_path = Path.home() / ".arcade" / "credentials.yaml"
    if not creds_path.exists():
        return None

    try:
        with creds_path.open() as f:
            data = yaml.safe_load(f) or {}

        cloud = data.get("cloud", {})
        if isinstance(cloud, dict) and "api" in cloud:
            api_key = cloud.get("api", {}).get("key")
            email = cloud.get("user", {}).get("email")
            if api_key and email:
                return api_key, email
    except Exception:
        pass

    return None


# --- Singleton Config Class ---


class AppConfig:
    """Singleton configuration class for CadeCoder.

    Loads credentials from arcade-core (OAuth) or falls back to
    legacy API key format. CadeCoder-specific settings are loaded
    from ~/.cadecoder/cadecoder.toml.
    """

    _instance: "AppConfig | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "AppConfig":
        """Create or return the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_configuration()
        return cls._instance

    def _load_configuration(self) -> None:
        """Load configurations from arcade-core and cadecoder.toml."""
        self._arcade_config: ArcadeConfig | None = None
        self._legacy_api_key: str | None = None
        self._legacy_email: str | None = None

        # Try to load arcade-core config (new OAuth format)
        self._arcade_config = _load_arcade_config()

        # Check for environment variable override
        env_api_key = os.environ.get("ARCADE_API_KEY")
        env_email = os.environ.get("ARCADE_USER_EMAIL")

        if env_api_key:
            # Environment variable takes precedence
            self._legacy_api_key = env_api_key
            self._legacy_email = env_email
        elif self._arcade_config and self._arcade_config.is_authenticated():
            # New OAuth format is available
            pass
        else:
            # Fall back to legacy API key format
            legacy = _check_legacy_api_key()
            if legacy:
                self._legacy_api_key, self._legacy_email = legacy

        # Load CadeCoder-specific settings
        try:
            self._settings = _load_cadecoder_settings()
        except ConfigError:
            self._settings = CadeCoderSettings()

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (OAuth or API key)."""
        if self._legacy_api_key:
            return True
        if self._arcade_config and self._arcade_config.is_authenticated():
            return True
        return False

    @property
    def api_key(self) -> str:
        """Get the API key or access token for Arcade API calls.

        For OAuth auth, this returns a valid access token (auto-refreshed).
        For legacy auth, this returns the API key.

        Raises:
            AuthError: If not authenticated.
        """
        # Environment variable override
        if self._legacy_api_key:
            return self._legacy_api_key

        # Try OAuth token
        if self._arcade_config and self._arcade_config.is_authenticated():
            try:
                coordinator_url = (
                    self._arcade_config.coordinator_url or f"https://{PROD_COORDINATOR_HOST}"
                )
                return get_valid_access_token(coordinator_url)
            except ValueError as e:
                raise AuthError(f"Failed to get access token: {e}") from e

        raise AuthError("Not authenticated. Run 'cade login' to authenticate with Arcade Cloud.")

    @property
    def base_url(self) -> str | None:
        """Returns the Arcade base URL from environment."""
        return os.environ.get("ARCADE_BASE_URL")

    @property
    def model_api_key(self) -> str:
        """Returns the API key for the model service (OpenAI, Anthropic, etc.)."""
        model_service = constants.MODEL_SERVICE
        try:
            if model_service == "openai":
                return os.environ["OPENAI_API_KEY"]
            elif model_service == "anthropic":
                return os.environ["ANTHROPIC_API_KEY"]
            else:
                raise ValueError(f"Invalid model service: {model_service}")
        except KeyError:
            raise AuthError(f"API key is not available for {model_service}.")

    @property
    def user_email(self) -> str:
        """Returns the user's email address."""
        # Legacy format or env override
        if self._legacy_email:
            return self._legacy_email

        # OAuth format
        if self._arcade_config and self._arcade_config.user:
            return self._arcade_config.user.email or ""

        return ""

    @property
    def org_id(self) -> str | None:
        """Returns the active organization ID (OAuth only)."""
        if self._arcade_config and self._arcade_config.context:
            return self._arcade_config.context.org_id
        return None

    @property
    def project_id(self) -> str | None:
        """Returns the active project ID (OAuth only)."""
        if self._arcade_config and self._arcade_config.context:
            return self._arcade_config.context.project_id
        return None

    @property
    def settings(self) -> CadeCoderSettings:
        """Returns the CadeCoder specific settings."""
        return self._settings

    @property
    def model_settings(self) -> ModelConfig:
        """Returns the model configuration."""
        return self._settings.model_settings

    @property
    def tool_settings(self) -> ToolConfig:
        """Returns the tool configuration."""
        return self._settings.tool_settings

    @property
    def app_dir(self) -> str:
        """Returns the CadeCoder application directory path."""
        base = os.environ.get("CADECODER_HOME", Path.home())
        return str(Path(base) / ".cadecoder")

    def ensure_app_dir(self) -> str:
        """Ensures the application directory exists and returns its path."""
        path = Path(self.app_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return str(path)
        except OSError as e:
            raise ConfigError(f"Could not create application directory {path}: {e}") from e

    def reload(self) -> None:
        """Clear caches and reload configuration."""
        _load_cadecoder_settings.cache_clear()
        self._load_configuration()


# --- Public Access ---

# Lazy initialization - don't create instance on import
_config: AppConfig | None = None

# Runtime verbose flag (set by CLI --verbose)
_verbose_mode: bool = False


def set_verbose_mode(verbose: bool) -> None:
    """Set the runtime verbose mode flag."""
    global _verbose_mode
    _verbose_mode = verbose


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return _verbose_mode


def is_local_only_mode() -> bool:
    """Check if local-only mode is enabled via environment variable.

    When enabled, remote tools are disabled and only local tools are used.

    Returns:
        True if CADE_LOCAL_ONLY environment variable is set to a truthy value.
    """
    return os.environ.get("CADE_LOCAL_ONLY", "").lower() in ("1", "true", "yes")


def get_config() -> AppConfig:
    """Get the singleton AppConfig instance.

    Use this function instead of directly accessing `config` to ensure
    lazy initialization (no AuthError on import).
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


# For backward compatibility with code that imports `config` directly
# Note: prefer using get_config() for lazy initialization
class _ConfigProxy:
    """Proxy that provides lazy access to AppConfig singleton."""

    def __getattr__(self, name: str):
        return getattr(get_config(), name)


config = _ConfigProxy()
