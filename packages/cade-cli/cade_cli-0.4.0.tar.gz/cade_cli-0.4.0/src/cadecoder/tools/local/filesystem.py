"""Filesystem tools for reading, writing, and editing files."""

import difflib
import fnmatch
import pathlib
from typing import Annotated, Any, Literal

from arcade_tdk import ToolContext, tool
from arcade_tdk.errors import ToolExecutionError

from cadecoder.core.constants import (
    DEFAULT_IGNORE_PATTERNS,
    MAX_LIST_DEPTH,
    MAX_LIST_RESULTS,
    MAX_PREVIEW_BYTES,
    MODE_APPEND,
    MODE_OVERWRITE,
)
from cadecoder.core.logging import log

PROJECT_ROOT = pathlib.Path.cwd()


def _resolve_safe_path(path_str: str, base_dir: pathlib.Path) -> pathlib.Path:
    """Resolve a path safely within a base directory."""
    path = pathlib.Path(path_str)
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


def _should_ignore(path: pathlib.Path, ignore_patterns: list[str]) -> bool:
    """Check if a path should be ignored based on patterns."""
    path_str = str(path)
    name = path.name

    for pattern in ignore_patterns:
        if pattern.startswith("*."):
            if name.endswith(pattern[1:]):
                return True
        elif "*" in pattern:
            if fnmatch.fnmatch(name, pattern):
                return True
        else:
            if pattern in path_str.split("/"):
                return True
            if name == pattern:
                return True
    return False


def _read_text_file(file_path: pathlib.Path) -> str:
    """Read a text file, attempting common encodings."""
    encodings = ["utf-8", "latin-1", "cp1252"]
    for encoding in encodings:
        try:
            with file_path.open("r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            log.warning(f"Error reading file {file_path} with encoding {encoding}: {e}")
            raise

    log.warning(f"Could not decode file {file_path} with standard encodings.")
    with file_path.open("rb") as f:
        binary_content = f.read()
    return binary_content.decode("utf-8", errors="replace")


def _write_text_file(file_path: pathlib.Path, content: str) -> None:
    """Write text content to a file safely within project root."""
    project_root = pathlib.Path.cwd().resolve()
    resolved_path = file_path.expanduser().resolve()

    if project_root not in resolved_path.parents and resolved_path != project_root:
        raise ToolExecutionError(f"Refusing to write outside project root: '{file_path}'")

    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    with resolved_path.open("w", encoding="utf-8") as f:
        f.write(content)
    log.debug(f"Successfully wrote content to {resolved_path}")


def _generate_diff(original: str, new: str, filename: str = "file", context_lines: int = 3) -> str:
    """Generate unified diff between two strings."""
    lines1 = original.splitlines()
    lines2 = new.splitlines()
    diff = difflib.unified_diff(
        lines1,
        lines2,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        n=context_lines,
        lineterm="",
    )
    return "\n".join(diff)


@tool(
    name="Local_ListFiles",
    desc="List files in a directory (recursively up to a depth limit).",
)
def list_files_tool(
    context: ToolContext,
    directory: Annotated[
        str | None,
        "Directory path to list (relative to project root). Defaults to current directory.",
    ] = ".",
    recursive: Annotated[bool, "Whether to list files recursively."] = True,
    depth: Annotated[
        int, "Maximum depth for listing files. 0 means no depth limit."
    ] = MAX_LIST_DEPTH,
) -> Annotated[dict, "Output containing a list of files and an optional message."]:
    """Lists files and directories within a specified path."""
    if not 0 <= depth <= MAX_LIST_DEPTH:
        raise ToolExecutionError(f"Depth must be between 0 and {MAX_LIST_DEPTH}")

    base_path = _resolve_safe_path(directory or ".", PROJECT_ROOT)
    if not base_path.is_dir():
        raise ToolExecutionError(f"Not a directory: {directory or '.'}")

    listed_paths: list[str] = []
    if not recursive:
        for item in base_path.iterdir():
            try:
                if _should_ignore(item, DEFAULT_IGNORE_PATTERNS):
                    continue
                relative_to_project = item.relative_to(PROJECT_ROOT)
                listed_paths.append(str(relative_to_project))
                if len(listed_paths) >= MAX_LIST_RESULTS:
                    break
            except ValueError:
                continue
            except OSError as e:
                log.warning(f"Error processing path {item}: {e}")
                continue
    else:
        queue: list[tuple[pathlib.Path, int]] = [
            (child, 0)
            for child in base_path.iterdir()
            if not _should_ignore(child, DEFAULT_IGNORE_PATTERNS)
        ]

        while queue:
            if len(listed_paths) >= MAX_LIST_RESULTS:
                break
            current_item, item_depth = queue.pop(0)

            if item_depth > depth:
                continue

            try:
                relative_to_project = current_item.relative_to(PROJECT_ROOT)
                listed_paths.append(str(relative_to_project))

                if current_item.is_dir() and item_depth < depth:
                    for child in current_item.iterdir():
                        if not _should_ignore(child, DEFAULT_IGNORE_PATTERNS):
                            queue.append((child, item_depth + 1))
            except ValueError:
                continue
            except OSError as e:
                log.warning(f"Error processing path {current_item}: {e}")
                continue

    message = None
    if len(listed_paths) >= MAX_LIST_RESULTS:
        message = f"... (truncated at {MAX_LIST_RESULTS} entries)"

    listed_paths.sort()

    return {
        "files": listed_paths,
        "message": message if message else "Files listed successfully.",
    }


@tool(
    name="Local_ReadFile",
    desc="Read the entire content of a text file from the workspace.",
)
def read_file_tool(
    context: ToolContext,
    file_path_arg: Annotated[str, "Path to the file to read (relative or absolute)."],
) -> Annotated[dict, "Output containing the file content and an optional message."]:
    """Reads content of a specified file."""
    file_path = _resolve_safe_path(file_path_arg, PROJECT_ROOT)
    if not file_path.is_file():
        raise ToolExecutionError(f"File not found: {file_path_arg} (resolved: {file_path})")

    try:
        size = file_path.stat().st_size
        if size > MAX_PREVIEW_BYTES:
            log.warning(f"File {file_path_arg} exceeds preview limit. Truncating.")
            with file_path.open("rb") as f:
                start_bytes = f.read(MAX_PREVIEW_BYTES // 2)
                f.seek(max(0, size - MAX_PREVIEW_BYTES // 2))
                end_bytes = f.read(MAX_PREVIEW_BYTES // 2)
            start_str = start_bytes.decode("utf-8", errors="replace")
            end_str = end_bytes.decode("utf-8", errors="replace")
            content = start_str + f"\n... (file truncated, size: {size} bytes) ...\n" + end_str
            return {"content": content, "message": "File was truncated due to size."}
        else:
            content = _read_text_file(file_path)
            return {"content": content, "message": "File read successfully."}
    except OSError as e:
        raise ToolExecutionError(f"Error accessing file {file_path_arg}: {e}") from e


@tool(
    name="Local_WriteFile",
    desc="Write content to a file, creating/overwriting or appending.",
)
def write_file_tool(
    context: ToolContext,
    file_path_arg: Annotated[str, "Path of the file to write."],
    content: Annotated[str, "The complete content to write into the file."],
    mode: Annotated[
        Literal["overwrite", "append"],
        f"How to write: '{MODE_OVERWRITE}' to replace, '{MODE_APPEND}' to add to end.",
    ] = "overwrite",
) -> Annotated[dict, "Result of the write operation."]:
    """Writes content to a file."""
    resolved_path = _resolve_safe_path(file_path_arg, PROJECT_ROOT)

    try:
        if mode == MODE_APPEND and resolved_path.exists():
            existing_content = _read_text_file(resolved_path)
            content = existing_content + content

        _write_text_file(resolved_path, content)
        return {
            "success": True,
            "message": f"Successfully wrote to {file_path_arg}",
        }
    except Exception as e:
        raise ToolExecutionError(f"Failed to write file {file_path_arg}: {e}") from e


@tool(
    name="Local_EditFile",
    desc="Edit a file by replacing specific text. Use for targeted changes.",
)
def edit_file_tool(
    context: ToolContext,
    file_path_arg: Annotated[str, "Path to the file to edit."],
    old_string: Annotated[
        str,
        "The exact text to find and replace. Must match exactly including whitespace.",
    ],
    new_string: Annotated[str, "The text to replace old_string with."],
    expected_count: Annotated[
        int | None,
        "Expected number of replacements. If provided, fails if count doesn't match.",
    ] = None,
) -> Annotated[dict[str, Any], "Result of the edit operation including diff."]:
    """Edit a file by finding and replacing specific text."""
    resolved_path = _resolve_safe_path(file_path_arg, PROJECT_ROOT)

    if not resolved_path.is_file():
        raise ToolExecutionError(f"File not found: {file_path_arg}")

    try:
        original_content = _read_text_file(resolved_path)
    except Exception as e:
        raise ToolExecutionError(f"Failed to read file: {e}") from e

    count = original_content.count(old_string)

    if count == 0:
        preview_len = 100
        old_preview = old_string[:preview_len]
        if len(old_string) > preview_len:
            old_preview += "..."

        return {
            "success": False,
            "error": "old_string not found in file",
            "old_string_preview": old_preview,
            "file_size": len(original_content),
            "suggestion": "Check whitespace, indentation, and exact character match",
        }

    if expected_count is not None and count != expected_count:
        return {
            "success": False,
            "error": f"Expected {expected_count} occurrences but found {count}",
            "actual_count": count,
        }

    new_content = original_content.replace(old_string, new_string)
    diff = _generate_diff(original_content, new_content, file_path_arg, 3)

    try:
        _write_text_file(resolved_path, new_content)
    except Exception as e:
        raise ToolExecutionError(f"Failed to write file: {e}") from e

    return {
        "success": True,
        "message": f"Successfully edited {file_path_arg}",
        "replacements": count,
        "diff": diff if diff else "(no visible diff - content may be identical)",
    }


@tool(
    name="Local_EditFileInsert",
    desc="Insert text at a specific line number in a file.",
)
def edit_file_insert_tool(
    context: ToolContext,
    file_path_arg: Annotated[str, "Path to the file to edit."],
    line_number: Annotated[int, "Line number to insert at (1-indexed). 0 = end of file."],
    content: Annotated[str, "The text to insert."],
    position: Annotated[
        Literal["before", "after"],
        "Insert before or after the specified line.",
    ] = "before",
) -> Annotated[dict, "Result of the insert operation including diff."]:
    """Insert text at a specific line in a file."""
    resolved_path = _resolve_safe_path(file_path_arg, PROJECT_ROOT)

    if not resolved_path.is_file():
        raise ToolExecutionError(f"File not found: {file_path_arg}")

    try:
        original_content = _read_text_file(resolved_path)
    except Exception as e:
        raise ToolExecutionError(f"Failed to read file: {e}") from e

    lines = original_content.splitlines(keepends=True)

    if line_number == 0:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(content if content.endswith("\n") else content + "\n")
    elif line_number < 0 or line_number > len(lines) + 1:
        raise ToolExecutionError(
            f"Line number {line_number} out of range (file has {len(lines)} lines)"
        )
    else:
        idx = line_number - 1
        insert_content = content if content.endswith("\n") else content + "\n"

        if position == "before":
            lines.insert(idx, insert_content)
        else:
            lines.insert(idx + 1, insert_content)

    new_content = "".join(lines)
    diff = _generate_diff(original_content, new_content, file_path_arg, 3)

    try:
        _write_text_file(resolved_path, new_content)
    except Exception as e:
        raise ToolExecutionError(f"Failed to write file: {e}") from e

    return {
        "success": True,
        "message": f"Successfully inserted content at line {line_number}",
        "diff": diff,
    }
