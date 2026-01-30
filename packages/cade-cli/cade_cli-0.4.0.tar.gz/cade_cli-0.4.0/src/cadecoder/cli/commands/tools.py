"""CLI commands for viewing and managing tools."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Create tool command group
tool_app = typer.Typer(
    name="tool",
    help="View and manage available tools",
    no_args_is_help=False,
    invoke_without_command=True,
)

console = Console()


@tool_app.callback()
def tool_callback(ctx: typer.Context) -> None:
    """View available tools. Lists all tools by default."""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, run list_tools
        list_tools(source=None, search=None, server=None, show_all=False)


@tool_app.command("list")
def list_tools(
    source: Annotated[
        str | None,
        typer.Option(
            "--source",
            "-s",
            help="Filter by source: local, remote, mcp",
        ),
    ] = None,
    search: Annotated[
        str | None,
        typer.Option(
            "--search",
            "-q",
            help="Search tools by name",
        ),
    ] = None,
    server: Annotated[
        str | None,
        typer.Option(
            "--server",
            help="Filter by MCP server name (e.g., Gmail, GoogleCalendar)",
        ),
    ] = None,
    show_all: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Include local tools in the display",
        ),
    ] = False,
) -> None:
    """List all available tools.

    By default, shows only MCP tools grouped by server.
    Use --all to include local tools."""

    async def get_tools() -> tuple[list[dict], dict[str, str], dict[str, str]]:
        # Import here to avoid circular dependency
        from cadecoder.tools.manager.composite import CompositeToolManager

        # Create tool manager directly without needing an AI provider
        tool_manager = CompositeToolManager(enable_mcp=True, local_only=False)
        tools = await tool_manager.get_tools()

        # Get source and server mapping
        source_map = {}
        server_map = {}
        if hasattr(tool_manager, "get_all_tool_info"):
            for info in tool_manager.get_all_tool_info():
                tool_name = info["name"]
                source_map[tool_name] = info.get("source", "unknown")
                server_map[tool_name] = info.get("server", "unknown")

        # Close tool manager
        await tool_manager.close()

        return tools, source_map, server_map

    with console.status("[cyan]Loading tools...", spinner="dots"):
        tools, source_map, server_map = asyncio.run(get_tools())

    # Filter out local tools by default unless --all is set
    if not show_all:
        tools = [
            t for t in tools if source_map.get(t.get("function", {}).get("name", ""), "") != "local"
        ]

    # Filter by source
    if source:
        source_lower = source.lower()
        tools = [
            t
            for t in tools
            if source_map.get(t.get("function", {}).get("name", ""), "").lower() == source_lower
        ]

    # Filter by server
    if server:
        # Extract server prefix from tool names (e.g., "Gmail" from "Gmail_ListEmails")
        tools = [t for t in tools if t.get("function", {}).get("name", "").startswith(f"{server}_")]

    # Filter by search
    if search:
        search_lower = search.lower()
        tools = [
            t
            for t in tools
            if search_lower in t.get("function", {}).get("name", "").lower()
            or search_lower in t.get("function", {}).get("description", "").lower()
        ]

    if not tools:
        console.print("[yellow]No tools found.[/yellow]")
        return

    # Group tools by server/prefix
    from collections import defaultdict

    grouped_tools = defaultdict(list)

    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name", "unknown")
        tool_source = source_map.get(name, "unknown")

        # Extract server prefix for MCP tools
        if tool_source == "mcp" and "_" in name:
            server_prefix = name.split("_", 1)[0]
            grouped_tools[server_prefix].append(tool)
        else:
            # Local tools grouped under "Local"
            grouped_tools["Local"].append(tool)

    # Sort server names
    sorted_servers = sorted(grouped_tools.keys())

    # Create table
    table = Table(title="Available Tools", show_lines=False, box=None)
    table.add_column("Name", style="cyan", no_wrap=True, width=45)
    table.add_column("Source", style="dim", no_wrap=True, width=8)
    table.add_column("Description", style="white", max_width=50)

    total_count = 0
    shown_count = 0

    for server_name in sorted_servers:
        server_tools = sorted(
            grouped_tools[server_name], key=lambda t: t.get("function", {}).get("name", "")
        )
        server_tool_count = len(server_tools)
        total_count += server_tool_count

        # Determine how many tools to show for this server
        max_tools_to_show = server_tool_count if (server or show_all) else min(3, server_tool_count)
        tools_to_display = server_tools[:max_tools_to_show]
        shown_count += len(tools_to_display)

        # Add server header row
        if server_name == "Local":
            server_header = (
                f"[bold white]Local Tools[/bold white] [dim]({server_tool_count} tools)[/dim]"
            )
        else:
            server_header = (
                f"[bold white]{server_name}[/bold white] [dim]({server_tool_count} tools)[/dim]"
            )

        table.add_row(server_header, "", "")

        # Add tools for this server
        for tool in tools_to_display:
            func = tool.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "")

            # Get source
            tool_source = source_map.get(name, "unknown")
            source_label = {
                "local": "local",
                "remote": "arcade",
                "mcp": "mcp",
            }.get(tool_source, tool_source)

            # Clean up description
            if desc.startswith("["):
                bracket_end = desc.find("]")
                if bracket_end != -1:
                    desc = desc[bracket_end + 1 :].strip()

            # Cut at first newline
            if "\n" in desc:
                desc = desc.split("\n")[0].strip()

            # Truncate long descriptions
            if len(desc) > 50:
                desc = desc[:47] + "..."

            # Indent tool name slightly
            display_name = f"  {name}"
            table.add_row(display_name, source_label, desc)

        # Show "and X more..." if there are hidden tools
        if max_tools_to_show < server_tool_count:
            remaining = server_tool_count - max_tools_to_show
            table.add_row(
                f"  [dim]...and {remaining} more[/dim]",
                "",
                f"[dim]Use --server {server_name} to see all[/dim]",
            )

        # Add spacing between servers
        if server_name != sorted_servers[-1]:
            table.add_row("", "", "")

    console.print(table)

    # Summary
    if shown_count < total_count:
        console.print(
            f"\n[dim]Showing {shown_count} of {total_count} tools. "
            f"Use --all to see local tools, --server <name> for specific servers.[/dim]"
        )
    else:
        console.print(f"\n[dim]Total: {total_count} tools[/dim]")


@tool_app.command("info")
def tool_info(
    name: Annotated[str, typer.Argument(help="Name of the tool")],
) -> None:
    """Show detailed information about a tool."""

    async def get_tool_details() -> tuple[dict | None, str | None]:
        # Import here to avoid circular dependency
        from cadecoder.tools.manager.composite import CompositeToolManager

        # Create tool manager directly without needing an AI provider
        tool_manager = CompositeToolManager(enable_mcp=True, local_only=False)
        tools = await tool_manager.get_tools()

        # Find the tool
        tool = None
        for t in tools:
            if t.get("function", {}).get("name", "") == name:
                tool = t
                break

        # Get source
        source = None
        if hasattr(tool_manager, "get_tool_source"):
            source = tool_manager.get_tool_source(name)

        # Close tool manager
        await tool_manager.close()

        return tool, source

    with console.status("[cyan]Loading tool info...", spinner="dots"):
        tool, source = asyncio.run(get_tool_details())

    if not tool:
        console.print(f"[red]Tool '{name}' not found.[/red]")
        raise typer.Exit(1)

    func = tool.get("function", {})
    tool_name = func.get("name", "unknown")
    description = func.get("description", "No description")
    parameters = func.get("parameters", {})

    # Build info display
    content = Text()

    # Name and source
    content.append(f"{tool_name}\n", style="bold cyan")
    if source:
        source_display = {
            "local": "Local",
            "remote": "Arcade Cloud",
            "mcp": "MCP Server",
        }.get(source, source.title())
        content.append(f"Source: {source_display}\n\n", style="dim")

    # Description
    # Clean up description prefix
    if description.startswith("["):
        bracket_end = description.find("]")
        if bracket_end != -1:
            description = description[bracket_end + 1 :].strip()

    content.append("Description:\n", style="bold")
    content.append(f"{description}\n\n", style="white")

    # Parameters
    props = parameters.get("properties", {})
    required = set(parameters.get("required", []))

    if props:
        content.append("Parameters:\n", style="bold")
        for param_name, param_info in props.items():
            param_type = param_info.get("type", "any")
            param_desc = param_info.get("description", "")
            is_required = param_name in required

            req_marker = " [required]" if is_required else ""
            content.append(f"  • {param_name}", style="cyan")
            content.append(f" ({param_type}){req_marker}\n", style="dim")
            if param_desc:
                content.append(f"    {param_desc}\n", style="white")
    else:
        content.append("Parameters: None\n", style="dim")

    panel = Panel(
        content,
        title="Tool Info",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


@tool_app.command("search")
def search_tools(
    query: Annotated[str, typer.Argument(help="Search query")],
) -> None:
    """Search for tools by name or description."""
    # Delegate to list with search parameter
    list_tools(source=None, search=query)
