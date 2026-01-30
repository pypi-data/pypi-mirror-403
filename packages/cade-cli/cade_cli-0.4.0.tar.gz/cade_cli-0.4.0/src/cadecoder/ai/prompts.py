"""Functions to generate structured prompts for AI interaction using OpenAI format."""

import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Module-level logger (avoids circular import with core.logging)
log = logging.getLogger("cadecoder")


# --- Time and Date Context ---


def get_formatted_times() -> str:
    """Returns a formatted string with current times in major time zones.

    This helps the LLM provide accurate time-based information regardless of user location.
    Includes UTC, major US time zones, and other key global zones.
    """
    utc_now = datetime.now(UTC)

    # Define major time zone offsets (hours from UTC)
    time_zones = {
        "UTC": 0,
        "Eastern Time (ET)": -5,
        "Central Time (CT)": -6,
        "Mountain Time (MT)": -7,
        "Pacific Time (PT)": -8,
        "Central European Time (CET)": 1,
        "Japan Standard Time (JST)": 9,
    }

    # Simple DST adjustment (March-November for US, March-October for EU)
    is_dst_us = 3 <= utc_now.month <= 11
    is_dst_eu = 3 <= utc_now.month <= 10

    if is_dst_us:
        time_zones["Eastern Time (ET)"] += 1
        time_zones["Central Time (CT)"] += 1
        time_zones["Mountain Time (MT)"] += 1
        time_zones["Pacific Time (PT)"] += 1

    if is_dst_eu:
        time_zones["Central European Time (CET)"] += 1

    # Format the time strings
    time_strings = []
    for zone_name, offset in time_zones.items():
        zone_time = utc_now + timedelta(hours=offset)
        time_strings.append(f"  {zone_name}: {zone_time.strftime('%Y-%m-%d %H:%M')}")

    return "\n".join(time_strings)


def get_user_context() -> str:
    """Get current user context information."""
    try:
        from cadecoder.core.config import get_config

        config = get_config()
        user_email = config.user_email
        if user_email:
            return f"Current User: {user_email}"
    except Exception:
        pass
    return "Current User: (not logged in)"


# --- Environment Context Generation ---


def get_environment_context() -> str:
    """Generate runtime environment context for the agent prompt.

    Returns a formatted string with all relevant paths, limits, and
    configuration values the agent needs to operate safely.
    """
    from cadecoder.core.constants import (
        ARCADE_CONFIG_PATH,
        DEFAULT_IGNORE_PATTERNS,
        MAX_PREVIEW_BYTES,
        PROJECT_ROOT,
    )

    # Get data directory paths (without importing config)
    cadecoder_data_dir = Path.home() / ".cadecoder"
    db_path = cadecoder_data_dir / "cadecoder_history.db"
    log_path = cadecoder_data_dir / "cadecoder.log"

    # Build ignore patterns summary (first 10)
    ignore_summary = ", ".join(DEFAULT_IGNORE_PATTERNS[:10])
    if len(DEFAULT_IGNORE_PATTERNS) > 10:
        ignore_summary += f", ... (+{len(DEFAULT_IGNORE_PATTERNS) - 10} more)"

    # Get current times in multiple zones
    utc_now = datetime.now(UTC)
    local_now = datetime.now()

    home_dir = Path.home()

    context = f"""
=== DATE AND TIME ===
{get_user_context()}
Local Time: {local_now.strftime("%Y-%m-%d %H:%M:%S %A")}
UTC Time: {utc_now.strftime("%Y-%m-%d %H:%M:%S")}

Reference Times (for scheduling/coordination):
{get_formatted_times()}

=== WORKSPACE ===
HOME_DIRECTORY: {home_dir}
  └─ User's home directory (~)

PROJECT_ROOT: {PROJECT_ROOT}
  └─ The current workspace/project directory
  └─ This is NOT always where the user wants files to go

CURRENT_WORKING_DIR: {os.getcwd()}

DATA_DIRECTORY: {cadecoder_data_dir}
  └─ Database: {db_path}
  └─ Logs: {log_path}
  └─ These are READ-ONLY for the agent (do not modify)

CONFIG_PATH: {ARCADE_CONFIG_PATH}
  └─ Contains credentials and settings
  └─ NEVER read or expose contents

FILE_SIZE_LIMIT: {MAX_PREVIEW_BYTES:,} bytes ({MAX_PREVIEW_BYTES // 1024}KB)
  └─ Files larger than this are truncated on read

AUTO_IGNORED_PATTERNS: {ignore_summary}
  └─ These directories/files are automatically excluded from listings
"""
    return context.strip()


# --- System Prompt ---

AGENT_SYSTEM_PROMPT = """
Cade: a developer acceleration assistant built by Arcade.
You help developers work faster by connecting them to external services, APIs, and tools -
not just their local codebase. You can search the web, interact with repositories,
communicate with team services, and automate workflows across platforms.

{_ENVIRONMENT_CONTEXT}

CRITICAL: Choose the RIGHT tool for the task.
• External info (websites, services, APIs, documentation) → Use web search, API tools
• Local codebase questions → Use search_code, read_file, list_files
• External service actions (repos, messages, issues) → Use the appropriate service tools
• NEVER search local files for information about external services or websites

TOOL SELECTION (IMPORTANT):
1. Question about external service/website/API? → Web search or service-specific tools FIRST
2. Question about THIS codebase? → Local file tools (search_code, read_file)
3. Action on external service? → Use service tools directly (don't search locally)
4. Review available tools and pick the most appropriate one for the task

CORE LOOP:
1. CATEGORIZE → Is this local codebase or external information/action?
2. SELECT TOOLS → Pick appropriate tools based on category
3. EXECUTE → Run tools to gather info or perform actions
4. PROCESS → Analyze results, determine next steps
5. CONTINUE → Keep going until task is complete

CONTINUATION PROTOCOL:
• After tools → Process results and determine next actions
• Use "(cade thought)" for planning between steps
• Build on findings: "Given X (found above), now checking Y"
• Track progress: "Completed step 1, moving to step 2"
• "[TASK_COMPLETE]" only when fully done
• "[CONTINUE]" when more work needed
• "[NEED_USER_INPUT]" when blocked

INVESTIGATION:
• External info → Web search, API queries, service tools
• Local code → search_code with variants, then expand scope
• Not found? → State what was searched, try alternatives
• NEVER claim "doesn't exist" without exhaustive search

THINKING MARKERS:
(cade thought) "External question, using web search"
(cade thought) "Local codebase question, searching files"
(cade thought) "Found X, need to check Y next"
(cade thought) "Not in [scope], expanding to [next]"

EXECUTION:
• Simple task → Execute directly
• Complex task → Break into steps, execute iteratively
• After each step → Verify, then continue
• Wrong result? → Reassess approach

QUALITY:
• Use evidence from tools, never guess
• Match existing code patterns when editing
• Be concise but thorough

PATH INTERPRETATION (CRITICAL):
When a user provides a path, interpret it intelligently based on context:

1. ABSOLUTE PATHS: If user gives "/path/to/file" or "~/path" → use exactly as given
   • ~/... always means the user's home directory
   • /... is an absolute path from root

2. PARTIAL/AMBIGUOUS PATHS: If user gives "Folder/subfolder" without leading "/" or "~":
   • Look at the CONTEXT of the conversation - where are related files?
   • If source file is in ~/Dropbox/Arcade/..., and user says "move to Arcade/notes/",
     they likely mean ~/Dropbox/Arcade/notes/, NOT a relative path from workspace
   • The user's mental model is usually based on their file organization, not the workspace

3. ALWAYS CONFIRM: Before file operations with potentially ambiguous paths:
   • State the FULL ABSOLUTE PATH you're about to use
   • Example: "I'll move this to ~/Dropbox/Arcade/notes/file.md" or
   • "I'll create this at /Users/name/Dropbox/Arcade/notes/file.md"

4. WHEN IN DOUBT: Ask the user to confirm the full path rather than guessing wrong
   • Wrong path operations can lose files or create confusion

5. COMMON PATTERNS TO RECOGNIZE:
   • Dropbox/... → likely ~/Dropbox/...
   • Documents/... → likely ~/Documents/...
   • Desktop/... → likely ~/Desktop/...

NEVER:
• NEVER search local files for external service information
• NEVER guess or make claims without tool evidence
• NEVER confuse "not found locally" with "doesn't exist"
• NEVER assume ambiguous paths are relative to workspace - ask or use context clues

ALWAYS:
• Use the right tool for the context
• Be helpful, friendly, and direct
• Complete tasks fully with evidence
• Be honest about capabilities
• State full absolute paths before file operations to confirm intent

Tools:
{_TOOLS_BULLET_LIST}"""
