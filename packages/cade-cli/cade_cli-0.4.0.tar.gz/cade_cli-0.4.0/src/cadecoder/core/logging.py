"""Basic logging setup for CadeCoder.

This module provides structured logging with:
    - File-based logging (rotating file handler)
    - Chat thread context injection
    - No console output (file-only)

The logging is initialized on import to ensure logs are captured
even before CLI arguments are parsed.
"""

import os

# Set environment variable to disable tokenizers parallelism warning
# This must be set before any imports that use tokenizers
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import logging
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import config

# Get the logger instance first
log = logging.getLogger("cadecoder")


# --- Chat Thread Context ---


chat_thread_ctx: ContextVar[str] = ContextVar("chat_thread_ctx", default="-")


class ChatThreadFilter(logging.Filter):
    """Inject chat thread name/id into log records as 'chat_thread'.

    This filter adds thread context to all log records, enabling
    filtering and searching logs by conversation thread.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to inject chat thread context.

        Args:
            record: The log record to filter

        Returns:
            Always True (all records pass through, context is injected)
        """
        try:
            record.chat_thread = chat_thread_ctx.get()
        except Exception:
            record.chat_thread = "-"
        return True


# --- Log File Path ---


def get_log_file_path() -> Path:
    """Get the path to the log file in the cadecoder app directory.

    Returns:
        Path to the log file (creates parent directory if needed)
    """
    app_dir = Path(config.app_dir)
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "cadecoder.log"


# --- Logging Setup ---


def _create_file_handler(log_file: Path) -> RotatingFileHandler:
    """Create and configure rotating file handler.

    Args:
        log_file: Path to log file

    Returns:
        Configured RotatingFileHandler
    """
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,  # Keep 3 backup files
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)  # Always capture DEBUG in file
    handler.addFilter(ChatThreadFilter())

    # Detailed formatter for file logs
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(filename)s:%(lineno)d] - chat=%(chat_thread)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    return handler


def _configure_root_logger() -> None:
    """Configure root logger to prevent console output from other libraries.

    Sets root logger to WARNING level and removes all handlers to prevent
    other libraries from outputting to console.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Only warnings and above
    # Remove all handlers from root logger
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


def setup_logging(verbose: bool = False) -> None:
    """Set up file-only logging with no console output.

    Side effect: configures logging system.

    Args:
        verbose: If True, sets log level to DEBUG, otherwise INFO
    """
    # Remove any existing handlers to avoid duplicates
    for handler in log.handlers[:]:
        log.removeHandler(handler)

    log_level = logging.DEBUG if verbose else logging.INFO
    log.setLevel(log_level)

    # Create and add file handler
    log_file = get_log_file_path()
    file_handler = _create_file_handler(log_file)
    log.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    log.propagate = False

    # Configure root logger to prevent console output
    _configure_root_logger()

    log.debug(f"Logging initialized. Log file: {log_file}")


# Initialize logging with default settings on import
# This ensures logs go to file even before CLI args are parsed
setup_logging(verbose=False)
