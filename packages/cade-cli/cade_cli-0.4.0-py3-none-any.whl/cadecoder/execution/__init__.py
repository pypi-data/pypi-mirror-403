"""Execution package for task processing.

This package contains:
- Orchestrator: Central control flow for agent execution
- Context window management: Token tracking and compaction
- Parallel execution: Concurrent tool execution with dependency analysis
"""

from cadecoder.execution.context_window import (
    CompactionStrategy,
    ContextBackup,
    ContextWindowManager,
    TokenEstimate,
    ToolOutputCollection,
    create_context_manager,
)
from cadecoder.execution.orchestrator import (
    ContinuationDecision,
    ExecutionContext,
    ExecutionEvent,
    ExecutionMode,
    ExecutionResult,
    Orchestrator,
    create_orchestrator,
)
from cadecoder.execution.parallel import AsyncToolExecutor

__all__ = [
    # Context window
    "CompactionStrategy",
    "ContextBackup",
    "ContextWindowManager",
    "TokenEstimate",
    "ToolOutputCollection",
    "create_context_manager",
    # Orchestrator
    "ContinuationDecision",
    "ExecutionContext",
    "ExecutionEvent",
    "ExecutionMode",
    "ExecutionResult",
    "Orchestrator",
    "create_orchestrator",
    # Async execution
    "AsyncToolExecutor",
]
