"""
Unit tests for System Prompt Cache (TODO-199.3.1).

Tests the LRU caching infrastructure for system prompts.
"""

import threading
import time
from typing import Dict, List

import pytest

from kaizen.performance.prompt_cache import (
    PromptCache,
    PromptCacheConfig,
    PromptCacheMetrics,
    PromptEntry,
    get_prompt_cache,
    set_prompt_cache,
)


# ═══════════════════════════════════════════════════════════════
# PromptCacheMetrics Tests
# ═══════════════════════════════════════════════════════════════


class TestPromptCacheMetrics:
    """Tests for PromptCacheMetrics dataclass."""

    def test_empty_metrics(self):
        """Empty metrics should have zero hit rate."""
        metrics = PromptCacheMetrics()
        assert metrics.hit_rate == 0.0
        assert metrics.avg_build_time_saved_ms == 0.0

    def test_hit_rate_calculation(self):
        """Hit rate should be calculated correctly."""
        metrics = PromptCacheMetrics(hits=80, misses=20)
        assert metrics.hit_rate == 0.8

    def test_avg_build_time_saved_calculation(self):
        """Average build time saved should be calculated correctly."""
        metrics = PromptCacheMetrics(
            hits=100,
            misses=10,
            total_build_time_ms=100.0  # 10ms per miss
        )
        # Average build per miss = 100/10 = 10ms
        # Saved = 10ms * 100 hits = 1000ms
        assert metrics.avg_build_time_saved_ms == 1000.0

    def test_avg_build_time_saved_no_misses(self):
        """Average build time saved should be 0 with no misses."""
        metrics = PromptCacheMetrics(hits=100, misses=0, total_build_time_ms=0)
        assert metrics.avg_build_time_saved_ms == 0.0

    def test_avg_build_time_saved_no_hits(self):
        """Average build time saved should be 0 with no hits."""
        metrics = PromptCacheMetrics(hits=0, misses=10, total_build_time_ms=100.0)
        assert metrics.avg_build_time_saved_ms == 0.0

    def test_to_dict(self):
        """to_dict should include all fields."""
        metrics = PromptCacheMetrics(
            hits=100,
            misses=50,
            evictions=10,
            expirations=5,
            static_hits=60,
            template_hits=40,
            total_build_time_ms=500.0,
        )
        result = metrics.to_dict()

        assert result["hits"] == 100
        assert result["misses"] == 50
        assert result["evictions"] == 10
        assert result["expirations"] == 5
        assert result["static_hits"] == 60
        assert result["template_hits"] == 40
        assert "hit_rate" in result
        assert "avg_build_time_saved_ms" in result


# ═══════════════════════════════════════════════════════════════
# PromptCache Tests
# ═══════════════════════════════════════════════════════════════


class TestPromptCache:
    """Tests for PromptCache."""

    def test_get_missing_key(self):
        """Getting missing key should return None."""
        cache = PromptCache()
        assert cache.get("missing_template", "some_hash") is None

    def test_set_and_get(self):
        """Set and get should work correctly."""
        cache = PromptCache()
        prompt = "You are a helpful assistant."

        cache.set("system_prompt", "config_123", prompt)
        result = cache.get("system_prompt", "config_123")

        assert result == prompt

    def test_different_configs_different_entries(self):
        """Same template with different configs should be cached separately."""
        cache = PromptCache()
        prompt1 = "Config A prompt"
        prompt2 = "Config B prompt"

        cache.set("template", "config_a", prompt1)
        cache.set("template", "config_b", prompt2)

        assert cache.get("template", "config_a") == prompt1
        assert cache.get("template", "config_b") == prompt2

    def test_lru_eviction(self):
        """Oldest entries should be evicted when max size reached."""
        config = PromptCacheConfig(max_size=3)
        cache = PromptCache(config)

        cache.set("t1", "h1", "prompt1")
        cache.set("t2", "h2", "prompt2")
        cache.set("t3", "h3", "prompt3")
        cache.set("t4", "h4", "prompt4")  # Should evict t1

        assert cache.get("t1", "h1") is None  # Evicted
        assert cache.get("t2", "h2") == "prompt2"
        assert cache.get("t3", "h3") == "prompt3"
        assert cache.get("t4", "h4") == "prompt4"

    def test_lru_access_updates_order(self):
        """Accessing an entry should update its LRU position."""
        config = PromptCacheConfig(max_size=3)
        cache = PromptCache(config)

        cache.set("t1", "h1", "prompt1")
        cache.set("t2", "h2", "prompt2")
        cache.set("t3", "h3", "prompt3")

        # Access t1, making it most recently used
        cache.get("t1", "h1")

        # Add new entry, should evict t2 (now oldest)
        cache.set("t4", "h4", "prompt4")

        assert cache.get("t1", "h1") == "prompt1"  # Still present
        assert cache.get("t2", "h2") is None  # Evicted
        assert cache.get("t3", "h3") == "prompt3"
        assert cache.get("t4", "h4") == "prompt4"

    def test_ttl_expiration(self):
        """Entries should expire after TTL."""
        config = PromptCacheConfig(ttl_seconds=0.1)  # 100ms TTL
        cache = PromptCache(config)

        cache.set("template", "hash", "prompt content")
        assert cache.get("template", "hash") == "prompt content"

        # Wait for expiration
        time.sleep(0.15)

        assert cache.get("template", "hash") is None

    def test_no_ttl_expiration(self):
        """Entries should not expire when TTL is None."""
        config = PromptCacheConfig(ttl_seconds=None)
        cache = PromptCache(config)

        cache.set("template", "hash", "prompt content")
        assert cache.get("template", "hash") == "prompt content"

        # Even after a short sleep, should still be there
        time.sleep(0.05)
        assert cache.get("template", "hash") == "prompt content"

    def test_static_flag(self):
        """Static flag should be stored correctly."""
        cache = PromptCache()

        cache.set("static_prompt", "hash", "Static content", is_static=True)
        cache.set("dynamic_prompt", "hash", "Dynamic content", is_static=False)

        # Both should be retrievable
        assert cache.get("static_prompt", "hash") == "Static content"
        assert cache.get("dynamic_prompt", "hash") == "Dynamic content"

    def test_get_or_build_cache_miss(self):
        """get_or_build should build and cache on miss."""
        cache = PromptCache()
        build_count = [0]

        def build():
            build_count[0] += 1
            return "Built prompt"

        result = cache.get_or_build("template", build)
        assert result == "Built prompt"
        assert build_count[0] == 1

    def test_get_or_build_cache_hit(self):
        """get_or_build should return cached value on hit."""
        cache = PromptCache()
        build_count = [0]

        def build():
            build_count[0] += 1
            return "Built prompt"

        # First call builds
        result1 = cache.get_or_build("template", build)
        assert build_count[0] == 1

        # Second call uses cache
        result2 = cache.get_or_build("template", build)
        assert build_count[0] == 1  # Not rebuilt
        assert result1 == result2

    def test_get_or_build_with_parts(self):
        """get_or_build should use static and dynamic parts for hash."""
        cache = PromptCache()

        result1 = cache.get_or_build(
            "template",
            lambda: "Prompt A",
            static_parts=["role", "capabilities"],
            dynamic_parts={"tools": ["tool1", "tool2"]},
        )

        result2 = cache.get_or_build(
            "template",
            lambda: "Prompt B",
            static_parts=["role", "capabilities"],
            dynamic_parts={"tools": ["tool1", "tool2"]},  # Same parts
        )

        # Same parts should hit cache
        assert result1 == result2 == "Prompt A"

    def test_get_or_build_different_dynamic_parts(self):
        """Different dynamic parts should create different cache entries."""
        cache = PromptCache()

        result1 = cache.get_or_build(
            "template",
            lambda: "Prompt A",
            dynamic_parts={"tools": ["tool1"]},
        )

        result2 = cache.get_or_build(
            "template",
            lambda: "Prompt B",
            dynamic_parts={"tools": ["tool2"]},  # Different tools
        )

        # Different parts should not hit cache
        assert result1 == "Prompt A"
        assert result2 == "Prompt B"

    def test_template_part_caching(self):
        """Template parts should be cached and retrievable."""
        cache = PromptCache()

        cache.cache_template_part("role", "You are a helpful assistant.")
        cache.cache_template_part("capabilities", "You can search and analyze data.")

        assert cache.get_template_part("role") == "You are a helpful assistant."
        assert cache.get_template_part("capabilities") == "You can search and analyze data."
        assert cache.get_template_part("missing") is None

    def test_build_from_parts(self):
        """build_from_parts should combine cached parts."""
        cache = PromptCache()

        cache.cache_template_part("role", "You are a helpful assistant.")
        cache.cache_template_part("capabilities", "You can search and analyze data.")
        cache.cache_template_part("constraints", "Be concise and accurate.")

        result = cache.build_from_parts(
            "combined_template",
            ["role", "capabilities", "constraints"],
        )

        expected = "\n\n".join([
            "You are a helpful assistant.",
            "You can search and analyze data.",
            "Be concise and accurate.",
        ])
        assert result == expected

    def test_build_from_parts_custom_separator(self):
        """build_from_parts should use custom separator."""
        cache = PromptCache()

        cache.cache_template_part("part1", "First")
        cache.cache_template_part("part2", "Second")

        result = cache.build_from_parts(
            "template",
            ["part1", "part2"],
            separator="\n---\n",
        )

        assert result == "First\n---\nSecond"

    def test_build_from_parts_missing_part(self):
        """build_from_parts should return None if any part is missing."""
        cache = PromptCache()

        cache.cache_template_part("part1", "First")
        # part2 is not cached

        result = cache.build_from_parts("template", ["part1", "part2"])
        assert result is None

    def test_invalidate_specific(self):
        """Invalidate should remove specific entry."""
        cache = PromptCache()
        cache.set("template", "hash1", "prompt1")
        cache.set("template", "hash2", "prompt2")

        count = cache.invalidate("template", "hash1")
        assert count == 1
        assert cache.get("template", "hash1") is None
        assert cache.get("template", "hash2") == "prompt2"

    def test_invalidate_template(self):
        """Invalidate should remove all entries for a template."""
        cache = PromptCache()
        cache.set("template_a", "hash1", "prompt1")
        cache.set("template_a", "hash2", "prompt2")
        cache.set("template_b", "hash3", "prompt3")

        count = cache.invalidate("template_a")
        assert count == 2
        assert cache.get("template_a", "hash1") is None
        assert cache.get("template_a", "hash2") is None
        assert cache.get("template_b", "hash3") == "prompt3"

    def test_invalidate_all(self):
        """Invalidate all should clear cache."""
        cache = PromptCache()
        cache.set("t1", "h1", "prompt1")
        cache.set("t2", "h2", "prompt2")
        cache.cache_template_part("part1", "content")

        count = cache.invalidate_all()
        assert count == 2
        assert cache.size() == 0
        assert cache.get_template_part("part1") is None

    def test_size(self):
        """Size should return current cache size."""
        cache = PromptCache()
        assert cache.size() == 0

        cache.set("t1", "h1", "prompt1")
        assert cache.size() == 1

        cache.set("t2", "h2", "prompt2")
        assert cache.size() == 2

    def test_metrics_tracking(self):
        """Metrics should track hits, misses, evictions."""
        config = PromptCacheConfig(max_size=2, enable_metrics=True)
        cache = PromptCache(config)

        cache.set("t1", "h1", "prompt1", is_static=True)
        cache.get("t1", "h1")  # Hit (static)
        cache.get("missing", "h")  # Miss
        cache.set("t2", "h2", "prompt2", is_static=False)
        cache.get("t2", "h2")  # Hit (template)
        cache.set("t3", "h3", "prompt3")  # Eviction

        metrics = cache.get_metrics()
        assert metrics.hits == 2
        assert metrics.misses == 1
        assert metrics.evictions == 1
        assert metrics.current_size == 2
        assert metrics.static_hits == 1
        assert metrics.template_hits == 1

    def test_metrics_disabled(self):
        """Metrics should not be tracked when disabled."""
        config = PromptCacheConfig(enable_metrics=False)
        cache = PromptCache(config)

        cache.set("t1", "h1", "prompt1")
        cache.get("t1", "h1")
        cache.get("missing", "h")

        # Metrics still accessible but counters won't be updated by operations
        metrics = cache.get_metrics()
        # Current size is still tracked for internal operations
        assert metrics.current_size == 1

    def test_reset_metrics(self):
        """Reset metrics should clear counters."""
        cache = PromptCache()
        cache.set("t1", "h1", "prompt1")
        cache.get("t1", "h1")
        cache.get("missing", "h")

        cache.reset_metrics()
        metrics = cache.get_metrics()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.current_size == 1  # Size preserved

    def test_thread_safety(self):
        """Cache should be thread-safe."""
        cache = PromptCache(PromptCacheConfig(max_size=1000))
        errors = []

        def worker(thread_id: int):
            try:
                for i in range(100):
                    template_id = f"thread_{thread_id}_template_{i}"
                    config_hash = f"hash_{i}"
                    content = f"Prompt content {thread_id}_{i}"
                    cache.set(template_id, config_hash, content)
                    result = cache.get(template_id, config_hash)
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

    def test_compute_config_hash_deterministic(self):
        """Config hash should be deterministic for same inputs."""
        cache = PromptCache()

        hash1 = cache._compute_config_hash(
            static_parts=["a", "b"],
            dynamic_parts={"x": 1, "y": 2}
        )
        hash2 = cache._compute_config_hash(
            static_parts=["a", "b"],
            dynamic_parts={"x": 1, "y": 2}
        )

        assert hash1 == hash2

    def test_compute_config_hash_order_independent(self):
        """Config hash should be independent of input order."""
        cache = PromptCache()

        hash1 = cache._compute_config_hash(
            static_parts=["a", "b"],
            dynamic_parts={"x": 1, "y": 2}
        )
        hash2 = cache._compute_config_hash(
            static_parts=["b", "a"],  # Different order
            dynamic_parts={"y": 2, "x": 1}  # Different order
        )

        assert hash1 == hash2


# ═══════════════════════════════════════════════════════════════
# Global Cache Tests
# ═══════════════════════════════════════════════════════════════


class TestGlobalPromptCache:
    """Tests for global cache functions."""

    def test_get_prompt_cache_creates_instance(self):
        """get_prompt_cache should create singleton."""
        set_prompt_cache(None)  # Reset

        cache = get_prompt_cache()
        assert cache is not None
        assert isinstance(cache, PromptCache)

    def test_set_prompt_cache(self):
        """set_prompt_cache should update global instance."""
        custom_cache = PromptCache()
        set_prompt_cache(custom_cache)

        assert get_prompt_cache() is custom_cache

    def test_singleton_pattern(self):
        """get_prompt_cache should return same instance."""
        set_prompt_cache(None)  # Reset

        cache1 = get_prompt_cache()
        cache2 = get_prompt_cache()

        assert cache1 is cache2


# ═══════════════════════════════════════════════════════════════
# Performance Tests
# ═══════════════════════════════════════════════════════════════


class TestPromptCachePerformance:
    """Performance tests for prompt cache."""

    def test_cached_access_fast(self):
        """Cached access should be very fast."""
        cache = PromptCache()
        # Simulate a system prompt (typically 500-2000 chars)
        prompt = "You are a helpful AI assistant. " * 50
        cache.set("system_prompt", "config_hash", prompt)

        # Warm up
        for _ in range(100):
            cache.get("system_prompt", "config_hash")

        # Measure
        start = time.perf_counter()
        iterations = 10000
        for _ in range(iterations):
            cache.get("system_prompt", "config_hash")
        duration = time.perf_counter() - start

        ops_per_sec = iterations / duration
        print(f"\nPrompt cache access: {ops_per_sec:,.0f} ops/sec")

        # Should be able to do at least 100K ops/sec
        assert ops_per_sec > 100000, f"Too slow: {ops_per_sec:.0f} ops/sec"

    def test_build_time_savings(self):
        """Cache should save significant build time."""
        cache = PromptCache()

        def expensive_build():
            time.sleep(0.001)  # 1ms build time
            return "Built system prompt with many components..."

        # First call builds
        start = time.perf_counter()
        cache.get_or_build("template", expensive_build)
        build_time = time.perf_counter() - start

        # Subsequent calls use cache
        start = time.perf_counter()
        for _ in range(100):
            cache.get_or_build("template", expensive_build)
        cached_time = time.perf_counter() - start

        # Cached should be at least 50x faster than rebuilding
        expected_time = build_time * 100
        speedup = expected_time / cached_time
        print(f"\nCache speedup: {speedup:.0f}x")

        assert speedup > 50, f"Speedup too low: {speedup:.1f}x"

    def test_template_assembly_fast(self):
        """Building prompts from cached parts should be fast."""
        cache = PromptCache()

        # Cache template parts
        cache.cache_template_part("role", "You are a helpful assistant." * 10)
        cache.cache_template_part("capabilities", "You can perform the following tasks:" * 10)
        cache.cache_template_part("constraints", "Please adhere to these guidelines:" * 10)
        cache.cache_template_part("context", "Here is the relevant context:" * 10)

        part_ids = ["role", "capabilities", "constraints", "context"]

        # Warm up
        for _ in range(100):
            cache.build_from_parts("combined", part_ids)

        # Measure
        start = time.perf_counter()
        iterations = 5000
        for i in range(iterations):
            cache.build_from_parts(f"combined_{i}", part_ids)
        duration = time.perf_counter() - start

        ops_per_sec = iterations / duration
        print(f"\nTemplate assembly: {ops_per_sec:,.0f} ops/sec")

        # Should be able to assemble at least 10K prompts/sec
        assert ops_per_sec > 10000, f"Too slow: {ops_per_sec:.0f} ops/sec"

    def test_high_hit_rate_scenario(self):
        """Simulating typical agent usage with high hit rate."""
        cache = PromptCache()
        build_count = [0]

        def build_prompt(template_id: str):
            build_count[0] += 1
            return f"System prompt for {template_id}"

        # Simulate 1000 agent iterations, most using same few prompts
        templates = ["main_agent", "tool_agent", "planning_agent"]

        for _ in range(1000):
            for template in templates:
                cache.get_or_build(
                    template,
                    lambda t=template: build_prompt(t)
                )

        metrics = cache.get_metrics()

        # Only 3 builds should happen (one per unique template)
        assert build_count[0] == 3
        # Hit rate should be very high
        assert metrics.hit_rate > 0.99
        print(f"\nHit rate: {metrics.hit_rate:.1%}")
        print(f"Builds saved: {metrics.hits}")
