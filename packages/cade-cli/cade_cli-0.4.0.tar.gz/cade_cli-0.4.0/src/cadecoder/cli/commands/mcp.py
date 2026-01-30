"""CLI commands for managing MCP servers."""

import asyncio
import http.server
import threading
import webbrowser
from typing import Annotated
from urllib.parse import parse_qs, urlparse

import typer
from rich.console import Console
from rich.table import Table

from cadecoder.tools.manager import (
    MCPAuthType,
    MCPServerConfig,
    MCPServerStore,
    MCPToolManager,
)

# Create MCP command group
mcp_app = typer.Typer(
    name="mcp",
    help="Manage MCP (Model Context Protocol) servers",
    no_args_is_help=True,
)

console = Console()


@mcp_app.command("list")
def list_servers() -> None:
    """List all configured MCP servers."""
    store = MCPServerStore()
    servers = store.list_all()

    if not servers:
        console.print("[yellow]No MCP servers configured.[/yellow]")
        console.print("[dim]Use 'cade mcp add <name> <url>' to add a server.[/dim]")
        return

    table = Table(title="MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Auth", style="yellow")
    table.add_column("Enabled", style="green")
    table.add_column("Tools", style="blue")
    table.add_column("Last Connected", style="dim")

    for server in servers:
        enabled = "✓" if server.enabled else "✗"
        last_conn = (
            server.last_connected.strftime("%Y-%m-%d %H:%M") if server.last_connected else "-"
        )
        auth_display = server.auth_type.value
        if server.auth_type != MCPAuthType.NONE:
            auth_display += " ✓" if server.auth_value else " ✗"

        table.add_row(
            server.name,
            server.url,
            auth_display,
            enabled,
            str(server.tool_count) if server.tool_count else "-",
            last_conn,
        )

    console.print(table)


@mcp_app.command("add")
def add_server(
    name: Annotated[str, typer.Argument(help="Unique name for the server")],
    url: Annotated[str, typer.Argument(help="Server URL (e.g., http://localhost:8080)")],
    auth_type: Annotated[
        str,
        typer.Option(
            "--auth",
            "-a",
            help="Authentication type: none, bearer, or api_key",
        ),
    ] = "none",
    auth_value: Annotated[
        str | None,
        typer.Option(
            "--token",
            "-t",
            help="Authentication token or API key",
        ),
    ] = None,
    disabled: Annotated[
        bool,
        typer.Option(
            "--disabled",
            "-d",
            help="Add server in disabled state",
        ),
    ] = False,
) -> None:
    """Add a new MCP server configuration."""
    store = MCPServerStore()

    # Check if server already exists
    existing = store.get(name)
    if existing:
        console.print(f"[red]Server '{name}' already exists.[/red]")
        console.print("[dim]Use 'cade mcp rm' first or choose a different name.[/dim]")
        raise typer.Exit(1)

    # Validate auth type
    try:
        auth_enum = MCPAuthType(auth_type.lower())
    except ValueError:
        console.print(f"[red]Invalid auth type: {auth_type}[/red]")
        console.print("[dim]Valid types: none, bearer, api_key[/dim]")
        raise typer.Exit(1)

    # Warn if auth requires value
    if auth_enum != MCPAuthType.NONE and not auth_value:
        console.print(
            f"[yellow]Warning: Auth type '{auth_type}' specified but no token provided.[/yellow]"
        )

    # Create and save config
    config = MCPServerConfig(
        name=name,
        url=url,
        auth_type=auth_enum,
        auth_value=auth_value,
        enabled=not disabled,
    )
    store.add(config)

    console.print(f"[green]✓[/green] Added MCP server '{name}'")
    console.print(f"  URL: {url}")
    console.print(f"  Auth: {auth_enum.value}")
    console.print(f"  Enabled: {not disabled}")


@mcp_app.command("rm")
def remove_server(
    name: Annotated[str, typer.Argument(help="Name of the server to remove")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Remove an MCP server configuration."""
    store = MCPServerStore()

    server = store.get(name)
    if not server:
        console.print(f"[red]Server '{name}' not found.[/red]")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Remove MCP server '{name}'?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    store.remove(name)
    console.print(f"[green]✓[/green] Removed MCP server '{name}'")


@mcp_app.command("status")
def check_status() -> None:
    """Check connectivity status of all MCP servers."""
    store = MCPServerStore()
    servers = store.list_all()

    if not servers:
        console.print("[yellow]No MCP servers configured.[/yellow]")
        return

    table = Table(title="MCP Server Status")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Status", style="white")
    table.add_column("Tools", style="blue")

    async def check_all() -> list[tuple[MCPServerConfig, bool, str, int]]:
        results = []
        for server in servers:
            if not server.enabled:
                results.append((server, False, "Disabled", 0))
                continue

            manager = MCPToolManager(server)
            try:
                connected, status_msg = await manager.check_status()
                tool_count = 0
                if connected:
                    tools = await manager.get_tools()
                    tool_count = len(tools)
                results.append((server, connected, status_msg, tool_count))
            except Exception as e:
                results.append((server, False, str(e)[:50], 0))
            finally:
                await manager.close()
        return results

    with console.status("[cyan]Checking servers...", spinner="dots"):
        results = asyncio.run(check_all())

    for server, connected, status_msg, tool_count in results:
        status_style = "green" if connected else "red"
        status_icon = "✓" if connected else "✗"
        table.add_row(
            server.name,
            server.url,
            f"[{status_style}]{status_icon} {status_msg}[/{status_style}]",
            str(tool_count) if tool_count else "-",
        )

    console.print(table)


@mcp_app.command("enable")
def enable_server(
    name: Annotated[str, typer.Argument(help="Name of the server to enable")],
) -> None:
    """Enable an MCP server."""
    store = MCPServerStore()
    server = store.get(name)

    if not server:
        console.print(f"[red]Server '{name}' not found.[/red]")
        raise typer.Exit(1)

    server.enabled = True
    store.add(server)
    console.print(f"[green]✓[/green] Enabled MCP server '{name}'")


@mcp_app.command("disable")
def disable_server(
    name: Annotated[str, typer.Argument(help="Name of the server to disable")],
) -> None:
    """Disable an MCP server."""
    store = MCPServerStore()
    server = store.get(name)

    if not server:
        console.print(f"[red]Server '{name}' not found.[/red]")
        raise typer.Exit(1)

    server.enabled = False
    store.add(server)
    console.print(f"[yellow]✓[/yellow] Disabled MCP server '{name}'")


@mcp_app.command("set-auth")
def set_auth(
    name: Annotated[str, typer.Argument(help="Name of the server")],
    auth_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Auth type: none, bearer, api_key"),
    ] = "bearer",
    token: Annotated[
        str | None,
        typer.Option("--token", help="Auth token or API key"),
    ] = None,
) -> None:
    """Set authentication for an MCP server."""
    store = MCPServerStore()
    server = store.get(name)

    if not server:
        console.print(f"[red]Server '{name}' not found.[/red]")
        raise typer.Exit(1)

    try:
        auth_enum = MCPAuthType(auth_type.lower())
    except ValueError:
        console.print(f"[red]Invalid auth type: {auth_type}[/red]")
        raise typer.Exit(1)

    server.auth_type = auth_enum
    server.auth_value = token
    store.add(server)

    console.print(f"[green]✓[/green] Updated auth for '{name}'")
    console.print(f"  Type: {auth_enum.value}")
    console.print(f"  Token: {'set' if token else 'not set'}")


# OAuth callback handler
_oauth_result: dict[str, str | None] = {"code": None, "error": None}


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle OAuth callback from authorization server."""

    def do_GET(self) -> None:
        """Handle callback GET request."""
        global _oauth_result

        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            _oauth_result["code"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authorization successful!</h1>"
                b"<p>You can close this window and return to the terminal.</p>"
                b"</body></html>"
            )
        elif "error" in params:
            _oauth_result["error"] = params.get("error_description", params["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h1>Authorization failed</h1>"
                f"<p>{_oauth_result['error']}</p></body></html>".encode()
            )
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Suppress logging."""
        pass


@mcp_app.command("authorize")
def authorize_server(
    name: Annotated[str, typer.Argument(help="Name of the server to authorize")],
    client_id: Annotated[
        str | None,
        typer.Option("--client-id", "-c", help="OAuth client ID (auto-registers if not provided)"),
    ] = None,
    scope: Annotated[
        str | None,
        typer.Option("--scope", "-s", help="OAuth scopes (space-separated)"),
    ] = None,
    skip_dcr: Annotated[
        bool,
        typer.Option("--skip-dcr", help="Skip Dynamic Client Registration"),
    ] = False,
) -> None:
    """Initiate OAuth authorization flow for an MCP server.

    This command will:
    1. Discover the authorization server from the MCP server
    2. Register as a client (DCR) if no client_id is configured
    3. Open a browser for you to authorize
    4. Capture the callback and exchange the code for tokens
    5. Store the tokens for future use
    """
    global _oauth_result
    _oauth_result = {"code": None, "error": None}

    store = MCPServerStore()
    server = store.get(name)

    if not server:
        console.print(f"[red]Server '{name}' not found.[/red]")
        raise typer.Exit(1)

    if client_id:
        server.oauth_client_id = client_id
    if scope:
        server.oauth_scopes = scope.split()

    async def run_oauth_flow() -> bool:
        manager = MCPToolManager(server, store)

        try:
            # First, try to initialize to trigger 401 and discover auth server
            console.print("[cyan]Discovering authorization server...[/cyan]")

            try:
                # Make a test request to get 401
                await manager._send_request(
                    "initialize",
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "cade", "version": "1.0.0"},
                    },
                )
                console.print("[yellow]Server doesn't require authentication.[/yellow]")
                return True
            except Exception as e:
                if "ToolAuthorizationRequired" not in str(type(e).__name__):
                    console.print(f"[red]Error: {e}[/red]")
                    return False

            # Check if we got an auth URL
            if not hasattr(manager, "_pending_code_verifier"):
                console.print("[red]Failed to discover authorization server.[/red]")
                return False

            if not manager._auth_server_metadata:
                console.print("[red]No authorization server metadata available.[/red]")
                return False

            # Perform DCR if needed (no client_id provided or configured)
            effective_client_id = client_id or server.oauth_client_id
            if not effective_client_id and not skip_dcr:
                registration_endpoint = manager._auth_server_metadata.get("registration_endpoint")
                if registration_endpoint:
                    console.print(
                        "[cyan]Registering client (Dynamic Client Registration)...[/cyan]"
                    )
                    try:
                        (
                            registered_id,
                            registered_secret,
                        ) = await manager._oauth_handler.register_client(
                            manager._auth_server_metadata,
                            client_name=f"cade-{name}",
                        )
                        effective_client_id = registered_id
                        server.oauth_client_id = registered_id
                        server.oauth_client_secret = registered_secret
                        store.add(server)  # add() also updates existing servers
                        console.print(
                            f"[green]✓[/green] Registered as client: {registered_id[:50]}..."
                        )
                    except Exception as e:
                        console.print(f"[red]Client registration failed: {e}[/red]")
                        console.print(
                            "[yellow]Tip: Try providing a client_id with --client-id[/yellow]"
                        )
                        return False
                else:
                    console.print(
                        "[red]No client_id provided and server doesn't support DCR.[/red]"
                    )
                    console.print("[yellow]Tip: Provide a client_id with --client-id[/yellow]")
                    return False

            # Start local callback server
            server_address = ("127.0.0.1", 9876)
            httpd = http.server.HTTPServer(server_address, OAuthCallbackHandler)
            httpd.timeout = 300  # 5 minute timeout

            # Generate new OAuth flow with proper PKCE
            auth_url, code_verifier, state = await manager._oauth_handler.start_oauth_flow(
                manager._auth_server_metadata,
                scope,
                effective_client_id,
            )
            # Update the manager's pending verifier to match this auth flow
            # (the initial 401 discovery generated a different verifier)
            manager._pending_code_verifier = code_verifier
            manager._pending_state = state

            console.print("\n[cyan]Opening browser for authorization...[/cyan]")
            console.print(f"[dim]URL: {auth_url[:80]}...[/dim]\n")
            webbrowser.open(auth_url)

            console.print("[yellow]Waiting for authorization (5 min timeout)...[/yellow]")

            # Handle one request
            def handle_callback() -> None:
                httpd.handle_request()

            thread = threading.Thread(target=handle_callback)
            thread.start()
            thread.join(timeout=300)

            if _oauth_result["error"]:
                console.print(f"[red]Authorization failed: {_oauth_result['error']}[/red]")
                return False

            if not _oauth_result["code"]:
                console.print("[red]No authorization code received.[/red]")
                return False

            # Exchange code for tokens
            console.print("[cyan]Exchanging code for tokens...[/cyan]")
            success = await manager.complete_oauth_flow(_oauth_result["code"])

            if success:
                console.print(f"[green]✓[/green] Successfully authorized '{name}'")
                return True
            else:
                console.print("[red]Failed to exchange code for tokens.[/red]")
                return False

        finally:
            await manager.close()

    success = asyncio.run(run_oauth_flow())
    if not success:
        raise typer.Exit(1)


@mcp_app.command("token-info")
def token_info(
    name: Annotated[str, typer.Argument(help="Name of the server")],
) -> None:
    """Show OAuth token information for an MCP server."""
    store = MCPServerStore()
    server = store.get(name)

    if not server:
        console.print(f"[red]Server '{name}' not found.[/red]")
        raise typer.Exit(1)

    if server.auth_type != MCPAuthType.OAUTH or not server.oauth_tokens:
        console.print(f"[yellow]Server '{name}' is not using OAuth authentication.[/yellow]")
        return

    tokens = server.oauth_tokens
    console.print(f"[cyan]OAuth Token Info for '{name}':[/cyan]")
    console.print(f"  Token Type: {tokens.token_type}")
    console.print(f"  Access Token: {tokens.access_token[:20]}...")
    console.print(f"  Refresh Token: {'set' if tokens.refresh_token else 'not set'}")
    if tokens.expires_at:
        if tokens.is_expired():
            console.print(f"  [red]Expired: {tokens.expires_at}[/red]")
        else:
            console.print(f"  Expires: {tokens.expires_at}")
    if tokens.scope:
        console.print(f"  Scopes: {tokens.scope}")
