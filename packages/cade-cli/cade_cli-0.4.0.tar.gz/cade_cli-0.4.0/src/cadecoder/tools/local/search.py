"""Search tools using grep and ripgrep."""

import json
import pathlib
import subprocess
from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.errors import ToolExecutionError

from cadecoder.core.constants import DEFAULT_IGNORE_PATTERNS
from cadecoder.core.logging import log

PROJECT_ROOT = pathlib.Path.cwd()


def _resolve_safe_path(path_str: str, base_dir: pathlib.Path) -> pathlib.Path:
    """Resolve a path safely within a base directory."""
    path = pathlib.Path(path_str)
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


@tool(
    name="Local_SearchCode",
    desc="Search for files containing specific text or patterns using ripgrep.",
)
def search_code_tool(
    context: ToolContext,
    pattern: Annotated[str, "Text or regex pattern to search for."],
    directory: Annotated[str, "Directory to search in (relative to project root)."] = ".",
    file_extensions: Annotated[
        list[str] | None,
        "File extensions to search (e.g., ['py', 'js']). None searches all.",
    ] = None,
    case_sensitive: Annotated[bool, "Whether search should be case sensitive."] = False,
    max_results: Annotated[int, "Maximum number of results to return."] = 100,
) -> Annotated[dict[str, Any], "Search results with file paths and matching lines."]:
    """Search for files containing specific patterns using ripgrep."""
    if not pattern or not pattern.strip():
        raise ToolExecutionError("Search pattern cannot be empty.")

    safe_dir = _resolve_safe_path(directory, PROJECT_ROOT)
    if not safe_dir.exists() or not safe_dir.is_dir():
        return {
            "results": [],
            "summary": {
                "total_matches": 0,
                "error": f"Directory '{directory}' not found or not a directory",
            },
        }

    # Build ripgrep command
    rg_cmd = ["rg", "--json", "-m", str(max_results)]
    if not case_sensitive:
        rg_cmd.append("-i")
    if file_extensions:
        for ext in file_extensions:
            rg_cmd.extend(["-g", f"*.{ext.lstrip('.')}"])

    # Add ignore patterns
    for ignore in DEFAULT_IGNORE_PATTERNS:
        rg_cmd.extend(["-g", f"!{ignore}"])

    rg_cmd.append(pattern)
    rg_cmd.append(str(safe_dir))

    try:
        result = subprocess.run(
            rg_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        results = []
        files_with_matches: set[str] = set()

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    match_data = data.get("data", {})
                    path = match_data.get("path", {}).get("text", "")
                    line_num = match_data.get("line_number", 0)
                    line_text = match_data.get("lines", {}).get("text", "").strip()

                    try:
                        rel_path = str(pathlib.Path(path).relative_to(PROJECT_ROOT))
                    except ValueError:
                        rel_path = path

                    results.append(
                        {
                            "file": rel_path,
                            "line": line_num,
                            "content": line_text,
                        }
                    )
                    files_with_matches.add(rel_path)
            except json.JSONDecodeError:
                continue

        return {
            "results": results,
            "summary": {
                "total_matches": len(results),
                "files_with_matches": len(files_with_matches),
                "pattern_searched": pattern,
            },
        }
    except FileNotFoundError:
        log.warning("ripgrep not found, falling back to grep")
        return _search_with_grep(pattern, safe_dir, case_sensitive, max_results)
    except subprocess.TimeoutExpired:
        raise ToolExecutionError("Search timed out")
    except Exception as e:
        log.error(f"Search failed: {e}")
        raise ToolExecutionError(f"Search failed: {e}") from e


def _search_with_grep(
    pattern: str,
    directory: pathlib.Path,
    case_sensitive: bool,
    max_results: int,
) -> dict[str, Any]:
    """Fallback search using grep."""
    grep_cmd = ["grep", "-rn"]
    if not case_sensitive:
        grep_cmd.append("-i")
    grep_cmd.extend([pattern, str(directory)])

    try:
        result = subprocess.run(
            grep_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        results = []
        files_with_matches: set[str] = set()

        for line in result.stdout.strip().split("\n")[:max_results]:
            if not line:
                continue
            parts = line.split(":", 2)
            if len(parts) >= 3:
                try:
                    rel_path = str(pathlib.Path(parts[0]).relative_to(PROJECT_ROOT))
                except ValueError:
                    rel_path = parts[0]

                results.append(
                    {
                        "file": rel_path,
                        "line": int(parts[1]) if parts[1].isdigit() else 0,
                        "content": parts[2].strip(),
                    }
                )
                files_with_matches.add(rel_path)

        return {
            "results": results,
            "summary": {
                "total_matches": len(results),
                "files_with_matches": len(files_with_matches),
                "pattern_searched": pattern,
            },
        }
    except Exception as e:
        return {
            "results": [],
            "summary": {"total_matches": 0, "error": str(e)},
        }


@tool(
    name="Local_Grep",
    desc="Search files using grep with full grep syntax support.",
)
def grep_tool(
    context: ToolContext,
    pattern: Annotated[str, "Pattern to search for (supports basic regex)."],
    path: Annotated[str, "File or directory to search (relative to project root)."] = ".",
    recursive: Annotated[bool, "Search recursively in directories."] = True,
    case_sensitive: Annotated[bool, "Case sensitive search."] = False,
    whole_word: Annotated[bool, "Match whole words only."] = False,
    context_lines: Annotated[int, "Number of context lines before and after match."] = 0,
    max_results: Annotated[int, "Maximum number of results."] = 100,
) -> Annotated[dict[str, Any], "Grep search results."]:
    """Search files using grep with full grep syntax support."""
    if not pattern:
        raise ToolExecutionError("Pattern cannot be empty.")

    safe_path = _resolve_safe_path(path, PROJECT_ROOT)
    if not safe_path.exists():
        raise ToolExecutionError(f"Path not found: {path}")

    grep_cmd = ["grep", "-n"]
    if recursive and safe_path.is_dir():
        grep_cmd.append("-r")
    if not case_sensitive:
        grep_cmd.append("-i")
    if whole_word:
        grep_cmd.append("-w")
    if context_lines > 0:
        grep_cmd.extend(["-C", str(context_lines)])

    grep_cmd.extend([pattern, str(safe_path)])

    try:
        result = subprocess.run(
            grep_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        results = []
        for line in result.stdout.strip().split("\n")[:max_results]:
            if not line:
                continue
            # Parse grep output: file:line:content or line:content (single file)
            if safe_path.is_file():
                parts = line.split(":", 1)
                if len(parts) >= 2:
                    results.append(
                        {
                            "file": path,
                            "line": int(parts[0]) if parts[0].isdigit() else 0,
                            "content": parts[1],
                        }
                    )
            else:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    try:
                        rel_path = str(pathlib.Path(parts[0]).relative_to(PROJECT_ROOT))
                    except ValueError:
                        rel_path = parts[0]
                    results.append(
                        {
                            "file": rel_path,
                            "line": int(parts[1]) if parts[1].isdigit() else 0,
                            "content": parts[2],
                        }
                    )

        return {
            "results": results,
            "total": len(results),
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        raise ToolExecutionError("Grep search timed out")
    except Exception as e:
        raise ToolExecutionError(f"Grep failed: {e}") from e


@tool(
    name="Local_Ripgrep",
    desc="Fast search using ripgrep (rg) with advanced options.",
)
def ripgrep_tool(
    context: ToolContext,
    pattern: Annotated[str, "Pattern to search for (Rust regex syntax)."],
    path: Annotated[str, "File or directory to search (relative to project root)."] = ".",
    file_type: Annotated[str | None, "File type to search (e.g., 'py', 'js', 'rust')."] = None,
    glob: Annotated[
        str | None, "Glob pattern to filter files (e.g., '*.py', '!*.test.js')."
    ] = None,
    case_sensitive: Annotated[bool, "Case sensitive search."] = False,
    whole_word: Annotated[bool, "Match whole words only."] = False,
    hidden: Annotated[bool, "Search hidden files and directories."] = False,
    context_lines: Annotated[int, "Context lines before and after match."] = 0,
    max_results: Annotated[int, "Maximum number of results."] = 100,
) -> Annotated[dict[str, Any], "Ripgrep search results."]:
    """Fast search using ripgrep (rg) with advanced options.

    Ripgrep is faster than grep and respects .gitignore by default.
    """
    if not pattern:
        raise ToolExecutionError("Pattern cannot be empty.")

    safe_path = _resolve_safe_path(path, PROJECT_ROOT)
    if not safe_path.exists():
        raise ToolExecutionError(f"Path not found: {path}")

    rg_cmd = ["rg", "--line-number"]
    if not case_sensitive:
        rg_cmd.append("-i")
    if whole_word:
        rg_cmd.append("-w")
    if hidden:
        rg_cmd.append("--hidden")
    if context_lines > 0:
        rg_cmd.extend(["-C", str(context_lines)])
    if file_type:
        rg_cmd.extend(["-t", file_type])
    if glob:
        rg_cmd.extend(["-g", glob])

    rg_cmd.extend(["-m", str(max_results)])
    rg_cmd.extend([pattern, str(safe_path)])

    try:
        result = subprocess.run(
            rg_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        results = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Parse ripgrep output: file:line:content
            parts = line.split(":", 2)
            if len(parts) >= 3:
                try:
                    rel_path = str(pathlib.Path(parts[0]).relative_to(PROJECT_ROOT))
                except ValueError:
                    rel_path = parts[0]
                results.append(
                    {
                        "file": rel_path,
                        "line": int(parts[1]) if parts[1].isdigit() else 0,
                        "content": parts[2],
                    }
                )
            elif len(parts) == 2 and safe_path.is_file():
                results.append(
                    {
                        "file": path,
                        "line": int(parts[0]) if parts[0].isdigit() else 0,
                        "content": parts[1],
                    }
                )

        return {
            "results": results,
            "total": len(results),
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        raise ToolExecutionError("ripgrep (rg) not installed. Install with: brew install ripgrep")
    except subprocess.TimeoutExpired:
        raise ToolExecutionError("Ripgrep search timed out")
    except Exception as e:
        raise ToolExecutionError(f"Ripgrep failed: {e}") from e
