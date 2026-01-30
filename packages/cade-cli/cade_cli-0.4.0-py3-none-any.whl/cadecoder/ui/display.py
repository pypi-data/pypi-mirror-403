"""Display helper functions for the TUI."""

import json
import os
import re
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cadecoder.core.constants import UI_STYLE
from cadecoder.core.logging import get_log_file_path

# Console instance - let Rich auto-detect terminal width
console = Console(stderr=True)


def _format_result_summary(result: str, max_len: int = 80) -> str:
    """Format a tool result into a brief summary.

    Intelligently summarizes JSON structures without hardcoded field names.

    Args:
        result: Raw result string (often JSON)
        max_len: Maximum summary length

    Returns:
        Brief summary string
    """
    if not result:
        return "[dim]empty[/dim]"

    # Check for error patterns
    result_lower = result.lower()
    if "failed" in result_lower[:100] or "error" in result_lower[:100]:
        # Extract HTTP status if present
        for code in ["404", "401", "403", "500", "502", "503"]:
            if code in result:
                return f"[red]{code} error[/red]"
        return "[red]failed[/red]"

    # Try to parse as JSON
    try:
        data = json.loads(result)
        return _summarize_json(data)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: truncate raw string
    preview = result.replace("\n", " ").strip()
    if len(preview) > max_len:
        return preview[: max_len - 3] + "..."
    return preview if preview else "[dim]empty[/dim]"


def _summarize_json(data: Any, depth: int = 0) -> str:
    """Recursively summarize a JSON structure.

    Args:
        data: Parsed JSON data
        depth: Current recursion depth

    Returns:
        Brief summary string
    """
    if depth > 2:
        return "..."

    if data is None:
        return "null"

    if isinstance(data, bool):
        return "✓" if data else "✗"

    if isinstance(data, int | float):
        return str(data)

    if isinstance(data, str):
        if len(data) > 40:
            return f'"{data[:37]}..."'
        return f'"{data}"' if len(data) < 20 else data[:40]

    if isinstance(data, list):
        length = len(data)
        if length == 0:
            return "[]"
        # Peek at first item type
        first = data[0]
        if isinstance(first, dict):
            return f"{length} items"
        if isinstance(first, str):
            return f"{length} strings"
        return f"{length} items"

    if isinstance(data, dict):
        if not data:
            return "{}"

        # Count totals
        total_lists = 0
        total_items = 0
        for v in data.values():
            if isinstance(v, list):
                total_lists += 1
                total_items += len(v)

        # If there are lists, summarize by total items
        if total_lists > 0:
            return f"{total_items} items" if total_items > 0 else "OK"

        # Otherwise show key count
        key_count = len(data)
        if key_count <= 3:
            return ", ".join(data.keys())
        return f"{key_count} fields"

    return str(type(data).__name__)


# Control signals that should be hidden from display but kept for continuation logic
CONTROL_SIGNAL_PATTERN = re.compile(
    r"\[(?:TASK_COMPLETE|CONTINUE|NEED_USER_INPUT)\]", re.IGNORECASE
)


def strip_control_signals(content: str, strip_whitespace: bool = False) -> str:
    """Remove control signals from content for display.

    Strips [TASK_COMPLETE], [CONTINUE], [NEED_USER_INPUT] markers
    that are used by the continuation strategy but shouldn't be
    shown to the user.

    Args:
        content: Raw content that may contain control signals
        strip_whitespace: If True, also strip leading/trailing whitespace.
                         Set to False when processing streaming chunks to
                         preserve word spacing.

    Returns:
        Content with control signals removed
    """
    if not content:
        return content
    # Remove the control signals
    cleaned = CONTROL_SIGNAL_PATTERN.sub("", content)
    # Clean up any resulting triple+ newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if strip_whitespace:
        cleaned = cleaned.strip()
    return cleaned


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def display_thread_header(thread_name: str) -> None:
    """Display the thread header/title."""
    if UI_STYLE == "minimal":
        console.print(f"[bold green]Chat Thread:[/bold green] {thread_name}")
        console.print("[dim]/help for commands, Ctrl+C to exit[/dim]")
        console.print()
    else:
        console.print(
            Panel(
                f"[bold green]{thread_name}[/bold green]",
                title="Chat Thread",
                border_style="green",
            )
        )


def display_git_branch_info(branch_name: str | None) -> None:
    """Display the current git branch information."""
    if branch_name:
        console.print(f"[dim]Git branch: {branch_name}[/dim]")


def display_help() -> None:
    """Display help information."""
    help_text = """
[bold cyan]Available Commands:[/bold cyan]

[bold]/help[/bold]          - Show this help message
[bold]/clear[/bold]         - Clear the screen
[bold]/tools[/bold]         - Show available tools
[bold]/logs[/bold]          - Show log file location and recent logs
[bold]/context[/bold]       - Show context window status and token usage
[bold]/history[/bold]       - Show conversation history
[bold]/model[/bold] [list|name] - Show current model, list available, or switch
[bold]/thread[/bold]        - Show current thread info
[bold]/! <cmd>[/bold]       - Execute shell command

[bold cyan]Keyboard Shortcuts:[/bold cyan]

Ctrl+C           - Cancel current operation
Ctrl+C Ctrl+C    - Exit chat (press twice quickly)
Up/Down arrows   - Navigate message history
"""
    console.print(Panel(help_text, title="Help", border_style="cyan"))


def display_logs(num_lines: int = 20) -> None:
    """Display the log file location and recent log entries."""
    log_path = get_log_file_path()

    console.print(f"[bold cyan]Log file:[/bold cyan] {log_path}")
    console.print()

    try:
        if log_path.exists():
            with open(log_path, encoding="utf-8") as f:
                lines = f.readlines()
                recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines

            if recent_lines:
                console.print(f"[dim]Last {len(recent_lines)} log entries:[/dim]")
                console.print()
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Color code by log level
                    if "ERROR" in line:
                        console.print(f"[red]{line}[/red]")
                    elif "WARNING" in line:
                        console.print(f"[yellow]{line}[/yellow]")
                    elif "INFO" in line:
                        console.print(f"[green]{line}[/green]")
                    else:
                        console.print(f"[dim]{line}[/dim]")
            else:
                console.print("[dim]Log file is empty.[/dim]")
        else:
            console.print("[yellow]Log file does not exist yet.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading log file: {e}[/red]")


def display_messages(messages: list[Any], limit: int = 10) -> None:
    """Display recent messages."""
    if not messages:
        console.print("[dim]No messages in this thread.[/dim]")
        return

    recent = messages[-limit:]
    for msg in recent:
        role = getattr(msg, "role", "unknown")
        content = getattr(msg, "content", "")

        if role == "user":
            console.print(f"[bold blue]You:[/bold blue] {content}")
        elif role == "assistant":
            console.print(f"[bold green]Assistant:[/bold green] {content[:500]}...")
        elif role == "system":
            console.print(f"[dim]System: {content[:100]}...[/dim]")


async def display_tools_async(tool_manager: Any) -> None:
    """Display available tools."""
    if not tool_manager:
        console.print("[yellow]No tool manager available.[/yellow]")
        return

    try:
        tools = await tool_manager.get_tools()
        if not tools:
            console.print("[yellow]No tools available.[/yellow]")
            return

        # Get source map if available (from CompositeToolManager)
        source_map = getattr(tool_manager, "_tool_source_map", {})

        table = Table(title="Available Tools", box=box.ROUNDED)
        table.add_column("Name", style="cyan", max_width=45)
        table.add_column("Source", style="dim", max_width=8)
        table.add_column("Description", style="white", max_width=50)

        # Group by source for better organization
        local_tools = []
        arcade_tools = []
        mcp_tools = []

        for tool in tools:
            func_info = tool.get("function", {})
            name = func_info.get("name", "Unknown")
            desc = func_info.get("description", "No description")

            # Clean up description
            desc = desc.replace("[Arcade Cloud] ", "")
            if len(desc) > 50:
                desc = desc[:47] + "..."

            # Determine source from map or fallback to description check
            source = source_map.get(name, "")
            if not source:
                source = (
                    "arcade" if "[Arcade Cloud]" in func_info.get("description", "") else "local"
                )

            entry = (name, source, desc)
            if source == "local":
                local_tools.append(entry)
            elif source == "arcade" or source == "remote":
                arcade_tools.append(entry)
            elif source == "mcp":
                mcp_tools.append(entry)
            else:
                local_tools.append(entry)

        # Add tools in order: local, arcade, mcp
        for name, source, desc in local_tools:
            table.add_row(name, "local", desc)
        for name, source, desc in arcade_tools:
            table.add_row(name, "arcade", desc)
        for name, source, desc in mcp_tools:
            table.add_row(name, "mcp", desc)

        console.print(table)
        console.print(
            f"\n[dim]Total: {len(tools)} tools "
            f"(Local: {len(local_tools)}, Arcade: {len(arcade_tools)}, MCP: {len(mcp_tools)})[/dim]"
        )
    except Exception as e:
        console.print(f"[red]Error loading tools: {e}[/red]")


def display_tool_result(name: str, content: Any, status: str = "success") -> None:
    """Display a tool execution result as a single compact line."""
    content_str = str(content)
    summary = _format_result_summary(content_str)

    # Check if it's an error - status is primary indicator
    is_error = status != "success"

    # Also check content for common error patterns as fallback
    if not is_error:
        error_patterns = [
            "Failed to execute",
            "Error:",
            "error:",
            "Exception:",
            "Traceback",
            "Expecting value:",  # JSON parse error
            "[red]",
        ]
        is_error = any(pattern in content_str for pattern in error_patterns)

    if is_error:
        icon = "[red]✗[/red]"
        name_style = f"[red]{name}[/red]"
    else:
        icon = "[green]✓[/green]"
        name_style = f"[cyan]{name}[/cyan]"

    console.print(f"{icon} {name_style}: {summary}")


def display_tool_error(name: str, error: str) -> None:
    """Display a tool execution error as a compact line."""
    # Extract brief error message
    brief_error = error
    if len(brief_error) > 80:
        brief_error = brief_error[:77] + "..."
    brief_error = brief_error.replace("\n", " ")

    console.print(f"[red]✗ {name}[/red]: [dim]{brief_error}[/dim]")
