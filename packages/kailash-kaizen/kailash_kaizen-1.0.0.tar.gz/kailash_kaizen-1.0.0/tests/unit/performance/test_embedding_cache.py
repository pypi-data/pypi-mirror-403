"""
Unit tests for Embedding Cache (TODO-199.2.2).

Tests the LRU caching infrastructure for embedding vectors.
"""

import threading
import time
from typing import List

import pytest

from kaizen.performance.embedding_cache import (
    EmbeddingCache,
    EmbeddingCacheConfig,
    EmbeddingCacheMetrics,
    EmbeddingEntry,
    get_embedding_cache,
    set_embedding_cache,
)


# ═══════════════════════════════════════════════════════════════
# Mock Embedding Provider
# ═══════════════════════════════════════════════════════════════


class MockEmbeddingProvider:
    """Mock embedding provider for testing."""

    def __init__(self, dimensions: int = 384, delay_ms: float = 10.0):
        self.dimensions = dimensions
        self.delay_ms = delay_ms
        self.call_count = 0

    def embed(self, text: str) -> List[float]:
        """Generate mock embedding."""
        self.call_count += 1
        time.sleep(self.delay_ms / 1000)

        # Generate deterministic embedding based on text hash
        import hashlib
        hash_val = int(hashlib.md5(text.encode(), usedforsecurity=False).hexdigest(), 16)
        
        # Create normalized vector
        vector = [(hash_val >> (i * 8) & 0xFF) / 255.0 for i in range(self.dimensions)]
        return vector


# ═══════════════════════════════════════════════════════════════
# EmbeddingCacheMetrics Tests
# ═══════════════════════════════════════════════════════════════


class TestEmbeddingCacheMetrics:
    """Tests for EmbeddingCacheMetrics dataclass."""

    def test_empty_metrics(self):
        """Empty metrics should have zero hit rate."""
        metrics = EmbeddingCacheMetrics()
        assert metrics.hit_rate == 0.0
        assert metrics.api_savings_rate == 0.0

    def test_hit_rate_calculation(self):
        """Hit rate should be calculated correctly."""
        metrics = EmbeddingCacheMetrics(hits=80, misses=20)
        assert metrics.hit_rate == 0.8

    def test_api_savings_calculation(self):
        """API savings rate should equal hit rate."""
        metrics = EmbeddingCacheMetrics(hits=75, misses=25)
        assert metrics.api_savings_rate == 0.75

    def test_to_dict(self):
        """to_dict should include all fields."""
        metrics = EmbeddingCacheMetrics(
            hits=100,
            misses=50,
            evictions=10,
            total_api_calls_saved=100,
        )
        result = metrics.to_dict()

        assert result["hits"] == 100
        assert result["misses"] == 50
        assert result["evictions"] == 10
        assert result["total_api_calls_saved"] == 100
        assert "hit_rate" in result
        assert "api_savings_rate" in result


# ═══════════════════════════════════════════════════════════════
# EmbeddingCache Tests
# ═══════════════════════════════════════════════════════════════


class TestEmbeddingCache:
    """Tests for EmbeddingCache."""

    def test_get_missing_key(self):
        """Getting missing key should return None."""
        cache = EmbeddingCache()
        assert cache.get("missing text", "model") is None

    def test_set_and_get(self):
        """Set and get should work correctly."""
        cache = EmbeddingCache()
        vector = [0.1, 0.2, 0.3, 0.4]

        cache.set("hello world", vector, "text-embedding-3-small")
        result = cache.get("hello world", "text-embedding-3-small")

        assert result == vector

    def test_different_models_different_entries(self):
        """Same text with different models should be cached separately."""
        cache = EmbeddingCache()
        vector1 = [0.1, 0.2, 0.3]
        vector2 = [0.4, 0.5, 0.6]

        cache.set("hello", vector1, "model-a")
        cache.set("hello", vector2, "model-b")

        assert cache.get("hello", "model-a") == vector1
        assert cache.get("hello", "model-b") == vector2

    def test_different_providers_different_entries(self):
        """Same text with different providers should be cached separately."""
        cache = EmbeddingCache()
        vector1 = [0.1, 0.2, 0.3]
        vector2 = [0.4, 0.5, 0.6]

        cache.set("hello", vector1, "model", "openai")
        cache.set("hello", vector2, "model", "azure")

        assert cache.get("hello", "model", "openai") == vector1
        assert cache.get("hello", "model", "azure") == vector2

    def test_lru_eviction(self):
        """Oldest entries should be evicted when max size reached."""
        config = EmbeddingCacheConfig(max_size=3)
        cache = EmbeddingCache(config)

        cache.set("text1", [0.1], "model")
        cache.set("text2", [0.2], "model")
        cache.set("text3", [0.3], "model")
        cache.set("text4", [0.4], "model")  # Should evict text1

        assert cache.get("text1", "model") is None  # Evicted
        assert cache.get("text2", "model") == [0.2]
        assert cache.get("text3", "model") == [0.3]
        assert cache.get("text4", "model") == [0.4]

    def test_lru_access_updates_order(self):
        """Accessing an entry should update its LRU position."""
        config = EmbeddingCacheConfig(max_size=3)
        cache = EmbeddingCache(config)

        cache.set("text1", [0.1], "model")
        cache.set("text2", [0.2], "model")
        cache.set("text3", [0.3], "model")

        # Access text1, making it most recently used
        cache.get("text1", "model")

        # Add new entry, should evict text2 (now oldest)
        cache.set("text4", [0.4], "model")

        assert cache.get("text1", "model") == [0.1]  # Still present
        assert cache.get("text2", "model") is None  # Evicted
        assert cache.get("text3", "model") == [0.3]
        assert cache.get("text4", "model") == [0.4]

    def test_ttl_expiration(self):
        """Entries should expire after TTL."""
        config = EmbeddingCacheConfig(ttl_seconds=0.1)  # 100ms TTL
        cache = EmbeddingCache(config)

        cache.set("text", [0.1, 0.2], "model")
        assert cache.get("text", "model") == [0.1, 0.2]

        # Wait for expiration
        time.sleep(0.15)

        assert cache.get("text", "model") is None

    def test_whitespace_normalization(self):
        """Whitespace should be normalized before hashing."""
        config = EmbeddingCacheConfig(normalize_text=True)
        cache = EmbeddingCache(config)

        cache.set("hello   world", [0.1, 0.2], "model")

        # Different whitespace should hit same cache entry
        assert cache.get("hello world", "model") == [0.1, 0.2]
        assert cache.get("hello\t\nworld", "model") == [0.1, 0.2]

    def test_max_text_length_skip(self):
        """Text exceeding max length should skip caching."""
        config = EmbeddingCacheConfig(max_text_length=10)
        cache = EmbeddingCache(config)

        long_text = "a" * 100
        cache.set(long_text, [0.1], "model")

        assert cache.get(long_text, "model") is None
        assert cache.size() == 0

    def test_get_or_compute(self):
        """get_or_compute should compute on miss and cache result."""
        cache = EmbeddingCache()
        provider = MockEmbeddingProvider()

        # First call computes
        result1 = cache.get_or_compute(
            "test text",
            "model",
            lambda: provider.embed("test text"),
        )
        assert provider.call_count == 1

        # Second call uses cache
        result2 = cache.get_or_compute(
            "test text",
            "model",
            lambda: provider.embed("test text"),
        )
        assert provider.call_count == 1  # Not recomputed
        assert result1 == result2

    def test_batch_operations(self):
        """Batch get and set should work correctly."""
        cache = EmbeddingCache()

        # Set batch
        texts = ["text1", "text2", "text3"]
        vectors = [[0.1], [0.2], [0.3]]
        cache.set_batch(texts, vectors, "model")

        # Get batch
        results, uncached = cache.get_batch(["text1", "text2", "missing"], "model")

        assert results[0] == [0.1]
        assert results[1] == [0.2]
        assert results[2] is None
        assert uncached == [2]

    def test_batch_set_length_mismatch(self):
        """Batch set should raise error on length mismatch."""
        cache = EmbeddingCache()

        with pytest.raises(ValueError):
            cache.set_batch(["text1", "text2"], [[0.1]], "model")

    def test_invalidate(self):
        """Invalidate should remove entry."""
        cache = EmbeddingCache()
        cache.set("text", [0.1], "model")

        assert cache.invalidate("text", "model") is True
        assert cache.get("text", "model") is None
        assert cache.invalidate("text", "model") is False

    def test_invalidate_model(self):
        """Invalidate model should remove all entries for that model."""
        cache = EmbeddingCache()
        cache.set("text1", [0.1], "model-a")
        cache.set("text2", [0.2], "model-a")
        cache.set("text3", [0.3], "model-b")

        count = cache.invalidate_model("model-a")
        assert count == 2
        assert cache.get("text1", "model-a") is None
        assert cache.get("text2", "model-a") is None
        assert cache.get("text3", "model-b") == [0.3]

    def test_invalidate_all(self):
        """Invalidate all should clear cache."""
        cache = EmbeddingCache()
        cache.set("text1", [0.1], "model")
        cache.set("text2", [0.2], "model")

        count = cache.invalidate_all()
        assert count == 2
        assert cache.size() == 0

    def test_contains(self):
        """Contains should check without affecting LRU order."""
        cache = EmbeddingCache()
        cache.set("text", [0.1], "model")

        assert cache.contains("text", "model") is True
        assert cache.contains("missing", "model") is False

    def test_metrics_tracking(self):
        """Metrics should track hits, misses, evictions."""
        config = EmbeddingCacheConfig(max_size=2, enable_metrics=True)
        cache = EmbeddingCache(config)

        cache.set("text1", [0.1], "model")
        cache.get("text1", "model")  # Hit
        cache.get("missing", "model")  # Miss
        cache.set("text2", [0.2], "model")
        cache.set("text3", [0.3], "model")  # Eviction

        metrics = cache.get_metrics()
        assert metrics.hits == 1
        assert metrics.misses == 1
        assert metrics.evictions == 1
        assert metrics.current_size == 2
        assert metrics.total_api_calls_saved == 1

    def test_reset_metrics(self):
        """Reset metrics should clear counters."""
        cache = EmbeddingCache()
        cache.set("text", [0.1], "model")
        cache.get("text", "model")
        cache.get("missing", "model")

        cache.reset_metrics()
        metrics = cache.get_metrics()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.current_size == 1

    def test_thread_safety(self):
        """Cache should be thread-safe."""
        cache = EmbeddingCache(EmbeddingCacheConfig(max_size=1000))
        errors = []

        def worker(thread_id: int):
            try:
                for i in range(100):
                    text = f"thread_{thread_id}_text_{i}"
                    vector = [float(thread_id * 100 + i)]
                    cache.set(text, vector, "model")
                    result = cache.get(text, "model")
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


# ═══════════════════════════════════════════════════════════════
# Global Cache Tests
# ═══════════════════════════════════════════════════════════════


class TestGlobalEmbeddingCache:
    """Tests for global cache functions."""

    def test_get_embedding_cache_creates_instance(self):
        """get_embedding_cache should create singleton."""
        set_embedding_cache(None)  # Reset

        cache = get_embedding_cache()
        assert cache is not None
        assert isinstance(cache, EmbeddingCache)

    def test_set_embedding_cache(self):
        """set_embedding_cache should update global instance."""
        custom_cache = EmbeddingCache()
        set_embedding_cache(custom_cache)

        assert get_embedding_cache() is custom_cache


# ═══════════════════════════════════════════════════════════════
# Performance Tests
# ═══════════════════════════════════════════════════════════════


class TestEmbeddingCachePerformance:
    """Performance tests for embedding cache."""

    def test_cached_access_fast(self):
        """Cached access should be very fast."""
        cache = EmbeddingCache()
        vector = [float(i) / 384 for i in range(384)]  # 384-dim vector
        cache.set("test text", vector, "model")

        # Warm up
        for _ in range(100):
            cache.get("test text", "model")

        # Measure
        start = time.perf_counter()
        iterations = 10000
        for _ in range(iterations):
            cache.get("test text", "model")
        duration = time.perf_counter() - start

        ops_per_sec = iterations / duration
        print(f"\nEmbedding cache access: {ops_per_sec:,.0f} ops/sec")

        # Should be able to do at least 50K ops/sec
        assert ops_per_sec > 50000, f"Too slow: {ops_per_sec:.0f} ops/sec"

    def test_api_call_savings(self):
        """Cache should save significant API calls."""
        cache = EmbeddingCache()
        provider = MockEmbeddingProvider(delay_ms=10)

        # Simulate workload with repeated texts
        texts = ["query 1", "query 2", "query 3"] * 100

        for text in texts:
            cache.get_or_compute(
                text, "model", lambda t=text: provider.embed(t)
            )

        metrics = cache.get_metrics()

        # Should have high hit rate (texts repeated 100x)
        assert metrics.hit_rate > 0.95
        assert metrics.total_api_calls_saved > 290  # ~297 saved

        print(f"\nHit rate: {metrics.hit_rate:.1%}")
        print(f"API calls saved: {metrics.total_api_calls_saved}")

    def test_speedup_vs_recompute(self):
        """Cache should be much faster than recomputing."""
        cache = EmbeddingCache()
        provider = MockEmbeddingProvider(delay_ms=5)

        text = "test embedding text"

        # First call computes
        start = time.perf_counter()
        cache.get_or_compute(text, "model", lambda: provider.embed(text))
        compute_time = time.perf_counter() - start

        # Subsequent calls use cache
        start = time.perf_counter()
        for _ in range(100):
            cache.get_or_compute(text, "model", lambda: provider.embed(text))
        cached_time = time.perf_counter() - start

        # Cached should be at least 50x faster
        expected_time = compute_time * 100
        speedup = expected_time / cached_time
        print(f"\nCache speedup: {speedup:.0f}x")

        assert speedup > 50, f"Speedup too low: {speedup:.1f}x"
