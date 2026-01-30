"""Authentication commands for CadeCoder CLI.

Uses arcade-core for OAuth 2.0 authentication with PKCE.
Credentials are shared with arcade-cli at ~/.arcade/credentials.yaml.
"""

from typing import Annotated

import typer
from arcade_core.config_model import Config
from arcade_core.constants import PROD_COORDINATOR_HOST
from rich.console import Console
from rich.markup import escape

from cadecoder.cli.auth import (
    OAuthLoginError,
    build_coordinator_url,
    check_existing_login,
    perform_oauth_login,
    save_credentials_from_whoami,
)
from cadecoder.core.logging import log

console = Console(stderr=True)


def login(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            help="The Arcade Coordinator host (defaults to production).",
            envvar="ARCADE_CLOUD_HOST",
        ),
    ] = PROD_COORDINATOR_HOST,
    port: Annotated[
        int | None,
        typer.Option(
            "--port",
            help="Coordinator port (for local development).",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force login even if already logged in.",
        ),
    ] = False,
) -> None:
    """Log in to Arcade Cloud using OAuth.

    Opens a browser for authentication and stores credentials
    at ~/.arcade/credentials.yaml (shared with arcade-cli).
    """
    try:
        # Check if already logged in
        if not force and check_existing_login(suppress_message=False):
            console.print("\n[dim]Use --force to re-authenticate.[/dim]")
            return

        # Build coordinator URL
        coordinator_url = build_coordinator_url(host, port)

        # Perform OAuth login
        def on_status(msg: str) -> None:
            console.print(f"[dim]{msg}[/dim]")

        tokens, whoami = perform_oauth_login(coordinator_url, on_status=on_status)

        # Save credentials
        save_credentials_from_whoami(tokens, whoami, coordinator_url)

        # Success message
        console.print("\n[green]✓ Login successful![/green]")
        console.print(f"  Email: {whoami.email}")

        org = whoami.get_selected_org()
        project = whoami.get_selected_project()
        if org and project:
            org_name = org.get("name", "unknown")
            project_name = project.get("name", "unknown")
            console.print(f"  Active: {org_name} / {project_name}")

        log.info(f"User {whoami.email} logged in via OAuth.")

    except OAuthLoginError as e:
        console.print(f"\n[red]✗ Login failed:[/red] {escape(str(e))}")
        raise typer.Exit(code=1)
    except Exception as e:
        log.exception("Unexpected error during login.")
        console.print(f"\n[red]✗ Unexpected error:[/red] {escape(str(e))}")
        raise typer.Exit(code=1)


def logout() -> None:
    """Log out of Arcade Cloud by removing stored credentials."""
    try:
        cred_path = Config.get_config_file_path()

        if cred_path.exists():
            cred_path.unlink()
            console.print("[green]✓ Logged out successfully![/green]")
            log.info("User credentials removed.")
        else:
            console.print("[yellow]You were not logged in.[/yellow]")
            log.info("No credentials found to remove.")

    except Exception as e:
        log.exception("Error during logout.")
        console.print(f"[red]✗ Error during logout:[/red] {escape(str(e))}")
        raise typer.Exit(code=1)


def whoami() -> None:
    """Show current login status and user information."""
    try:
        config = Config.load_from_file()

        if not config.is_authenticated():
            console.print("[yellow]Not logged in.[/yellow]")
            console.print("[dim]Run 'cade login' to authenticate.[/dim]")
            raise typer.Exit(code=1)

        email = config.user.email if config.user else "unknown"
        console.print(f"[green]✓[/green] Logged in as: [bold]{email}[/bold]")

        if config.context:
            console.print(f"  Organization: {config.context.org_name}")
            console.print(f"  Project: {config.context.project_name}")

        if config.auth and config.is_token_expired():
            console.print("\n[yellow]⚠ Access token expired (will refresh on next use)[/yellow]")

    except FileNotFoundError:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("[dim]Run 'cade login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]✗ Invalid credentials:[/red] {escape(str(e))}")
        console.print("[dim]Run 'cade login' to re-authenticate.[/dim]")
        raise typer.Exit(code=1)
