"""Core modules for CadeCoder.

Note: config is intentionally NOT imported at module level to avoid
triggering auth validation on simple imports (e.g., importing constants).
Use `from cadecoder.core.config import get_config` when config is needed.
"""

from cadecoder.core.errors import CadeCoderError

__all__ = [
    "CadeCoderError",
]
