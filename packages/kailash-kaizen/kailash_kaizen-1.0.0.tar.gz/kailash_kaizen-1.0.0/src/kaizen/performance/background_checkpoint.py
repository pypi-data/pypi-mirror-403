"""
Background Checkpoint I/O for non-blocking persistence (TODO-199.3.4).

Provides asynchronous checkpoint writing that doesn't block the TAOD loop.
Uses write coalescing to batch frequent checkpoint requests.

Features:
- Background asyncio task for checkpoint persistence
- Write coalescing (keeps only latest state per agent)
- Configurable flush intervals
- Thread pool for blocking I/O operations
- Metrics for checkpoint performance
- Graceful shutdown with pending write completion

Usage:
    from kaizen.performance import BackgroundCheckpointWriter

    writer = BackgroundCheckpointWriter(storage=my_storage)
    await writer.start()

    # Queue checkpoint (returns immediately)
    await writer.queue_checkpoint(agent_state)

    # Graceful shutdown
    await writer.stop()
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol for checkpoint storage backends."""

    async def save(self, state: Any) -> str:
        """Save checkpoint and return checkpoint_id."""
        ...


@dataclass
class BackgroundCheckpointConfig:
    """Configuration for background checkpoint writer."""

    flush_interval: float = 1.0  # Seconds between flush attempts
    max_queue_size: int = 100  # Maximum pending checkpoints per agent
    coalesce_writes: bool = True  # Keep only latest checkpoint per agent
    thread_pool_size: int = 2  # Threads for blocking I/O
    enable_metrics: bool = True
    shutdown_timeout: float = 30.0  # Max seconds to wait for pending writes


@dataclass
class CheckpointWriteResult:
    """Result of a checkpoint write operation."""

    checkpoint_id: str
    agent_id: str
    success: bool
    duration_ms: float
    size_bytes: int = 0
    error: Optional[str] = None
    coalesced_count: int = 0  # How many writes were coalesced


@dataclass
class BackgroundCheckpointMetrics:
    """Metrics for background checkpoint operations."""

    checkpoints_queued: int = 0
    checkpoints_written: int = 0
    checkpoints_failed: int = 0
    checkpoints_coalesced: int = 0
    total_write_time_ms: float = 0.0
    total_bytes_written: int = 0
    avg_write_time_ms: float = 0.0
    max_queue_depth: int = 0
    flush_cycles: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate write success rate."""
        total = self.checkpoints_written + self.checkpoints_failed
        return self.checkpoints_written / total if total > 0 else 1.0

    @property
    def coalesce_ratio(self) -> float:
        """Calculate coalescing ratio (how many writes saved)."""
        total = self.checkpoints_queued
        return self.checkpoints_coalesced / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "checkpoints_queued": self.checkpoints_queued,
            "checkpoints_written": self.checkpoints_written,
            "checkpoints_failed": self.checkpoints_failed,
            "checkpoints_coalesced": self.checkpoints_coalesced,
            "total_write_time_ms": self.total_write_time_ms,
            "total_bytes_written": self.total_bytes_written,
            "avg_write_time_ms": self.avg_write_time_ms,
            "max_queue_depth": self.max_queue_depth,
            "flush_cycles": self.flush_cycles,
            "success_rate": self.success_rate,
            "coalesce_ratio": self.coalesce_ratio,
        }


@dataclass
class PendingCheckpoint:
    """A checkpoint waiting to be written."""

    state: Any  # AgentState
    agent_id: str
    queued_at: float
    coalesced_count: int = 0


class BackgroundCheckpointWriter:
    """
    Background checkpoint writer for non-blocking persistence.

    Queues checkpoint operations and writes them in background tasks,
    allowing the TAOD loop to continue without waiting for I/O.
    """

    def __init__(
        self,
        storage: StorageBackend,
        config: Optional[BackgroundCheckpointConfig] = None,
    ):
        """
        Initialize background checkpoint writer.

        Args:
            storage: Storage backend for checkpoint persistence
            config: Writer configuration
        """
        self.storage = storage
        self.config = config or BackgroundCheckpointConfig()

        # Pending checkpoints per agent (for coalescing)
        self._pending: Dict[str, PendingCheckpoint] = {}
        self._lock = threading.Lock()

        # Background task control
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        self._flush_event = asyncio.Event()

        # Thread pool for blocking I/O
        self._thread_pool: Optional[ThreadPoolExecutor] = None

        # Metrics
        self._metrics = BackgroundCheckpointMetrics()

        # Write callbacks (for testing/monitoring)
        self._on_write_complete: Optional[
            Callable[[CheckpointWriteResult], None]
        ] = None

    async def start(self) -> None:
        """Start the background writer."""
        if self._running:
            logger.warning("Background checkpoint writer already running")
            return

        self._running = True
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.config.thread_pool_size,
            thread_name_prefix="checkpoint_io",
        )

        # Start flush loop
        self._flush_task = asyncio.create_task(self._flush_loop())

        logger.info(
            f"Background checkpoint writer started "
            f"(flush_interval={self.config.flush_interval}s, "
            f"coalesce={self.config.coalesce_writes})"
        )

    async def stop(self, timeout: Optional[float] = None) -> int:
        """
        Stop the background writer gracefully.

        Flushes all pending checkpoints before stopping.

        Args:
            timeout: Maximum seconds to wait (default: config.shutdown_timeout)

        Returns:
            Number of pending checkpoints that were flushed
        """
        if not self._running:
            return 0

        effective_timeout = timeout or self.config.shutdown_timeout
        self._running = False

        # Signal flush task to wake up
        self._flush_event.set()

        # Wait for flush task to complete
        if self._flush_task:
            try:
                await asyncio.wait_for(self._flush_task, timeout=effective_timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    f"Checkpoint writer shutdown timed out after {effective_timeout}s"
                )
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass

        # Flush any remaining checkpoints
        pending_count = len(self._pending)
        if pending_count > 0:
            logger.info(f"Flushing {pending_count} remaining checkpoints on shutdown")
            await self._flush_pending()

        # Shutdown thread pool
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None

        logger.info("Background checkpoint writer stopped")
        return pending_count

    async def queue_checkpoint(
        self,
        state: Any,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Queue a checkpoint for background writing.

        If coalescing is enabled, only the latest state per agent is kept.

        Args:
            state: AgentState to checkpoint
            agent_id: Agent ID (extracted from state if not provided)
        """
        if not self._running:
            raise RuntimeError("Background checkpoint writer not running")

        effective_agent_id = agent_id or getattr(state, "agent_id", "unknown")

        with self._lock:
            now = time.time()

            if self.config.coalesce_writes and effective_agent_id in self._pending:
                # Coalesce: update existing pending checkpoint
                existing = self._pending[effective_agent_id]
                existing.state = state
                existing.coalesced_count += 1

                if self.config.enable_metrics:
                    self._metrics.checkpoints_coalesced += 1

                logger.debug(
                    f"Coalesced checkpoint for {effective_agent_id} "
                    f"(count: {existing.coalesced_count})"
                )
            else:
                # New pending checkpoint
                self._pending[effective_agent_id] = PendingCheckpoint(
                    state=state,
                    agent_id=effective_agent_id,
                    queued_at=now,
                )

            if self.config.enable_metrics:
                self._metrics.checkpoints_queued += 1
                self._metrics.max_queue_depth = max(
                    self._metrics.max_queue_depth, len(self._pending)
                )

        # Signal flush task
        self._flush_event.set()

    async def flush_now(self) -> List[CheckpointWriteResult]:
        """
        Immediately flush all pending checkpoints.

        Returns:
            List of write results
        """
        return await self._flush_pending()

    def get_pending_count(self) -> int:
        """Get number of pending checkpoints."""
        with self._lock:
            return len(self._pending)

    def get_pending_agents(self) -> List[str]:
        """Get list of agent IDs with pending checkpoints."""
        with self._lock:
            return list(self._pending.keys())

    def set_write_callback(
        self,
        callback: Optional[Callable[[CheckpointWriteResult], None]],
    ) -> None:
        """
        Set callback to be invoked after each write completes.

        Args:
            callback: Function called with CheckpointWriteResult
        """
        self._on_write_complete = callback

    async def _flush_loop(self) -> None:
        """Background loop that periodically flushes pending checkpoints."""
        while self._running:
            try:
                # Wait for flush interval or signal
                try:
                    await asyncio.wait_for(
                        self._flush_event.wait(),
                        timeout=self.config.flush_interval,
                    )
                except asyncio.TimeoutError:
                    pass

                self._flush_event.clear()

                if self._pending:
                    await self._flush_pending()

                if self.config.enable_metrics:
                    self._metrics.flush_cycles += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in checkpoint flush loop: {e}")
                await asyncio.sleep(1)  # Backoff on error

    async def _flush_pending(self) -> List[CheckpointWriteResult]:
        """Flush all pending checkpoints."""
        # Get pending checkpoints atomically
        with self._lock:
            if not self._pending:
                return []

            to_write = dict(self._pending)
            self._pending.clear()

        # Write checkpoints concurrently
        tasks = [
            self._write_checkpoint(pending) for pending in to_write.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        write_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Checkpoint write failed: {result}")
            elif isinstance(result, CheckpointWriteResult):
                write_results.append(result)

                # Invoke callback
                if self._on_write_complete:
                    try:
                        self._on_write_complete(result)
                    except Exception as e:
                        logger.error(f"Write callback failed: {e}")

        return write_results

    async def _write_checkpoint(
        self,
        pending: PendingCheckpoint,
    ) -> CheckpointWriteResult:
        """Write a single checkpoint."""
        start_time = time.perf_counter()

        try:
            # Get checkpoint_id from state
            checkpoint_id = getattr(pending.state, "checkpoint_id", "unknown")

            # Perform write (may use thread pool for blocking I/O)
            if self._thread_pool:
                # Run storage.save in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._thread_pool,
                    lambda: asyncio.run(self.storage.save(pending.state)),
                )
            else:
                await self.storage.save(pending.state)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Estimate size (simplified)
            size_bytes = len(str(pending.state.to_dict())) if hasattr(pending.state, "to_dict") else 0

            if self.config.enable_metrics:
                self._metrics.checkpoints_written += 1
                self._metrics.total_write_time_ms += duration_ms
                self._metrics.total_bytes_written += size_bytes
                if self._metrics.checkpoints_written > 0:
                    self._metrics.avg_write_time_ms = (
                        self._metrics.total_write_time_ms
                        / self._metrics.checkpoints_written
                    )

            logger.debug(
                f"Checkpoint written: {checkpoint_id} "
                f"({duration_ms:.2f}ms, coalesced={pending.coalesced_count})"
            )

            return CheckpointWriteResult(
                checkpoint_id=checkpoint_id,
                agent_id=pending.agent_id,
                success=True,
                duration_ms=duration_ms,
                size_bytes=size_bytes,
                coalesced_count=pending.coalesced_count,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            checkpoint_id = getattr(pending.state, "checkpoint_id", "unknown")

            if self.config.enable_metrics:
                self._metrics.checkpoints_failed += 1

            logger.error(f"Failed to write checkpoint {checkpoint_id}: {e}")

            return CheckpointWriteResult(
                checkpoint_id=checkpoint_id,
                agent_id=pending.agent_id,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
                coalesced_count=pending.coalesced_count,
            )

    def get_metrics(self) -> BackgroundCheckpointMetrics:
        """Get checkpoint writer metrics."""
        return BackgroundCheckpointMetrics(
            checkpoints_queued=self._metrics.checkpoints_queued,
            checkpoints_written=self._metrics.checkpoints_written,
            checkpoints_failed=self._metrics.checkpoints_failed,
            checkpoints_coalesced=self._metrics.checkpoints_coalesced,
            total_write_time_ms=self._metrics.total_write_time_ms,
            total_bytes_written=self._metrics.total_bytes_written,
            avg_write_time_ms=self._metrics.avg_write_time_ms,
            max_queue_depth=self._metrics.max_queue_depth,
            flush_cycles=self._metrics.flush_cycles,
        )

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self._metrics = BackgroundCheckpointMetrics()


# Convenience function
def create_background_writer(
    storage: StorageBackend,
    flush_interval: float = 1.0,
    coalesce: bool = True,
) -> BackgroundCheckpointWriter:
    """
    Create a background checkpoint writer with common configuration.

    Args:
        storage: Storage backend
        flush_interval: Seconds between flush attempts
        coalesce: Whether to coalesce writes per agent

    Returns:
        Configured BackgroundCheckpointWriter
    """
    config = BackgroundCheckpointConfig(
        flush_interval=flush_interval,
        coalesce_writes=coalesce,
    )
    return BackgroundCheckpointWriter(storage=storage, config=config)
