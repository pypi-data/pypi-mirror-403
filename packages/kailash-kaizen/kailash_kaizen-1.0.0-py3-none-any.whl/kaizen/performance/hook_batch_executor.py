"""
Hook Batch Executor for parallel hook execution (TODO-199.3.3).

Provides optimized hook execution by running independent hooks
concurrently within the same priority level.

Features:
- Priority-based batching (hooks at same priority run in parallel)
- Semaphore-controlled concurrency
- Fail-fast option for critical hooks
- Metrics for execution performance
- Configurable timeout per hook

Usage:
    from kaizen.performance import HookBatchExecutor

    executor = HookBatchExecutor(config=HookBatchConfig(max_concurrent=10))

    # Execute hooks in batches by priority
    results = await executor.execute_batch(
        hooks_with_priority=[(HookPriority.HIGH, hook1), (HookPriority.NORMAL, hook2)],
        context=hook_context,
    )
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BatchExecutionMode(Enum):
    """Execution mode for hook batches."""

    SEQUENTIAL = "sequential"  # Execute one at a time (original behavior)
    PARALLEL_BY_PRIORITY = "parallel_by_priority"  # Parallel within priority, sequential across
    FULLY_PARALLEL = "fully_parallel"  # All hooks in parallel (ignores priority)


@dataclass
class HookBatchConfig:
    """Configuration for hook batch executor."""

    max_concurrent: int = 10  # Maximum concurrent hooks
    default_timeout: float = 0.5  # Default timeout per hook (seconds)
    execution_mode: BatchExecutionMode = BatchExecutionMode.PARALLEL_BY_PRIORITY
    fail_fast_on_critical: bool = True  # Stop if critical hook fails
    enable_metrics: bool = True


@dataclass
class HookExecutionResult:
    """Result of a single hook execution."""

    hook_name: str
    priority: int
    success: bool
    duration_ms: float
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class BatchExecutionResult:
    """Result of batch hook execution."""

    results: List[HookExecutionResult]
    total_duration_ms: float
    hooks_executed: int
    hooks_succeeded: int
    hooks_failed: int
    parallel_batches: int
    execution_mode: str

    @property
    def success(self) -> bool:
        """Check if all hooks succeeded."""
        return self.hooks_failed == 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.hooks_executed == 0:
            return 1.0
        return self.hooks_succeeded / self.hooks_executed

    def get_failed_hooks(self) -> List[HookExecutionResult]:
        """Get list of failed hooks."""
        return [r for r in self.results if not r.success]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_duration_ms": self.total_duration_ms,
            "hooks_executed": self.hooks_executed,
            "hooks_succeeded": self.hooks_succeeded,
            "hooks_failed": self.hooks_failed,
            "parallel_batches": self.parallel_batches,
            "execution_mode": self.execution_mode,
            "success_rate": self.success_rate,
        }


@dataclass
class HookBatchMetrics:
    """Metrics for hook batch execution."""

    total_executions: int = 0
    total_hooks_run: int = 0
    total_duration_ms: float = 0.0
    parallel_executions: int = 0
    sequential_executions: int = 0
    hooks_succeeded: int = 0
    hooks_failed: int = 0
    avg_batch_size: float = 0.0
    max_concurrent_achieved: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        total = self.hooks_succeeded + self.hooks_failed
        return self.hooks_succeeded / total if total > 0 else 1.0

    @property
    def parallel_ratio(self) -> float:
        """Calculate ratio of parallel vs sequential executions."""
        total = self.parallel_executions + self.sequential_executions
        return self.parallel_executions / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_executions": self.total_executions,
            "total_hooks_run": self.total_hooks_run,
            "total_duration_ms": self.total_duration_ms,
            "parallel_executions": self.parallel_executions,
            "sequential_executions": self.sequential_executions,
            "hooks_succeeded": self.hooks_succeeded,
            "hooks_failed": self.hooks_failed,
            "success_rate": self.success_rate,
            "parallel_ratio": self.parallel_ratio,
            "avg_batch_size": self.avg_batch_size,
            "max_concurrent_achieved": self.max_concurrent_achieved,
        }


# Type alias for hook handler (matches HookManager's handler type)
HookHandler = Any  # BaseHook or callable


class HookBatchExecutor:
    """
    Executor for parallel hook batch execution.

    Optimizes hook execution by running hooks at the same priority
    level concurrently, while respecting priority ordering across levels.
    """

    def __init__(self, config: Optional[HookBatchConfig] = None):
        """
        Initialize hook batch executor.

        Args:
            config: Execution configuration
        """
        self.config = config or HookBatchConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._metrics = HookBatchMetrics()
        self._batch_sizes: List[int] = []

    async def execute_batch(
        self,
        hooks_with_priority: List[Tuple[int, HookHandler]],
        context: Any,
        timeout: Optional[float] = None,
    ) -> BatchExecutionResult:
        """
        Execute hooks in batches by priority.

        Args:
            hooks_with_priority: List of (priority, handler) tuples
            context: HookContext to pass to handlers
            timeout: Optional timeout override per hook

        Returns:
            BatchExecutionResult with all results and metrics
        """
        if not hooks_with_priority:
            return BatchExecutionResult(
                results=[],
                total_duration_ms=0.0,
                hooks_executed=0,
                hooks_succeeded=0,
                hooks_failed=0,
                parallel_batches=0,
                execution_mode=self.config.execution_mode.value,
            )

        effective_timeout = timeout or self.config.default_timeout
        start_time = time.perf_counter()

        if self.config.execution_mode == BatchExecutionMode.SEQUENTIAL:
            results, batches = await self._execute_sequential(
                hooks_with_priority, context, effective_timeout
            )
        elif self.config.execution_mode == BatchExecutionMode.FULLY_PARALLEL:
            results, batches = await self._execute_fully_parallel(
                hooks_with_priority, context, effective_timeout
            )
        else:  # PARALLEL_BY_PRIORITY
            results, batches = await self._execute_parallel_by_priority(
                hooks_with_priority, context, effective_timeout
            )

        total_duration_ms = (time.perf_counter() - start_time) * 1000

        # Calculate success/failure counts
        succeeded = sum(1 for r in results if r.success)
        failed = len(results) - succeeded

        # Update metrics
        if self.config.enable_metrics:
            self._update_metrics(results, batches, total_duration_ms)

        return BatchExecutionResult(
            results=results,
            total_duration_ms=total_duration_ms,
            hooks_executed=len(results),
            hooks_succeeded=succeeded,
            hooks_failed=failed,
            parallel_batches=batches,
            execution_mode=self.config.execution_mode.value,
        )

    async def _execute_sequential(
        self,
        hooks_with_priority: List[Tuple[int, HookHandler]],
        context: Any,
        timeout: float,
    ) -> Tuple[List[HookExecutionResult], int]:
        """Execute hooks sequentially (original behavior)."""
        results = []

        for priority, handler in hooks_with_priority:
            result = await self._execute_single_hook(handler, context, timeout, priority)
            results.append(result)

            # Fail fast on critical hooks
            if (
                self.config.fail_fast_on_critical
                and priority == 0  # CRITICAL priority
                and not result.success
            ):
                break

        if self.config.enable_metrics:
            self._metrics.sequential_executions += 1

        return results, len(hooks_with_priority)

    async def _execute_fully_parallel(
        self,
        hooks_with_priority: List[Tuple[int, HookHandler]],
        context: Any,
        timeout: float,
    ) -> Tuple[List[HookExecutionResult], int]:
        """Execute all hooks in parallel."""
        tasks = []

        for priority, handler in hooks_with_priority:
            task = self._execute_single_hook_with_semaphore(
                handler, context, timeout, priority
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        if self.config.enable_metrics:
            self._metrics.parallel_executions += 1
            self._metrics.max_concurrent_achieved = max(
                self._metrics.max_concurrent_achieved,
                min(len(tasks), self.config.max_concurrent),
            )

        return list(results), 1

    async def _execute_parallel_by_priority(
        self,
        hooks_with_priority: List[Tuple[int, HookHandler]],
        context: Any,
        timeout: float,
    ) -> Tuple[List[HookExecutionResult], int]:
        """Execute hooks in parallel batches by priority level."""
        # Group hooks by priority
        priority_groups: Dict[int, List[HookHandler]] = defaultdict(list)
        for priority, handler in hooks_with_priority:
            priority_groups[priority].append(handler)

        # Sort priorities (lower = earlier)
        sorted_priorities = sorted(priority_groups.keys())

        all_results = []
        batch_count = 0

        for priority in sorted_priorities:
            handlers = priority_groups[priority]
            batch_count += 1

            if len(handlers) == 1:
                # Single hook, no need for parallelism
                result = await self._execute_single_hook(
                    handlers[0], context, timeout, priority
                )
                all_results.append(result)
            else:
                # Execute batch in parallel
                tasks = [
                    self._execute_single_hook_with_semaphore(
                        handler, context, timeout, priority
                    )
                    for handler in handlers
                ]
                results = await asyncio.gather(*tasks)
                all_results.extend(results)

                if self.config.enable_metrics:
                    self._metrics.max_concurrent_achieved = max(
                        self._metrics.max_concurrent_achieved,
                        min(len(tasks), self.config.max_concurrent),
                    )

            # Check for critical failures
            if self.config.fail_fast_on_critical and priority == 0:
                failed = [r for r in all_results if not r.success and r.priority == 0]
                if failed:
                    break

        if self.config.enable_metrics:
            self._metrics.parallel_executions += 1
            self._batch_sizes.append(
                len(hooks_with_priority) / batch_count if batch_count > 0 else 0
            )

        return all_results, batch_count

    async def _execute_single_hook_with_semaphore(
        self,
        handler: HookHandler,
        context: Any,
        timeout: float,
        priority: int,
    ) -> HookExecutionResult:
        """Execute single hook with semaphore control."""
        async with self._semaphore:
            return await self._execute_single_hook(handler, context, timeout, priority)

    async def _execute_single_hook(
        self,
        handler: HookHandler,
        context: Any,
        timeout: float,
        priority: int,
    ) -> HookExecutionResult:
        """Execute a single hook with timeout."""
        handler_name = getattr(handler, "name", handler.__class__.__name__)
        start_time = time.perf_counter()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                handler.handle(context),
                timeout=timeout,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000

            return HookExecutionResult(
                hook_name=handler_name,
                priority=priority,
                success=result.success,
                duration_ms=duration_ms,
                error=result.error,
                data=result.data,
            )

        except asyncio.TimeoutError:
            duration_ms = timeout * 1000
            return HookExecutionResult(
                hook_name=handler_name,
                priority=priority,
                success=False,
                duration_ms=duration_ms,
                error=f"Hook timeout after {timeout}s",
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(f"Hook failed: {handler_name}")

            return HookExecutionResult(
                hook_name=handler_name,
                priority=priority,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _update_metrics(
        self,
        results: List[HookExecutionResult],
        batches: int,
        total_duration_ms: float,
    ) -> None:
        """Update execution metrics."""
        self._metrics.total_executions += 1
        self._metrics.total_hooks_run += len(results)
        self._metrics.total_duration_ms += total_duration_ms

        for result in results:
            if result.success:
                self._metrics.hooks_succeeded += 1
            else:
                self._metrics.hooks_failed += 1

        # Update average batch size
        if self._batch_sizes:
            self._metrics.avg_batch_size = sum(self._batch_sizes) / len(self._batch_sizes)

    def get_metrics(self) -> HookBatchMetrics:
        """Get execution metrics."""
        return HookBatchMetrics(
            total_executions=self._metrics.total_executions,
            total_hooks_run=self._metrics.total_hooks_run,
            total_duration_ms=self._metrics.total_duration_ms,
            parallel_executions=self._metrics.parallel_executions,
            sequential_executions=self._metrics.sequential_executions,
            hooks_succeeded=self._metrics.hooks_succeeded,
            hooks_failed=self._metrics.hooks_failed,
            avg_batch_size=self._metrics.avg_batch_size,
            max_concurrent_achieved=self._metrics.max_concurrent_achieved,
        )

    def reset_metrics(self) -> None:
        """Reset execution metrics."""
        self._metrics = HookBatchMetrics()
        self._batch_sizes = []


# Convenience function to create executor with common configurations
def create_hook_executor(
    mode: str = "parallel_by_priority",
    max_concurrent: int = 10,
    timeout: float = 0.5,
) -> HookBatchExecutor:
    """
    Create a hook batch executor with specified configuration.

    Args:
        mode: Execution mode ("sequential", "parallel_by_priority", "fully_parallel")
        max_concurrent: Maximum concurrent hooks
        timeout: Default timeout per hook

    Returns:
        Configured HookBatchExecutor
    """
    mode_map = {
        "sequential": BatchExecutionMode.SEQUENTIAL,
        "parallel_by_priority": BatchExecutionMode.PARALLEL_BY_PRIORITY,
        "fully_parallel": BatchExecutionMode.FULLY_PARALLEL,
    }

    config = HookBatchConfig(
        max_concurrent=max_concurrent,
        default_timeout=timeout,
        execution_mode=mode_map.get(mode, BatchExecutionMode.PARALLEL_BY_PRIORITY),
    )

    return HookBatchExecutor(config)
