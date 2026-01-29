"""
Parallel Tool Executor for Kaizen agents (TODO-199.2.1).

Enables concurrent execution of independent tools to improve TAOD loop performance.

Features:
- Dependency analysis for safe parallelization
- Configurable concurrency limits
- Error handling and result aggregation
- Performance metrics collection

Usage:
    from kaizen.performance import ParallelToolExecutor

    executor = ParallelToolExecutor(
        tool_registry=registry,
        max_concurrent=5,
    )

    results = await executor.execute_parallel(tool_calls)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ParallelExecutionConfig:
    """Configuration for parallel tool execution."""

    enabled: bool = True
    max_concurrent: int = 5
    timeout_per_tool: float = 30.0
    fail_fast: bool = False
    collect_metrics: bool = True


@dataclass
class ToolExecutionResult:
    """Result of a single tool execution."""

    tool_name: str
    tool_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ParallelExecutionResult:
    """Aggregated result of parallel tool execution."""

    results: List[ToolExecutionResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    parallel_speedup: float = 1.0
    tools_executed: int = 0
    tools_succeeded: int = 0
    tools_failed: int = 0

    @property
    def all_succeeded(self) -> bool:
        """Check if all tools succeeded."""
        return self.tools_failed == 0

    def get_result(self, tool_id: str) -> Optional[ToolExecutionResult]:
        """Get result by tool ID."""
        for result in self.results:
            if result.tool_id == tool_id:
                return result
        return None


class ToolDependencyAnalyzer:
    """
    Analyzes tool calls to determine execution dependencies.

    Tools are considered independent if they:
    1. Don't reference outputs from other pending tools
    2. Don't modify the same resources
    3. Are explicitly marked as parallelizable
    """

    # Tools that should never run in parallel (modifies shared state)
    SEQUENTIAL_ONLY_TOOLS: Set[str] = {
        "save_file",
        "write_file",
        "delete_file",
        "git_commit",
        "database_write",
        "state_update",
    }

    # Tools that are always safe to parallelize
    PARALLELIZABLE_TOOLS: Set[str] = {
        "read_file",
        "search",
        "web_search",
        "get_weather",
        "calculate",
        "fetch_url",
        "list_files",
        "get_time",
    }

    def __init__(
        self,
        sequential_tools: Optional[Set[str]] = None,
        parallelizable_tools: Optional[Set[str]] = None,
    ):
        """
        Initialize analyzer.

        Args:
            sequential_tools: Additional tools that must run sequentially
            parallelizable_tools: Additional tools safe to parallelize
        """
        self.sequential_tools = self.SEQUENTIAL_ONLY_TOOLS.copy()
        self.parallelizable_tools = self.PARALLELIZABLE_TOOLS.copy()

        if sequential_tools:
            self.sequential_tools.update(sequential_tools)
        if parallelizable_tools:
            self.parallelizable_tools.update(parallelizable_tools)

    def analyze(
        self, tool_calls: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze tool calls and split into parallel vs sequential groups.

        Args:
            tool_calls: List of tool call dictionaries with 'name', 'arguments', 'id'

        Returns:
            Tuple of (parallel_tools, sequential_tools)
        """
        parallel = []
        sequential = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")

            if self._must_run_sequentially(tool_call, tool_calls):
                sequential.append(tool_call)
            else:
                parallel.append(tool_call)

        logger.debug(
            f"Dependency analysis: {len(parallel)} parallel, {len(sequential)} sequential"
        )
        return parallel, sequential

    def _must_run_sequentially(
        self, tool_call: Dict[str, Any], all_tools: List[Dict[str, Any]]
    ) -> bool:
        """Determine if a tool must run sequentially."""
        tool_name = tool_call.get("name", "")

        # Check explicit sequential-only tools
        if tool_name in self.sequential_tools:
            return True

        # Check if tool references another tool's output
        args = tool_call.get("arguments", {})
        if isinstance(args, dict):
            args_str = str(args)
            for other_tool in all_tools:
                if other_tool is tool_call:
                    continue
                other_id = other_tool.get("id", "")
                if other_id and other_id in args_str:
                    # References another tool's output
                    return True

        # Default to parallel if tool is known safe
        if tool_name in self.parallelizable_tools:
            return False

        # Unknown tools default to parallel (conservative assumption)
        return False


class ParallelToolExecutor:
    """
    Executes tool calls in parallel with dependency analysis.

    This executor optimizes TAOD loop performance by running independent
    tools concurrently while respecting dependencies.
    """

    def __init__(
        self,
        tool_registry: Any,
        config: Optional[ParallelExecutionConfig] = None,
        dependency_analyzer: Optional[ToolDependencyAnalyzer] = None,
    ):
        """
        Initialize parallel executor.

        Args:
            tool_registry: Registry for executing tools
            config: Execution configuration
            dependency_analyzer: Custom dependency analyzer
        """
        self.tool_registry = tool_registry
        self.config = config or ParallelExecutionConfig()
        self.analyzer = dependency_analyzer or ToolDependencyAnalyzer()

        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._metrics: Dict[str, List[float]] = {}

    async def execute_parallel(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> ParallelExecutionResult:
        """
        Execute tool calls with parallelization where safe.

        Args:
            tool_calls: List of tool calls to execute
            context: Optional execution context

        Returns:
            ParallelExecutionResult with all tool results
        """
        if not self.config.enabled or len(tool_calls) <= 1:
            # Fall back to sequential for single tool or if disabled
            return await self._execute_sequential(tool_calls, context)

        start_time = time.perf_counter()

        # Analyze dependencies
        parallel_tools, sequential_tools = self.analyzer.analyze(tool_calls)

        result = ParallelExecutionResult()

        # Execute parallel tools first (concurrently)
        if parallel_tools:
            parallel_results = await self._execute_batch(parallel_tools, context)
            result.results.extend(parallel_results)

        # Execute sequential tools (one by one)
        if sequential_tools:
            sequential_results = await self._execute_sequential_batch(
                sequential_tools, context
            )
            result.results.extend(sequential_results)

        # Calculate metrics
        end_time = time.perf_counter()
        result.total_duration_ms = (end_time - start_time) * 1000
        result.tools_executed = len(tool_calls)
        result.tools_succeeded = sum(1 for r in result.results if r.success)
        result.tools_failed = result.tools_executed - result.tools_succeeded

        # Calculate speedup vs sequential
        sequential_time = sum(r.duration_ms for r in result.results)
        if sequential_time > 0:
            result.parallel_speedup = sequential_time / result.total_duration_ms

        logger.debug(
            f"Parallel execution: {result.tools_executed} tools in "
            f"{result.total_duration_ms:.2f}ms (speedup: {result.parallel_speedup:.2f}x)"
        )

        return result

    async def _execute_batch(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> List[ToolExecutionResult]:
        """Execute a batch of tools concurrently."""
        tasks = []

        async with asyncio.TaskGroup() as tg:
            for tool_call in tool_calls:
                task = tg.create_task(
                    self._execute_single_with_semaphore(tool_call, context)
                )
                tasks.append(task)

        return [task.result() for task in tasks]

    async def _execute_sequential_batch(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> List[ToolExecutionResult]:
        """Execute tools one at a time (sequential)."""
        results = []
        for tool_call in tool_calls:
            result = await self._execute_single(tool_call, context)
            results.append(result)

            # Fail fast if configured and tool failed
            if self.config.fail_fast and not result.success:
                break

        return results

    async def _execute_sequential(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> ParallelExecutionResult:
        """Execute all tools sequentially (fallback mode)."""
        start_time = time.perf_counter()
        results = await self._execute_sequential_batch(tool_calls, context)

        result = ParallelExecutionResult(
            results=results,
            total_duration_ms=(time.perf_counter() - start_time) * 1000,
            parallel_speedup=1.0,
            tools_executed=len(tool_calls),
            tools_succeeded=sum(1 for r in results if r.success),
        )
        result.tools_failed = result.tools_executed - result.tools_succeeded
        return result

    async def _execute_single_with_semaphore(
        self,
        tool_call: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> ToolExecutionResult:
        """Execute a single tool with semaphore for concurrency control."""
        async with self._semaphore:
            return await self._execute_single(tool_call, context)

    async def _execute_single(
        self,
        tool_call: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> ToolExecutionResult:
        """Execute a single tool call."""
        tool_name = tool_call.get("name", "unknown")
        tool_id = tool_call.get("id", "")
        tool_args = tool_call.get("arguments", {})

        start_time = time.perf_counter()

        try:
            # Handle string arguments (JSON string)
            if isinstance(tool_args, str):
                import json

                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}

            # Execute through registry
            if asyncio.iscoroutinefunction(self.tool_registry.execute):
                result = await self.tool_registry.execute(tool_name, tool_args)
            else:
                result = self.tool_registry.execute(tool_name, tool_args)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record metrics
            if self.config.collect_metrics:
                self._record_metric(tool_name, duration_ms)

            return ToolExecutionResult(
                tool_name=tool_name,
                tool_id=tool_id,
                success=True,
                result=result if isinstance(result, dict) else {"output": str(result)},
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                tool_name=tool_name,
                tool_id=tool_id,
                success=False,
                error=f"Tool execution timed out after {self.config.timeout_per_tool}s",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Tool {tool_name} failed: {e}")
            return ToolExecutionResult(
                tool_name=tool_name,
                tool_id=tool_id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

    def _record_metric(self, tool_name: str, duration_ms: float) -> None:
        """Record execution time metric for a tool."""
        if tool_name not in self._metrics:
            self._metrics[tool_name] = []
        self._metrics[tool_name].append(duration_ms)

        # Keep only last 100 samples
        if len(self._metrics[tool_name]) > 100:
            self._metrics[tool_name] = self._metrics[tool_name][-100:]

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get execution metrics for all tools."""
        result = {}
        for tool_name, durations in self._metrics.items():
            if durations:
                sorted_durations = sorted(durations)
                result[tool_name] = {
                    "count": len(durations),
                    "mean_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "p50_ms": sorted_durations[len(sorted_durations) // 2],
                    "p95_ms": sorted_durations[int(len(sorted_durations) * 0.95)]
                    if len(sorted_durations) >= 20
                    else sorted_durations[-1],
                }
        return result

    def reset_metrics(self) -> None:
        """Reset collected metrics."""
        self._metrics.clear()
