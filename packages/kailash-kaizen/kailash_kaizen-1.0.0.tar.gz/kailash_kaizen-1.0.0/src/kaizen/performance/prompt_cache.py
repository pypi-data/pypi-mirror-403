"""
System Prompt Cache for Kaizen agents (TODO-199.3.1).

Provides caching for static portions of system prompts to avoid
repeated string concatenation and template rendering.

Features:
- Static/dynamic prompt separation
- Hash-based invalidation on config changes
- Template caching with variable substitution
- Thread-safe operations
- Cache hit/miss metrics

Usage:
    from kaizen.performance import PromptCache

    cache = PromptCache()

    # Get cached prompt or build if missing
    prompt = cache.get_or_build(
        template_id="agent_system_prompt",
        static_parts=["role", "capabilities"],
        dynamic_parts={"tools": tool_schemas, "memory": context},
        build_fn=lambda: build_prompt(...)
    )
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PromptCacheConfig:
    """Configuration for prompt cache."""

    max_size: int = 100  # Maximum number of cached prompts
    ttl_seconds: Optional[float] = 3600.0  # 1 hour, None = no expiration
    enable_metrics: bool = True
    cache_static_only: bool = False  # Only cache fully static prompts


@dataclass
class PromptEntry:
    """Entry in the prompt cache."""

    content: str
    template_id: str
    config_hash: str
    created_at: float
    accessed_at: float
    access_count: int = 0
    is_static: bool = False


@dataclass
class PromptCacheMetrics:
    """Metrics for prompt cache performance."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    current_size: int = 0
    max_size: int = 0
    static_hits: int = 0
    template_hits: int = 0
    total_build_time_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def avg_build_time_saved_ms(self) -> float:
        """Average build time saved per hit."""
        if self.hits == 0:
            return 0.0
        if self.misses == 0:
            return 0.0
        avg_build = self.total_build_time_ms / self.misses
        return avg_build * self.hits

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "current_size": self.current_size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
            "static_hits": self.static_hits,
            "template_hits": self.template_hits,
            "total_build_time_ms": self.total_build_time_ms,
            "avg_build_time_saved_ms": self.avg_build_time_saved_ms,
        }


class PromptCache:
    """
    LRU cache for system prompts with template support.

    This cache significantly improves performance by avoiding repeated
    prompt construction, which involves string concatenation and
    template rendering.
    """

    def __init__(self, config: Optional[PromptCacheConfig] = None):
        """
        Initialize prompt cache.

        Args:
            config: Cache configuration
        """
        self.config = config or PromptCacheConfig()
        self._cache: OrderedDict[str, PromptEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._metrics = PromptCacheMetrics(max_size=self.config.max_size)

        # Template cache for reusable parts
        self._template_cache: Dict[str, str] = {}

    def _generate_cache_key(
        self,
        template_id: str,
        config_hash: str,
    ) -> str:
        """
        Generate cache key for prompt lookup.

        Args:
            template_id: Template identifier
            config_hash: Hash of configuration affecting prompt

        Returns:
            Cache key string
        """
        return f"prompt_{template_id}_{config_hash}"

    def _compute_config_hash(
        self,
        static_parts: Optional[List[str]] = None,
        dynamic_parts: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Compute hash of prompt configuration.

        Args:
            static_parts: List of static part identifiers
            dynamic_parts: Dictionary of dynamic content

        Returns:
            Hash string
        """
        hash_input = []

        if static_parts:
            hash_input.append(":".join(sorted(static_parts)))

        if dynamic_parts:
            # Sort keys for deterministic hashing
            for key in sorted(dynamic_parts.keys()):
                value = dynamic_parts[key]
                # Convert value to string representation for hashing
                str_value = str(value)
                # Use hash of actual content, not just length
                value_hash = hashlib.md5(
                    str_value.encode(), usedforsecurity=False
                ).hexdigest()[:8]
                hash_input.append(f"{key}:{value_hash}")

        combined = "|".join(hash_input)
        return hashlib.md5(combined.encode(), usedforsecurity=False).hexdigest()[:12]

    def get(
        self,
        template_id: str,
        config_hash: str,
    ) -> Optional[str]:
        """
        Get cached prompt.

        Args:
            template_id: Template identifier
            config_hash: Configuration hash

        Returns:
            Cached prompt or None if not found/expired
        """
        key = self._generate_cache_key(template_id, config_hash)

        with self._lock:
            if key not in self._cache:
                if self.config.enable_metrics:
                    self._metrics.misses += 1
                return None

            entry = self._cache[key]

            # Check TTL expiration
            if self.config.ttl_seconds is not None:
                if time.time() - entry.created_at > self.config.ttl_seconds:
                    del self._cache[key]
                    if self.config.enable_metrics:
                        self._metrics.expirations += 1
                        self._metrics.misses += 1
                        self._metrics.current_size -= 1
                    return None

            # Update access metadata
            entry.accessed_at = time.time()
            entry.access_count += 1
            self._cache.move_to_end(key)

            if self.config.enable_metrics:
                self._metrics.hits += 1
                if entry.is_static:
                    self._metrics.static_hits += 1
                else:
                    self._metrics.template_hits += 1

            return entry.content

    def set(
        self,
        template_id: str,
        config_hash: str,
        content: str,
        is_static: bool = False,
    ) -> None:
        """
        Cache a prompt.

        Args:
            template_id: Template identifier
            config_hash: Configuration hash
            content: Prompt content
            is_static: Whether prompt is fully static
        """
        key = self._generate_cache_key(template_id, config_hash)
        now = time.time()

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                entry.content = content
                entry.accessed_at = now
                entry.access_count += 1
                entry.is_static = is_static
                self._cache.move_to_end(key)
            else:
                self._cache[key] = PromptEntry(
                    content=content,
                    template_id=template_id,
                    config_hash=config_hash,
                    created_at=now,
                    accessed_at=now,
                    access_count=1,
                    is_static=is_static,
                )
                if self.config.enable_metrics:
                    self._metrics.current_size += 1

                while len(self._cache) > self.config.max_size:
                    self._evict_oldest()

    def get_or_build(
        self,
        template_id: str,
        build_fn: Callable[[], str],
        static_parts: Optional[List[str]] = None,
        dynamic_parts: Optional[Dict[str, Any]] = None,
        is_static: bool = False,
    ) -> str:
        """
        Get cached prompt or build and cache if missing.

        Args:
            template_id: Template identifier
            build_fn: Function to build prompt if not cached
            static_parts: List of static part identifiers
            dynamic_parts: Dictionary of dynamic content
            is_static: Whether prompt is fully static

        Returns:
            Prompt content (cached or built)
        """
        config_hash = self._compute_config_hash(static_parts, dynamic_parts)

        # Fast path: check cache first
        content = self.get(template_id, config_hash)
        if content is not None:
            return content

        # Build prompt
        start_time = time.perf_counter()
        content = build_fn()
        build_time_ms = (time.perf_counter() - start_time) * 1000

        if self.config.enable_metrics:
            self._metrics.total_build_time_ms += build_time_ms

        # Cache it
        self.set(template_id, config_hash, content, is_static)

        return content

    def cache_template_part(self, part_id: str, content: str) -> None:
        """
        Cache a reusable template part.

        Args:
            part_id: Part identifier
            content: Part content
        """
        with self._lock:
            self._template_cache[part_id] = content

    def get_template_part(self, part_id: str) -> Optional[str]:
        """
        Get cached template part.

        Args:
            part_id: Part identifier

        Returns:
            Part content or None if not cached
        """
        with self._lock:
            return self._template_cache.get(part_id)

    def build_from_parts(
        self,
        template_id: str,
        part_ids: List[str],
        separator: str = "\n\n",
    ) -> Optional[str]:
        """
        Build prompt from cached parts.

        Args:
            template_id: Template identifier for caching result
            part_ids: List of part identifiers to combine
            separator: Separator between parts

        Returns:
            Combined prompt or None if any part missing
        """
        with self._lock:
            parts = []
            for part_id in part_ids:
                part = self._template_cache.get(part_id)
                if part is None:
                    return None
                parts.append(part)

            content = separator.join(parts)

            # Cache the combined result
            config_hash = self._compute_config_hash(part_ids)
            self.set(template_id, config_hash, content, is_static=True)

            return content

    def invalidate(self, template_id: str, config_hash: Optional[str] = None) -> int:
        """
        Invalidate cached prompts.

        Args:
            template_id: Template identifier
            config_hash: Optional specific config hash

        Returns:
            Number of entries removed
        """
        with self._lock:
            if config_hash:
                key = self._generate_cache_key(template_id, config_hash)
                if key in self._cache:
                    del self._cache[key]
                    if self.config.enable_metrics:
                        self._metrics.current_size -= 1
                    return 1
                return 0

            # Remove all entries for template
            keys_to_remove = [
                k for k, v in self._cache.items() if v.template_id == template_id
            ]
            for key in keys_to_remove:
                del self._cache[key]

            if self.config.enable_metrics:
                self._metrics.current_size -= len(keys_to_remove)

            return len(keys_to_remove)

    def invalidate_all(self) -> int:
        """
        Clear all cached prompts.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._template_cache.clear()
            if self.config.enable_metrics:
                self._metrics.current_size = 0
            return count

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def get_metrics(self) -> PromptCacheMetrics:
        """Get cache metrics."""
        with self._lock:
            self._metrics.current_size = len(self._cache)
            return PromptCacheMetrics(
                hits=self._metrics.hits,
                misses=self._metrics.misses,
                evictions=self._metrics.evictions,
                expirations=self._metrics.expirations,
                current_size=self._metrics.current_size,
                max_size=self._metrics.max_size,
                static_hits=self._metrics.static_hits,
                template_hits=self._metrics.template_hits,
                total_build_time_ms=self._metrics.total_build_time_ms,
            )

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        with self._lock:
            self._metrics = PromptCacheMetrics(
                max_size=self.config.max_size,
                current_size=len(self._cache),
            )

    def _evict_oldest(self) -> None:
        """Evict the oldest (least recently used) entry."""
        if self._cache:
            self._cache.popitem(last=False)
            if self.config.enable_metrics:
                self._metrics.evictions += 1
                self._metrics.current_size -= 1


# Global singleton instance
_global_prompt_cache: Optional[PromptCache] = None
_global_cache_lock = threading.Lock()


def get_prompt_cache() -> PromptCache:
    """Get the global prompt cache instance."""
    global _global_prompt_cache
    with _global_cache_lock:
        if _global_prompt_cache is None:
            _global_prompt_cache = PromptCache()
        return _global_prompt_cache


def set_prompt_cache(cache: Optional[PromptCache]) -> None:
    """Set the global prompt cache instance."""
    global _global_prompt_cache
    with _global_cache_lock:
        _global_prompt_cache = cache
