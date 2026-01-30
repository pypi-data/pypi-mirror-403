"""Git operations tools."""

import subprocess
from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.errors import ToolExecutionError

from cadecoder.core.logging import log

# ==============================================================================
# Helper functions (not tools, used by other parts of the codebase)
# ==============================================================================


def get_current_branch_name() -> tuple[str, str | None]:
    """Get the current active Git branch name.

    Returns:
        Tuple of (branch_name, error_message). error_message is None on success.
    """
    command = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    try:
        log.debug(f"Running git command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout_val = result.stdout.strip()
        if result.returncode != 0:
            err_msg = (
                result.stderr.strip()
                if result.stderr
                else f"Command failed: exit code {result.returncode}"
            )
            return stdout_val, err_msg
        return stdout_val, None
    except Exception as e:
        log.error(f"Unexpected error running git command: {e}")
        return "", f"Error running git command: {str(e)}"


def get_status() -> tuple[str, str | None]:
    """Get repository status using 'git status --short'.

    Returns:
        Tuple of (status_output, error_message). error_message is None on success.
    """
    command = ["git", "status", "--short"]
    try:
        log.debug(f"Running git command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout_val = result.stdout.strip()
        if result.returncode != 0:
            err_msg = (
                result.stderr.strip()
                if result.stderr
                else f"Command failed: exit code {result.returncode}"
            )
            return stdout_val, err_msg
        return stdout_val, None
    except Exception as e:
        log.error(f"Unexpected error running git command: {e}")
        return "", f"Error running git command: {str(e)}"


# ==============================================================================
# Internal helper for tools
# ==============================================================================


def _run_git_command(args: list[str], timeout: int = 30) -> tuple[str, str | None, int]:
    """Run a git command and return (stdout, stderr_if_error, exit_code)."""
    command = ["git"] + args
    try:
        log.debug(f"Running git command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip() if result.returncode != 0 else None
        return stdout, stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        log.error(f"Git command failed: {e}")
        return "", str(e), 1


@tool(name="Local_GitStatus", desc="Check git status of the repository.")
def git_status_tool(
    context: ToolContext,
    short: Annotated[bool, "Use short format output."] = True,
) -> Annotated[dict[str, Any], "Git status information."]:
    """Get the current git status of the repository."""
    args = ["status"]
    if short:
        args.append("--short")

    stdout, stderr, exit_code = _run_git_command(args)

    if stderr:
        raise ToolExecutionError(f"Git status failed: {stderr}")

    files = []
    for line in stdout.split("\n"):
        if line.strip():
            if short and len(line) >= 3:
                status = line[:2]
                filename = line[3:].strip()
                files.append({"status": status, "file": filename})
            else:
                files.append({"line": line})

    # Get current branch
    branch_stdout, _, _ = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    current_branch = branch_stdout if branch_stdout else "unknown"

    return {
        "branch": current_branch,
        "files": files if files else [],
        "clean": len(files) == 0,
        "raw_output": stdout if stdout else "",
    }


@tool(
    name="Local_GitDiff",
    desc="Show changes between commits, working tree, etc.",
)
def git_diff_tool(
    context: ToolContext,
    path: Annotated[str | None, "Specific file or directory to diff."] = None,
    staged: Annotated[bool, "Show staged changes (--cached)."] = False,
    commit: Annotated[str | None, "Compare with specific commit (e.g., 'HEAD~1', 'main')."] = None,
    stat: Annotated[bool, "Show diffstat instead of full diff."] = False,
    name_only: Annotated[bool, "Show only names of changed files."] = False,
) -> Annotated[dict[str, Any], "Git diff output."]:
    """Show changes in the repository."""
    args = ["diff"]

    if staged:
        args.append("--cached")
    if commit:
        args.append(commit)
    if stat:
        args.append("--stat")
    if name_only:
        args.append("--name-only")
    if path:
        args.extend(["--", path])

    stdout, stderr, exit_code = _run_git_command(args, timeout=60)

    if stderr and exit_code != 0:
        raise ToolExecutionError(f"Git diff failed: {stderr}")

    # Parse output if name_only
    if name_only:
        files = [f.strip() for f in stdout.split("\n") if f.strip()]
        return {
            "files": files,
            "count": len(files),
        }

    return {
        "diff": stdout if stdout else "(no changes)",
        "has_changes": bool(stdout.strip()),
    }


@tool(
    name="Local_GitLog",
    desc="Show commit history log.",
)
def git_log_tool(
    context: ToolContext,
    count: Annotated[int, "Number of commits to show."] = 10,
    oneline: Annotated[bool, "Show one line per commit."] = True,
    path: Annotated[str | None, "Show history for specific file/directory."] = None,
    author: Annotated[str | None, "Filter by author name or email."] = None,
    since: Annotated[str | None, "Show commits since date (e.g., '2 weeks ago')."] = None,
    until: Annotated[str | None, "Show commits until date."] = None,
    grep: Annotated[str | None, "Search commit messages."] = None,
) -> Annotated[dict[str, Any], "Git log output."]:
    """Show commit history."""
    args = ["log", f"-{count}"]

    if oneline:
        args.append("--oneline")
    else:
        args.append("--format=%H|%an|%ae|%ad|%s")
        args.append("--date=short")

    if author:
        args.extend(["--author", author])
    if since:
        args.extend(["--since", since])
    if until:
        args.extend(["--until", until])
    if grep:
        args.extend(["--grep", grep])
    if path:
        args.extend(["--", path])

    stdout, stderr, exit_code = _run_git_command(args, timeout=30)

    if stderr and exit_code != 0:
        raise ToolExecutionError(f"Git log failed: {stderr}")

    commits = []
    if stdout:
        for line in stdout.split("\n"):
            if not line.strip():
                continue
            if oneline:
                parts = line.split(" ", 1)
                if len(parts) >= 2:
                    commits.append(
                        {
                            "hash": parts[0],
                            "message": parts[1],
                        }
                    )
                else:
                    commits.append({"hash": line, "message": ""})
            else:
                parts = line.split("|")
                if len(parts) >= 5:
                    commits.append(
                        {
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "date": parts[3],
                            "message": parts[4],
                        }
                    )

    return {
        "commits": commits,
        "count": len(commits),
    }


@tool(
    name="Local_GitBranch",
    desc="List, create, or switch branches.",
)
def git_branch_tool(
    context: ToolContext,
    action: Annotated[str, "Action: 'list', 'current', 'create', 'delete', 'switch'."] = "list",
    name: Annotated[str | None, "Branch name (for create/delete/switch)."] = None,
    all_branches: Annotated[bool, "Include remote branches (for list)."] = False,
    force: Annotated[bool, "Force action (for delete)."] = False,
) -> Annotated[dict[str, Any], "Git branch operation result."]:
    """Perform git branch operations."""
    if action == "list":
        args = ["branch"]
        if all_branches:
            args.append("-a")
        stdout, stderr, exit_code = _run_git_command(args)

        if stderr and exit_code != 0:
            raise ToolExecutionError(f"Git branch list failed: {stderr}")

        branches = []
        current = None
        for line in stdout.split("\n"):
            if not line.strip():
                continue
            is_current = line.startswith("*")
            branch_name = line.lstrip("* ").strip()
            if is_current:
                current = branch_name
            branches.append(
                {
                    "name": branch_name,
                    "current": is_current,
                }
            )

        return {
            "branches": branches,
            "current": current,
            "count": len(branches),
        }

    elif action == "current":
        stdout, stderr, exit_code = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        if stderr and exit_code != 0:
            raise ToolExecutionError(f"Failed to get current branch: {stderr}")
        return {"current": stdout}

    elif action == "create":
        if not name:
            raise ToolExecutionError("Branch name required for create action")
        stdout, stderr, exit_code = _run_git_command(["checkout", "-b", name])
        if stderr and exit_code != 0:
            raise ToolExecutionError(f"Failed to create branch: {stderr}")
        return {
            "success": True,
            "message": f"Created and switched to branch '{name}'",
            "branch": name,
        }

    elif action == "delete":
        if not name:
            raise ToolExecutionError("Branch name required for delete action")
        args = ["branch", "-D" if force else "-d", name]
        stdout, stderr, exit_code = _run_git_command(args)
        if stderr and exit_code != 0:
            raise ToolExecutionError(f"Failed to delete branch: {stderr}")
        return {
            "success": True,
            "message": f"Deleted branch '{name}'",
        }

    elif action == "switch":
        if not name:
            raise ToolExecutionError("Branch name required for switch action")
        stdout, stderr, exit_code = _run_git_command(["checkout", name])
        if stderr and exit_code != 0:
            raise ToolExecutionError(f"Failed to switch branch: {stderr}")
        return {
            "success": True,
            "message": f"Switched to branch '{name}'",
            "branch": name,
        }

    else:
        raise ToolExecutionError(
            f"Unknown action: {action}. Use 'list', 'current', 'create', 'delete', or 'switch'."
        )
