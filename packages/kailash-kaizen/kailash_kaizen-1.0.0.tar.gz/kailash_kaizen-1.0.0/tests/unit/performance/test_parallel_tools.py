"""
Unit tests for Parallel Tool Executor (TODO-199.2.1).

Tests the parallel execution infrastructure for tool calls.
"""

import asyncio
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from kaizen.performance.parallel_tools import (
    ParallelExecutionConfig,
    ParallelExecutionResult,
    ParallelToolExecutor,
    ToolDependencyAnalyzer,
    ToolExecutionResult,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


class MockToolRegistry:
    """Mock tool registry for testing."""

    def __init__(self, delay_ms: float = 10.0):
        self.delay_ms = delay_ms
        self.call_count = 0
        self.calls: list[tuple[str, Dict[str, Any]]] = []

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with simulated delay."""
        self.call_count += 1
        self.calls.append((tool_name, args))

        # Simulate tool execution time
        await asyncio.sleep(self.delay_ms / 1000)

        return {"tool": tool_name, "args": args, "success": True}


@pytest.fixture
def mock_registry():
    """Create a mock tool registry."""
    return MockToolRegistry(delay_ms=10.0)


@pytest.fixture
def executor(mock_registry):
    """Create a parallel executor with mock registry."""
    return ParallelToolExecutor(
        tool_registry=mock_registry,
        config=ParallelExecutionConfig(max_concurrent=5),
    )


# ═══════════════════════════════════════════════════════════════
# ToolDependencyAnalyzer Tests
# ═══════════════════════════════════════════════════════════════


class TestToolDependencyAnalyzer:
    """Tests for ToolDependencyAnalyzer."""

    def test_empty_tool_list(self):
        """Empty list should return empty groups."""
        analyzer = ToolDependencyAnalyzer()
        parallel, sequential = analyzer.analyze([])

        assert parallel == []
        assert sequential == []

    def test_single_parallelizable_tool(self):
        """Single parallelizable tool should be in parallel group."""
        analyzer = ToolDependencyAnalyzer()
        tools = [{"name": "read_file", "id": "1", "arguments": {"path": "/test"}}]

        parallel, sequential = analyzer.analyze(tools)

        assert len(parallel) == 1
        assert len(sequential) == 0

    def test_single_sequential_tool(self):
        """Sequential-only tool should be in sequential group."""
        analyzer = ToolDependencyAnalyzer()
        tools = [{"name": "save_file", "id": "1", "arguments": {"path": "/test"}}]

        parallel, sequential = analyzer.analyze(tools)

        assert len(parallel) == 0
        assert len(sequential) == 1

    def test_mixed_tools(self):
        """Mixed tools should be correctly categorized."""
        analyzer = ToolDependencyAnalyzer()
        tools = [
            {"name": "read_file", "id": "1", "arguments": {"path": "/a"}},
            {"name": "save_file", "id": "2", "arguments": {"path": "/b"}},
            {"name": "search", "id": "3", "arguments": {"query": "test"}},
        ]

        parallel, sequential = analyzer.analyze(tools)

        assert len(parallel) == 2
        assert len(sequential) == 1
        assert any(t["name"] == "save_file" for t in sequential)

    def test_tool_with_dependency_reference(self):
        """Tool referencing another tool's output should be sequential."""
        analyzer = ToolDependencyAnalyzer()
        tools = [
            {"name": "search", "id": "tool_1", "arguments": {"query": "test"}},
            {
                "name": "process",
                "id": "tool_2",
                "arguments": {"input": "Result from tool_1"},
            },
        ]

        parallel, sequential = analyzer.analyze(tools)

        # tool_2 references tool_1 in its arguments
        assert len(sequential) == 1
        assert sequential[0]["id"] == "tool_2"

    def test_custom_sequential_tools(self):
        """Custom sequential tools should be respected."""
        analyzer = ToolDependencyAnalyzer(
            sequential_tools={"custom_write"},
        )
        tools = [
            {"name": "custom_write", "id": "1", "arguments": {}},
            {"name": "read_file", "id": "2", "arguments": {}},
        ]

        parallel, sequential = analyzer.analyze(tools)

        assert len(sequential) == 1
        assert sequential[0]["name"] == "custom_write"

    def test_custom_parallelizable_tools(self):
        """Custom parallelizable tools should be respected."""
        analyzer = ToolDependencyAnalyzer(
            parallelizable_tools={"custom_read"},
        )
        tools = [{"name": "custom_read", "id": "1", "arguments": {}}]

        parallel, sequential = analyzer.analyze(tools)

        assert len(parallel) == 1


# ═══════════════════════════════════════════════════════════════
# ToolExecutionResult Tests
# ═══════════════════════════════════════════════════════════════


class TestToolExecutionResult:
    """Tests for ToolExecutionResult dataclass."""

    def test_successful_result(self):
        """Successful result should have correct fields."""
        result = ToolExecutionResult(
            tool_name="test_tool",
            tool_id="123",
            success=True,
            result={"output": "value"},
            duration_ms=15.5,
        )

        assert result.tool_name == "test_tool"
        assert result.tool_id == "123"
        assert result.success is True
        assert result.result == {"output": "value"}
        assert result.error is None
        assert result.duration_ms == 15.5

    def test_failed_result(self):
        """Failed result should have error message."""
        result = ToolExecutionResult(
            tool_name="test_tool",
            tool_id="123",
            success=False,
            error="Tool failed",
            duration_ms=5.0,
        )

        assert result.success is False
        assert result.error == "Tool failed"
        assert result.result is None


# ═══════════════════════════════════════════════════════════════
# ParallelExecutionResult Tests
# ═══════════════════════════════════════════════════════════════


class TestParallelExecutionResult:
    """Tests for ParallelExecutionResult dataclass."""

    def test_empty_result(self):
        """Empty result should have correct defaults."""
        result = ParallelExecutionResult()

        assert result.results == []
        assert result.all_succeeded is True  # No failures = all succeeded
        assert result.tools_executed == 0
        assert result.tools_succeeded == 0
        assert result.tools_failed == 0

    def test_all_succeeded(self):
        """all_succeeded should be True when no failures."""
        result = ParallelExecutionResult(
            results=[
                ToolExecutionResult("a", "1", True),
                ToolExecutionResult("b", "2", True),
            ],
            tools_executed=2,
            tools_succeeded=2,
            tools_failed=0,
        )

        assert result.all_succeeded is True

    def test_some_failed(self):
        """all_succeeded should be False when there are failures."""
        result = ParallelExecutionResult(
            results=[
                ToolExecutionResult("a", "1", True),
                ToolExecutionResult("b", "2", False, error="Failed"),
            ],
            tools_executed=2,
            tools_succeeded=1,
            tools_failed=1,
        )

        assert result.all_succeeded is False

    def test_get_result_by_id(self):
        """get_result should find result by tool ID."""
        result = ParallelExecutionResult(
            results=[
                ToolExecutionResult("a", "tool_1", True),
                ToolExecutionResult("b", "tool_2", True),
            ]
        )

        found = result.get_result("tool_2")
        assert found is not None
        assert found.tool_name == "b"

    def test_get_result_not_found(self):
        """get_result should return None for unknown ID."""
        result = ParallelExecutionResult()

        assert result.get_result("unknown") is None


# ═══════════════════════════════════════════════════════════════
# ParallelToolExecutor Tests
# ═══════════════════════════════════════════════════════════════


class TestParallelToolExecutor:
    """Tests for ParallelToolExecutor."""

    @pytest.mark.asyncio
    async def test_execute_single_tool(self, executor, mock_registry):
        """Single tool should execute correctly."""
        tools = [{"name": "test_tool", "id": "1", "arguments": {"key": "value"}}]

        result = await executor.execute_parallel(tools)

        assert result.tools_executed == 1
        assert result.tools_succeeded == 1
        assert result.all_succeeded is True
        assert mock_registry.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_parallel_tools(self, executor, mock_registry):
        """Multiple independent tools should execute in parallel."""
        # Create 5 parallelizable tools
        tools = [
            {"name": "read_file", "id": f"tool_{i}", "arguments": {"path": f"/file_{i}"}}
            for i in range(5)
        ]

        start = time.perf_counter()
        result = await executor.execute_parallel(tools)
        duration = (time.perf_counter() - start) * 1000

        assert result.tools_executed == 5
        assert result.tools_succeeded == 5
        assert mock_registry.call_count == 5

        # Should be faster than sequential (5 * 10ms = 50ms)
        # Parallel should complete in ~10-15ms
        assert duration < 40, f"Parallel execution too slow: {duration:.1f}ms"

    @pytest.mark.asyncio
    async def test_execute_sequential_fallback(self, mock_registry):
        """Disabled parallel execution should fall back to sequential."""
        executor = ParallelToolExecutor(
            tool_registry=mock_registry,
            config=ParallelExecutionConfig(enabled=False),
        )

        tools = [
            {"name": "read_file", "id": f"tool_{i}", "arguments": {}}
            for i in range(3)
        ]

        result = await executor.execute_parallel(tools)

        assert result.tools_executed == 3
        assert result.parallel_speedup == 1.0  # No speedup when sequential

    @pytest.mark.asyncio
    async def test_mixed_parallel_sequential(self, executor, mock_registry):
        """Mixed tools should respect dependencies."""
        tools = [
            {"name": "read_file", "id": "1", "arguments": {}},  # Parallel
            {"name": "save_file", "id": "2", "arguments": {}},  # Sequential
            {"name": "search", "id": "3", "arguments": {}},  # Parallel
        ]

        result = await executor.execute_parallel(tools)

        assert result.tools_executed == 3
        assert result.tools_succeeded == 3

    @pytest.mark.asyncio
    async def test_tool_failure_handling(self, mock_registry):
        """Failed tools should be captured in result."""

        async def failing_execute(name: str, args: Dict) -> Dict:
            if name == "fail_tool":
                raise ValueError("Tool failed intentionally")
            return {"success": True}

        mock_registry.execute = failing_execute

        executor = ParallelToolExecutor(tool_registry=mock_registry)

        tools = [
            {"name": "good_tool", "id": "1", "arguments": {}},
            {"name": "fail_tool", "id": "2", "arguments": {}},
        ]

        result = await executor.execute_parallel(tools)

        assert result.tools_executed == 2
        assert result.tools_succeeded == 1
        assert result.tools_failed == 1
        assert not result.all_succeeded

        failed = result.get_result("2")
        assert failed is not None
        assert not failed.success
        assert "intentionally" in failed.error

    @pytest.mark.asyncio
    async def test_fail_fast_mode(self, mock_registry):
        """Fail fast should stop execution on first failure."""

        call_order = []

        async def tracking_execute(name: str, args: Dict) -> Dict:
            call_order.append(name)
            if name == "tool_2":
                raise ValueError("Fail at tool_2")
            await asyncio.sleep(0.001)
            return {"success": True}

        mock_registry.execute = tracking_execute

        executor = ParallelToolExecutor(
            tool_registry=mock_registry,
            config=ParallelExecutionConfig(fail_fast=True, enabled=False),  # Sequential for predictable order
        )

        tools = [
            {"name": "tool_1", "id": "1", "arguments": {}},
            {"name": "tool_2", "id": "2", "arguments": {}},
            {"name": "tool_3", "id": "3", "arguments": {}},
        ]

        result = await executor.execute_parallel(tools)

        # Should stop after tool_2 fails
        assert len(result.results) == 2
        assert "tool_3" not in call_order

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, mock_registry):
        """Concurrency should be limited by semaphore."""
        max_concurrent = []
        current_concurrent = [0]

        original_execute = mock_registry.execute

        async def tracking_execute(name: str, args: Dict) -> Dict:
            current_concurrent[0] += 1
            max_concurrent.append(current_concurrent[0])
            result = await original_execute(name, args)
            current_concurrent[0] -= 1
            return result

        mock_registry.execute = tracking_execute

        executor = ParallelToolExecutor(
            tool_registry=mock_registry,
            config=ParallelExecutionConfig(max_concurrent=3),
        )

        # Create 10 parallelizable tools
        tools = [
            {"name": "read_file", "id": f"tool_{i}", "arguments": {}}
            for i in range(10)
        ]

        await executor.execute_parallel(tools)

        # Max concurrent should never exceed limit
        assert max(max_concurrent) <= 3

    @pytest.mark.asyncio
    async def test_metrics_collection(self, executor, mock_registry):
        """Metrics should be collected when enabled."""
        tools = [
            {"name": "read_file", "id": "1", "arguments": {}},
            {"name": "read_file", "id": "2", "arguments": {}},
            {"name": "search", "id": "3", "arguments": {}},
        ]

        await executor.execute_parallel(tools)

        metrics = executor.get_metrics()

        assert "read_file" in metrics
        assert metrics["read_file"]["count"] == 2
        assert "mean_ms" in metrics["read_file"]
        assert "p50_ms" in metrics["read_file"]

    @pytest.mark.asyncio
    async def test_string_arguments_parsing(self, executor, mock_registry):
        """String arguments should be parsed as JSON."""
        tools = [
            {"name": "test_tool", "id": "1", "arguments": '{"key": "value"}'},
        ]

        result = await executor.execute_parallel(tools)

        assert result.tools_succeeded == 1
        # Check that the registry received parsed dict
        assert mock_registry.calls[0][1] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_reset_metrics(self, executor, mock_registry):
        """Metrics should be clearable."""
        tools = [{"name": "test_tool", "id": "1", "arguments": {}}]

        await executor.execute_parallel(tools)
        assert len(executor.get_metrics()) > 0

        executor.reset_metrics()
        assert len(executor.get_metrics()) == 0


# ═══════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════


class TestParallelExecutorIntegration:
    """Integration tests for parallel execution."""

    @pytest.mark.asyncio
    async def test_speedup_measurement(self):
        """Measure actual speedup from parallelization."""
        # Create registry with 50ms delay
        registry = MockToolRegistry(delay_ms=50.0)

        executor = ParallelToolExecutor(
            tool_registry=registry,
            config=ParallelExecutionConfig(max_concurrent=10),
        )

        # Create 10 parallelizable tools
        tools = [
            {"name": "read_file", "id": f"tool_{i}", "arguments": {}}
            for i in range(10)
        ]

        result = await executor.execute_parallel(tools)

        # Sequential would take 10 * 50ms = 500ms
        # Parallel should take ~50ms (limited by single tool)
        # Actual speedup should be significant
        assert result.parallel_speedup > 3.0, (
            f"Speedup too low: {result.parallel_speedup:.2f}x"
        )

    @pytest.mark.asyncio
    async def test_large_batch_execution(self):
        """Test execution of large batch of tools."""
        registry = MockToolRegistry(delay_ms=5.0)

        executor = ParallelToolExecutor(
            tool_registry=registry,
            config=ParallelExecutionConfig(max_concurrent=20),
        )

        # Create 100 tools
        tools = [
            {"name": "read_file", "id": f"tool_{i}", "arguments": {}}
            for i in range(100)
        ]

        result = await executor.execute_parallel(tools)

        assert result.tools_executed == 100
        assert result.tools_succeeded == 100
        assert result.total_duration_ms < 5000  # Should complete in reasonable time
