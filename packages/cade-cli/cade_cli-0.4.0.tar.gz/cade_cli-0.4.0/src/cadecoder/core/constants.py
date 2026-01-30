"""Constants used across the cade application."""

from __future__ import annotations

import os
import pathlib  # Added for PROJECT_ROOT
from typing import Final

# ------------------------------------------------------------------------------
# General Application & AI Configuration
# ------------------------------------------------------------------------------

DEFAULT_AI_MODEL: Final[str] = "claude-opus-4-5-20251101"
DEFAULT_MAX_TOKENS: Final[int] = 1_000_000
MODEL_SERVICE: Final[str] = os.environ.get("CADE_MODEL_SERVICE", "openai").lower()
DEFAULT_TEMPERATURE: Final[float] = 0.7

# Backwards‑compatibility aliases for AI model (scheduled for deprecation)
DEFAULT_MODEL: Final[str] = DEFAULT_AI_MODEL
MAX_TOKENS: Final[int] = DEFAULT_MAX_TOKENS

# ------------------------------------------------------------------------------
# Project & File Operations
# ------------------------------------------------------------------------------

PROJECT_ROOT: Final[pathlib.Path] = pathlib.Path(os.getenv("PROJECT_ROOT", ".")).resolve()
MAX_PREVIEW_BYTES: Final[int] = 65_536  # For truncating file previews by tools
MAX_LIST_DEPTH: Final[int] = 40  # Max depth for listing files by tools
MAX_LIST_RESULTS: Final[int] = 10_000  # Max results for listing files by tools
MODE_OVERWRITE: Final[str] = "overwrite"  # File write mode
MODE_APPEND: Final[str] = "append"  # File write mode

MAX_AGENT_TOOLS: Final[int] = 120  # Max tools to provide to agent (OpenAI limit is 128)
MAX_CONCURRENT_STEPS: Final[int] = (
    5  # Max steps to execute in parallel (prevents resource exhaustion)
)

# ------------------------------------------------------------------------------
# Orchestrator & Execution Configuration
# ------------------------------------------------------------------------------

# Execution limits
MAX_EXECUTION_ITERATIONS: Final[int] = 100  # Max iterations for streaming execution

# Planning defaults
DEFAULT_COMPLEXITY_HINT: Final[str] = "moderate"  # Default complexity hint for planning

# ------------------------------------------------------------------------------
# Hosts & Paths
# ------------------------------------------------------------------------------

PROD_CLOUD_HOST: Final[str] = "cloud.arcade.dev"
PROD_ENGINE_HOST: Final[str] = "api.arcade.dev"
LOCALHOST: Final[str] = "localhost"

# Port constants
DEFAULT_DEV_PORT: Final[int] = 9099  # Default port for localhost development
DEFAULT_CALLBACK_PORT: Final[int] = 9905  # Port for OAuth callback server
DEFAULT_LOGIN_PORT: Final[int] = 8000  # Default port for login endpoint

# Output truncation limits (line length, not total characters)
MAX_DEBUG_OUTPUT_LENGTH: Final[int] = 500  # Max chars per line for debug/log output
MAX_DISPLAY_LINE_LENGTH: Final[int] = 100  # Content width (10-char margins on 120-char terminal)
MAX_ERROR_LINE_LENGTH: Final[int] = 100  # Max chars per line for error messages

# Tool display configuration
DEFAULT_PANEL_WIDTH: Final[int] = 100  # Width for tool result panels (matches content width)
DEFAULT_MAX_LINES: Final[int] = 10  # Default max lines for tool result display

# Output formatting
OUTPUT_MAX_WIDTH: Final[int] = 100  # Max content width (120 terminal - 10 margin each side)
OUTPUT_MARGIN: Final[int] = 10  # Margin on each side of terminal

# UI Style configuration
UI_STYLE: Final[str] = os.environ.get("CADE_UI_STYLE", "minimal")  # Options: "minimal", "panels"

ARCADE_CONFIG_PATH: Final[str] = os.path.join(
    os.path.expanduser(os.getenv("ARCADE_WORK_DIR", "~")), ".arcade"
)
CREDENTIALS_FILE_PATH: Final[str] = os.path.join(ARCADE_CONFIG_PATH, "credentials.yaml")

# ------------------------------------------------------------------------------
# Template Paths
# ------------------------------------------------------------------------------

TEMPLATES_DIR: Final[pathlib.Path] = pathlib.Path(__file__).parent.parent / "templates"
LOGIN_SUCCESS_TEMPLATE: Final[str] = "login_success.html"
LOGIN_FAILED_TEMPLATE: Final[str] = "login_failed.html"


def get_template_path(template_name: str) -> pathlib.Path:
    """Get the full path to a template file."""
    return TEMPLATES_DIR / template_name


def load_template(template_name: str) -> bytes:
    """Load a template file and return its contents as bytes."""
    template_path = get_template_path(template_name)
    return template_path.read_bytes()


# ------------------------------------------------------------------------------
# Code Analysis & File Patterns
# ------------------------------------------------------------------------------

DEFAULT_IGNORE_PATTERNS: Final[list[str]] = [
    # Build & distribution
    "node_modules",
    "dist",
    "build",
    "*.egg-info",
    # Version control
    ".git",
    # Editors & IDEs
    ".vscode",
    ".idea",
    ".cursor",
    ".claude",
    # OS files
    ".DS_Store",
    "Thumbs.db",
    # Testing & coverage
    "coverage",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "htmlcov",
    ".coverage",
    # Virtual environments
    ".venv",
    "venv",
    "env",
    # Environment & secrets
    ".env",
    ".env.local",
    ".env.*.local",
    # Compiled & bundled files
    "*.min.js",
    "*.bundle.js",
    "*.map",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dylib",
    "__pycache__",
]

EXTENSION_TO_LANGUAGE: Final[dict[str, str]] = {
    "ts": "TypeScript",
    "tsx": "TypeScript (React)",
    "js": "JavaScript",
    "jsx": "JavaScript (React)",
    "py": "Python",
    "java": "Java",
    "c": "C",
    "cpp": "C++",
    "cs": "C#",
    "go": "Go",
    "rs": "Rust",
    "php": "PHP",
    "rb": "Ruby",
    "swift": "Swift",
    "kt": "Kotlin",
    "scala": "Scala",
    "html": "HTML",
    "css": "CSS",
    "scss": "SCSS",
    "less": "Less",
    "json": "JSON",
    "md": "Markdown",
    "yml": "YAML",
    "yaml": "YAML",
    "xml": "XML",
    "sql": "SQL",
    "sh": "Shell",
    "bat": "Batch",
    "ps1": "PowerShell",
    "dockerfile": "Dockerfile",
    "tf": "Terraform",
    "hcl": "HCL",
}

CODE_EXTENSIONS: Final[set[str]] = {
    "js",
    "jsx",
    "ts",
    "tsx",
    "py",
    "java",
    "c",
    "cpp",
    "cs",
    "go",
    "rs",
    "php",
    "rb",
    "swift",
    "kt",
    "scala",
}

PYTHON_STDLIB_MODULES: Final[set[str]] = {
    "os",
    "sys",
    "re",
    "math",
    "datetime",
    "time",
    "random",
    "json",
    "csv",
    "collections",
    "itertools",
    "functools",
    "pathlib",
    "shutil",
    "glob",
    "pickle",
    "urllib",
    "http",
    "logging",
    "argparse",
    "unittest",
    "subprocess",
    "threading",
    "multiprocessing",
    "typing",
    "enum",
    "io",
    "tempfile",
    "contextlib",
    "decimal",
    "fractions",
    "statistics",
    "asyncio",
    "concurrent",
    "socket",
    "ssl",
    "select",
    "signal",
    "struct",
    "zlib",
    "gzip",
    "bz2",
    "lzma",
    "tarfile",
    "zipfile",
    "calendar",
    "copy",
    "pprint",
    "base64",
    "hashlib",
    "hmac",
    "secrets",
    "uuid",
    "xml",
    "gettext",
    "locale",
    "platform",
    "importlib",
    "inspect",
    "pdb",
    "profile",
    "traceback",
    "warnings",
    "weakref",
    "abc",
    "numbers",
    "operator",
    "heapq",
    "bisect",
    "array",
    "queue",
    "dataclasses",
    "graphlib",
    "sched",
    "zoneinfo",
}
