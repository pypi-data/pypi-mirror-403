"""Main CLI application setup and entry point for CadeCoder."""

import os

# Set environment variable to disable tokenizers parallelism warning
# This must be set before any imports that use tokenizers
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from typing import Annotated

import typer
from rich.console import Console

from cadecoder import __version__
from cadecoder.cli.commands import auth, chat
from cadecoder.cli.commands.context import context_app
from cadecoder.cli.commands.mcp import mcp_app
from cadecoder.cli.commands.model import model_app
from cadecoder.cli.commands.thread import thread_app
from cadecoder.cli.commands.tools import tool_app
from cadecoder.core.config import set_verbose_mode
from cadecoder.core.logging import setup_logging

# Create the main app
app = typer.Typer(
    name="cade",
    help="Cade - The CLI Agent from Arcade.dev",
    add_completion=True,
    no_args_is_help=False,  # Changed to False to allow default command
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="markdown",
    invoke_without_command=True,  # Allow callback to run when no command given
)

# Register individual commands with explicit names and help panels
app.command(name="login", help="Log in to Arcade Cloud", rich_help_panel="User")(auth.login)
app.command(name="logout", help="Log out of Arcade Cloud", rich_help_panel="User")(auth.logout)
app.command(name="whoami", help="Show current login status", rich_help_panel="User")(auth.whoami)
app.command(name="chat")(chat.chat)
app.command(name="resume", help="Resume the most recent thread or a specific thread by name")(
    chat.resume
)

# Register sub-command groups
app.add_typer(
    context_app,
    name="context",
    help="Manage organization and project context",
    rich_help_panel="User",
)
app.add_typer(mcp_app, name="mcp", help="Manage MCP servers", rich_help_panel="Tools")
app.add_typer(model_app, name="model", help="Manage AI models", rich_help_panel="Tools")
app.add_typer(tool_app, name="tools", help="View available tools", rich_help_panel="Tools")
app.add_typer(thread_app, name="thread", help="Manage chat threads", rich_help_panel="Storage")

# Use stderr for messages, logs, prompts to avoid interfering with stdout piping
console = Console(stderr=True)


def version_callback(value: bool) -> None:
    """Prints the version of the package."""
    if value:
        # Use stdout for version
        print(f"cade Version: {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose debug logging.", is_eager=True),
    ] = False,
    resume_flag: Annotated[
        bool,
        typer.Option(
            "--resume",
            "-r",
            help="Resume the most recent thread (shortcut for 'cade resume').",
            is_eager=True,
        ),
    ] = False,
    message: Annotated[
        str | None,
        typer.Option(
            "--message",
            "-m",
            help="Single message mode: process one message and exit. "
            "Reads from stdin if no argument given.",
        ),
    ] = None,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """
    Main callback to initialize things if needed.
    Ensure configuration is loaded/available here or before storage access.

    Args:
        ctx: Typer context object
        verbose: Enable verbose logging if True
        resume_flag: Resume most recent thread if True
        message: Single message mode - process one message and exit
        version: Show version and exit if True
    """
    # Setup logging level and verbose mode
    setup_logging(verbose)
    set_verbose_mode(verbose)

    # Load config early - may be needed by commands
    # Store config in context for potential use by commands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Handle single message mode
    if message is not None and ctx.invoked_subcommand is None:
        import sys

        from cadecoder.ui.session import run_single_message_mode

        # If message is empty string, read from stdin
        if message == "":
            # Check if stdin has data
            if not sys.stdin.isatty():
                message = sys.stdin.read().strip()
            else:
                console.print(
                    "[red]Error: No message provided. Use -m 'message' or pipe input.[/red]"
                )
                raise typer.Exit(1)

        if not message:
            console.print("[red]Error: Empty message provided.[/red]")
            raise typer.Exit(1)

        exit_code = run_single_message_mode(message)
        raise typer.Exit(exit_code)

    # Handle eager resume flag before default chat
    if resume_flag and ctx.invoked_subcommand is None:
        # Invoke resume command directly
        chat.resume()
        raise typer.Exit()

    # If no command was invoked (just "cade"), launch chat
    if ctx.invoked_subcommand is None:
        # Import and run chat command directly
        chat.chat()


if __name__ == "__main__":
    app()
