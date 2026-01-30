"""Shell and command execution tools."""

import pathlib
import subprocess
from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.errors import ToolExecutionError

from cadecoder.core.logging import log

PROJECT_ROOT = pathlib.Path.cwd()


def _resolve_safe_path(path_str: str, base_dir: pathlib.Path) -> pathlib.Path:
    """Resolve a path safely within a base directory."""
    path = pathlib.Path(path_str)
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


@tool(name="Local_ExecuteCommand", desc="Execute a shell command. Use with caution.")
def execute_command_tool(
    context: ToolContext,
    command: Annotated[str, "The shell command to execute."],
    cwd: Annotated[
        str | None,
        "Working directory for the command (relative to project root).",
    ] = None,
    timeout: Annotated[int, "Timeout for the command in seconds."] = 30,
) -> Annotated[dict, "Output of the command execution."]:
    """Executes a shell command."""
    if cwd:
        working_dir = _resolve_safe_path(cwd, PROJECT_ROOT)
        if not working_dir.is_dir():
            raise ToolExecutionError(f"Working directory not found: {cwd}")
    else:
        working_dir = PROJECT_ROOT

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=timeout if timeout > 0 else None,
        )

        return {
            "stdout": result.stdout if result.stdout else "no output",
            "stderr": result.stderr if result.stderr else "no stderr",
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        raise ToolExecutionError(f"Command timed out after {timeout} seconds")
    except Exception as e:
        log.error(f"Command execution failed: {e}")
        raise ToolExecutionError(f"Command execution failed: {e}") from e


@tool(
    name="Local_Bash",
    desc="Execute a bash command or script. Preferred for complex shell operations.",
)
def bash_tool(
    context: ToolContext,
    script: Annotated[str, "Bash command or script to execute."],
    cwd: Annotated[
        str | None,
        "Working directory for the script (relative to project root).",
    ] = None,
    timeout: Annotated[int, "Timeout for the script in seconds."] = 60,
    env: Annotated[
        dict[str, str] | None,
        "Additional environment variables to set.",
    ] = None,
) -> Annotated[dict, "Output of the bash execution."]:
    """Execute a bash command or script.

    This tool runs the provided script using /bin/bash -c.
    It's preferred over execute_command for complex shell operations
    that need bash-specific features like pipes, redirects, loops, etc.
    """
    import os

    if cwd:
        working_dir = _resolve_safe_path(cwd, PROJECT_ROOT)
        if not working_dir.is_dir():
            raise ToolExecutionError(f"Working directory not found: {cwd}")
    else:
        working_dir = PROJECT_ROOT

    # Merge environment variables
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    try:
        result = subprocess.run(
            ["/bin/bash", "-c", script],
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=timeout if timeout > 0 else None,
            env=full_env,
        )

        return {
            "stdout": result.stdout if result.stdout else "",
            "stderr": result.stderr if result.stderr else "",
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        raise ToolExecutionError(f"Script timed out after {timeout} seconds")
    except FileNotFoundError:
        raise ToolExecutionError("Bash not found at /bin/bash")
    except Exception as e:
        log.error(f"Bash execution failed: {e}")
        raise ToolExecutionError(f"Bash execution failed: {e}") from e
