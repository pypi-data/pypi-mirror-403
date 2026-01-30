"""Context management commands for switching orgs and projects."""

from typing import Annotated

import httpx
import typer
from arcade_core.auth_tokens import get_valid_access_token
from arcade_core.config_model import Config, ContextConfig
from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm
from rich.table import Table

from cadecoder.core.logging import log

console = Console(stderr=True)
context_app = typer.Typer(help="Manage organization and project context", no_args_is_help=True)


@context_app.command(name="show")
def show_context() -> None:
    """Show current organization and project context."""
    try:
        config = Config.load_from_file()

        if not config.is_authenticated():
            console.print("[yellow]Not logged in.[/yellow]")
            console.print("[dim]Run 'cade login' to authenticate.[/dim]")
            raise typer.Exit(code=1)

        email = config.user.email if config.user else "unknown"
        console.print(f"[green]✓[/green] Logged in as: [bold]{email}[/bold]\n")

        if config.context:
            console.print(f"  Organization: [cyan]{config.context.org_name}[/cyan]")
            console.print(f"  Organization ID: [dim]{config.context.org_id}[/dim]")
            console.print(f"  Project: [cyan]{config.context.project_name}[/cyan]")
            console.print(f"  Project ID: [dim]{config.context.project_id}[/dim]")
        else:
            console.print("[yellow]No context set.[/yellow]")
            console.print(
                "[dim]Run 'cade context switch' to select an organization and project.[/dim]"
            )

    except FileNotFoundError:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("[dim]Run 'cade login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]✗ Invalid credentials:[/red] {escape(str(e))}")
        console.print("[dim]Run 'cade login' to re-authenticate.[/dim]")
        raise typer.Exit(code=1)


@context_app.command(name="list")
def list_contexts() -> None:
    """List available organizations and projects."""
    try:
        config = Config.load_from_file()

        if not config.is_authenticated():
            console.print("[yellow]Not logged in.[/yellow]")
            console.print("[dim]Run 'cade login' to authenticate.[/dim]")
            raise typer.Exit(code=1)

        # Fetch updated whoami info from coordinator
        orgs, projects = _fetch_whoami_info(config)

        if not orgs:
            console.print("[yellow]No organizations found.[/yellow]")
            return

        # Display organizations
        console.print("\n[bold]Organizations:[/bold]")
        org_table = Table(show_header=True, header_style="bold cyan")
        org_table.add_column("Name", style="cyan")
        org_table.add_column("ID", style="dim")
        org_table.add_column("Active", justify="center")

        current_org_id = config.context.org_id if config.context else None
        for org in orgs:
            org_id = org.get("org_id") or org.get("organization_id", "")
            is_active = "✓" if org_id == current_org_id else ""
            org_table.add_row(org["name"], org_id, is_active)

        console.print(org_table)

        # Display projects
        if projects:
            console.print("\n[bold]Projects:[/bold]")
            proj_table = Table(show_header=True, header_style="bold cyan")
            proj_table.add_column("Name", style="cyan")
            proj_table.add_column("ID", style="dim")
            proj_table.add_column("Organization", style="dim")
            proj_table.add_column("Active", justify="center")

            current_proj_id = config.context.project_id if config.context else None
            for proj in projects:
                proj_id = proj.get("project_id", "")
                proj_org_id = proj.get("org_id") or proj.get("organization_id", "")
                is_active = "✓" if proj_id == current_proj_id else ""
                org_name = next(
                    (
                        o["name"]
                        for o in orgs
                        if (o.get("org_id") or o.get("organization_id", "")) == proj_org_id
                    ),
                    "unknown",
                )
                proj_table.add_row(proj["name"], proj_id, org_name, is_active)

            console.print(proj_table)

    except FileNotFoundError:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("[dim]Run 'cade login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except Exception as e:
        log.exception("Error listing contexts.")
        console.print(f"[red]✗ Error:[/red] {escape(str(e))}")
        raise typer.Exit(code=1)


@context_app.command(name="switch")
def switch_context(
    org: Annotated[
        str | None,
        typer.Option(
            "--org",
            help="Organization ID or name to switch to",
        ),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option(
            "--project",
            help="Project ID or name to switch to",
        ),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Interactive mode: select from a list",
        ),
    ] = False,
) -> None:
    """Switch organization and project context.

    Examples:
        cade context switch --org my-org --project my-project
        cade context switch --interactive
    """
    try:
        config = Config.load_from_file()

        if not config.is_authenticated():
            console.print("[yellow]Not logged in.[/yellow]")
            console.print("[dim]Run 'cade login' to authenticate.[/dim]")
            raise typer.Exit(code=1)

        # Fetch updated whoami info
        orgs, projects = _fetch_whoami_info(config)

        if not orgs:
            console.print("[yellow]No organizations found.[/yellow]")
            return

        # Interactive mode
        if interactive or (not org and not project):
            selected_org = _interactive_select_org(orgs, config)
            if not selected_org:
                console.print("[yellow]No organization selected.[/yellow]")
                return

            org_id = selected_org.get("org_id") or selected_org.get("organization_id", "")
            org_projects = [
                p for p in projects if (p.get("org_id") or p.get("organization_id", "")) == org_id
            ]
            if not org_projects:
                console.print(f"[yellow]No projects found for {selected_org['name']}.[/yellow]")
                return

            selected_project = _interactive_select_project(org_projects, config)
            if not selected_project:
                console.print("[yellow]No project selected.[/yellow]")
                return

        # Direct mode
        else:
            selected_org = _find_org(orgs, org) if org else _get_current_org(orgs, config)
            if not selected_org:
                console.print(f"[red]✗ Organization not found:[/red] {org}")
                raise typer.Exit(code=1)

            selected_project = _find_project(projects, project) if project else None
            if project and not selected_project:
                console.print(f"[red]✗ Project not found:[/red] {project}")
                raise typer.Exit(code=1)

        # Update config with new context
        org_id = selected_org.get("org_id") or selected_org.get("organization_id", "")
        proj_id = selected_project.get("project_id", "")

        new_context = ContextConfig(
            org_id=org_id,
            org_name=selected_org["name"],
            project_id=proj_id,
            project_name=selected_project["name"],
        )

        config.context = new_context
        config.save_to_file()

        console.print("\n[green]✓ Context updated![/green]")
        console.print(f"  Organization: {selected_org['name']}")
        console.print(f"  Project: {selected_project['name']}")

        log.info(f"Context switched to {selected_org['name']} / {selected_project['name']}")

    except FileNotFoundError:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("[dim]Run 'cade login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        log.exception("Error switching context.")
        console.print(f"[red]✗ Error:[/red] {escape(str(e))}")
        raise typer.Exit(code=1)


def _fetch_whoami_info(config: Config) -> tuple[list[dict], list[dict]]:
    """Fetch current whoami info from coordinator."""
    try:
        access_token = get_valid_access_token(config.coordinator_url or "")

        headers = {"Authorization": f"Bearer {access_token}"}
        response = httpx.get(
            f"{config.coordinator_url}/api/v1/auth/whoami", headers=headers, timeout=30.0
        )
        response.raise_for_status()

        data = response.json().get("data", {})
        orgs = data.get("organizations", [])
        projects = data.get("projects", [])

        return orgs, projects

    except Exception as e:
        log.error(f"Failed to fetch whoami info: {e}")
        raise Exception(f"Failed to fetch account info: {e}")


def _find_org(orgs: list[dict], identifier: str) -> dict | None:
    """Find org by ID or name."""
    for org in orgs:
        org_id = org.get("org_id") or org.get("organization_id", "")
        if org_id == identifier or org["name"].lower() == identifier.lower():
            return org
    return None


def _find_project(projects: list[dict], identifier: str) -> dict | None:
    """Find project by ID or name."""
    for proj in projects:
        proj_id = proj.get("project_id", "")
        if proj_id == identifier or proj["name"].lower() == identifier.lower():
            return proj
    return None


def _get_current_org(orgs: list[dict], config: Config) -> dict | None:
    """Get current org from config."""
    if config.context:
        return _find_org(orgs, config.context.org_id)
    return orgs[0] if orgs else None


def _interactive_select_org(orgs: list[dict], config: Config) -> dict | None:
    """Interactive org selection."""
    if len(orgs) == 1:
        org = orgs[0]
        if Confirm.ask(f"Use organization '{org['name']}'?"):
            return org
        return None

    console.print("\n[bold]Select an organization:[/bold]")
    current_org_id = config.context.org_id if config.context else None

    for i, org in enumerate(orgs, 1):
        org_id = org.get("org_id") or org.get("organization_id", "")
        is_current = " [dim](current)[/dim]" if org_id == current_org_id else ""
        console.print(f"  {i}. {org['name']}{is_current}")

    choice = typer.prompt("\nEnter number", type=int)
    if 1 <= choice <= len(orgs):
        return orgs[choice - 1]
    return None


def _interactive_select_project(projects: list[dict], config: Config) -> dict | None:
    """Interactive project selection."""
    if len(projects) == 1:
        proj = projects[0]
        if Confirm.ask(f"Use project '{proj['name']}'?"):
            return proj
        return None

    console.print("\n[bold]Select a project:[/bold]")
    current_proj_id = config.context.project_id if config.context else None

    for i, proj in enumerate(projects, 1):
        proj_id = proj.get("project_id", "")
        is_current = " [dim](current)[/dim]" if proj_id == current_proj_id else ""
        console.print(f"  {i}. {proj['name']}{is_current}")

    choice = typer.prompt("\nEnter number", type=int)
    if 1 <= choice <= len(projects):
        return projects[choice - 1]
    return None
