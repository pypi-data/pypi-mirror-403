"""Thread management commands for CadeCoder."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from cadecoder.storage.threads import get_thread_history

thread_app = typer.Typer(
    name="thread",
    help="Manage chat threads",
    no_args_is_help=True,
)

console = Console()


@thread_app.command("list")
def list_threads(
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of threads to show"),
    ] = 20,
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Filter by git branch"),
    ] = None,
) -> None:
    """List recent chat threads.

    Shows threads sorted by last modified date, most recent first.
    """
    history = get_thread_history()
    threads = history.list_threads()

    # Filter by branch if specified
    if branch:
        threads = [t for t in threads if t.git_branch == branch]

    # Apply limit
    threads = threads[:limit]

    if not threads:
        console.print("[yellow]No threads found.[/yellow]")
        return

    table = Table(title="Chat Threads", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold", max_width=25)
    table.add_column("Branch", style="green", max_width=20)
    table.add_column("Last Modified", style="magenta")
    table.add_column("ID", style="dim", max_width=14)

    for thread in threads:
        # Format the timestamp
        last_modified = thread.last_modified_at.strftime("%Y-%m-%d %H:%M")

        table.add_row(
            thread.name or "-",
            thread.git_branch or "-",
            last_modified,
            thread.thread_id[:12] + "...",
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(threads)} thread(s)[/dim]")
    console.print("[dim]Use 'cade resume <name>' to resume a thread[/dim]")


@thread_app.command("get")
def get_thread(
    identifier: Annotated[str, typer.Argument(help="Thread name, ID, or partial ID")],
    show_messages: Annotated[
        bool,
        typer.Option("--messages", "-m", help="Show message history"),
    ] = False,
) -> None:
    """Get details about a specific thread by name or ID.

    You can provide a thread name (e.g., 'cool_squid'), thread ID, or partial ID.
    The first matching thread will be shown.
    """
    history = get_thread_history()

    # Try exact ID match first
    thread = history.get_thread(identifier)

    # If not found, try name match or partial ID match
    if not thread:
        all_threads = history.list_threads()

        # Try exact name match
        name_matches = [t for t in all_threads if t.name == identifier]
        if name_matches:
            thread = name_matches[0]
        else:
            # Try partial ID match
            id_matches = [t for t in all_threads if t.thread_id.startswith(identifier)]
            if len(id_matches) == 1:
                thread = id_matches[0]
            elif len(id_matches) > 1:
                console.print(f"[yellow]Multiple threads match '{identifier}':[/yellow]")
                for t in id_matches[:5]:
                    console.print(f"  {t.thread_id} ({t.name or 'unnamed'})")
                return
            else:
                console.print(f"[red]Thread '{identifier}' not found.[/red]")
                console.print("[dim]Use 'cade thread list' to see available threads[/dim]")
                raise typer.Exit(1)

    # Display thread info
    console.print("\n[bold cyan]Thread Details[/bold cyan]")
    console.print(f"  [bold]ID:[/bold] {thread.thread_id}")
    console.print(f"  [bold]Name:[/bold] {thread.name or '-'}")
    console.print(f"  [bold]Branch:[/bold] {thread.git_branch or '-'}")
    console.print(f"  [bold]Model:[/bold] {thread.model or '-'}")
    console.print(f"  [bold]User:[/bold] {thread.user_id or '-'}")
    console.print(f"  [bold]Created:[/bold] {thread.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(
        f"  [bold]Last Modified:[/bold] {thread.last_modified_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if thread.tags:
        console.print(f"  [bold]Tags:[/bold] {', '.join(thread.tags)}")

    # Show messages if requested
    if show_messages:
        messages = history.get_messages(thread.thread_id)
        console.print(f"\n[bold cyan]Messages ({len(messages)})[/bold cyan]")

        for msg in messages:
            role_style = {
                "user": "green",
                "assistant": "blue",
                "system": "yellow",
                "tool": "magenta",
            }.get(msg.role, "white")

            # Truncate long content
            content = msg.content or ""
            if len(content) > 200:
                content = content[:200] + "..."

            timestamp = msg.timestamp.strftime("%H:%M:%S")
            console.print(f"\n  [{role_style}][{msg.role}][/{role_style}] [dim]{timestamp}[/dim]")

            if content:
                # Indent content
                for line in content.split("\n")[:5]:  # Show first 5 lines
                    console.print(f"    {line}")
                if content.count("\n") > 5:
                    console.print("    [dim]...[/dim]")

            if msg.tool_calls:
                console.print(f"    [dim]Tool calls: {len(msg.tool_calls)}[/dim]")

    console.print(f"\n[dim]Resume with: cade resume {thread.thread_id}[/dim]")


@thread_app.command("delete")
def delete_thread(
    identifier: Annotated[str, typer.Argument(help="Thread name, ID, or partial ID to delete")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Delete a thread and all its messages by name or ID."""
    history = get_thread_history()
    thread = history.get_thread(identifier)

    if not thread:
        all_threads = history.list_threads()

        # Try exact name match
        name_matches = [t for t in all_threads if t.name == identifier]
        if name_matches:
            thread = name_matches[0]
        else:
            # Try partial ID match
            id_matches = [t for t in all_threads if t.thread_id.startswith(identifier)]
            if len(id_matches) == 1:
                thread = id_matches[0]
            elif len(id_matches) > 1:
                console.print(f"[yellow]Multiple threads match '{identifier}':[/yellow]")
                for t in id_matches[:5]:
                    console.print(f"  {t.thread_id} ({t.name or 'unnamed'})")
                return
            else:
                console.print(f"[red]Thread '{identifier}' not found.[/red]")
                console.print("[dim]Use 'cade thread list' to see available threads[/dim]")
                raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete thread '{thread.thread_id}'?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Abort()

    history.delete_thread(thread.thread_id)
    console.print(f"[green]✓[/green] Deleted thread '{thread.thread_id}'")
