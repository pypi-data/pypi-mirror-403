"""
Unit tests for Tool Schema Cache (TODO-199.2.3).

Tests the LRU caching infrastructure for tool schemas.
"""

import threading
import time
from unittest.mock import MagicMock

import pytest

from kaizen.performance.schema_cache import (
    CacheEntry,
    CacheMetrics,
    SchemaCache,
    SchemaCacheConfig,
    ToolSchemaCache,
    get_schema_cache,
    set_schema_cache,
)


# ═══════════════════════════════════════════════════════════════
# CacheMetrics Tests
# ═══════════════════════════════════════════════════════════════


class TestCacheMetrics:
    """Tests for CacheMetrics dataclass."""

    def test_empty_metrics(self):
        """Empty metrics should have zero hit rate."""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Hit rate should be calculated correctly."""
        metrics = CacheMetrics(hits=75, misses=25)
        assert metrics.hit_rate == 0.75

    def test_to_dict(self):
        """to_dict should include all fields."""
        metrics = CacheMetrics(hits=10, misses=5, evictions=2)
        result = metrics.to_dict()

        assert result["hits"] == 10
        assert result["misses"] == 5
        assert result["evictions"] == 2
        assert "hit_rate" in result


# ═══════════════════════════════════════════════════════════════
# SchemaCache Tests
# ═══════════════════════════════════════════════════════════════


class TestSchemaCache:
    """Tests for SchemaCache."""

    def test_get_missing_key(self):
        """Getting missing key should return None."""
        cache = SchemaCache()
        assert cache.get("missing") is None

    def test_set_and_get(self):
        """Set and get should work correctly."""
        cache = SchemaCache()
        cache.set("key1", {"value": 1})

        result = cache.get("key1")
        assert result == {"value": 1}

    def test_lru_eviction(self):
        """Oldest entries should be evicted when max size reached."""
        config = SchemaCacheConfig(max_size=3)
        cache = SchemaCache(config)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Add one more, should evict key1
        cache.set("key4", "value4")

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_access_updates_order(self):
        """Accessing an entry should update its LRU position."""
        config = SchemaCacheConfig(max_size=3)
        cache = SchemaCache(config)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1, making it most recently used
        cache.get("key1")

        # Add new entry, should evict key2 (now oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_ttl_expiration(self):
        """Entries should expire after TTL."""
        config = SchemaCacheConfig(ttl_seconds=0.1)  # 100ms TTL
        cache = SchemaCache(config)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.15)

        assert cache.get("key1") is None

    def test_get_or_compute(self):
        """get_or_compute should compute on miss and cache result."""
        cache = SchemaCache()
        compute_count = [0]

        def compute():
            compute_count[0] += 1
            return {"computed": True}

        # First call computes
        result1 = cache.get_or_compute("key1", compute)
        assert result1 == {"computed": True}
        assert compute_count[0] == 1

        # Second call uses cache
        result2 = cache.get_or_compute("key1", compute)
        assert result2 == {"computed": True}
        assert compute_count[0] == 1  # Not recomputed

    def test_invalidate(self):
        """Invalidate should remove entry."""
        cache = SchemaCache()
        cache.set("key1", "value1")

        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None
        assert cache.invalidate("key1") is False  # Already removed

    def test_invalidate_all(self):
        """Invalidate all should clear cache."""
        cache = SchemaCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        count = cache.invalidate_all()
        assert count == 2
        assert cache.size() == 0

    def test_contains(self):
        """Contains should check without affecting LRU order."""
        cache = SchemaCache()
        cache.set("key1", "value1")

        assert cache.contains("key1") is True
        assert cache.contains("missing") is False

    def test_metrics_tracking(self):
        """Metrics should track hits, misses, evictions."""
        config = SchemaCacheConfig(max_size=2, enable_metrics=True)
        cache = SchemaCache(config)

        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("missing")  # Miss
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Eviction

        metrics = cache.get_metrics()
        assert metrics.hits == 1
        assert metrics.misses == 1
        assert metrics.evictions == 1
        assert metrics.current_size == 2

    def test_reset_metrics(self):
        """Reset metrics should clear counters."""
        cache = SchemaCache()
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("missing")

        cache.reset_metrics()
        metrics = cache.get_metrics()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.current_size == 1  # Size preserved

    def test_thread_safety(self):
        """Cache should be thread-safe."""
        cache = SchemaCache(SchemaCacheConfig(max_size=100))
        errors = []

        def worker(thread_id):
            try:
                for i in range(100):
                    key = f"thread_{thread_id}_key_{i}"
                    cache.set(key, {"value": i})
                    result = cache.get(key)
                    if result is None:
                        # May have been evicted
                        pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ═══════════════════════════════════════════════════════════════
# ToolSchemaCache Tests
# ═══════════════════════════════════════════════════════════════


class TestToolSchemaCache:
    """Tests for ToolSchemaCache."""

    def test_get_schema_key_simple(self):
        """Key generation should work for simple tool names."""
        cache = ToolSchemaCache()
        key = cache.get_schema_key("my_tool")
        assert key == "my_tool"

    def test_get_schema_key_with_definition(self):
        """Key should include definition hash when provided."""
        cache = ToolSchemaCache(hash_tool_definition=True)
        key1 = cache.get_schema_key("my_tool", {"version": 1})
        key2 = cache.get_schema_key("my_tool", {"version": 2})

        assert key1.startswith("my_tool:")
        assert key2.startswith("my_tool:")
        assert key1 != key2  # Different definitions = different keys

    def test_get_tool_schema(self):
        """get_tool_schema should return cached schema."""
        cache = ToolSchemaCache()
        schema = {"name": "test", "parameters": {}}

        cache.set_tool_schema("test_tool", schema)
        result = cache.get_tool_schema("test_tool")

        assert result == schema

    def test_get_tool_schema_with_compute(self):
        """get_tool_schema should compute when not cached."""
        cache = ToolSchemaCache()
        compute_count = [0]

        def compute():
            compute_count[0] += 1
            return {"name": "computed", "parameters": {}}

        result = cache.get_tool_schema("new_tool", compute_fn=compute)
        assert result["name"] == "computed"
        assert compute_count[0] == 1

        # Second call should use cache
        result2 = cache.get_tool_schema("new_tool", compute_fn=compute)
        assert compute_count[0] == 1

    def test_invalidate_tool(self):
        """invalidate_tool should remove all schemas for a tool."""
        cache = ToolSchemaCache()

        # Add multiple versions
        cache.set_tool_schema("tool1", {"v": 1}, {"version": 1})
        cache.set_tool_schema("tool1", {"v": 2}, {"version": 2})
        cache.set_tool_schema("tool2", {"v": 1})

        count = cache.invalidate_tool("tool1")
        assert count == 2

        assert cache.get_tool_schema("tool1", {"version": 1}) is None
        assert cache.get_tool_schema("tool1", {"version": 2}) is None
        assert cache.get_tool_schema("tool2") is not None


# ═══════════════════════════════════════════════════════════════
# Global Cache Tests
# ═══════════════════════════════════════════════════════════════


class TestGlobalSchemaCache:
    """Tests for global cache functions."""

    def test_get_schema_cache_creates_instance(self):
        """get_schema_cache should create singleton."""
        set_schema_cache(None)  # Reset

        cache = get_schema_cache()
        assert cache is not None
        assert isinstance(cache, ToolSchemaCache)

    def test_set_schema_cache(self):
        """set_schema_cache should update global instance."""
        custom_cache = ToolSchemaCache()
        set_schema_cache(custom_cache)

        assert get_schema_cache() is custom_cache


# ═══════════════════════════════════════════════════════════════
# Performance Tests
# ═══════════════════════════════════════════════════════════════


class TestSchemaCachePerformance:
    """Performance tests for schema cache."""

    def test_cached_access_fast(self):
        """Cached access should be very fast."""
        cache = SchemaCache()
        cache.set("key", {"schema": "value"})

        # Warm up
        for _ in range(100):
            cache.get("key")

        # Measure
        start = time.perf_counter()
        iterations = 10000
        for _ in range(iterations):
            cache.get("key")
        duration = time.perf_counter() - start

        ops_per_sec = iterations / duration
        print(f"\nCache access: {ops_per_sec:,.0f} ops/sec")

        # Should be able to do at least 100K ops/sec
        assert ops_per_sec > 100000, f"Too slow: {ops_per_sec:.0f} ops/sec"

    def test_get_or_compute_speedup(self):
        """get_or_compute should be much faster than recomputing."""
        cache = SchemaCache()

        def expensive_compute():
            time.sleep(0.001)  # 1ms computation
            return {"result": "computed"}

        # First call computes
        start = time.perf_counter()
        cache.get_or_compute("key", expensive_compute)
        compute_time = time.perf_counter() - start

        # Subsequent calls use cache
        start = time.perf_counter()
        for _ in range(100):
            cache.get_or_compute("key", expensive_compute)
        cached_time = time.perf_counter() - start

        # Cached should be at least 10x faster than computing 100 times
        expected_compute_time = compute_time * 100
        speedup = expected_compute_time / cached_time
        print(f"\nCache speedup: {speedup:.0f}x")

        assert speedup > 10, f"Speedup too low: {speedup:.1f}x"
