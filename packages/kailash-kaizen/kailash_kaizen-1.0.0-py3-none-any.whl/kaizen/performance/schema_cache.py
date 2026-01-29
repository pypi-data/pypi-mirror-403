"""
Tool Schema Cache for Kaizen agents (TODO-199.2.3).

Provides LRU caching for tool schemas to avoid repeated generation.

Features:
- LRU eviction policy
- TTL-based expiration (optional)
- Thread-safe operations
- Cache hit/miss metrics
- Configurable size limits

Usage:
    from kaizen.performance import SchemaCache

    cache = SchemaCache(max_size=1000)

    # Get cached schema or generate if missing
    schema = cache.get_or_compute(
        "tool_name",
        lambda: generate_schema(tool)
    )
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Entry in the cache with metadata."""

    value: T
    created_at: float
    accessed_at: float
    access_count: int = 0


@dataclass
class CacheMetrics:
    """Metrics for cache performance."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    current_size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

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
        }


@dataclass
class SchemaCacheConfig:
    """Configuration for schema cache."""

    max_size: int = 1000
    ttl_seconds: Optional[float] = None  # None = no expiration
    enable_metrics: bool = True


class SchemaCache:
    """
    LRU cache for tool schemas with optional TTL.

    This cache significantly improves performance by avoiding repeated
    schema generation, which involves reflection and type introspection.
    """

    def __init__(self, config: Optional[SchemaCacheConfig] = None):
        """
        Initialize schema cache.

        Args:
            config: Cache configuration
        """
        self.config = config or SchemaCacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._metrics = CacheMetrics(max_size=self.config.max_size)

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                if self.config.enable_metrics:
                    self._metrics.misses += 1
                return None

            entry = self._cache[key]

            # Check TTL expiration
            if self.config.ttl_seconds is not None:
                if time.time() - entry.created_at > self.config.ttl_seconds:
                    # Entry expired
                    del self._cache[key]
                    if self.config.enable_metrics:
                        self._metrics.expirations += 1
                        self._metrics.misses += 1
                        self._metrics.current_size -= 1
                    return None

            # Update access metadata and move to end (most recently used)
            entry.accessed_at = time.time()
            entry.access_count += 1
            self._cache.move_to_end(key)

            if self.config.enable_metrics:
                self._metrics.hits += 1

            return entry.value

    def set(self, key: str, value: Any) -> None:
        """
        Set cached value.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            now = time.time()

            if key in self._cache:
                # Update existing entry
                entry = self._cache[key]
                entry.value = value
                entry.accessed_at = now
                entry.access_count += 1
                self._cache.move_to_end(key)
            else:
                # Create new entry
                self._cache[key] = CacheEntry(
                    value=value,
                    created_at=now,
                    accessed_at=now,
                    access_count=1,
                )
                if self.config.enable_metrics:
                    self._metrics.current_size += 1

                # Evict if over capacity
                while len(self._cache) > self.config.max_size:
                    self._evict_oldest()

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], T],
    ) -> T:
        """
        Get cached value or compute and cache if missing.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached

        Returns:
            Cached or computed value
        """
        # Fast path: check cache first
        value = self.get(key)
        if value is not None:
            return value

        # Compute and cache
        with self._lock:
            # Double-check after acquiring lock
            if key in self._cache:
                entry = self._cache[key]
                entry.accessed_at = time.time()
                entry.access_count += 1
                self._cache.move_to_end(key)
                return entry.value

            # Compute value
            value = compute_fn()

            # Cache it
            now = time.time()
            self._cache[key] = CacheEntry(
                value=value,
                created_at=now,
                accessed_at=now,
                access_count=1,
            )
            if self.config.enable_metrics:
                self._metrics.misses += 1  # Already counted, but needed for get_or_compute
                self._metrics.current_size += 1

            # Evict if needed
            while len(self._cache) > self.config.max_size:
                self._evict_oldest()

            return value

    def invalidate(self, key: str) -> bool:
        """
        Remove entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was removed
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if self.config.enable_metrics:
                    self._metrics.current_size -= 1
                return True
            return False

    def invalidate_all(self) -> int:
        """
        Clear all entries from cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            if self.config.enable_metrics:
                self._metrics.current_size = 0
            return count

    def contains(self, key: str) -> bool:
        """Check if key is in cache (without affecting LRU order)."""
        with self._lock:
            if key not in self._cache:
                return False

            # Check expiration without updating access
            if self.config.ttl_seconds is not None:
                entry = self._cache[key]
                if time.time() - entry.created_at > self.config.ttl_seconds:
                    return False

            return True

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics."""
        with self._lock:
            self._metrics.current_size = len(self._cache)
            return CacheMetrics(
                hits=self._metrics.hits,
                misses=self._metrics.misses,
                evictions=self._metrics.evictions,
                expirations=self._metrics.expirations,
                current_size=self._metrics.current_size,
                max_size=self._metrics.max_size,
            )

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        with self._lock:
            self._metrics = CacheMetrics(
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


class ToolSchemaCache(SchemaCache):
    """
    Specialized schema cache for tool definitions.

    Provides additional functionality for tool-specific caching patterns.
    """

    def __init__(
        self,
        config: Optional[SchemaCacheConfig] = None,
        hash_tool_definition: bool = True,
    ):
        """
        Initialize tool schema cache.

        Args:
            config: Cache configuration
            hash_tool_definition: Use hash of tool definition as cache key
        """
        super().__init__(config)
        self.hash_tool_definition = hash_tool_definition

    def get_schema_key(self, tool_name: str, tool_definition: Optional[Any] = None) -> str:
        """
        Generate cache key for a tool.

        Args:
            tool_name: Name of the tool
            tool_definition: Optional tool definition object for hashing

        Returns:
            Cache key string
        """
        if tool_definition is not None and self.hash_tool_definition:
            # Include definition hash for invalidation on changes
            definition_str = str(tool_definition)
            definition_hash = hashlib.md5(
                definition_str.encode(), usedforsecurity=False
            ).hexdigest()[:8]
            return f"{tool_name}:{definition_hash}"
        return tool_name

    def get_tool_schema(
        self,
        tool_name: str,
        tool_definition: Optional[Any] = None,
        compute_fn: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached schema for a tool.

        Args:
            tool_name: Name of the tool
            tool_definition: Tool definition for key generation
            compute_fn: Function to compute schema if not cached

        Returns:
            Tool schema dictionary or None
        """
        key = self.get_schema_key(tool_name, tool_definition)

        if compute_fn is not None:
            return self.get_or_compute(key, compute_fn)
        return self.get(key)

    def set_tool_schema(
        self,
        tool_name: str,
        schema: Dict[str, Any],
        tool_definition: Optional[Any] = None,
    ) -> None:
        """
        Cache a tool schema.

        Args:
            tool_name: Name of the tool
            schema: Schema dictionary to cache
            tool_definition: Tool definition for key generation
        """
        key = self.get_schema_key(tool_name, tool_definition)
        self.set(key, schema)

    def invalidate_tool(self, tool_name: str) -> int:
        """
        Invalidate all cached schemas for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [
                k for k in self._cache.keys() if k.startswith(f"{tool_name}:")
            ]
            for key in keys_to_remove:
                del self._cache[key]

            if self.config.enable_metrics:
                self._metrics.current_size -= len(keys_to_remove)

            return len(keys_to_remove)


# Global singleton instance
_global_schema_cache: Optional[ToolSchemaCache] = None
_global_cache_lock = threading.Lock()


def get_schema_cache() -> ToolSchemaCache:
    """Get the global schema cache instance."""
    global _global_schema_cache
    with _global_cache_lock:
        if _global_schema_cache is None:
            _global_schema_cache = ToolSchemaCache()
        return _global_schema_cache


def set_schema_cache(cache: Optional[ToolSchemaCache]) -> None:
    """Set the global schema cache instance."""
    global _global_schema_cache
    with _global_cache_lock:
        _global_schema_cache = cache
