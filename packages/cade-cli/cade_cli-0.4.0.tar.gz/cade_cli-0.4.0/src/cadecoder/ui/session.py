"""Main chat session for the TUI."""

import asyncio
import json
import os
import signal
import sys
from typing import Any

from rich.live import Live
from rich.markdown import Markdown
from ulid import ulid

from cadecoder.core.config import is_verbose
from cadecoder.core.constants import DEFAULT_AI_MODEL
from cadecoder.core.errors import AuthError
from cadecoder.core.logging import log
from cadecoder.core.types import ExecutionEventType
from cadecoder.execution.orchestrator import (
    ExecutionContext,
    create_orchestrator,
)
from cadecoder.storage.threads import (
    Message,
    ModelInfo,
    ToolCallInfo,
    get_thread_history,
)
from cadecoder.tools.local.git import get_current_branch_name
from cadecoder.ui.display import (
    clear_screen,
    console,
    display_git_branch_info,
    display_help,
    display_logs,
    display_messages,
    display_thread_header,
    display_tool_result,
    display_tools_async,
    strip_control_signals,
)

# Box-drawing characters that break Rich Markdown rendering
_BOX_CHARS = frozenset("┌┐└┘├┤┬┴┼─│═║╔╗╚╝╠╣╦╩╬")


def _has_box_chars(text: str) -> bool:
    """Check if text contains box-drawing characters."""
    return bool(_BOX_CHARS & set(text))


class ChatSession:
    """Manages a chat session with the AI agent."""

    def __init__(
        self,
        thread_id: str,
        model: str = DEFAULT_AI_MODEL,
        system_prompt: str | None = None,
        local_only: bool = False,
    ) -> None:
        """Initialize chat session."""
        self.thread_id = thread_id
        self.model = model
        self.system_prompt = system_prompt
        self.local_only = local_only
        self.history_manager = get_thread_history()
        self.thread = self.history_manager.get_thread(thread_id)
        self.orchestrator = create_orchestrator(default_model=model, local_only=local_only)
        self.current_task: asyncio.Task | None = None
        self._ctrl_c_count = 0

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """Get conversation history in LLM format."""
        messages = self.history_manager.get_messages(self.thread_id)
        history: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                history.append({"role": "system", "content": msg.content or ""})
            elif msg.role == "user":
                history.append({"role": "user", "content": msg.content or ""})
            elif msg.role == "assistant":
                entry: dict[str, Any] = {"role": "assistant", "content": msg.content}
                if msg.tool_calls:
                    entry["tool_calls"] = [
                        {
                            "id": tc.call_id,
                            "type": "function",
                            "function": {
                                "name": tc.tool_name,
                                "arguments": json.dumps(tc.parameters),
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                history.append(entry)
            elif msg.role == "tool":
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.responding_tool_call_id or "",
                        "content": msg.content or "",
                    }
                )

        return history

    def save_user_message(self, content: str) -> Message:
        """Save a user message."""
        message = Message(
            id=str(ulid()).lower(),
            thread_id=self.thread_id,
            role="user",
            content=content,
        )
        self.history_manager.add_message(message)
        return message

    def save_assistant_message(
        self,
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
        model_info: ModelInfo | None = None,
    ) -> Message:
        """Save an assistant message."""
        tc_infos = []
        if tool_calls:
            for tc in tool_calls:
                func = tc.get("function", {})
                args_raw = func.get("arguments", "{}")
                if isinstance(args_raw, str):
                    try:
                        params = json.loads(args_raw)
                    except json.JSONDecodeError:
                        params = {"raw": args_raw}
                else:
                    params = args_raw if isinstance(args_raw, dict) else {}

                tc_infos.append(
                    ToolCallInfo(
                        call_id=tc.get("id", str(ulid()).lower()),
                        tool_name=func.get("name", "unknown"),
                        parameters=params,
                    )
                )

        message = Message(
            id=str(ulid()).lower(),
            thread_id=self.thread_id,
            role="assistant",
            content=content,
            tool_calls=tc_infos,
            model_info=model_info,
        )
        self.history_manager.add_message(message)
        return message

    def save_tool_message(self, tool_call_id: str, content: str, tool_name: str) -> Message:
        """Save a tool response message."""
        message = Message(
            id=str(ulid()).lower(),
            thread_id=self.thread_id,
            role="tool",
            content=content,
            responding_tool_call_id=tool_call_id,
        )
        self.history_manager.add_message(message)
        return message

    async def process_input(self, user_input: str) -> None:
        """Process user input."""
        if user_input.startswith("/"):
            await self.handle_command(user_input)
            return

        history = self.get_conversation_history()
        self.save_user_message(user_input)

        context = ExecutionContext(task=user_input, conversation_history=history)
        # Track content for display only - saving happens on ASSISTANT_TURN_END
        display_content = ""

        console.print()

        try:
            with Live(console=console, refresh_per_second=10) as live:
                async for event in self.orchestrator.stream(context):
                    if event.type == ExecutionEventType.CONTENT:
                        display_content += event.content or ""
                        stripped = strip_control_signals(display_content, strip_whitespace=True)
                        if stripped:
                            # Plain text for box chars (Markdown breaks them)
                            if _has_box_chars(stripped):
                                live.update(stripped)
                            else:
                                live.update(Markdown(stripped))

                    elif event.type == ExecutionEventType.TOOL_CALL:
                        tc = event.metadata.get("tool_call", {})
                        func = tc.get("function", {})
                        tool_name = func.get("name", "unknown")
                        if is_verbose():
                            # Show tool name and arguments in verbose mode
                            args_str = func.get("arguments", "{}")
                            try:
                                args = json.loads(args_str)
                                # Truncate long values for display
                                display_args = {
                                    k: (
                                        v[:100] + "..."
                                        if isinstance(v, str) and len(v) > 100
                                        else v
                                    )
                                    for k, v in args.items()
                                }
                                args_display = json.dumps(display_args, indent=2)
                            except (json.JSONDecodeError, TypeError):
                                args_display = (
                                    args_str[:200] + "..." if len(args_str) > 200 else args_str
                                )
                            console.print(f"[dim]Calling tool: {tool_name}[/dim]")
                            console.print(
                                f"[dim bright_black]  args: {args_display}[/dim bright_black]"
                            )
                        else:
                            console.print(f"[dim]Calling tool: {tool_name}[/dim]")

                    elif event.type == ExecutionEventType.TOOL_RESULT:
                        tool_name = event.metadata.get("tool_name", "unknown")
                        tool_status = event.metadata.get("status", "success")
                        result_content = event.content or ""
                        display_tool_result(tool_name, result_content, status=tool_status)

                    elif event.type == ExecutionEventType.ASSISTANT_TURN_END:
                        # Save messages at end of each assistant turn
                        turn_content = event.content
                        turn_tool_calls = event.metadata.get("tool_calls", [])
                        turn_tool_results = event.metadata.get("tool_results", [])

                        # Save assistant message with tool calls for this turn
                        if turn_content or turn_tool_calls:
                            self.save_assistant_message(turn_content, turn_tool_calls)

                        # Save tool results for this turn
                        for tr in turn_tool_results:
                            self.save_tool_message(
                                tr.get("tool_call_id", ""),
                                tr.get("content", ""),
                                tr.get("tool_name", "unknown"),
                            )

                        # Reset display content for next turn
                        display_content = ""

        except asyncio.CancelledError:
            console.print("\n[yellow]Operation cancelled.[/yellow]")
            return
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            log.error(f"Error processing input: {e}", exc_info=True)
            return

        console.print()

    async def handle_command(self, cmd: str) -> None:
        """Handle slash commands."""
        cmd = cmd.strip()

        if cmd in ("/exit", "/quit"):
            raise SystemExit(0)
        elif cmd == "/help":
            display_help()
        elif cmd == "/clear":
            clear_screen()
        elif cmd == "/history":
            messages = self.history_manager.get_messages(self.thread_id)
            display_messages(messages)
        elif cmd == "/model":
            console.print(f"[cyan]Current model: {self.model}[/cyan]")
            console.print("[dim]Usage: /model list | /model <name>[/dim]")
        elif cmd.startswith("/model "):
            arg = cmd[7:].strip()
            if arg in ("list", "-l", "--list"):
                # Show available models
                console.print("[cyan]Available models:[/cyan]")
                try:
                    provider = self.orchestrator.provider
                    models = (
                        provider.supported_models if hasattr(provider, "supported_models") else []
                    )
                    if models:
                        for m in models:
                            marker = " [green]←[/green]" if m == self.model else ""
                            console.print(f"  • {m}{marker}")
                    else:
                        console.print("  [dim]Could not fetch model list[/dim]")
                except Exception as e:
                    console.print(f"  [red]Error fetching models: {e}[/red]")
            elif arg in ("help", "-h", "--help"):
                console.print("[cyan]Model command usage:[/cyan]")
                console.print("  /model          - Show current model")
                console.print("  /model list     - List available models")
                console.print("  /model <name>   - Switch to a specific model")
                console.print("\n[cyan]Examples:[/cyan]")
                console.print("  /model claude-3-5-sonnet-20241022")
                console.print("  /model claude-3-opus-20240229")
            elif arg:
                old_model = self.model
                # Validate model before switching
                try:
                    provider = self.orchestrator.provider
                    if hasattr(provider, "is_valid_model") and not provider.is_valid_model(arg):
                        console.print(f"[yellow]Warning: '{arg}' may not be a valid model[/yellow]")
                        console.print("[dim]Use /model list to see available models[/dim]")
                except Exception:
                    pass  # Skip validation if it fails

                self.model = arg
                try:
                    self.orchestrator = create_orchestrator(
                        default_model=arg, local_only=self.local_only
                    )
                    console.print(f"[green]Model changed: {old_model} → {arg}[/green]")
                except Exception as e:
                    self.model = old_model
                    console.print(f"[red]Failed to switch model: {e}[/red]")
        elif cmd == "/thread":
            if self.thread:
                console.print(f"[cyan]Thread ID: {self.thread.thread_id}[/cyan]")
                console.print(f"[cyan]Name: {self.thread.name or 'Unnamed'}[/cyan]")
            else:
                console.print(f"[cyan]Thread ID: {self.thread_id}[/cyan]")
        elif cmd == "/logs":
            display_logs()
        elif cmd == "/tools":
            await display_tools_async(self.orchestrator.tool_manager)
        elif cmd == "/context":
            history = self.get_conversation_history()
            status = self.orchestrator.get_context_status(history)
            console.print("[cyan]Context Window Status:[/cyan]")
            console.print(f"  Tokens: {status['token_count']:,} / {status['effective_limit']:,}")
            console.print(f"  Used: {status['percentage_used']}%")
            console.print(f"  Messages: {status['message_count']}")
            console.print(f"  Needs compaction: {status['needs_compaction']}")

            tool_summary = self.orchestrator.get_tool_outputs_summary()
            if tool_summary["total_outputs"] > 0:
                console.print("\n[cyan]Tool Outputs:[/cyan]")
                console.print(f"  Total outputs: {tool_summary['total_outputs']}")
                console.print(f"  Unique tools: {tool_summary['unique_tools']}")
                console.print(f"  Estimated tokens: {tool_summary['estimated_tokens']:,}")
        elif cmd == "/pwd":
            console.print(f"[cyan]{os.getcwd()}[/cyan]")
        elif cmd.startswith("/cd "):
            path = cmd[4:].strip()
            try:
                os.chdir(path)
                console.print(f"[green]Changed to: {os.getcwd()}[/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        elif cmd.startswith("/! "):
            import subprocess

            shell_cmd = cmd[3:].strip()
            try:
                result = subprocess.run(shell_cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    console.print(result.stdout)
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        else:
            console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            console.print("[dim]Type /help for available commands[/dim]")

    def cancel_current_task(self) -> None:
        """Cancel the current running task."""
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()


async def run_session(session: ChatSession) -> None:
    """Run the chat session loop."""
    loop = asyncio.get_running_loop()
    stop_requested = False

    def handle_sigint() -> None:
        """Handle Ctrl+C - exit immediately."""
        nonlocal stop_requested
        if stop_requested or session._ctrl_c_count >= 1:
            console.print("\n[bold red]Exiting.[/bold red]")
            os._exit(0)
        session._ctrl_c_count += 1
        stop_requested = True
        session.cancel_current_task()
        console.print("\n[yellow]Exiting... (Ctrl+C again to force)[/yellow]")

    try:
        loop.add_signal_handler(signal.SIGINT, handle_sigint)
    except (NotImplementedError, ValueError):
        pass

    # Display header
    branch_name, _ = get_current_branch_name()
    display_git_branch_info(branch_name)

    thread_name = session.thread.name if session.thread else session.thread_id[:8]
    display_thread_header(thread_name)

    # Show system prompt info in verbose mode
    if is_verbose():
        from cadecoder.ai.prompts import get_environment_context

        try:
            env_ctx = get_environment_context()
            # Show abbreviated prompt info
            console.print(
                "[dim bright_black]System prompt loaded with environment context:[/dim bright_black]"
            )
            # Show first few lines of environment context
            env_lines = env_ctx.split("\n")[:5]
            for line in env_lines:
                console.print(f"[dim bright_black]  {line}[/dim bright_black]")
            if len(env_ctx.split("\n")) > 5:
                console.print("[dim bright_black]  ...[/dim bright_black]")
        except Exception:
            pass

    # Display existing messages
    messages = session.history_manager.get_messages(session.thread_id)
    if messages:
        display_messages(messages)

    # Main loop
    while not stop_requested:
        try:
            session._ctrl_c_count = 0
            user_input = await loop.run_in_executor(None, lambda: input("> "))

            if stop_requested:
                break

            if not user_input.strip():
                continue

            session.current_task = asyncio.create_task(session.process_input(user_input.strip()))

            try:
                await session.current_task
            except asyncio.CancelledError:
                console.print("[yellow]Cancelled.[/yellow]")
                if stop_requested:
                    break

        except EOFError:
            console.print("\n[dim]Exiting.[/dim]")
            break
        except KeyboardInterrupt:
            console.print("\n[dim]Exiting.[/dim]")
            break
        except SystemExit:
            break

    console.print("[dim]Session ended.[/dim]")


def main(
    thread_id_to_run: str,
    model: str = DEFAULT_AI_MODEL,
    stream: bool = False,
    system_prompt: str | None = None,
    target_symbol: str | None = None,
    local_only: bool = False,
) -> None:
    """Main entry point for the TUI."""
    try:
        session = ChatSession(
            thread_id=thread_id_to_run,
            model=model,
            system_prompt=system_prompt,
            local_only=local_only,
        )
        asyncio.run(run_session(session))
    except AuthError as e:
        console.print(f"[red]Authentication error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        log.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


async def _run_single_message(
    message: str, model: str = DEFAULT_AI_MODEL, local_only: bool = False
) -> int:
    """Run a single message through the orchestrator.

    Args:
        message: The user message to process
        model: Model to use
        local_only: If True, skip remote tools

    Returns:
        Exit code (0=success, 1=error, 2=needs interactive)
    """
    orchestrator = create_orchestrator(default_model=model, local_only=local_only)
    context = ExecutionContext(task=message, conversation_history=[])

    accumulated_content = ""

    try:
        # Status to stderr
        print("\033[2m\033[3m[Processing...]\033[0m", file=sys.stderr)

        async for event in orchestrator.stream(context):
            if event.type == ExecutionEventType.CONTENT:
                chunk = event.content or ""
                cleaned = strip_control_signals(chunk, strip_whitespace=False)
                accumulated_content += cleaned

            elif event.type == ExecutionEventType.TOOL_CALL:
                tc = event.metadata.get("tool_call", {})
                func = tc.get("function", {})
                tool_name = func.get("name", "unknown")
                print(f"\033[2m\033[3m[Calling: {tool_name}]\033[0m", file=sys.stderr)

            elif event.type == ExecutionEventType.TOOL_RESULT:
                tool_name = event.metadata.get("tool_name", "unknown")
                result = event.content or ""
                preview = result[:80] + "..." if len(result) > 80 else result
                preview = preview.replace("\n", " ")
                print(
                    f"\033[2m\033[3m[Result: {tool_name}] {preview}\033[0m",
                    file=sys.stderr,
                )

        # Final output to stdout
        final_output = strip_control_signals(accumulated_content, strip_whitespace=True)
        if final_output:
            print(final_output)

        return 0

    except AuthError:
        print("\033[2m\033[3m[Authentication required]\033[0m", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        log.error(f"Single message error: {e}", exc_info=True)
        return 1


def run_single_message_mode(
    message: str, model: str = DEFAULT_AI_MODEL, local_only: bool = False
) -> int:
    """Entry point for single message mode.

    Args:
        message: The user message to process
        model: Model to use
        local_only: If True, skip remote tools

    Returns:
        Exit code (0=success, 1=error, 2=needs interactive)
    """
    return asyncio.run(_run_single_message(message, model, local_only=local_only))
