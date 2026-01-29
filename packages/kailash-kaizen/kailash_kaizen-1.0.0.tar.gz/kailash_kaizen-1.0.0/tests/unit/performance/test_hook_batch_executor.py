"""
Unit tests for Hook Batch Executor (TODO-199.3.3).

Tests the parallel hook execution system with priority batching.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from kaizen.performance.hook_batch_executor import (
    BatchExecutionMode,
    BatchExecutionResult,
    HookBatchConfig,
    HookBatchExecutor,
    HookBatchMetrics,
    HookExecutionResult,
    create_hook_executor,
)


# ═══════════════════════════════════════════════════════════════
# Mock Classes
# ═══════════════════════════════════════════════════════════════


@dataclass
class MockHookResult:
    """Mock HookResult matching the expected interface."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class MockHookContext:
    """Mock HookContext for testing."""

    agent_id: str = "test-agent"
    event_type: str = "test_event"
    data: Dict[str, Any] = field(default_factory=dict)


class MockHook:
    """Mock hook for testing."""

    def __init__(
        self,
        name: str = "mock_hook",
        delay_ms: float = 0,
        should_fail: bool = False,
        error_message: str = "Mock error",
    ):
        self.name = name
        self.delay_ms = delay_ms
        self.should_fail = should_fail
        self.error_message = error_message
        self.call_count = 0
        self.call_times: List[float] = []

    async def handle(self, context: Any) -> MockHookResult:
        """Handle the hook call."""
        self.call_count += 1
        self.call_times.append(time.perf_counter())

        if self.delay_ms > 0:
            await asyncio.sleep(self.delay_ms / 1000)

        if self.should_fail:
            return MockHookResult(success=False, error=self.error_message)

        return MockHookResult(success=True, data={"hook": self.name})


class SlowHook(MockHook):
    """Hook that takes time to execute."""

    def __init__(self, name: str, delay_ms: float):
        super().__init__(name=name, delay_ms=delay_ms)


class FailingHook(MockHook):
    """Hook that always fails."""

    def __init__(self, name: str, error_message: str = "Hook failed"):
        super().__init__(name=name, should_fail=True, error_message=error_message)


class ExceptionHook:
    """Hook that raises an exception."""

    def __init__(self, name: str = "exception_hook"):
        self.name = name
        self.call_count = 0

    async def handle(self, context: Any) -> MockHookResult:
        """Raise an exception."""
        self.call_count += 1
        raise RuntimeError("Unexpected exception")


class TimeoutHook:
    """Hook that takes too long and times out."""

    def __init__(self, name: str = "timeout_hook", delay_seconds: float = 10):
        self.name = name
        self.delay_seconds = delay_seconds
        self.call_count = 0

    async def handle(self, context: Any) -> MockHookResult:
        """Sleep for too long."""
        self.call_count += 1
        await asyncio.sleep(self.delay_seconds)
        return MockHookResult(success=True)


# ═══════════════════════════════════════════════════════════════
# HookBatchConfig Tests
# ═══════════════════════════════════════════════════════════════


class TestHookBatchConfig:
    """Tests for HookBatchConfig dataclass."""

    def test_default_config(self):
        """Default config should have sensible defaults."""
        config = HookBatchConfig()
        assert config.max_concurrent == 10
        assert config.default_timeout == 0.5
        assert config.execution_mode == BatchExecutionMode.PARALLEL_BY_PRIORITY
        assert config.fail_fast_on_critical is True
        assert config.enable_metrics is True

    def test_custom_config(self):
        """Custom config values should be respected."""
        config = HookBatchConfig(
            max_concurrent=5,
            default_timeout=1.0,
            execution_mode=BatchExecutionMode.SEQUENTIAL,
            fail_fast_on_critical=False,
        )
        assert config.max_concurrent == 5
        assert config.default_timeout == 1.0
        assert config.execution_mode == BatchExecutionMode.SEQUENTIAL
        assert config.fail_fast_on_critical is False


# ═══════════════════════════════════════════════════════════════
# HookExecutionResult Tests
# ═══════════════════════════════════════════════════════════════


class TestHookExecutionResult:
    """Tests for HookExecutionResult dataclass."""

    def test_successful_result(self):
        """Successful result should have correct fields."""
        result = HookExecutionResult(
            hook_name="test_hook",
            priority=1,
            success=True,
            duration_ms=5.0,
            data={"key": "value"},
        )
        assert result.success is True
        assert result.hook_name == "test_hook"
        assert result.duration_ms == 5.0
        assert result.error is None

    def test_failed_result(self):
        """Failed result should include error."""
        result = HookExecutionResult(
            hook_name="test_hook",
            priority=0,
            success=False,
            duration_ms=10.0,
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"


# ═══════════════════════════════════════════════════════════════
# BatchExecutionResult Tests
# ═══════════════════════════════════════════════════════════════


class TestBatchExecutionResult:
    """Tests for BatchExecutionResult dataclass."""

    def test_all_successful(self):
        """All successful results should have 100% success rate."""
        result = BatchExecutionResult(
            results=[
                HookExecutionResult("h1", 0, True, 5.0),
                HookExecutionResult("h2", 1, True, 10.0),
            ],
            total_duration_ms=15.0,
            hooks_executed=2,
            hooks_succeeded=2,
            hooks_failed=0,
            parallel_batches=2,
            execution_mode="parallel_by_priority",
        )
        assert result.success is True
        assert result.success_rate == 1.0
        assert len(result.get_failed_hooks()) == 0

    def test_some_failed(self):
        """Some failures should be reflected in success rate."""
        result = BatchExecutionResult(
            results=[
                HookExecutionResult("h1", 0, True, 5.0),
                HookExecutionResult("h2", 1, False, 10.0, error="Failed"),
            ],
            total_duration_ms=15.0,
            hooks_executed=2,
            hooks_succeeded=1,
            hooks_failed=1,
            parallel_batches=2,
            execution_mode="parallel_by_priority",
        )
        assert result.success is False
        assert result.success_rate == 0.5
        assert len(result.get_failed_hooks()) == 1

    def test_to_dict(self):
        """to_dict should include all key fields."""
        result = BatchExecutionResult(
            results=[],
            total_duration_ms=100.0,
            hooks_executed=5,
            hooks_succeeded=4,
            hooks_failed=1,
            parallel_batches=3,
            execution_mode="parallel_by_priority",
        )
        d = result.to_dict()
        assert d["total_duration_ms"] == 100.0
        assert d["hooks_executed"] == 5
        assert d["success_rate"] == 0.8


# ═══════════════════════════════════════════════════════════════
# HookBatchExecutor Basic Tests
# ═══════════════════════════════════════════════════════════════


class TestHookBatchExecutorBasic:
    """Basic tests for HookBatchExecutor."""

    @pytest.mark.asyncio
    async def test_empty_hooks_list(self):
        """Empty hooks list should return empty result."""
        executor = HookBatchExecutor()
        context = MockHookContext()

        result = await executor.execute_batch([], context)

        assert result.hooks_executed == 0
        assert result.success is True

    @pytest.mark.asyncio
    async def test_single_hook_execution(self):
        """Single hook should execute correctly."""
        executor = HookBatchExecutor()
        context = MockHookContext()
        hook = MockHook(name="single_hook")

        result = await executor.execute_batch([(1, hook)], context)

        assert result.hooks_executed == 1
        assert result.hooks_succeeded == 1
        assert hook.call_count == 1

    @pytest.mark.asyncio
    async def test_multiple_hooks_same_priority(self):
        """Multiple hooks at same priority should all execute."""
        executor = HookBatchExecutor()
        context = MockHookContext()
        hooks = [
            (1, MockHook(name="hook1")),
            (1, MockHook(name="hook2")),
            (1, MockHook(name="hook3")),
        ]

        result = await executor.execute_batch(hooks, context)

        assert result.hooks_executed == 3
        assert result.hooks_succeeded == 3

    @pytest.mark.asyncio
    async def test_hooks_different_priorities(self):
        """Hooks at different priorities should all execute."""
        executor = HookBatchExecutor()
        context = MockHookContext()
        hooks = [
            (0, MockHook(name="critical")),
            (1, MockHook(name="high")),
            (2, MockHook(name="normal")),
        ]

        result = await executor.execute_batch(hooks, context)

        assert result.hooks_executed == 3
        assert result.parallel_batches == 3  # One batch per priority


# ═══════════════════════════════════════════════════════════════
# Execution Mode Tests
# ═══════════════════════════════════════════════════════════════


class TestExecutionModes:
    """Tests for different execution modes."""

    @pytest.mark.asyncio
    async def test_sequential_mode(self):
        """Sequential mode should execute hooks one at a time."""
        config = HookBatchConfig(execution_mode=BatchExecutionMode.SEQUENTIAL)
        executor = HookBatchExecutor(config)
        context = MockHookContext()

        # Create hooks that track call order
        hooks = [
            (1, SlowHook(name=f"hook{i}", delay_ms=10))
            for i in range(3)
        ]

        result = await executor.execute_batch(hooks, context)

        assert result.hooks_executed == 3
        # In sequential mode, hooks should be called in order
        # Total time should be at least sum of delays
        assert result.total_duration_ms >= 30

    @pytest.mark.asyncio
    async def test_parallel_by_priority_mode(self):
        """Parallel by priority should execute same-priority hooks concurrently."""
        config = HookBatchConfig(execution_mode=BatchExecutionMode.PARALLEL_BY_PRIORITY)
        executor = HookBatchExecutor(config)
        context = MockHookContext()

        # Three hooks at same priority, each taking 50ms
        hooks = [
            (1, SlowHook(name=f"hook{i}", delay_ms=50))
            for i in range(3)
        ]

        start = time.perf_counter()
        result = await executor.execute_batch(hooks, context)
        duration = (time.perf_counter() - start) * 1000

        assert result.hooks_executed == 3
        # Parallel execution should be faster than sequential (3 * 50 = 150ms)
        assert duration < 150  # Should be ~50ms + overhead

    @pytest.mark.asyncio
    async def test_fully_parallel_mode(self):
        """Fully parallel should execute all hooks concurrently."""
        config = HookBatchConfig(execution_mode=BatchExecutionMode.FULLY_PARALLEL)
        executor = HookBatchExecutor(config)
        context = MockHookContext()

        # Hooks at different priorities, each taking 50ms
        hooks = [
            (0, SlowHook(name="critical", delay_ms=50)),
            (1, SlowHook(name="high", delay_ms=50)),
            (2, SlowHook(name="normal", delay_ms=50)),
        ]

        start = time.perf_counter()
        result = await executor.execute_batch(hooks, context)
        duration = (time.perf_counter() - start) * 1000

        assert result.hooks_executed == 3
        # All in parallel should be ~50ms, not 150ms
        assert duration < 100
        assert result.parallel_batches == 1  # All in one batch


# ═══════════════════════════════════════════════════════════════
# Error Handling Tests
# ═══════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_failing_hook_captured(self):
        """Failing hooks should be captured in results."""
        executor = HookBatchExecutor()
        context = MockHookContext()
        hooks = [
            (1, MockHook(name="good")),
            (1, FailingHook(name="bad", error_message="Failed!")),
        ]

        result = await executor.execute_batch(hooks, context)

        assert result.hooks_executed == 2
        assert result.hooks_succeeded == 1
        assert result.hooks_failed == 1
        failed = result.get_failed_hooks()
        assert len(failed) == 1
        assert failed[0].error == "Failed!"

    @pytest.mark.asyncio
    async def test_exception_hook_captured(self):
        """Hooks that raise exceptions should be captured."""
        executor = HookBatchExecutor()
        context = MockHookContext()
        hooks = [
            (1, MockHook(name="good")),
            (1, ExceptionHook(name="exception")),
        ]

        result = await executor.execute_batch(hooks, context)

        assert result.hooks_failed == 1
        failed = result.get_failed_hooks()
        assert "Unexpected exception" in failed[0].error

    @pytest.mark.asyncio
    async def test_timeout_hook(self):
        """Hooks that timeout should be captured."""
        config = HookBatchConfig(default_timeout=0.1)  # 100ms timeout
        executor = HookBatchExecutor(config)
        context = MockHookContext()
        hooks = [
            (1, TimeoutHook(name="slow", delay_seconds=1)),  # Will timeout
        ]

        result = await executor.execute_batch(hooks, context)

        assert result.hooks_failed == 1
        failed = result.get_failed_hooks()
        assert "timeout" in failed[0].error.lower()

    @pytest.mark.asyncio
    async def test_fail_fast_critical(self):
        """Fail fast should stop on critical hook failure."""
        config = HookBatchConfig(
            fail_fast_on_critical=True,
            execution_mode=BatchExecutionMode.SEQUENTIAL,
        )
        executor = HookBatchExecutor(config)
        context = MockHookContext()

        hook_after_failure = MockHook(name="after")
        hooks = [
            (0, FailingHook(name="critical_fail")),  # Priority 0 = critical
            (1, hook_after_failure),
        ]

        result = await executor.execute_batch(hooks, context)

        # Should stop after critical failure
        assert result.hooks_executed == 1
        assert hook_after_failure.call_count == 0

    @pytest.mark.asyncio
    async def test_no_fail_fast(self):
        """Without fail fast, all hooks should execute."""
        config = HookBatchConfig(
            fail_fast_on_critical=False,
            execution_mode=BatchExecutionMode.SEQUENTIAL,
        )
        executor = HookBatchExecutor(config)
        context = MockHookContext()

        hook_after_failure = MockHook(name="after")
        hooks = [
            (0, FailingHook(name="critical_fail")),
            (1, hook_after_failure),
        ]

        result = await executor.execute_batch(hooks, context)

        # Should continue after failure
        assert result.hooks_executed == 2
        assert hook_after_failure.call_count == 1


# ═══════════════════════════════════════════════════════════════
# Concurrency Control Tests
# ═══════════════════════════════════════════════════════════════


class TestConcurrencyControl:
    """Tests for concurrency control."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """Semaphore should limit concurrent execution."""
        config = HookBatchConfig(
            max_concurrent=2,
            execution_mode=BatchExecutionMode.FULLY_PARALLEL,
        )
        executor = HookBatchExecutor(config)
        context = MockHookContext()

        # Track concurrent executions
        concurrent_count = [0]
        max_concurrent = [0]

        class TrackingHook:
            def __init__(self, name):
                self.name = name

            async def handle(self, ctx):
                concurrent_count[0] += 1
                max_concurrent[0] = max(max_concurrent[0], concurrent_count[0])
                await asyncio.sleep(0.05)  # 50ms
                concurrent_count[0] -= 1
                return MockHookResult(success=True)

        hooks = [(1, TrackingHook(f"hook{i}")) for i in range(5)]

        await executor.execute_batch(hooks, context)

        # Max concurrent should be limited to 2
        assert max_concurrent[0] <= 2


# ═══════════════════════════════════════════════════════════════
# Metrics Tests
# ═══════════════════════════════════════════════════════════════


class TestMetrics:
    """Tests for metrics tracking."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        """Metrics should track execution stats."""
        config = HookBatchConfig(enable_metrics=True)
        executor = HookBatchExecutor(config)
        context = MockHookContext()

        hooks = [
            (1, MockHook(name="good1")),
            (1, MockHook(name="good2")),
            (1, FailingHook(name="bad")),
        ]

        await executor.execute_batch(hooks, context)
        metrics = executor.get_metrics()

        assert metrics.total_executions == 1
        assert metrics.total_hooks_run == 3
        assert metrics.hooks_succeeded == 2
        assert metrics.hooks_failed == 1

    @pytest.mark.asyncio
    async def test_metrics_accumulate(self):
        """Metrics should accumulate across executions."""
        executor = HookBatchExecutor()
        context = MockHookContext()

        hooks = [(1, MockHook(name="hook"))]

        # Execute multiple times
        for _ in range(5):
            await executor.execute_batch(hooks, context)

        metrics = executor.get_metrics()
        assert metrics.total_executions == 5
        assert metrics.total_hooks_run == 5

    @pytest.mark.asyncio
    async def test_reset_metrics(self):
        """Reset should clear all metrics."""
        executor = HookBatchExecutor()
        context = MockHookContext()

        hooks = [(1, MockHook(name="hook"))]
        await executor.execute_batch(hooks, context)

        executor.reset_metrics()
        metrics = executor.get_metrics()

        assert metrics.total_executions == 0
        assert metrics.total_hooks_run == 0

    def test_metrics_to_dict(self):
        """Metrics to_dict should include all fields."""
        metrics = HookBatchMetrics(
            total_executions=10,
            total_hooks_run=50,
            hooks_succeeded=45,
            hooks_failed=5,
        )
        d = metrics.to_dict()

        assert d["total_executions"] == 10
        assert d["success_rate"] == 0.9


# ═══════════════════════════════════════════════════════════════
# Factory Function Tests
# ═══════════════════════════════════════════════════════════════


class TestFactoryFunction:
    """Tests for create_hook_executor factory function."""

    def test_default_creation(self):
        """Default creation should use parallel_by_priority."""
        executor = create_hook_executor()
        assert executor.config.execution_mode == BatchExecutionMode.PARALLEL_BY_PRIORITY

    def test_sequential_creation(self):
        """Sequential mode creation."""
        executor = create_hook_executor(mode="sequential")
        assert executor.config.execution_mode == BatchExecutionMode.SEQUENTIAL

    def test_fully_parallel_creation(self):
        """Fully parallel mode creation."""
        executor = create_hook_executor(mode="fully_parallel")
        assert executor.config.execution_mode == BatchExecutionMode.FULLY_PARALLEL

    def test_custom_settings(self):
        """Custom settings should be applied."""
        executor = create_hook_executor(max_concurrent=5, timeout=1.0)
        assert executor.config.max_concurrent == 5
        assert executor.config.default_timeout == 1.0


# ═══════════════════════════════════════════════════════════════
# Performance Tests
# ═══════════════════════════════════════════════════════════════


class TestPerformance:
    """Performance tests for hook batch executor."""

    @pytest.mark.asyncio
    async def test_parallel_speedup(self):
        """Parallel execution should be faster than sequential."""
        context = MockHookContext()

        # Create hooks with 20ms delay each
        hooks = [(1, SlowHook(f"hook{i}", delay_ms=20)) for i in range(5)]

        # Sequential execution
        seq_executor = create_hook_executor(mode="sequential")
        start = time.perf_counter()
        await seq_executor.execute_batch(hooks, context)
        seq_duration = (time.perf_counter() - start) * 1000

        # Parallel execution
        par_executor = create_hook_executor(mode="fully_parallel")
        start = time.perf_counter()
        await par_executor.execute_batch(hooks, context)
        par_duration = (time.perf_counter() - start) * 1000

        # Parallel should be at least 2x faster
        speedup = seq_duration / par_duration if par_duration > 0 else 1
        print(f"\nSequential: {seq_duration:.1f}ms, Parallel: {par_duration:.1f}ms")
        print(f"Speedup: {speedup:.1f}x")

        assert speedup > 2, f"Parallel speedup too low: {speedup:.1f}x"

    @pytest.mark.asyncio
    async def test_priority_batch_speedup(self):
        """Priority batching should be faster than sequential."""
        context = MockHookContext()

        # Hooks at same priority (20ms each)
        hooks = [(1, SlowHook(f"hook{i}", delay_ms=20)) for i in range(3)]

        # Add another batch at different priority
        hooks.extend([(2, SlowHook(f"hook{i+3}", delay_ms=20)) for i in range(3)])

        # Sequential would take ~120ms (6 * 20)
        # Priority batch: batch1 (3 parallel) + batch2 (3 parallel) = ~40ms + overhead

        executor = create_hook_executor(mode="parallel_by_priority")
        start = time.perf_counter()
        result = await executor.execute_batch(hooks, context)
        duration = (time.perf_counter() - start) * 1000

        print(f"\nPriority batch execution: {duration:.1f}ms")
        print(f"Batches: {result.parallel_batches}")

        # Should be significantly faster than 120ms
        assert duration < 80, f"Priority batching too slow: {duration:.1f}ms"

    @pytest.mark.asyncio
    async def test_many_fast_hooks(self):
        """Many fast hooks should complete quickly."""
        context = MockHookContext()
        executor = create_hook_executor(mode="fully_parallel", max_concurrent=20)

        # 50 fast hooks
        hooks = [(1, MockHook(f"hook{i}")) for i in range(50)]

        start = time.perf_counter()
        result = await executor.execute_batch(hooks, context)
        duration = (time.perf_counter() - start) * 1000

        print(f"\n50 fast hooks: {duration:.1f}ms")

        assert result.hooks_executed == 50
        assert result.hooks_succeeded == 50
        # Should complete in reasonable time
        assert duration < 500, f"Too slow for fast hooks: {duration:.1f}ms"
