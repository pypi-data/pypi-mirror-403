"""Model management commands."""

from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from cadecoder.core.constants import DEFAULT_AI_MODEL

console = Console()

model_app = typer.Typer(
    name="model",
    help="Manage AI models",
    no_args_is_help=False,
    invoke_without_command=True,
)


def _get_providers() -> tuple[Any, Any]:
    """Get OpenAI and Anthropic providers if available."""
    from cadecoder.providers import provider_registry
    from cadecoder.providers.base import ProviderType

    openai = provider_registry.get(ProviderType.OPENAI)
    anthropic = provider_registry.get(ProviderType.ANTHROPIC)
    return openai, anthropic


@model_app.callback()
def model_callback(ctx: typer.Context) -> None:
    """Show current default model if no subcommand given."""
    if ctx.invoked_subcommand is None:
        # Show current model
        console.print(f"[cyan]Default model:[/cyan] {DEFAULT_AI_MODEL}")
        console.print()
        console.print("[dim]Commands:[/dim]")
        console.print("  cade model list    - List available models")
        console.print("  cade model set     - Set default model (coming soon)")


@model_app.command(name="list")
def list_models(
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            "-p",
            help="Filter by provider: openai, anthropic, or all",
        ),
    ] = None,
) -> None:
    """List all available models from configured providers."""
    openai_provider, anthropic_provider = _get_providers()

    table = Table(title="Available Models")
    table.add_column("Model ID", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Default", style="yellow")

    models_found = False

    # Show Anthropic models
    if provider in (None, "all", "anthropic") and anthropic_provider:
        try:
            models = anthropic_provider.supported_models
            for model in models:
                is_default = "←" if model == DEFAULT_AI_MODEL else ""
                table.add_row(model, "Anthropic", is_default)
                models_found = True
        except Exception as e:
            console.print(f"[yellow]Could not fetch Anthropic models: {e}[/yellow]")

    # Show OpenAI models
    if provider in (None, "all", "openai") and openai_provider:
        try:
            models = openai_provider.supported_models
            for model in models:
                is_default = "←" if model == DEFAULT_AI_MODEL else ""
                table.add_row(model, "OpenAI", is_default)
                models_found = True
        except Exception as e:
            console.print(f"[yellow]Could not fetch OpenAI models: {e}[/yellow]")

    if models_found:
        console.print(table)
        console.print()
        console.print(f"[dim]Current default: {DEFAULT_AI_MODEL}[/dim]")
        console.print("[dim]Use /model <name> in chat to switch models for that session[/dim]")
    else:
        console.print("[yellow]No models available.[/yellow]")
        console.print(
            "[dim]Set OPENAI_API_KEY or ANTHROPIC_API_KEY, or use --endpoint for local LLMs.[/dim]"
        )


@model_app.command(name="info")
def model_info(
    model_name: Annotated[
        str | None,
        typer.Argument(help="Model name to get info about"),
    ] = None,
) -> None:
    """Show information about a specific model or the default."""
    model = model_name or DEFAULT_AI_MODEL

    # Determine provider from model name
    model_lower = model.lower()
    if model_lower.startswith("claude"):
        provider_name = "Anthropic"
        provider_type = "anthropic"
    elif any(model_lower.startswith(p) for p in ["gpt-", "o1-", "o3-", "o4-"]):
        provider_name = "OpenAI"
        provider_type = "openai"
    else:
        provider_name = "Unknown"
        provider_type = None

    console.print(f"[bold cyan]Model:[/bold cyan] {model}")
    console.print(f"[bold cyan]Provider:[/bold cyan] {provider_name}")
    console.print(
        f"[bold cyan]Is Default:[/bold cyan] {'Yes' if model == DEFAULT_AI_MODEL else 'No'}"
    )

    # Check if provider is available
    openai_provider, anthropic_provider = _get_providers()
    if provider_type == "anthropic":
        if anthropic_provider:
            valid = (
                anthropic_provider.is_valid_model(model)
                if hasattr(anthropic_provider, "is_valid_model")
                else True
            )
            console.print(
                f"[bold cyan]Available:[/bold cyan] {'Yes' if valid else 'No (not in model list)'}"
            )
        else:
            console.print(
                "[yellow]Anthropic provider not configured (ANTHROPIC_API_KEY not set)[/yellow]"
            )
    elif provider_type == "openai":
        if openai_provider:
            valid = model in openai_provider.supported_models
            console.print(
                f"[bold cyan]Available:[/bold cyan] {'Yes' if valid else 'No (not in model list)'}"
            )
        else:
            console.print(
                "[yellow]OpenAI provider not configured "
                "(set OPENAI_API_KEY or use --endpoint for local LLMs)[/yellow]"
            )
