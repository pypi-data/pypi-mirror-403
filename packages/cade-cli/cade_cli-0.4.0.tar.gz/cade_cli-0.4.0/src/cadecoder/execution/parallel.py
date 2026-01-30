"""Async tool executor.

This module provides intelligent async execution of tools with parallelization.
"""

import asyncio
import json
from typing import TYPE_CHECKING, Any

from cadecoder.core.logging import log
from cadecoder.core.types import (
    ResourceSet,
    ToolCallList,
    ToolExecutionResult,
    ToolGroup,
    ToolGroups,
    extract_tool_output_content,
)
from cadecoder.tools.manager import ToolAuthorizationRequired

if TYPE_CHECKING:
    from cadecoder.tools.manager import ToolManager


class AsyncToolExecutor:
    """Executes tools asynchronously with intelligent parallelization."""

    def __init__(self, tool_manager: "ToolManager", max_concurrent: int = 10):
        """Initialize parallel executor."""
        self.tool_manager = tool_manager
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._interactive_lock = asyncio.Lock()

    async def execute_tools(
        self, tool_calls: ToolCallList, preserve_order: bool = True
    ) -> list[ToolExecutionResult]:
        """Execute tools with intelligent parallelization."""
        if not tool_calls:
            return []

        independent_groups = self._analyze_tool_dependencies(tool_calls)

        # Log detailed parallelization info
        if len(independent_groups) == 1 and len(tool_calls) > 1:
            log.info(f"Parallel execution: {len(tool_calls)} tools in 1 group (all parallel)")
        elif len(independent_groups) == len(tool_calls):
            log.info(f"Sequential execution: {len(tool_calls)} tools (dependencies detected)")
        else:
            group_sizes = [len(g) for g in independent_groups]
            log.info(
                f"Mixed execution: {len(tool_calls)} tools in "
                f"{len(independent_groups)} groups {group_sizes}"
            )

        all_results: list[ToolExecutionResult] = []

        for group_idx, group in enumerate(independent_groups):
            log.debug(f"Executing group {group_idx + 1} with {len(group)} tools")

            group_tasks: list[asyncio.Task[ToolExecutionResult]] = []
            for tool_call in group:
                task = asyncio.create_task(self._execute_single_tool_with_semaphore(tool_call))
                group_tasks.append(task)

            try:
                group_results: list[ToolExecutionResult | BaseException] = await asyncio.gather(
                    *group_tasks, return_exceptions=True
                )
            except asyncio.CancelledError:
                for task in group_tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*group_tasks, return_exceptions=True)
                raise

            for tool_call, result in zip(group, group_results):
                if isinstance(result, Exception):
                    auth_url = None
                    # Check for authorization exception
                    if isinstance(result, ToolAuthorizationRequired):
                        auth_url = result.authorization_url
                        log.error(f"Authorization required: {result}")
                    else:
                        log.error(f"Tool execution failed: {result}")

                    all_results.append(
                        ToolExecutionResult(
                            tool_call_id=tool_call.get("id", ""),
                            name=tool_call.get("function", {}).get("name", ""),
                            content=str(result),
                            status="error",
                            error=str(result),
                            authorization_url=auth_url,
                        )
                    )
                else:
                    if isinstance(result, ToolExecutionResult):
                        all_results.append(result)

        if preserve_order:
            ordered_results = self._restore_order(tool_calls, all_results)
            return ordered_results

        return all_results

    async def _execute_single_tool_with_semaphore(
        self, tool_call: dict[str, Any]
    ) -> ToolExecutionResult:
        """Execute a single tool with semaphore for rate limiting."""
        async with self._semaphore:
            if await self._is_interactive_call(tool_call):
                async with self._interactive_lock:
                    return await self._execute_single_tool(tool_call)
            return await self._execute_single_tool(tool_call)

    async def _is_interactive_call(self, tool_call: dict[str, Any]) -> bool:
        """Determine if the tool call requires exclusive terminal access."""
        function = tool_call.get("function", {})
        name = function.get("name", "")

        if hasattr(self.tool_manager, "is_interactive_tool"):
            try:
                return bool(self.tool_manager.is_interactive_tool(name))
            except Exception:
                return False
        return False

    async def _execute_single_tool(
        self,
        tool_call: dict[str, Any],
        timeout: float = 120.0,
    ) -> ToolExecutionResult:
        """Execute a single tool with timeout and cancellation support."""
        function = tool_call.get("function", {})
        name = function.get("name", "unknown")
        tool_call_id = tool_call.get("id", "unknown")

        try:
            args = json.loads(function.get("arguments", "{}"))
            log.debug(f"Executing tool: {name} with args: {args}")

            try:
                result_content = await asyncio.wait_for(
                    self.tool_manager.execute(name, args),
                    timeout=timeout,
                )
            except TimeoutError:
                log.warning(f"Tool {name} timed out after {timeout}s")
                return ToolExecutionResult(
                    tool_call_id=tool_call_id,
                    name=name,
                    content=f"Tool execution timed out after {timeout} seconds",
                    status="error",
                    error="timeout",
                    authorization_url=None,
                )
            except asyncio.CancelledError:
                log.info(f"Tool {name} was cancelled")
                return ToolExecutionResult(
                    tool_call_id=tool_call_id,
                    name=name,
                    content="Tool execution was cancelled",
                    status="cancelled",
                    error="cancelled",
                    authorization_url=None,
                )

            actual_content = extract_tool_output_content(result_content)

            return ToolExecutionResult(
                tool_call_id=tool_call_id,
                name=name,
                content=actual_content,
                status="success",
                error=None,
                authorization_url=None,
            )

        except Exception as e:
            auth_url = None
            if isinstance(e, ToolAuthorizationRequired):
                auth_url = e.authorization_url
                log.error(f"Authorization required for tool {name}")
            else:
                log.error(f"Tool execution failed for {name}: {e}")

            return ToolExecutionResult(
                tool_call_id=tool_call_id,
                name=name,
                content=str(e),
                status="error",
                error=str(e),
                authorization_url=auth_url,
            )

    def _analyze_tool_dependencies(self, tool_calls: ToolCallList) -> ToolGroups:
        """Analyze tool dependencies to determine execution groups.

        Tools are grouped for parallel execution unless they operate on
        the same resource (detected by examining argument values).
        """
        if len(tool_calls) <= 1:
            return [tool_calls] if tool_calls else []

        # Extract resources for each tool call
        tool_resources: list[ResourceSet] = []
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            args_str = function.get("arguments", "{}")
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}
            resources = self._extract_resources(args)
            tool_resources.append(resources)

        # Group tools - only serialize if same resource is accessed
        groups: ToolGroups = []
        current_group: ToolGroup = []
        current_group_resources: ResourceSet = set()

        for i, tool_call in enumerate(tool_calls):
            resources = tool_resources[i]

            # Check if this tool conflicts with current group
            if resources & current_group_resources:
                # Conflict - start new group
                if current_group:
                    groups.append(current_group)
                current_group = [tool_call]
                current_group_resources = resources.copy()
            else:
                # No conflict - add to current group
                current_group.append(tool_call)
                current_group_resources.update(resources)

        if current_group:
            groups.append(current_group)

        return groups if groups else [[tc] for tc in tool_calls]

    def _extract_resources(self, obj: Any) -> ResourceSet:
        """Extract resource identifiers from tool arguments.

        Looks for any string values that appear to be paths or identifiers.
        """
        resources: set[str] = set()

        if isinstance(obj, str):
            # Include strings that look like paths or identifiers
            if "/" in obj or "\\" in obj or "." in obj:
                resources.add(obj)
        elif isinstance(obj, dict):
            for value in obj.values():
                resources.update(self._extract_resources(value))
        elif isinstance(obj, list):
            for item in obj:
                resources.update(self._extract_resources(item))

        return resources

    def _restore_order(
        self, original_calls: list[dict[str, Any]], results: list[ToolExecutionResult]
    ) -> list[ToolExecutionResult]:
        """Restore original order of results."""
        result_map = {r.tool_call_id: r for r in results}
        ordered = []

        for call in original_calls:
            call_id = call.get("id", "unknown")
            if call_id in result_map:
                ordered.append(result_map[call_id])
            else:
                log.warning(f"No result found for tool call {call_id}")
                ordered.append(
                    ToolExecutionResult(
                        tool_call_id=call_id,
                        name=call.get("function", {}).get("name", ""),
                        content="No result",
                        status="error",
                        error="Result not found",
                        authorization_url=None,
                    )
                )

        return ordered
