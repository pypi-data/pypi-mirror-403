"""
Embedding Cache for Kaizen agents (TODO-199.2.2).

Provides LRU caching for embeddings to avoid repeated API calls.

Features:
- LRU eviction with configurable size limits
- TTL-based expiration for stale embeddings
- Thread-safe operations
- Cache hit/miss metrics
- Hash-based keys for deduplication
- Batch operation support

Usage:
    from kaizen.performance import EmbeddingCache

    cache = EmbeddingCache(max_size=10000, ttl_seconds=86400)

    # Get cached embedding or compute if missing
    embedding = cache.get_or_compute(
        text="Hello world",
        model="text-embedding-3-small",
        compute_fn=lambda: api.embed(text)
    )
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCacheConfig:
    """Configuration for embedding cache."""

    max_size: int = 10000  # Maximum number of cached embeddings
    ttl_seconds: Optional[float] = 86400.0  # 24 hours, None = no expiration
    enable_metrics: bool = True
    normalize_text: bool = True  # Normalize whitespace before hashing
    max_text_length: int = 8192  # Maximum text length to cache


@dataclass
class EmbeddingEntry:
    """Entry in the embedding cache."""

    vector: List[float]
    model: str
    dimensions: int
    created_at: float
    accessed_at: float
    access_count: int = 0
    text_hash: str = ""


@dataclass
class EmbeddingCacheMetrics:
    """Metrics for embedding cache performance."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    current_size: int = 0
    max_size: int = 0
    total_embeddings_cached: int = 0
    total_api_calls_saved: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def api_savings_rate(self) -> float:
        """Calculate percentage of API calls saved."""
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
            "total_embeddings_cached": self.total_embeddings_cached,
            "total_api_calls_saved": self.total_api_calls_saved,
            "api_savings_rate": self.api_savings_rate,
        }


class EmbeddingCache:
    """
    LRU cache for embedding vectors with optional TTL.

    This cache significantly improves performance by avoiding repeated
    API calls for embeddings of identical or similar texts.
    """

    def __init__(self, config: Optional[EmbeddingCacheConfig] = None):
        """
        Initialize embedding cache.

        Args:
            config: Cache configuration
        """
        self.config = config or EmbeddingCacheConfig()
        self._cache: OrderedDict[str, EmbeddingEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._metrics = EmbeddingCacheMetrics(max_size=self.config.max_size)

    def _generate_cache_key(
        self,
        text: str,
        model: str,
        provider: str = "default",
    ) -> str:
        """
        Generate cache key for embedding lookup.

        Args:
            text: Text to embed
            model: Embedding model name
            provider: Embedding provider

        Returns:
            Cache key string
        """
        # Normalize text if configured
        normalized_text = text
        if self.config.normalize_text:
            normalized_text = " ".join(text.split())  # Normalize whitespace

        # Create deterministic hash
        key_input = f"{provider}:{model}:{normalized_text}"
        text_hash = hashlib.md5(
            key_input.encode("utf-8"), usedforsecurity=False
        ).hexdigest()

        return f"emb_{text_hash}"

    def get(
        self,
        text: str,
        model: str,
        provider: str = "default",
    ) -> Optional[List[float]]:
        """
        Get cached embedding for text.

        Args:
            text: Text to look up
            model: Embedding model name
            provider: Embedding provider

        Returns:
            Cached embedding vector or None if not found/expired
        """
        if len(text) > self.config.max_text_length:
            # Text too long, skip cache
            return None

        key = self._generate_cache_key(text, model, provider)

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
                self._metrics.total_api_calls_saved += 1

            return entry.vector

    def set(
        self,
        text: str,
        vector: List[float],
        model: str,
        provider: str = "default",
    ) -> None:
        """
        Cache an embedding vector.

        Args:
            text: Text that was embedded
            vector: Embedding vector
            model: Embedding model name
            provider: Embedding provider
        """
        if len(text) > self.config.max_text_length:
            # Text too long, skip caching
            return

        key = self._generate_cache_key(text, model, provider)
        now = time.time()

        with self._lock:
            if key in self._cache:
                # Update existing entry
                entry = self._cache[key]
                entry.vector = vector
                entry.accessed_at = now
                entry.access_count += 1
                self._cache.move_to_end(key)
            else:
                # Create new entry
                self._cache[key] = EmbeddingEntry(
                    vector=vector,
                    model=model,
                    dimensions=len(vector),
                    created_at=now,
                    accessed_at=now,
                    access_count=1,
                    text_hash=key,
                )
                if self.config.enable_metrics:
                    self._metrics.current_size += 1
                    self._metrics.total_embeddings_cached += 1

                # Evict if over capacity
                while len(self._cache) > self.config.max_size:
                    self._evict_oldest()

    def get_or_compute(
        self,
        text: str,
        model: str,
        compute_fn: Callable[[], List[float]],
        provider: str = "default",
    ) -> List[float]:
        """
        Get cached embedding or compute and cache if missing.

        Args:
            text: Text to embed
            model: Embedding model name
            compute_fn: Function to compute embedding if not cached
            provider: Embedding provider

        Returns:
            Embedding vector (cached or computed)
        """
        # Fast path: check cache first
        vector = self.get(text, model, provider)
        if vector is not None:
            return vector

        # Compute embedding
        vector = compute_fn()

        # Cache it
        self.set(text, vector, model, provider)

        return vector

    def get_batch(
        self,
        texts: List[str],
        model: str,
        provider: str = "default",
    ) -> Tuple[List[Optional[List[float]]], List[int]]:
        """
        Get cached embeddings for batch of texts.

        Args:
            texts: List of texts to look up
            model: Embedding model name
            provider: Embedding provider

        Returns:
            Tuple of (embeddings, uncached_indices)
            - embeddings: List with cached vectors or None for misses
            - uncached_indices: Indices of texts that need computation
        """
        embeddings: List[Optional[List[float]]] = []
        uncached_indices: List[int] = []

        for i, text in enumerate(texts):
            vector = self.get(text, model, provider)
            embeddings.append(vector)
            if vector is None:
                uncached_indices.append(i)

        return embeddings, uncached_indices

    def set_batch(
        self,
        texts: List[str],
        vectors: List[List[float]],
        model: str,
        provider: str = "default",
    ) -> None:
        """
        Cache batch of embeddings.

        Args:
            texts: List of texts that were embedded
            vectors: List of embedding vectors
            model: Embedding model name
            provider: Embedding provider
        """
        if len(texts) != len(vectors):
            raise ValueError("Texts and vectors must have same length")

        for text, vector in zip(texts, vectors):
            self.set(text, vector, model, provider)

    def invalidate(self, text: str, model: str, provider: str = "default") -> bool:
        """
        Remove cached embedding.

        Args:
            text: Text to invalidate
            model: Embedding model name
            provider: Embedding provider

        Returns:
            True if entry was removed
        """
        key = self._generate_cache_key(text, model, provider)

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if self.config.enable_metrics:
                    self._metrics.current_size -= 1
                return True
            return False

    def invalidate_model(self, model: str) -> int:
        """
        Remove all cached embeddings for a specific model.

        Args:
            model: Model name to invalidate

        Returns:
            Number of entries removed
        """
        with self._lock:
            keys_to_remove = [
                k for k, v in self._cache.items() if v.model == model
            ]
            for key in keys_to_remove:
                del self._cache[key]

            if self.config.enable_metrics:
                self._metrics.current_size -= len(keys_to_remove)

            return len(keys_to_remove)

    def invalidate_all(self) -> int:
        """
        Clear all cached embeddings.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            if self.config.enable_metrics:
                self._metrics.current_size = 0
            return count

    def contains(self, text: str, model: str, provider: str = "default") -> bool:
        """Check if embedding is cached (without affecting LRU order)."""
        key = self._generate_cache_key(text, model, provider)

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

    def get_metrics(self) -> EmbeddingCacheMetrics:
        """Get cache metrics."""
        with self._lock:
            self._metrics.current_size = len(self._cache)
            return EmbeddingCacheMetrics(
                hits=self._metrics.hits,
                misses=self._metrics.misses,
                evictions=self._metrics.evictions,
                expirations=self._metrics.expirations,
                current_size=self._metrics.current_size,
                max_size=self._metrics.max_size,
                total_embeddings_cached=self._metrics.total_embeddings_cached,
                total_api_calls_saved=self._metrics.total_api_calls_saved,
            )

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        with self._lock:
            self._metrics = EmbeddingCacheMetrics(
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
_global_embedding_cache: Optional[EmbeddingCache] = None
_global_cache_lock = threading.Lock()


def get_embedding_cache() -> EmbeddingCache:
    """Get the global embedding cache instance."""
    global _global_embedding_cache
    with _global_cache_lock:
        if _global_embedding_cache is None:
            _global_embedding_cache = EmbeddingCache()
        return _global_embedding_cache


def set_embedding_cache(cache: Optional[EmbeddingCache]) -> None:
    """Set the global embedding cache instance."""
    global _global_embedding_cache
    with _global_cache_lock:
        _global_embedding_cache = cache
