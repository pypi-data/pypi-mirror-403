"""Local built-in tools for the agent.

This module provides filesystem, shell, search, and git tools
that run locally on the user's machine.
"""

from collections.abc import Callable

from cadecoder.tools.local.filesystem import (
    edit_file_insert_tool,
    edit_file_tool,
    list_files_tool,
    read_file_tool,
    write_file_tool,
)
from cadecoder.tools.local.git import (
    git_branch_tool,
    git_diff_tool,
    git_log_tool,
    git_status_tool,
)
from cadecoder.tools.local.search import grep_tool, ripgrep_tool, search_code_tool
from cadecoder.tools.local.shell import bash_tool, execute_command_tool

# All exported tools
_ALL_TOOLS: list[Callable] = [
    # Filesystem
    list_files_tool,
    read_file_tool,
    write_file_tool,
    edit_file_tool,
    edit_file_insert_tool,
    # Shell
    execute_command_tool,
    bash_tool,
    # Search
    search_code_tool,
    grep_tool,
    ripgrep_tool,
    # Git
    git_status_tool,
    git_diff_tool,
    git_log_tool,
    git_branch_tool,
]


def get_all_tools() -> list[Callable]:
    """Returns a list of all local tool functions.

    Returns:
        List of callable tool functions with __tool_name__ and
        __tool_description__ attributes set by the @tool decorator.
    """
    return _ALL_TOOLS.copy()


__all__ = [
    "get_all_tools",
    # Filesystem
    "list_files_tool",
    "read_file_tool",
    "write_file_tool",
    "edit_file_tool",
    "edit_file_insert_tool",
    # Shell
    "execute_command_tool",
    "bash_tool",
    # Search
    "search_code_tool",
    "grep_tool",
    "ripgrep_tool",
    # Git
    "git_status_tool",
    "git_diff_tool",
    "git_log_tool",
    "git_branch_tool",
]
