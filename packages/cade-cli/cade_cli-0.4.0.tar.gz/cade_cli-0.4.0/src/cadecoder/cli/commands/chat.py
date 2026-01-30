"""Interactive chat command for CadeCoder CLI."""

import os
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape

from cadecoder.core.config import get_config, is_local_only_mode
from cadecoder.core.errors import CadeCoderError, StorageError, get_provider_config_help
from cadecoder.core.logging import log
from cadecoder.execution.orchestrator import create_orchestrator
from cadecoder.providers import initialize_providers
from cadecoder.providers.base import provider_registry
from cadecoder.storage.threads import get_thread_history
from cadecoder.tools.local.git import get_current_branch_name
from cadecoder.ui.session import main as run_tui_main

console = Console(stderr=True)


def _configure_custom_endpoint(endpoint: str) -> None:
    """Configure a custom API endpoint for local LLMs.

    Automatically detects Ollama endpoints and uses the native OllamaProvider
    for full tool calling support. Falls back to OpenAI-compatible mode for
    other endpoints.

    Args:
        endpoint: The custom API endpoint URL (e.g., http://localhost:11434/v1)
    """
    # Detect Ollama endpoint (port 11434 or contains "ollama")
    is_ollama = ":11434" in endpoint or "ollama" in endpoint.lower()

    if is_ollama:
        # Use native Ollama provider for full tool calling support
        # Remove /v1 suffix if present (native API doesn't use it)
        ollama_base = endpoint.rstrip("/").replace("/v1", "").replace("/api", "")
        os.environ["OLLAMA_BASE_URL"] = ollama_base
        log.info(f"Detected Ollama endpoint, using native OllamaProvider at {ollama_base}")
    else:
        # Use OpenAI-compatible provider for other endpoints
        os.environ["OPENAI_BASE_URL"] = endpoint
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "local"
        log.info(f"Using OpenAI-compatible provider with endpoint {endpoint}")

    # Re-initialize providers with the new endpoint
    provider_registry._providers.clear()
    provider_registry._default_provider = None
    initialize_providers()


def chat(
    thread_or_name: Annotated[
        str | None,
        typer.Argument(help="Thread ID or Thread Name to resume (optional)"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="AI model to use for the conversation.",
        ),
    ] = None,
    endpoint: Annotated[
        str | None,
        typer.Option(
            "--endpoint",
            "-e",
            help="Custom API endpoint URL (for OpenAI-compatible APIs like Ollama, vLLM, etc.)",
        ),
    ] = None,
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Name for the new thread (ignored if resuming existing thread).",
        ),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option(
            "--prompt",
            "-p",
            help="System prompt to guide the AI assistant's behavior.",
        ),
    ] = None,
    local_only: Annotated[
        bool,
        typer.Option(
            "--local-only",
            "-L",
            help="Disable Arcade Cloud tools (use only local tools).",
        ),
    ] = False,
) -> None:
    """
    Start an interactive chat session with AI.

    Can start a new chat or resume an existing thread. Supports multiple AI models
    and custom system prompts.
    """
    command_name = "chat"
    try:
        # Figure out which model to use: CLI flag > config > constant
        resolved_model = model or get_config().settings.default_model
        if endpoint:
            _configure_custom_endpoint(endpoint)

        effective_local_only = local_only or is_local_only_mode()

        # Preflight: ensure provider/API keys are configured before entering TUI
        try:
            _ = create_orchestrator(local_only=effective_local_only)
        except Exception:
            console.print(f"[bold red]Error:[/bold red] {get_provider_config_help()}")
            raise typer.Exit(code=1)

        # Get the thread history manager
        history_manager = get_thread_history()

        # Determine current git branch (used to disambiguate names)
        current_branch_raw, branch_error = get_current_branch_name()
        current_branch: str | None = current_branch_raw
        if branch_error:
            log.warning(f"Could not get git branch: {branch_error}")
            current_branch = None

        thread = None
        selected_thread_id: str | None = None

        if thread_or_name is not None:
            # First, try exact thread ID
            thread = history_manager.get_thread(thread_or_name)

            # If not found, treat as a thread name
            if not thread:
                # Prefer branch-scoped lookup if available
                if current_branch:
                    thread = history_manager.find_thread_by_name_and_branch(
                        thread_or_name, current_branch
                    )
                # Fallback: search most recently updated thread with that exact name
                if not thread:
                    all_threads = history_manager.list_threads()
                    for t in all_threads:
                        if t.name == thread_or_name:
                            thread = t
                            break

                # If still not found, create a new thread with this name
                if not thread:
                    try:
                        user_id = get_config().user_email
                    except Exception:
                        user_id = None
                    thread = history_manager.create_thread(
                        name=thread_or_name,
                        git_branch=current_branch,
                        model=resolved_model,
                        user_id=user_id,
                    )
                    log.info(
                        f"Created new thread '{thread_or_name}' with ID: {thread.thread_id} for branch: {current_branch}"
                    )

            selected_thread_id = thread.thread_id
        else:
            # No positional provided: follow original behavior (optionally use --name)
            if name and current_branch:
                thread = history_manager.find_thread_by_name_and_branch(name, current_branch)
                if thread:
                    selected_thread_id = thread.thread_id
                    log.info(
                        f"Resuming existing thread '{name}' (ID: {selected_thread_id}) for branch: {current_branch}"
                    )

            if not thread:
                try:
                    user_id = get_config().user_email
                except Exception:
                    user_id = None
                thread = history_manager.create_thread(
                    name=name,
                    git_branch=current_branch,
                    model=resolved_model,
                    user_id=user_id,
                )
                selected_thread_id = thread.thread_id
                if name:
                    log.info(
                        f"Created new thread '{name}' with ID: {selected_thread_id} for branch: {current_branch}"
                    )
                else:
                    log.info(
                        f"Created new thread with ID: {selected_thread_id} for branch: {current_branch}"
                    )

        # Safety check
        if not selected_thread_id:
            console.print("[red]Failed to determine or create a thread to run.[/red]")
            raise typer.Exit(code=1)

        # Launch TUI
        run_tui_main(
            thread_id_to_run=str(selected_thread_id),
            model=resolved_model,
            stream=True,
            system_prompt=prompt,
            local_only=effective_local_only,
        )
    except (StorageError, CadeCoderError) as e:
        console.print(":x: [bold red]Error:[/bold red] " + escape(str(e)))
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat session ended by user.[/yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        log.exception(f"An unexpected error occurred during '{command_name}'.")
        console.print(":x: [bold red]Unexpected Error:[/bold red] " + escape(str(e)))
        raise typer.Exit(code=1)


def resume(
    name: Annotated[
        str | None,
        typer.Argument(help="Thread name to resume (optional)"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="AI model to use for the conversation.",
        ),
    ] = None,
    endpoint: Annotated[
        str | None,
        typer.Option(
            "--endpoint",
            "-e",
            help="Custom API endpoint URL (for OpenAI-compatible APIs like Ollama, vLLM).",
        ),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option(
            "--prompt",
            "-p",
            help="System prompt to guide the AI assistant's behavior.",
        ),
    ] = None,
    local_only: Annotated[
        bool,
        typer.Option(
            "--local-only",
            "-L",
            help="Only use local tools.",
        ),
    ] = False,
) -> None:
    """Resume a saved chat thread.

    If a thread name is provided, the most recently updated thread matching that
    name will be resumed. Otherwise, the most recently updated thread overall is resumed.

    Examples
    --------
    - cade resume
    - cade resume "Onboarding Tasks"
    - cade -r  # resumes most recent thread (shortcut)
    """
    command_name = "resume"
    try:
        # Figure out which model to use: CLI flag > config > constant
        resolved_model = model or get_config().settings.default_model
        if endpoint:
            _configure_custom_endpoint(endpoint)

        effective_local_only = local_only or is_local_only_mode()

        # Preflight provider before entering TUI
        try:
            _ = create_orchestrator(local_only=effective_local_only)
        except Exception:
            console.print(f"[bold red]Error:[/bold red] {get_provider_config_help()}")
            raise typer.Exit(code=1)

        history_manager = get_thread_history()

        threads = history_manager.list_threads()
        if not threads:
            console.print("[yellow]No saved threads found.[/yellow]")
            raise typer.Exit(code=0)

        target_thread = None
        if name:
            # Try exact name match first
            matching = [t for t in threads if t.name and t.name == name]
            if matching:
                target_thread = matching[0]
            else:
                # Try partial match (prefix)
                partial = [t for t in threads if t.name and t.name.startswith(name)]
                if len(partial) == 1:
                    target_thread = partial[0]
                elif len(partial) > 1:
                    console.print(f"[yellow]Multiple threads match '{name}':[/yellow]")
                    for t in partial[:5]:
                        console.print(f"  - {t.name}")
                    raise typer.Exit(code=1)
                else:
                    # Try ID match as fallback
                    id_match = [t for t in threads if t.thread_id.startswith(name)]
                    if len(id_match) == 1:
                        target_thread = id_match[0]
                    elif len(id_match) > 1:
                        console.print(f"[yellow]Multiple threads match ID '{name}':[/yellow]")
                        for t in id_match[:5]:
                            console.print(f"  - {t.thread_id} ({t.name})")
                        raise typer.Exit(code=1)
                    else:
                        console.print(f"[red]No thread found matching '{name}'.[/red]")
                        unique_names = [t.name for t in threads if t.name][:10]
                        if unique_names:
                            console.print("[dim]Available threads (recent first):[/dim]")
                            for n in unique_names:
                                console.print(f"  - {n}")
                        raise typer.Exit(code=1)
        else:
            target_thread = threads[0]

        run_tui_main(
            thread_id_to_run=str(target_thread.thread_id),
            model=resolved_model,
            stream=True,
            system_prompt=prompt,
            local_only=effective_local_only,
        )
    except (StorageError, CadeCoderError) as e:
        console.print(":x: [bold red]Error:[/bold red] " + escape(str(e)))
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat session ended by user.[/yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        log.exception(f"An unexpected error occurred during '{command_name}'.")
        console.print(":x: [bold red]Unexpected Error:[/bold red] " + escape(str(e)))
        raise typer.Exit(code=1)
