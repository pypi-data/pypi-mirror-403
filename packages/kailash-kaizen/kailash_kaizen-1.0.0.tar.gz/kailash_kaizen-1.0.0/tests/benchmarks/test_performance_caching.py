"""
Pytest benchmarks for performance caching (TODO-199.4.2).

These tests use pytest-benchmark for integration with CI
and regression tracking.

Usage:
    pytest tests/benchmarks/test_performance_caching.py --benchmark-only
    pytest tests/benchmarks/test_performance_caching.py --benchmark-json=results.json
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pytest


# ═══════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def schema_cache():
    """Pre-populated schema cache."""
    from kaizen.performance import SchemaCache, SchemaCacheConfig

    cache = SchemaCache(config=SchemaCacheConfig(max_size=1000, ttl_seconds=None))
    # Pre-populate
    for i in range(100):
        cache.get_or_compute(f"tool_{i}", lambda: {"name": f"tool_{i}", "params": {}})
    return cache


@pytest.fixture
def embedding_cache():
    """Pre-populated embedding cache."""
    from kaizen.performance import EmbeddingCache, EmbeddingCacheConfig

    cache = EmbeddingCache(config=EmbeddingCacheConfig(max_size=1000, ttl_seconds=None))
    model = "text-embedding-3-small"
    # Pre-populate
    for i in range(100):
        cache.set(f"text_{i}", [0.1 * i, 0.2 * i, 0.3 * i], model=model)
    return cache


@pytest.fixture
def prompt_cache():
    """Pre-populated prompt cache."""
    from kaizen.performance import PromptCache, PromptCacheConfig

    cache = PromptCache(config=PromptCacheConfig(max_size=100, ttl_seconds=None))
    # Pre-populate
    for i in range(10):
        cache.get_or_build(
            template_id=f"base_prompt_{i}",
            build_fn=lambda: f"Prompt with tools: tool1, tool2",
            static_parts=[f"base_prompt_{i}"],
            dynamic_parts={"tools": ["tool1", "tool2"]},
        )
    return cache


@pytest.fixture
def memory_context_cache():
    """Pre-populated memory context cache."""
    from kaizen.performance import MemoryContextCache, MemoryContextConfig

    def build_segment(name: str, data: Any) -> str:
        return f"[{name}]\n{str(data)}"

    cache = MemoryContextCache(config=MemoryContextConfig(max_sessions=50))
    # Pre-populate
    for i in range(10):
        cache.build_context_incremental(
            session_id=f"session_{i}",
            segments={
                "conversation": ["msg1", "msg2"],
                "knowledge": ["fact1", "fact2"],
            },
            build_segment_fn=build_segment,
        )
    return cache


# ═══════════════════════════════════════════════════════════════
# Schema Cache Benchmarks
# ═══════════════════════════════════════════════════════════════


@pytest.mark.benchmark(group="schema_cache")
def test_schema_cache_hit(benchmark, schema_cache):
    """Benchmark schema cache hit performance."""

    def run():
        for _ in range(100):
            schema_cache.get_or_compute("tool_0", lambda: {"name": "tool_0"})

    result = benchmark(run)
    # Target: < 1ms for 100 hits (10μs per hit)
    assert result is None  # Just measure, don't fail


@pytest.mark.benchmark(group="schema_cache")
def test_schema_cache_miss(benchmark):
    """Benchmark schema cache miss performance."""
    from kaizen.performance import SchemaCache, SchemaCacheConfig

    cache = SchemaCache(config=SchemaCacheConfig(max_size=1000))

    def run():
        for i in range(10):
            cache.get_or_compute(f"new_tool_{i}", lambda: {"name": f"new_{i}"})

    result = benchmark(run)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# Embedding Cache Benchmarks
# ═══════════════════════════════════════════════════════════════


@pytest.mark.benchmark(group="embedding_cache")
def test_embedding_cache_hit(benchmark, embedding_cache):
    """Benchmark embedding cache hit performance."""
    model = "text-embedding-3-small"

    def run():
        for _ in range(100):
            embedding_cache.get("text_0", model=model)

    result = benchmark(run)
    assert result is None


@pytest.mark.benchmark(group="embedding_cache")
def test_embedding_cache_miss(benchmark):
    """Benchmark embedding cache miss performance."""
    from kaizen.performance import EmbeddingCache, EmbeddingCacheConfig

    cache = EmbeddingCache(config=EmbeddingCacheConfig(max_size=1000))
    model = "text-embedding-3-small"

    def run():
        for i in range(10):
            cache.set(f"new_text_{i}", [0.1, 0.2, 0.3], model=model)
            cache.get(f"new_text_{i}", model=model)

    result = benchmark(run)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# Prompt Cache Benchmarks
# ═══════════════════════════════════════════════════════════════


@pytest.mark.benchmark(group="prompt_cache")
def test_prompt_cache_hit(benchmark, prompt_cache):
    """Benchmark prompt cache hit performance."""

    def run():
        for _ in range(100):
            prompt_cache.get_or_build(
                template_id="base_prompt_0",
                build_fn=lambda: "Cached prompt",
                static_parts=["base_prompt_0"],
                dynamic_parts={"tools": ["tool1", "tool2"]},
            )

    result = benchmark(run)
    assert result is None


@pytest.mark.benchmark(group="prompt_cache")
def test_prompt_cache_miss(benchmark):
    """Benchmark prompt cache miss performance."""
    from kaizen.performance import PromptCache, PromptCacheConfig

    cache = PromptCache(config=PromptCacheConfig(max_size=100))

    def run():
        for i in range(10):
            cache.get_or_build(
                template_id=f"unique_{i}",
                build_fn=lambda: f"Built {i}",
                static_parts=[f"unique_{i}"],
            )

    result = benchmark(run)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# Memory Context Cache Benchmarks
# ═══════════════════════════════════════════════════════════════


@pytest.mark.benchmark(group="memory_context")
def test_memory_context_incremental_cached(benchmark, memory_context_cache):
    """Benchmark memory context with fully cached segments."""

    def build_segment(name: str, data: Any) -> str:
        return f"[{name}]\n{str(data)}"

    def run():
        memory_context_cache.build_context_incremental(
            session_id="session_0",
            segments={
                "conversation": ["msg1", "msg2"],
                "knowledge": ["fact1", "fact2"],
            },
            build_segment_fn=build_segment,
        )

    result = benchmark(run)
    assert result is None


@pytest.mark.benchmark(group="memory_context")
def test_memory_context_incremental_partial(benchmark, memory_context_cache):
    """Benchmark memory context with partial cache (one segment changed)."""
    import random

    def build_segment(name: str, data: Any) -> str:
        return f"[{name}]\n{str(data)}"

    def run():
        memory_context_cache.build_context_incremental(
            session_id="session_0",
            segments={
                "conversation": ["msg1", "msg2"],  # Cached
                "knowledge": [f"fact_{random.randint(0, 1000)}"],  # New
            },
            build_segment_fn=build_segment,
        )

    result = benchmark(run)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# Parallel Execution Benchmarks
# ═══════════════════════════════════════════════════════════════


@dataclass
class MockTool:
    """Mock tool for benchmarking."""

    name: str
    delay_ms: float = 2.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(self.delay_ms / 1000)
        return {"result": f"{self.name}_result"}


@pytest.mark.benchmark(group="parallel_execution")
def test_tools_parallel(benchmark):
    """Benchmark parallel tool execution."""
    tools = [MockTool(f"tool_{i}", delay_ms=2.0) for i in range(5)]

    async def run_async():
        tasks = [tool.execute(input=f"test_{i}") for i, tool in enumerate(tools)]
        await asyncio.gather(*tasks)

    def run():
        asyncio.run(run_async())

    result = benchmark(run)
    assert result is None


@pytest.mark.benchmark(group="parallel_execution")
def test_tools_sequential(benchmark):
    """Benchmark sequential tool execution (baseline)."""
    tools = [MockTool(f"tool_{i}", delay_ms=2.0) for i in range(5)]

    async def run_async():
        for i, tool in enumerate(tools):
            await tool.execute(input=f"test_{i}")

    def run():
        asyncio.run(run_async())

    result = benchmark(run)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# Hook Batch Benchmarks
# ═══════════════════════════════════════════════════════════════


@dataclass
class MockHookResult:
    """Mock hook result."""

    success: bool = True
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class MockHook:
    """Mock hook for benchmarking."""

    def __init__(self, name: str, delay_ms: float = 1.0):
        self.name = name
        self.delay_ms = delay_ms

    async def handle(self, context: Any) -> MockHookResult:
        await asyncio.sleep(self.delay_ms / 1000)
        return MockHookResult(success=True, data={"hook": self.name})


@pytest.mark.benchmark(group="hook_batch")
def test_hooks_sequential(benchmark):
    """Benchmark sequential hook execution."""
    from kaizen.performance import HookBatchExecutor, HookBatchConfig, BatchExecutionMode

    hooks = [MockHook(f"hook_{i}", delay_ms=1.0) for i in range(10)]
    hooks_with_priority = [(i % 3, hooks[i]) for i in range(10)]

    executor = HookBatchExecutor(
        config=HookBatchConfig(execution_mode=BatchExecutionMode.SEQUENTIAL)
    )

    async def run_async():
        await executor.execute_batch(hooks_with_priority, context={})

    def run():
        asyncio.run(run_async())

    result = benchmark(run)
    assert result is None


@pytest.mark.benchmark(group="hook_batch")
def test_hooks_parallel(benchmark):
    """Benchmark fully parallel hook execution."""
    from kaizen.performance import HookBatchExecutor, HookBatchConfig, BatchExecutionMode

    hooks = [MockHook(f"hook_{i}", delay_ms=1.0) for i in range(10)]
    hooks_with_priority = [(i % 3, hooks[i]) for i in range(10)]

    executor = HookBatchExecutor(
        config=HookBatchConfig(execution_mode=BatchExecutionMode.FULLY_PARALLEL)
    )

    async def run_async():
        await executor.execute_batch(hooks_with_priority, context={})

    def run():
        asyncio.run(run_async())

    result = benchmark(run)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# Background Checkpoint Benchmarks
# ═══════════════════════════════════════════════════════════════


@dataclass
class MockAgentState:
    """Mock agent state."""

    checkpoint_id: str = "ckpt_bench"
    agent_id: str = "agent-bench"

    def to_dict(self) -> Dict[str, Any]:
        return {"checkpoint_id": self.checkpoint_id, "agent_id": self.agent_id}


class MockStorage:
    """Mock storage."""

    def __init__(self, delay_ms: float = 1.0):
        self.delay_ms = delay_ms

    async def save(self, state: Any) -> str:
        await asyncio.sleep(self.delay_ms / 1000)
        return getattr(state, "checkpoint_id", "unknown")


@pytest.mark.benchmark(group="background_checkpoint")
def test_checkpoint_queue_nonblocking(benchmark):
    """Benchmark checkpoint queue (non-blocking)."""
    from kaizen.performance import BackgroundCheckpointWriter, BackgroundCheckpointConfig

    storage = MockStorage(delay_ms=5.0)

    async def run_async():
        writer = BackgroundCheckpointWriter(
            storage=storage,
            config=BackgroundCheckpointConfig(flush_interval=10.0, coalesce_writes=True),
        )
        await writer.start()

        for i in range(10):
            state = MockAgentState(checkpoint_id=f"ckpt_{i}", agent_id="agent-1")
            await writer.queue_checkpoint(state)

        await writer.stop()

    def run():
        asyncio.run(run_async())

    result = benchmark(run)
    assert result is None


# ═══════════════════════════════════════════════════════════════
# Combined Optimization Benchmarks
# ═══════════════════════════════════════════════════════════════


@pytest.mark.benchmark(group="combined")
def test_combined_cached(benchmark):
    """Benchmark combined schema + prompt + memory with caching."""
    from kaizen.performance import (
        SchemaCache,
        SchemaCacheConfig,
        PromptCache,
        PromptCacheConfig,
        MemoryContextCache,
        MemoryContextConfig,
    )

    schema_cache = SchemaCache(config=SchemaCacheConfig(max_size=100))
    prompt_cache = PromptCache(config=PromptCacheConfig(max_size=50))
    memory_cache = MemoryContextCache(config=MemoryContextConfig(max_sessions=20))

    # Pre-populate
    for i in range(10):
        schema_cache.get_or_compute(f"tool_{i}", lambda: {"name": f"tool_{i}"})

    def build_segment(name: str, data: Any) -> str:
        return f"[{name}]: {data}"

    def run():
        # Schema lookup
        schemas = [
            schema_cache.get_or_compute(f"tool_{i}", lambda: {"name": f"tool_{i}"})
            for i in range(5)
        ]

        # Prompt build
        prompt_cache.get_or_build(
            template_id="system",
            build_fn=lambda: f"Prompt with {len(schemas)} tools",
            static_parts=["system"],
            dynamic_parts={"tools": schemas},
        )

        # Memory context
        memory_cache.build_context_incremental(
            session_id="combined",
            segments={"history": ["msg1"], "facts": ["fact1"]},
            build_segment_fn=build_segment,
        )

    result = benchmark(run)
    assert result is None


@pytest.mark.benchmark(group="combined")
def test_combined_uncached(benchmark):
    """Benchmark combined operations without caching (baseline)."""

    def run():
        # Direct schema generation
        schemas = [{"name": f"tool_{i}"} for i in range(5)]

        # Direct prompt build
        _ = f"Prompt with {len(schemas)} tools"

        # Direct context build
        segments = {"history": ["msg1"], "facts": ["fact1"]}
        _ = "\n".join([f"[{k}]: {v}" for k, v in segments.items()])

    result = benchmark(run)
    assert result is None
