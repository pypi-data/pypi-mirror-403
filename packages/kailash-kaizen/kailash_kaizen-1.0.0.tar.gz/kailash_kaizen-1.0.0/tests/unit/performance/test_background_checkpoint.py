"""
Tests for BackgroundCheckpointWriter (TODO-199.3.4).

Tests cover:
- Basic write operations
- Write coalescing
- Flush behavior
- Concurrent operations
- Error handling
- Metrics tracking
- Lifecycle management
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock

import pytest

from kaizen.performance.background_checkpoint import (
    BackgroundCheckpointConfig,
    BackgroundCheckpointMetrics,
    BackgroundCheckpointWriter,
    CheckpointWriteResult,
    PendingCheckpoint,
    create_background_writer,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@dataclass
class MockAgentState:
    """Mock agent state for testing."""

    checkpoint_id: str = "ckpt_test123"
    agent_id: str = "agent-1"
    step_number: int = 0
    status: str = "running"
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "agent_id": self.agent_id,
            "step_number": self.step_number,
            "status": self.status,
            "data": self.data,
        }


class MockStorage:
    """Mock storage backend for testing."""

    def __init__(
        self,
        delay: float = 0.0,
        fail_on: Optional[List[str]] = None,
    ):
        self.saved_states: List[Any] = []
        self.save_calls: int = 0
        self.delay = delay
        self.fail_on = fail_on or []

    async def save(self, state: Any) -> str:
        self.save_calls += 1

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        checkpoint_id = getattr(state, "checkpoint_id", "unknown")

        if checkpoint_id in self.fail_on:
            raise IOError(f"Simulated failure for {checkpoint_id}")

        self.saved_states.append(state)
        return checkpoint_id


@pytest.fixture
def mock_storage():
    """Create mock storage."""
    return MockStorage()


@pytest.fixture
def mock_storage_with_delay():
    """Create mock storage with artificial delay."""
    return MockStorage(delay=0.05)


@pytest.fixture
def config():
    """Default test configuration."""
    return BackgroundCheckpointConfig(
        flush_interval=0.1,
        max_queue_size=100,
        coalesce_writes=True,
        thread_pool_size=2,
        enable_metrics=True,
        shutdown_timeout=5.0,
    )


# =============================================================================
# Basic Functionality Tests
# =============================================================================


class TestBasicOperations:
    """Test basic background checkpoint operations."""

    @pytest.mark.asyncio
    async def test_create_writer(self, mock_storage, config):
        """Test writer creation."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        assert writer.storage == mock_storage
        assert writer.config == config
        assert not writer._running

    @pytest.mark.asyncio
    async def test_start_and_stop(self, mock_storage, config):
        """Test writer start and stop lifecycle."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)

        await writer.start()
        assert writer._running
        assert writer._thread_pool is not None
        assert writer._flush_task is not None

        await writer.stop()
        assert not writer._running
        assert writer._thread_pool is None

    @pytest.mark.asyncio
    async def test_queue_checkpoint(self, mock_storage, config):
        """Test queueing a checkpoint."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        state = MockAgentState(checkpoint_id="ckpt_1", agent_id="agent-1")
        await writer.queue_checkpoint(state)

        assert writer.get_pending_count() == 1
        assert "agent-1" in writer.get_pending_agents()

        await writer.stop()

    @pytest.mark.asyncio
    async def test_queue_without_start_raises(self, mock_storage, config):
        """Test that queueing without starting raises error."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)

        state = MockAgentState()
        with pytest.raises(RuntimeError, match="not running"):
            await writer.queue_checkpoint(state)

    @pytest.mark.asyncio
    async def test_flush_now(self, mock_storage, config):
        """Test immediate flush."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        state = MockAgentState(checkpoint_id="ckpt_1")
        await writer.queue_checkpoint(state)

        results = await writer.flush_now()

        assert len(results) == 1
        assert results[0].success
        assert results[0].checkpoint_id == "ckpt_1"
        assert mock_storage.save_calls == 1

        await writer.stop()

    @pytest.mark.asyncio
    async def test_auto_flush_on_interval(self, mock_storage):
        """Test automatic flush on interval."""
        config = BackgroundCheckpointConfig(
            flush_interval=0.05,  # 50ms
            coalesce_writes=True,
        )
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        state = MockAgentState(checkpoint_id="ckpt_1")
        await writer.queue_checkpoint(state)

        # Wait for auto-flush
        await asyncio.sleep(0.15)

        assert mock_storage.save_calls >= 1
        assert len(mock_storage.saved_states) >= 1

        await writer.stop()


# =============================================================================
# Write Coalescing Tests
# =============================================================================


class TestWriteCoalescing:
    """Test write coalescing behavior."""

    @pytest.mark.asyncio
    async def test_coalesce_multiple_writes_same_agent(self, mock_storage, config):
        """Test that multiple writes for same agent are coalesced."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue multiple checkpoints for same agent
        for i in range(5):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id="agent-1",
                step_number=i,
            )
            await writer.queue_checkpoint(state)

        # Should only have one pending (latest)
        assert writer.get_pending_count() == 1

        # Flush and verify only last state was written
        results = await writer.flush_now()

        assert len(results) == 1
        assert results[0].checkpoint_id == "ckpt_4"
        assert results[0].coalesced_count == 4
        assert mock_storage.save_calls == 1

        # Verify last state
        saved_state = mock_storage.saved_states[0]
        assert saved_state.step_number == 4

        await writer.stop()

    @pytest.mark.asyncio
    async def test_no_coalesce_different_agents(self, mock_storage, config):
        """Test that writes for different agents are not coalesced."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue checkpoints for different agents
        for i in range(3):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        assert writer.get_pending_count() == 3

        results = await writer.flush_now()

        assert len(results) == 3
        assert mock_storage.save_calls == 3

        await writer.stop()

    @pytest.mark.asyncio
    async def test_coalesce_disabled(self, mock_storage):
        """Test behavior with coalescing disabled."""
        config = BackgroundCheckpointConfig(
            flush_interval=10.0,  # Long interval, won't auto-flush
            coalesce_writes=False,
        )
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue multiple checkpoints for same agent
        for i in range(3):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id="agent-1",
            )
            await writer.queue_checkpoint(state)

        # With coalescing disabled, each write replaces previous
        # (pending dict keyed by agent_id)
        assert writer.get_pending_count() == 1

        await writer.stop()

    @pytest.mark.asyncio
    async def test_coalesce_metrics(self, mock_storage, config):
        """Test coalescing metrics tracking."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue 5 checkpoints, 4 will be coalesced
        for i in range(5):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id="agent-1",
            )
            await writer.queue_checkpoint(state)

        await writer.flush_now()

        metrics = writer.get_metrics()
        assert metrics.checkpoints_queued == 5
        assert metrics.checkpoints_coalesced == 4
        assert metrics.checkpoints_written == 1

        await writer.stop()


# =============================================================================
# Concurrent Operations Tests
# =============================================================================


class TestConcurrentOperations:
    """Test concurrent checkpoint operations."""

    @pytest.mark.asyncio
    async def test_concurrent_queues(self, mock_storage):
        """Test concurrent queue operations complete successfully."""
        config = BackgroundCheckpointConfig(
            flush_interval=0.05,  # Fast flush for concurrent test
            coalesce_writes=True,
        )
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        async def queue_checkpoints(agent_id: str, count: int):
            for i in range(count):
                state = MockAgentState(
                    checkpoint_id=f"ckpt_{agent_id}_{i}",
                    agent_id=agent_id,
                )
                await writer.queue_checkpoint(state)

        # Queue concurrently for multiple agents
        await asyncio.gather(
            queue_checkpoints("agent-1", 5),
            queue_checkpoints("agent-2", 5),
            queue_checkpoints("agent-3", 5),
        )

        # Wait for flush to complete
        await asyncio.sleep(0.1)
        await writer.flush_now()
        await writer.stop()

        # Verify all checkpoints were queued
        metrics = writer.get_metrics()
        assert metrics.checkpoints_queued == 15
        # All should have succeeded (writes + coalesced = queued)
        total_handled = metrics.checkpoints_written + metrics.checkpoints_coalesced
        assert total_handled == 15
        assert metrics.checkpoints_failed == 0

    @pytest.mark.asyncio
    async def test_concurrent_writes_with_delay(self, mock_storage_with_delay, config):
        """Test concurrent writes with storage delay."""
        writer = BackgroundCheckpointWriter(
            storage=mock_storage_with_delay, config=config
        )
        await writer.start()

        # Queue for multiple agents
        for i in range(5):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        # Flush and ensure all complete
        results = await writer.flush_now()

        assert len(results) == 5
        assert all(r.success for r in results)

        await writer.stop()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Test error handling in checkpoint operations."""

    @pytest.mark.asyncio
    async def test_storage_failure_tracked(self, config):
        """Test that storage failures are tracked in metrics."""
        storage = MockStorage(fail_on=["ckpt_fail"])
        writer = BackgroundCheckpointWriter(storage=storage, config=config)
        await writer.start()

        # Queue a checkpoint that will fail
        state = MockAgentState(checkpoint_id="ckpt_fail", agent_id="agent-1")
        await writer.queue_checkpoint(state)

        results = await writer.flush_now()

        assert len(results) == 1
        assert not results[0].success
        assert "Simulated failure" in results[0].error

        metrics = writer.get_metrics()
        assert metrics.checkpoints_failed == 1
        assert metrics.checkpoints_written == 0

        await writer.stop()

    @pytest.mark.asyncio
    async def test_partial_failure(self, config):
        """Test partial failure handling."""
        storage = MockStorage(fail_on=["ckpt_2"])
        writer = BackgroundCheckpointWriter(storage=storage, config=config)
        await writer.start()

        # Queue multiple checkpoints, one will fail
        for i in range(3):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        results = await writer.flush_now()

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        assert len(successful) == 2
        assert len(failed) == 1
        assert failed[0].checkpoint_id == "ckpt_2"

        await writer.stop()

    @pytest.mark.asyncio
    async def test_double_start_warning(self, mock_storage, config, caplog):
        """Test warning on double start."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)

        await writer.start()
        await writer.start()  # Should log warning

        assert "already running" in caplog.text.lower()

        await writer.stop()


# =============================================================================
# Lifecycle Tests
# =============================================================================


class TestLifecycle:
    """Test writer lifecycle management."""

    @pytest.mark.asyncio
    async def test_graceful_shutdown_flushes_pending(self, mock_storage, config):
        """Test that graceful shutdown flushes pending checkpoints."""
        config.flush_interval = 10.0  # Long interval, won't auto-flush
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue checkpoints
        for i in range(3):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        # Stop should flush pending
        flushed_count = await writer.stop()

        assert flushed_count == 3
        assert mock_storage.save_calls == 3

    @pytest.mark.asyncio
    async def test_stop_returns_zero_when_empty(self, mock_storage, config):
        """Test stop returns zero when no pending checkpoints."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        flushed_count = await writer.stop()

        assert flushed_count == 0

    @pytest.mark.asyncio
    async def test_stop_idempotent(self, mock_storage, config):
        """Test that stop can be called multiple times."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        await writer.stop()
        result = await writer.stop()  # Second call should be safe

        assert result == 0


# =============================================================================
# Metrics Tests
# =============================================================================


class TestMetrics:
    """Test metrics tracking."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, mock_storage, config):
        """Test comprehensive metrics tracking."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue and flush checkpoints
        for i in range(3):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        await writer.flush_now()

        metrics = writer.get_metrics()

        assert metrics.checkpoints_queued == 3
        assert metrics.checkpoints_written == 3
        assert metrics.checkpoints_failed == 0
        assert metrics.total_write_time_ms > 0
        assert metrics.avg_write_time_ms > 0
        assert metrics.success_rate == 1.0
        assert metrics.flush_cycles >= 0

        await writer.stop()

    @pytest.mark.asyncio
    async def test_max_queue_depth_tracking(self, mock_storage, config):
        """Test max queue depth tracking."""
        config.flush_interval = 10.0  # Long interval
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue 5 checkpoints for different agents
        for i in range(5):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        metrics = writer.get_metrics()
        assert metrics.max_queue_depth == 5

        await writer.stop()

    @pytest.mark.asyncio
    async def test_metrics_to_dict(self, mock_storage, config):
        """Test metrics serialization."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        state = MockAgentState()
        await writer.queue_checkpoint(state)
        await writer.flush_now()

        metrics = writer.get_metrics()
        metrics_dict = metrics.to_dict()

        assert "checkpoints_queued" in metrics_dict
        assert "checkpoints_written" in metrics_dict
        assert "success_rate" in metrics_dict
        assert "coalesce_ratio" in metrics_dict

        await writer.stop()

    @pytest.mark.asyncio
    async def test_reset_metrics(self, mock_storage, config):
        """Test metrics reset."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        state = MockAgentState()
        await writer.queue_checkpoint(state)
        await writer.flush_now()

        writer.reset_metrics()
        metrics = writer.get_metrics()

        assert metrics.checkpoints_queued == 0
        assert metrics.checkpoints_written == 0

        await writer.stop()


# =============================================================================
# Callback Tests
# =============================================================================


class TestCallbacks:
    """Test write callbacks."""

    @pytest.mark.asyncio
    async def test_write_callback_invoked(self, mock_storage, config):
        """Test that write callback is invoked after each write."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)

        callback_results: List[CheckpointWriteResult] = []

        def on_write(result: CheckpointWriteResult):
            callback_results.append(result)

        writer.set_write_callback(on_write)
        await writer.start()

        for i in range(3):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        await writer.flush_now()

        assert len(callback_results) == 3
        assert all(r.success for r in callback_results)

        await writer.stop()

    @pytest.mark.asyncio
    async def test_callback_error_handled(self, mock_storage, config, caplog):
        """Test that callback errors don't crash the writer."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)

        def failing_callback(result: CheckpointWriteResult):
            raise ValueError("Callback error")

        writer.set_write_callback(failing_callback)
        await writer.start()

        state = MockAgentState()
        await writer.queue_checkpoint(state)

        # Should not raise
        results = await writer.flush_now()

        assert len(results) == 1
        assert results[0].success
        assert "callback failed" in caplog.text.lower()

        await writer.stop()


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_create_background_writer(self, mock_storage):
        """Test create_background_writer helper."""
        writer = create_background_writer(
            storage=mock_storage,
            flush_interval=0.5,
            coalesce=True,
        )

        assert writer.config.flush_interval == 0.5
        assert writer.config.coalesce_writes is True

    @pytest.mark.asyncio
    async def test_create_background_writer_no_coalesce(self, mock_storage):
        """Test create_background_writer without coalescing."""
        writer = create_background_writer(
            storage=mock_storage,
            coalesce=False,
        )

        assert writer.config.coalesce_writes is False


# =============================================================================
# Data Class Tests
# =============================================================================


class TestDataClasses:
    """Test data classes."""

    def test_checkpoint_write_result(self):
        """Test CheckpointWriteResult creation."""
        result = CheckpointWriteResult(
            checkpoint_id="ckpt_1",
            agent_id="agent-1",
            success=True,
            duration_ms=10.5,
            size_bytes=1024,
            coalesced_count=3,
        )

        assert result.checkpoint_id == "ckpt_1"
        assert result.success
        assert result.duration_ms == 10.5
        assert result.coalesced_count == 3

    def test_checkpoint_write_result_with_error(self):
        """Test CheckpointWriteResult with error."""
        result = CheckpointWriteResult(
            checkpoint_id="ckpt_1",
            agent_id="agent-1",
            success=False,
            duration_ms=5.0,
            error="Write failed",
        )

        assert not result.success
        assert result.error == "Write failed"

    def test_pending_checkpoint(self):
        """Test PendingCheckpoint creation."""
        state = MockAgentState()
        pending = PendingCheckpoint(
            state=state,
            agent_id="agent-1",
            queued_at=1000.0,
            coalesced_count=2,
        )

        assert pending.state == state
        assert pending.coalesced_count == 2

    def test_background_checkpoint_config_defaults(self):
        """Test BackgroundCheckpointConfig defaults."""
        config = BackgroundCheckpointConfig()

        assert config.flush_interval == 1.0
        assert config.max_queue_size == 100
        assert config.coalesce_writes is True
        assert config.thread_pool_size == 2
        assert config.enable_metrics is True
        assert config.shutdown_timeout == 30.0

    def test_background_checkpoint_metrics_properties(self):
        """Test BackgroundCheckpointMetrics computed properties."""
        metrics = BackgroundCheckpointMetrics(
            checkpoints_queued=10,
            checkpoints_written=8,
            checkpoints_failed=2,
            checkpoints_coalesced=5,
        )

        assert metrics.success_rate == 0.8
        assert metrics.coalesce_ratio == 0.5

    def test_metrics_success_rate_zero_writes(self):
        """Test success rate with no writes."""
        metrics = BackgroundCheckpointMetrics()
        assert metrics.success_rate == 1.0

    def test_metrics_coalesce_ratio_zero_queued(self):
        """Test coalesce ratio with no queued."""
        metrics = BackgroundCheckpointMetrics()
        assert metrics.coalesce_ratio == 0.0


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_queue_performance(self, mock_storage, config):
        """Test queue operation performance."""
        import time

        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        start = time.perf_counter()
        iterations = 1000

        for i in range(iterations):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i % 10}",  # 10 agents
            )
            await writer.queue_checkpoint(state)

        duration_ms = (time.perf_counter() - start) * 1000
        ops_per_sec = iterations / (duration_ms / 1000)

        # Should handle at least 1K queue ops/sec (conservative threshold for CI)
        assert ops_per_sec > 1000, f"Queue performance too low: {ops_per_sec:.0f} ops/sec"

        await writer.stop()

    @pytest.mark.asyncio
    async def test_coalesce_reduces_writes(self, mock_storage, config):
        """Test that coalescing significantly reduces writes."""
        config.flush_interval = 10.0  # No auto-flush
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        # Queue 100 checkpoints for 5 agents
        for i in range(100):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i % 5}",
            )
            await writer.queue_checkpoint(state)

        await writer.flush_now()

        metrics = writer.get_metrics()

        # Should only write 5 checkpoints (one per agent)
        assert metrics.checkpoints_written == 5
        # 95 should be coalesced
        assert metrics.checkpoints_coalesced == 95

        await writer.stop()

    @pytest.mark.asyncio
    async def test_non_blocking_queue(self, config):
        """Test that queue doesn't block on slow storage."""
        import time

        slow_storage = MockStorage(delay=0.1)  # 100ms per write
        writer = BackgroundCheckpointWriter(storage=slow_storage, config=config)
        await writer.start()

        start = time.perf_counter()

        # Queue should be fast regardless of storage speed
        for i in range(10):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id=f"agent-{i}",
            )
            await writer.queue_checkpoint(state)

        queue_time_ms = (time.perf_counter() - start) * 1000

        # Queueing 10 items should be < 50ms (non-blocking)
        assert queue_time_ms < 50, f"Queue blocked: {queue_time_ms:.1f}ms"

        await writer.stop()


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for background checkpoint writer."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_storage, config):
        """Test complete checkpoint workflow."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)

        # Start
        await writer.start()
        assert writer._running

        # Queue checkpoints
        for i in range(5):
            state = MockAgentState(
                checkpoint_id=f"ckpt_{i}",
                agent_id="agent-1",
                step_number=i,
            )
            await writer.queue_checkpoint(state)

        # Verify coalescing
        assert writer.get_pending_count() == 1

        # Flush
        results = await writer.flush_now()
        assert len(results) == 1
        assert results[0].coalesced_count == 4

        # Verify saved state
        assert len(mock_storage.saved_states) == 1
        assert mock_storage.saved_states[0].step_number == 4

        # Check metrics
        metrics = writer.get_metrics()
        assert metrics.checkpoints_queued == 5
        assert metrics.checkpoints_written == 1
        assert metrics.checkpoints_coalesced == 4

        # Stop
        await writer.stop()
        assert not writer._running

    @pytest.mark.asyncio
    async def test_agent_id_from_state(self, mock_storage, config):
        """Test agent_id extraction from state."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        state = MockAgentState(agent_id="my-agent-123")
        await writer.queue_checkpoint(state)

        assert "my-agent-123" in writer.get_pending_agents()

        await writer.stop()

    @pytest.mark.asyncio
    async def test_explicit_agent_id(self, mock_storage, config):
        """Test explicit agent_id parameter."""
        writer = BackgroundCheckpointWriter(storage=mock_storage, config=config)
        await writer.start()

        state = MockAgentState(agent_id="state-agent")
        await writer.queue_checkpoint(state, agent_id="explicit-agent")

        assert "explicit-agent" in writer.get_pending_agents()
        assert "state-agent" not in writer.get_pending_agents()

        await writer.stop()
