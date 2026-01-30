"""Context window management for the agent.

Provides token tracking, context compaction, and backup functionality
to manage the LLM context window effectively.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Module-level logger (avoids circular import)
log = logging.getLogger("cadecoder")


class CompactionStrategy(str, Enum):
    """Strategy for compacting context when window is full."""

    KEEP_RECENT = "keep_recent"  # Keep most recent messages
    SUMMARIZE_EARLY = "summarize_early"  # Summarize early messages, keep recent
    KEEP_TOOL_RESULTS_FINAL = "keep_tool_results_final"  # Only keep final tool results
    DROP_TOOL_OUTPUTS = "drop_tool_outputs"  # Remove tool outputs, keep structure


@dataclass
class TokenEstimate:
    """Token estimate for a message or context."""

    text_tokens: int
    tool_call_tokens: int
    total: int

    @classmethod
    def from_text(cls, text: str, chars_per_token: float = 4.0) -> "TokenEstimate":
        """Estimate tokens from text using character ratio."""
        text_tokens = int(len(text) / chars_per_token)
        return cls(text_tokens=text_tokens, tool_call_tokens=0, total=text_tokens)

    @classmethod
    def from_message(cls, message: dict[str, Any], chars_per_token: float = 4.0) -> "TokenEstimate":
        """Estimate tokens from a message dict."""
        text_tokens = 0
        tool_tokens = 0

        content = message.get("content", "")
        if content:
            text_tokens = int(len(content) / chars_per_token)

        # Count tool calls
        tool_calls = message.get("tool_calls", [])
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            args = func.get("arguments", "")
            tool_tokens += int((len(name) + len(args)) / chars_per_token)

        return cls(
            text_tokens=text_tokens,
            tool_call_tokens=tool_tokens,
            total=text_tokens + tool_tokens,
        )


@dataclass
class ContextBackup:
    """Backup of context before compaction."""

    timestamp: datetime
    messages: list[dict[str, Any]]
    token_count: int
    compaction_reason: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "messages": self.messages,
            "token_count": self.token_count,
            "compaction_reason": self.compaction_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextBackup":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            messages=data["messages"],
            token_count=data["token_count"],
            compaction_reason=data["compaction_reason"],
        )


@dataclass
class ToolOutputCollection:
    """Collection of tool outputs with different retention strategies."""

    all_outputs: list[dict[str, Any]] = field(default_factory=list)
    final_outputs: dict[str, str] = field(default_factory=dict)

    def add_output(self, tool_name: str, output: str, tool_call_id: str) -> None:
        """Add a tool output to the collection."""
        self.all_outputs.append(
            {
                "tool_name": tool_name,
                "output": output,
                "tool_call_id": tool_call_id,
                "timestamp": datetime.now().isoformat(),
            }
        )
        # Always update final output to latest
        self.final_outputs[tool_name] = output

    def get_all_outputs(self) -> list[dict[str, Any]]:
        """Get all collected outputs."""
        return self.all_outputs.copy()

    def get_final_outputs(self) -> dict[str, str]:
        """Get only the final output for each tool."""
        return self.final_outputs.copy()

    def get_total_size(self) -> int:
        """Get total character size of all outputs."""
        return sum(len(o.get("output", "")) for o in self.all_outputs)

    def clear(self) -> None:
        """Clear all collected outputs."""
        self.all_outputs.clear()
        self.final_outputs.clear()


class ContextWindowManager:
    """Manages the LLM context window with compaction and backup support.

    Tracks token usage, manages context size, and provides methods for
    compacting context when the window is full.
    """

    # Model context limits (updated Jan 2026)
    # OpenAI: https://platform.openai.com/docs/models
    # Anthropic: https://docs.anthropic.com/en/docs/about-claude/models
    MODEL_CONTEXT_LIMITS = {
        # OpenAI GPT-4.1 family (1M context via API, max output 32,768)
        "gpt-4.1": 1_000_000,
        "gpt-4.1-mini": 1_000_000,
        "gpt-4.1-nano": 1_000_000,
        # OpenAI GPT-4o family
        "gpt-4o": 128_000,
        "gpt-4o-mini": 128_000,
        # OpenAI legacy models
        "gpt-4-turbo": 128_000,
        "gpt-4": 8_192,
        "gpt-3.5-turbo": 16_385,
        # Anthropic Claude 4 family (200K standard, 1M beta for Sonnet 4)
        "claude-opus-4.5": 200_000,
        "claude-sonnet-4": 200_000,
        # Anthropic Claude 3 family
        "claude-3-opus": 200_000,
        "claude-3-sonnet": 200_000,
        "claude-3-haiku": 200_000,
        "claude-3.5-sonnet": 200_000,
        "claude-3.5-haiku": 200_000,
    }

    # Max output tokens per model (for reserving response space)
    MODEL_MAX_OUTPUT = {
        "gpt-4.1": 32_768,
        "gpt-4.1-mini": 32_768,
        "gpt-4.1-nano": 32_768,
        "gpt-4o": 16_384,
        "gpt-4o-mini": 16_384,
        "gpt-4-turbo": 4_096,
        "gpt-4": 4_096,  # Legacy GPT-4 has smaller output
        "gpt-3.5-turbo": 4_096,
        "claude-opus-4.5": 8_192,
        "claude-sonnet-4": 8_192,
        "claude-3-opus": 4_096,
        "claude-3-sonnet": 4_096,
        "claude-3-haiku": 4_096,
        "claude-3.5-sonnet": 8_192,
        "claude-3.5-haiku": 8_192,
    }

    # Reserve tokens for response (fallback if model not in MODEL_MAX_OUTPUT)
    # Uses 10% of context limit or 4096, whichever is smaller
    RESPONSE_RESERVE = 4_096

    # Compaction threshold (% of window used before compaction)
    COMPACTION_THRESHOLD = 0.85

    def __init__(
        self,
        model: str = "gpt-4.1",
        backup_dir: Path | None = None,
        chars_per_token: float = 4.0,
    ) -> None:
        """Initialize context window manager.

        Args:
            model: Model name for context limit lookup
            backup_dir: Directory for storing context backups
            chars_per_token: Character to token ratio for estimation
        """
        self.model = model
        self.chars_per_token = chars_per_token

        # Set context limit based on model (default to 128K for unknown models)
        self.context_limit = self.MODEL_CONTEXT_LIMITS.get(model, 128_000)

        # Set response reserve based on model's max output tokens
        self.response_reserve = self.MODEL_MAX_OUTPUT.get(model, self.RESPONSE_RESERVE)
        self.effective_limit = self.context_limit - self.response_reserve

        # Backup directory
        if backup_dir is None:
            backup_dir = Path.home() / ".cadecoder" / "context_backups"
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Tool output collection
        self.tool_outputs = ToolOutputCollection()

        # Current context tracking
        self._current_token_count = 0
        self._message_count = 0
        self._backups: list[ContextBackup] = []

        log.info(
            f"ContextWindowManager initialized: model={model}, "
            f"limit={self.context_limit:,}, effective={self.effective_limit:,}"
        )

    def estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Estimate total tokens for a list of messages."""
        total = 0
        for msg in messages:
            estimate = TokenEstimate.from_message(msg, self.chars_per_token)
            total += estimate.total
        return total

    def estimate_message_tokens(self, message: dict[str, Any]) -> TokenEstimate:
        """Estimate tokens for a single message."""
        return TokenEstimate.from_message(message, self.chars_per_token)

    def check_context_status(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Check current context window status.

        Returns:
            Dict with token_count, percentage_used, needs_compaction, available_tokens
        """
        token_count = self.estimate_tokens(messages)
        percentage_used = token_count / self.effective_limit
        needs_compaction = percentage_used >= self.COMPACTION_THRESHOLD

        return {
            "token_count": token_count,
            "percentage_used": round(percentage_used * 100, 1),
            "needs_compaction": needs_compaction,
            "available_tokens": self.effective_limit - token_count,
            "effective_limit": self.effective_limit,
            "message_count": len(messages),
        }

    def compact_context(
        self,
        messages: list[dict[str, Any]],
        strategy: CompactionStrategy = CompactionStrategy.KEEP_RECENT,
        target_percentage: float = 0.6,
    ) -> tuple[list[dict[str, Any]], ContextBackup]:
        """Compact context to reduce token usage.

        Args:
            messages: Current message list
            strategy: Compaction strategy to use
            target_percentage: Target percentage of context limit after compaction

        Returns:
            Tuple of (compacted_messages, backup)
        """
        # Create backup before compaction
        current_tokens = self.estimate_tokens(messages)
        backup = ContextBackup(
            timestamp=datetime.now(),
            messages=messages.copy(),
            token_count=current_tokens,
            compaction_reason=f"strategy={strategy.value}, threshold={self.COMPACTION_THRESHOLD}",
        )

        # Save backup to disk
        self._save_backup(backup)
        self._backups.append(backup)

        target_tokens = int(self.effective_limit * target_percentage)

        log.info(
            f"Compacting context: {current_tokens:,} -> {target_tokens:,} tokens "
            f"(strategy={strategy.value})"
        )

        if strategy == CompactionStrategy.KEEP_RECENT:
            compacted = self._compact_keep_recent(messages, target_tokens)
        elif strategy == CompactionStrategy.SUMMARIZE_EARLY:
            compacted = self._compact_summarize_early(messages, target_tokens)
        elif strategy == CompactionStrategy.KEEP_TOOL_RESULTS_FINAL:
            compacted = self._compact_keep_final_tool_results(messages, target_tokens)
        elif strategy == CompactionStrategy.DROP_TOOL_OUTPUTS:
            compacted = self._compact_drop_tool_outputs(messages, target_tokens)
        else:
            compacted = self._compact_keep_recent(messages, target_tokens)

        new_token_count = self.estimate_tokens(compacted)
        log.info(
            f"Compaction complete: {len(messages)} -> {len(compacted)} messages, "
            f"{current_tokens:,} -> {new_token_count:,} tokens"
        )

        return compacted, backup

    def _compact_keep_recent(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Keep only the most recent messages within token budget.

        Preserves tool_call/tool_result pairs as atomic units to avoid
        breaking Anthropic's requirement that tool_use blocks must have
        corresponding tool_result blocks immediately after.
        """
        # Always keep system message if present
        system_msg = None
        other_msgs = []

        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg
            else:
                other_msgs.append(msg)

        # Group messages into atomic units (preserving tool_call + tool_result pairs)
        message_groups = self._group_messages_for_compaction(other_msgs)

        # Build from most recent groups, working backwards
        compacted_groups = []
        current_tokens = 0

        if system_msg:
            system_tokens = self.estimate_message_tokens(system_msg).total
            current_tokens += system_tokens

        # Add message groups from most recent
        for group in reversed(message_groups):
            group_tokens = sum(self.estimate_message_tokens(msg).total for msg in group)
            if current_tokens + group_tokens <= target_tokens:
                compacted_groups.insert(0, group)
                current_tokens += group_tokens
            else:
                break

        # Flatten groups back to message list
        compacted = []
        if system_msg:
            compacted.append(system_msg)
        for group in compacted_groups:
            compacted.extend(group)

        return compacted

    def _group_messages_for_compaction(
        self, messages: list[dict[str, Any]]
    ) -> list[list[dict[str, Any]]]:
        """Group messages into atomic units for compaction.

        Groups:
        - Assistant message with tool_calls + all following tool result messages
        - Regular user/assistant messages as single-item groups

        This ensures tool_call/tool_result pairs are never split during compaction.
        Handles both OpenAI format (tool_calls array) and Anthropic format
        (content array with tool_use blocks).
        """
        groups: list[list[dict[str, Any]]] = []
        i = 0

        while i < len(messages):
            msg = messages[i]
            role = msg.get("role")

            # Check for OpenAI format: assistant message with tool_calls array
            if role == "assistant" and msg.get("tool_calls"):
                group = [msg]
                tool_call_ids = {tc.get("id") for tc in msg.get("tool_calls", [])}

                # Collect subsequent tool result messages
                j = i + 1
                while j < len(messages):
                    next_msg = messages[j]
                    if next_msg.get("role") == "tool":
                        tool_call_id = next_msg.get("tool_call_id")
                        if tool_call_id in tool_call_ids:
                            group.append(next_msg)
                            tool_call_ids.discard(tool_call_id)
                            j += 1
                            continue
                    break

                groups.append(group)
                i = j

            # Check for Anthropic format: assistant message with tool_use in content
            elif role == "assistant" and self._has_tool_use_blocks(msg):
                group = [msg]
                tool_use_ids = self._extract_tool_use_ids(msg)

                # Collect subsequent user messages that contain tool_result blocks
                j = i + 1
                while j < len(messages) and tool_use_ids:
                    next_msg = messages[j]
                    if next_msg.get("role") == "user":
                        result_ids = self._extract_tool_result_ids(next_msg)
                        if result_ids & tool_use_ids:
                            # This user message has matching tool results
                            group.append(next_msg)
                            tool_use_ids -= result_ids
                            j += 1
                            continue
                    break

                groups.append(group)
                i = j

            else:
                # Single message group
                groups.append([msg])
                i += 1

        return groups

    def _has_tool_use_blocks(self, msg: dict[str, Any]) -> bool:
        """Check if message has Anthropic-style tool_use content blocks."""
        content = msg.get("content")
        if not isinstance(content, list):
            return False
        return any(isinstance(block, dict) and block.get("type") == "tool_use" for block in content)

    def _extract_tool_use_ids(self, msg: dict[str, Any]) -> set[str]:
        """Extract tool_use IDs from Anthropic-style assistant message."""
        ids: set[str] = set()
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_id = block.get("id")
                    if tool_id:
                        ids.add(tool_id)
        return ids

    def _extract_tool_result_ids(self, msg: dict[str, Any]) -> set[str]:
        """Extract tool_use_ids from Anthropic-style tool_result content blocks."""
        ids: set[str] = set()
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_use_id = block.get("tool_use_id")
                    if tool_use_id:
                        ids.add(tool_use_id)
        return ids

    def _compact_summarize_early(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Summarize early messages, keep recent ones in full."""
        # For now, use keep_recent with a summary placeholder
        # Full implementation would call LLM to summarize
        compacted = self._compact_keep_recent(messages, target_tokens)

        # Add summary placeholder for dropped messages
        dropped_count = len(messages) - len(compacted)
        if dropped_count > 0 and compacted:
            # Find first non-system message
            insert_idx = 1 if compacted[0].get("role") == "system" else 0
            summary_msg = {
                "role": "system",
                "content": f"[Context compacted: {dropped_count} earlier messages summarized. "
                "Continue from here.]",
            }
            compacted.insert(insert_idx, summary_msg)

        return compacted

    def _compact_keep_final_tool_results(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Keep only final tool results, replacing intermediate ones with summaries."""
        compacted = []
        tool_results_by_name: dict[str, dict[str, Any]] = {}

        # First pass: identify final tool results
        for msg in messages:
            if msg.get("role") == "tool":
                tool_name = msg.get("tool_name", msg.get("name", "unknown"))
                tool_results_by_name[tool_name] = msg
            else:
                compacted.append(msg)

        # Second pass: add final tool results
        for tool_msg in tool_results_by_name.values():
            compacted.append(tool_msg)

        # If still over budget, apply keep_recent
        if self.estimate_tokens(compacted) > target_tokens:
            compacted = self._compact_keep_recent(compacted, target_tokens)

        return compacted

    def _compact_drop_tool_outputs(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Drop tool output content but keep structure."""
        compacted = []

        for msg in messages:
            if msg.get("role") == "tool":
                # Replace content with placeholder
                compacted.append(
                    {
                        **msg,
                        "content": "[Tool output truncated for context management]",
                    }
                )
            else:
                compacted.append(msg)

        # If still over budget, apply keep_recent
        if self.estimate_tokens(compacted) > target_tokens:
            compacted = self._compact_keep_recent(compacted, target_tokens)

        return compacted

    def _save_backup(self, backup: ContextBackup) -> None:
        """Save backup to disk."""
        try:
            filename = f"context_backup_{backup.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = self.backup_dir / filename

            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup.to_dict(), f, indent=2)

            log.debug(f"Context backup saved: {backup_path}")

            # Clean old backups (keep last 10)
            self._cleanup_old_backups(keep_count=10)

        except Exception as e:
            log.warning(f"Failed to save context backup: {e}")

    def _cleanup_old_backups(self, keep_count: int = 10) -> None:
        """Remove old backup files, keeping only the most recent."""
        try:
            backup_files = sorted(
                self.backup_dir.glob("context_backup_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            for old_file in backup_files[keep_count:]:
                old_file.unlink()
                log.debug(f"Removed old context backup: {old_file.name}")

        except Exception as e:
            log.warning(f"Failed to cleanup old backups: {e}")

    def load_backup(self, backup_path: Path) -> ContextBackup | None:
        """Load a backup from disk."""
        try:
            with open(backup_path, encoding="utf-8") as f:
                data = json.load(f)
            return ContextBackup.from_dict(data)
        except Exception as e:
            log.warning(f"Failed to load backup {backup_path}: {e}")
            return None

    def list_backups(self) -> list[Path]:
        """List available backup files."""
        return sorted(
            self.backup_dir.glob("context_backup_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def add_tool_output(self, tool_name: str, output: str, tool_call_id: str) -> None:
        """Add a tool output to the collection."""
        self.tool_outputs.add_output(tool_name, output, tool_call_id)

    def get_tool_outputs_summary(self) -> dict[str, Any]:
        """Get summary of collected tool outputs."""
        return {
            "total_outputs": len(self.tool_outputs.all_outputs),
            "unique_tools": len(self.tool_outputs.final_outputs),
            "total_size_chars": self.tool_outputs.get_total_size(),
            "estimated_tokens": int(self.tool_outputs.get_total_size() / self.chars_per_token),
        }

    def clear_tool_outputs(self) -> None:
        """Clear collected tool outputs."""
        self.tool_outputs.clear()


def create_context_manager(
    model: str = "gpt-4.1",
    backup_dir: Path | None = None,
) -> ContextWindowManager:
    """Factory function to create a context window manager.

    Args:
        model: Model name for context limit lookup
        backup_dir: Directory for storing context backups

    Returns:
        Configured ContextWindowManager instance
    """
    return ContextWindowManager(model=model, backup_dir=backup_dir)


__all__ = [
    "ContextWindowManager",
    "CompactionStrategy",
    "TokenEstimate",
    "ContextBackup",
    "ToolOutputCollection",
    "create_context_manager",
]
