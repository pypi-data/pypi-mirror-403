"""
Unit tests for Memory Context Cache with Incremental Updates (TODO-199.3.2).

Tests the intelligent caching system for memory context that supports
incremental updates to avoid full context rebuilds.
"""

import threading
import time
from typing import Any, Dict

import pytest

from kaizen.performance.memory_context_cache import (
    MemoryContextCache,
    MemoryContextConfig,
    MemoryContextMetrics,
    SegmentEntry,
    SessionContext,
    get_memory_context_cache,
    set_memory_context_cache,
)


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════


def simple_segment_builder(name: str, data: Any) -> str:
    """Simple segment builder for testing."""
    if isinstance(data, list):
        return f"[{name}]\n" + "\n".join(str(item) for item in data)
    elif isinstance(data, dict):
        return f"[{name}]\n" + "\n".join(f"{k}: {v}" for k, v in data.items())
    else:
        return f"[{name}]\n{data}"


def slow_segment_builder(name: str, data: Any) -> str:
    """Slow segment builder to simulate expensive rendering."""
    time.sleep(0.001)  # 1ms delay
    return simple_segment_builder(name, data)


# ═══════════════════════════════════════════════════════════════
# MemoryContextMetrics Tests
# ═══════════════════════════════════════════════════════════════


class TestMemoryContextMetrics:
    """Tests for MemoryContextMetrics dataclass."""

    def test_empty_metrics(self):
        """Empty metrics should have zero rates."""
        metrics = MemoryContextMetrics()
        assert metrics.incremental_rate == 0.0
        assert metrics.segment_hit_rate == 0.0

    def test_incremental_rate_calculation(self):
        """Incremental rate should be calculated correctly."""
        metrics = MemoryContextMetrics(
            incremental_updates=75,
            full_rebuilds=25
        )
        assert metrics.incremental_rate == 0.75

    def test_segment_hit_rate_calculation(self):
        """Segment hit rate should be calculated correctly."""
        metrics = MemoryContextMetrics(
            segment_cache_hits=80,
            segment_cache_misses=20
        )
        assert metrics.segment_hit_rate == 0.8

    def test_to_dict(self):
        """to_dict should include all fields."""
        metrics = MemoryContextMetrics(
            context_builds=100,
            incremental_updates=80,
            full_rebuilds=20,
            segment_cache_hits=500,
            segment_cache_misses=100,
            sessions_cached=10,
            sessions_evicted=2,
            total_rebuild_time_saved_ms=1000.0,
        )
        result = metrics.to_dict()

        assert result["context_builds"] == 100
        assert result["incremental_updates"] == 80
        assert result["full_rebuilds"] == 20
        assert result["segment_cache_hits"] == 500
        assert result["segment_cache_misses"] == 100
        assert "incremental_rate" in result
        assert "segment_hit_rate" in result


# ═══════════════════════════════════════════════════════════════
# MemoryContextCache Basic Tests
# ═══════════════════════════════════════════════════════════════


class TestMemoryContextCacheBasic:
    """Basic tests for MemoryContextCache."""

    def test_empty_cache(self):
        """Empty cache should return None for lookups."""
        cache = MemoryContextCache()
        assert cache.get_cached_segment("session", "segment") is None
        assert cache.get_cached_context("session") is None
        assert cache.size() == 0

    def test_update_and_get_segment(self):
        """Update and get segment should work correctly."""
        cache = MemoryContextCache()

        cache.update_segment("session-1", "conversation", "Hello, World!")
        result = cache.get_cached_segment("session-1", "conversation")

        assert result == "Hello, World!"

    def test_multiple_segments_per_session(self):
        """Multiple segments in a session should be cached separately."""
        cache = MemoryContextCache()

        cache.update_segment("session-1", "conversation", "Conversation content")
        cache.update_segment("session-1", "knowledge", "Knowledge content")
        cache.update_segment("session-1", "facts", "Facts content")

        assert cache.get_cached_segment("session-1", "conversation") == "Conversation content"
        assert cache.get_cached_segment("session-1", "knowledge") == "Knowledge content"
        assert cache.get_cached_segment("session-1", "facts") == "Facts content"

    def test_multiple_sessions(self):
        """Multiple sessions should be cached separately."""
        cache = MemoryContextCache()

        cache.update_segment("session-1", "data", "Session 1 data")
        cache.update_segment("session-2", "data", "Session 2 data")

        assert cache.get_cached_segment("session-1", "data") == "Session 1 data"
        assert cache.get_cached_segment("session-2", "data") == "Session 2 data"
        assert cache.size() == 2

    def test_segment_update_returns_changed(self):
        """Update should return True when segment changes, False when unchanged."""
        cache = MemoryContextCache()

        # First update should indicate change
        changed = cache.update_segment("session-1", "data", "Initial content")
        assert changed is True

        # Same content should indicate no change
        changed = cache.update_segment("session-1", "data", "Initial content")
        assert changed is False

        # Different content should indicate change
        changed = cache.update_segment("session-1", "data", "Updated content")
        assert changed is True


# ═══════════════════════════════════════════════════════════════
# Incremental Build Tests
# ═══════════════════════════════════════════════════════════════


class TestIncrementalBuild:
    """Tests for incremental context building."""

    def test_first_build_is_full_rebuild(self):
        """First build should be a full rebuild."""
        cache = MemoryContextCache()

        segments = {
            "conversation": ["msg1", "msg2"],
            "knowledge": {"fact1": "value1"},
        }

        context, was_incremental = cache.build_context_incremental(
            "session-1",
            segments,
            simple_segment_builder,
        )

        assert was_incremental is False
        assert "[conversation]" in context
        assert "[knowledge]" in context

    def test_unchanged_segments_reused(self):
        """Unchanged segments should be reused from cache."""
        cache = MemoryContextCache()
        build_count = [0]

        def counting_builder(name: str, data: Any) -> str:
            build_count[0] += 1
            return simple_segment_builder(name, data)

        segments = {
            "conversation": ["msg1", "msg2"],
            "knowledge": {"fact1": "value1"},
        }

        # First build
        cache.build_context_incremental("session-1", segments, counting_builder)
        assert build_count[0] == 2

        # Second build with same data - should not rebuild
        _, was_incremental = cache.build_context_incremental(
            "session-1", segments, counting_builder
        )
        assert build_count[0] == 2  # No new builds
        assert was_incremental is True

    def test_only_changed_segments_rebuilt(self):
        """Only changed segments should be rebuilt."""
        cache = MemoryContextCache()
        built_segments = []

        def tracking_builder(name: str, data: Any) -> str:
            built_segments.append(name)
            return simple_segment_builder(name, data)

        segments_v1 = {
            "conversation": ["msg1"],
            "knowledge": {"fact1": "value1"},
            "facts": ["fact_a"],
        }

        # First build - all segments
        cache.build_context_incremental("session-1", segments_v1, tracking_builder)
        assert len(built_segments) == 3

        # Update only conversation
        built_segments.clear()
        segments_v2 = {
            "conversation": ["msg1", "msg2"],  # Changed
            "knowledge": {"fact1": "value1"},  # Unchanged
            "facts": ["fact_a"],  # Unchanged
        }

        _, was_incremental = cache.build_context_incremental(
            "session-1", segments_v2, tracking_builder
        )

        assert built_segments == ["conversation"]  # Only conversation rebuilt
        assert was_incremental is True

    def test_segment_order_preserved(self):
        """Segment order should be preserved in context."""
        cache = MemoryContextCache()

        segments = {
            "header": "HEADER",
            "body": "BODY",
            "footer": "FOOTER",
        }

        context, _ = cache.build_context_incremental(
            "session-1",
            segments,
            simple_segment_builder,
            segment_order=["header", "body", "footer"],
        )

        # Check order
        header_pos = context.find("[header]")
        body_pos = context.find("[body]")
        footer_pos = context.find("[footer]")

        assert header_pos < body_pos < footer_pos

    def test_custom_separator(self):
        """Custom separator should be used between segments."""
        cache = MemoryContextCache()

        segments = {"a": "A", "b": "B"}

        context, _ = cache.build_context_incremental(
            "session-1",
            segments,
            simple_segment_builder,
            separator="---",
            segment_order=["a", "b"],
        )

        assert "---" in context

    def test_get_changed_segments(self):
        """get_changed_segments should identify changed segments."""
        cache = MemoryContextCache()

        # Initial build
        segments_v1 = {
            "a": "content_a",
            "b": "content_b",
            "c": "content_c",
        }
        cache.build_context_incremental("session-1", segments_v1, simple_segment_builder)

        # Check changes
        segments_v2 = {
            "a": "content_a",  # Unchanged
            "b": "content_b_updated",  # Changed
            "c": "content_c",  # Unchanged
            "d": "content_d",  # New
        }

        changed = cache.get_changed_segments("session-1", segments_v2)
        assert set(changed) == {"b", "d"}

    def test_new_session_all_changed(self):
        """New session should report all segments as changed."""
        cache = MemoryContextCache()

        segments = {"a": "A", "b": "B"}
        changed = cache.get_changed_segments("new-session", segments)

        assert set(changed) == {"a", "b"}


# ═══════════════════════════════════════════════════════════════
# Cache Eviction Tests
# ═══════════════════════════════════════════════════════════════


class TestCacheEviction:
    """Tests for cache eviction."""

    def test_session_eviction_on_max_sessions(self):
        """Oldest sessions should be evicted when max reached."""
        config = MemoryContextConfig(max_sessions=3)
        cache = MemoryContextCache(config)

        cache.update_segment("session-1", "data", "Data 1")
        cache.update_segment("session-2", "data", "Data 2")
        cache.update_segment("session-3", "data", "Data 3")
        cache.update_segment("session-4", "data", "Data 4")  # Should evict session-1

        assert cache.get_cached_segment("session-1", "data") is None
        assert cache.get_cached_segment("session-2", "data") == "Data 2"
        assert cache.get_cached_segment("session-3", "data") == "Data 3"
        assert cache.get_cached_segment("session-4", "data") == "Data 4"

    def test_lru_order_updated_on_access(self):
        """Accessing a session should update LRU order."""
        config = MemoryContextConfig(max_sessions=3)
        cache = MemoryContextCache(config)

        cache.update_segment("session-1", "data", "Data 1")
        cache.update_segment("session-2", "data", "Data 2")
        cache.update_segment("session-3", "data", "Data 3")

        # Access session-1 to make it most recently used
        cache.get_cached_segment("session-1", "data")

        # Add session-4, should evict session-2 (now oldest)
        cache.update_segment("session-4", "data", "Data 4")

        assert cache.get_cached_segment("session-1", "data") == "Data 1"
        assert cache.get_cached_segment("session-2", "data") is None  # Evicted
        assert cache.get_cached_segment("session-3", "data") == "Data 3"
        assert cache.get_cached_segment("session-4", "data") == "Data 4"

    def test_segment_eviction_on_max_segments(self):
        """Oldest segments should be evicted when max reached."""
        config = MemoryContextConfig(max_segments_per_session=3)
        cache = MemoryContextCache(config)

        cache.update_segment("session-1", "seg-1", "Data 1")
        cache.update_segment("session-1", "seg-2", "Data 2")
        cache.update_segment("session-1", "seg-3", "Data 3")
        cache.update_segment("session-1", "seg-4", "Data 4")  # Should evict seg-1

        assert cache.get_cached_segment("session-1", "seg-1") is None
        assert cache.get_cached_segment("session-1", "seg-2") == "Data 2"

    def test_ttl_expiration(self):
        """Sessions should expire after TTL."""
        config = MemoryContextConfig(ttl_seconds=0.1)  # 100ms TTL
        cache = MemoryContextCache(config)

        cache.update_segment("session-1", "data", "Content")
        assert cache.get_cached_segment("session-1", "data") == "Content"

        # Wait for expiration
        time.sleep(0.15)

        assert cache.get_cached_segment("session-1", "data") is None


# ═══════════════════════════════════════════════════════════════
# Invalidation Tests
# ═══════════════════════════════════════════════════════════════


class TestInvalidation:
    """Tests for cache invalidation."""

    def test_invalidate_session(self):
        """Invalidating session should remove all its data."""
        cache = MemoryContextCache()

        cache.update_segment("session-1", "a", "A")
        cache.update_segment("session-1", "b", "B")
        cache.update_segment("session-2", "a", "A2")

        result = cache.invalidate_session("session-1")
        assert result is True

        assert cache.get_cached_segment("session-1", "a") is None
        assert cache.get_cached_segment("session-1", "b") is None
        assert cache.get_cached_segment("session-2", "a") == "A2"

    def test_invalidate_nonexistent_session(self):
        """Invalidating nonexistent session should return False."""
        cache = MemoryContextCache()
        result = cache.invalidate_session("nonexistent")
        assert result is False

    def test_invalidate_segment(self):
        """Invalidating segment should remove only that segment."""
        cache = MemoryContextCache()

        cache.update_segment("session-1", "a", "A")
        cache.update_segment("session-1", "b", "B")

        result = cache.invalidate_segment("session-1", "a")
        assert result is True

        assert cache.get_cached_segment("session-1", "a") is None
        assert cache.get_cached_segment("session-1", "b") == "B"

    def test_invalidate_nonexistent_segment(self):
        """Invalidating nonexistent segment should return False."""
        cache = MemoryContextCache()
        cache.update_segment("session-1", "a", "A")

        result = cache.invalidate_segment("session-1", "nonexistent")
        assert result is False

    def test_invalidate_all(self):
        """Invalidating all should clear entire cache."""
        cache = MemoryContextCache()

        cache.update_segment("session-1", "a", "A")
        cache.update_segment("session-2", "b", "B")

        count = cache.invalidate_all()
        assert count == 2
        assert cache.size() == 0


# ═══════════════════════════════════════════════════════════════
# Session Info Tests
# ═══════════════════════════════════════════════════════════════


class TestSessionInfo:
    """Tests for session information retrieval."""

    def test_get_session_info(self):
        """get_session_info should return session details."""
        cache = MemoryContextCache()

        cache.update_segment("session-1", "a", "Content A")
        cache.update_segment("session-1", "b", "Content B")

        info = cache.get_session_info("session-1")

        assert info is not None
        assert info["session_id"] == "session-1"
        assert info["segment_count"] == 2
        assert set(info["segments"]) == {"a", "b"}
        assert "created_at" in info
        assert "accessed_at" in info
        assert "total_size_bytes" in info

    def test_get_session_info_nonexistent(self):
        """get_session_info should return None for nonexistent session."""
        cache = MemoryContextCache()
        info = cache.get_session_info("nonexistent")
        assert info is None


# ═══════════════════════════════════════════════════════════════
# Metrics Tests
# ═══════════════════════════════════════════════════════════════


class TestMetrics:
    """Tests for metrics tracking."""

    def test_metrics_tracking(self):
        """Metrics should track builds and cache performance."""
        config = MemoryContextConfig(enable_metrics=True)
        cache = MemoryContextCache(config)

        segments = {"a": "A", "b": "B"}

        # First build - full rebuild
        cache.build_context_incremental("session-1", segments, simple_segment_builder)

        # Second build - incremental
        cache.build_context_incremental("session-1", segments, simple_segment_builder)

        # Third build with changes
        segments_changed = {"a": "A_new", "b": "B"}
        cache.build_context_incremental("session-1", segments_changed, simple_segment_builder)

        metrics = cache.get_metrics()

        assert metrics.context_builds == 3
        assert metrics.full_rebuilds >= 1
        assert metrics.incremental_updates >= 1

    def test_segment_hit_miss_tracking(self):
        """Metrics should track segment cache hits and misses."""
        cache = MemoryContextCache()

        # First update is a miss
        cache.update_segment("session-1", "data", "Content")

        # Same content is a hit
        cache.update_segment("session-1", "data", "Content")

        # Different content is a miss
        cache.update_segment("session-1", "data", "New Content")

        metrics = cache.get_metrics()
        assert metrics.segment_cache_hits >= 1
        assert metrics.segment_cache_misses >= 2

    def test_reset_metrics(self):
        """Reset metrics should clear counters."""
        cache = MemoryContextCache()
        cache.update_segment("session-1", "data", "Content")
        cache.update_segment("session-1", "data", "Content")

        cache.reset_metrics()
        metrics = cache.get_metrics()

        assert metrics.segment_cache_hits == 0
        assert metrics.segment_cache_misses == 0
        assert metrics.context_builds == 0


# ═══════════════════════════════════════════════════════════════
# Thread Safety Tests
# ═══════════════════════════════════════════════════════════════


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_session_access(self):
        """Cache should be thread-safe for concurrent access."""
        cache = MemoryContextCache(MemoryContextConfig(max_sessions=1000))
        errors = []

        def worker(thread_id: int):
            try:
                for i in range(50):
                    session_id = f"session_{thread_id}_{i % 10}"
                    segment_name = f"segment_{i % 5}"
                    content = f"Content from thread {thread_id}, iteration {i}"

                    cache.update_segment(session_id, segment_name, content)
                    result = cache.get_cached_segment(session_id, segment_name)

                    if result is None:
                        pass  # May have been evicted
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_incremental_builds(self):
        """Incremental builds should be thread-safe."""
        cache = MemoryContextCache()
        errors = []

        def worker(thread_id: int):
            try:
                session_id = f"session_{thread_id}"
                for i in range(20):
                    segments = {
                        "conversation": [f"msg_{i}"],
                        "knowledge": {"fact": f"value_{i}"},
                    }
                    cache.build_context_incremental(
                        session_id,
                        segments,
                        simple_segment_builder,
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ═══════════════════════════════════════════════════════════════
# Global Cache Tests
# ═══════════════════════════════════════════════════════════════


class TestGlobalMemoryContextCache:
    """Tests for global cache functions."""

    def test_get_memory_context_cache_creates_instance(self):
        """get_memory_context_cache should create singleton."""
        set_memory_context_cache(None)  # Reset

        cache = get_memory_context_cache()
        assert cache is not None
        assert isinstance(cache, MemoryContextCache)

    def test_set_memory_context_cache(self):
        """set_memory_context_cache should update global instance."""
        custom_cache = MemoryContextCache()
        set_memory_context_cache(custom_cache)

        assert get_memory_context_cache() is custom_cache

    def test_singleton_pattern(self):
        """get_memory_context_cache should return same instance."""
        set_memory_context_cache(None)  # Reset

        cache1 = get_memory_context_cache()
        cache2 = get_memory_context_cache()

        assert cache1 is cache2


# ═══════════════════════════════════════════════════════════════
# Performance Tests
# ═══════════════════════════════════════════════════════════════


class TestPerformance:
    """Performance tests for memory context cache."""

    def test_incremental_build_faster_than_full(self):
        """Incremental builds should be faster than full rebuilds."""
        cache = MemoryContextCache()

        # Create realistic segments
        segments = {
            "conversation": [f"Message {i}" for i in range(100)],
            "knowledge": {f"fact_{i}": f"value_{i}" for i in range(50)},
            "context": "A" * 1000,  # 1KB context
        }

        # First build (full)
        start = time.perf_counter()
        cache.build_context_incremental("session-1", segments, slow_segment_builder)
        full_build_time = time.perf_counter() - start

        # Second build (incremental - same data)
        start = time.perf_counter()
        _, was_incremental = cache.build_context_incremental(
            "session-1", segments, slow_segment_builder
        )
        incremental_time = time.perf_counter() - start

        assert was_incremental is True
        # Incremental should be at least 10x faster
        speedup = full_build_time / incremental_time if incremental_time > 0 else 100
        print(f"\nIncremental speedup: {speedup:.1f}x")
        assert speedup > 10, f"Incremental build not fast enough: {speedup:.1f}x"

    def test_high_cache_hit_rate(self):
        """Repeated builds should achieve high hit rate."""
        cache = MemoryContextCache()

        segments = {
            "conversation": ["msg1", "msg2", "msg3"],
            "knowledge": {"a": "b"},
            "facts": ["fact1", "fact2"],
        }

        # Multiple builds with same data
        for _ in range(100):
            cache.build_context_incremental("session-1", segments, simple_segment_builder)

        metrics = cache.get_metrics()

        # Should have high incremental rate
        assert metrics.incremental_rate > 0.95
        print(f"\nIncremental rate: {metrics.incremental_rate:.1%}")

    def test_segment_lookup_fast(self):
        """Segment lookups should be very fast."""
        cache = MemoryContextCache()

        # Set up segments
        for i in range(100):
            cache.update_segment("session-1", f"segment_{i}", f"Content {i}" * 100)

        # Warm up
        for _ in range(100):
            cache.get_cached_segment("session-1", "segment_50")

        # Measure
        start = time.perf_counter()
        iterations = 10000
        for _ in range(iterations):
            cache.get_cached_segment("session-1", "segment_50")
        duration = time.perf_counter() - start

        ops_per_sec = iterations / duration
        print(f"\nSegment lookup: {ops_per_sec:,.0f} ops/sec")

        # Should be at least 100K ops/sec
        assert ops_per_sec > 100000, f"Too slow: {ops_per_sec:.0f} ops/sec"

    def test_realistic_taod_cycle_simulation(self):
        """Simulate realistic TAOD cycle pattern."""
        cache = MemoryContextCache()

        # Simulate 50 TAOD cycles where only conversation changes
        base_knowledge = {f"fact_{i}": f"value_{i}" for i in range(20)}
        base_context = "System context " * 100

        build_count = [0]

        def counting_builder(name: str, data: Any) -> str:
            build_count[0] += 1
            return simple_segment_builder(name, data)

        conversation = []
        for cycle in range(50):
            # Conversation grows each cycle
            conversation.append(f"User: Message {cycle}")
            conversation.append(f"Assistant: Response {cycle}")

            segments = {
                "conversation": conversation.copy(),
                "knowledge": base_knowledge,  # Same each cycle
                "context": base_context,  # Same each cycle
            }

            cache.build_context_incremental(
                "session-1",
                segments,
                counting_builder,
                segment_order=["context", "knowledge", "conversation"],
            )

        # Only conversation should be rebuilt each cycle (except first)
        # First cycle: 3 builds, subsequent 49 cycles: 1 build each
        expected_builds = 3 + 49  # = 52
        assert build_count[0] == expected_builds, f"Expected {expected_builds}, got {build_count[0]}"

        metrics = cache.get_metrics()
        print(f"\nTAOD simulation: {metrics.incremental_rate:.1%} incremental rate")
        print(f"Builds performed: {build_count[0]} (vs {50 * 3} full rebuilds)")
