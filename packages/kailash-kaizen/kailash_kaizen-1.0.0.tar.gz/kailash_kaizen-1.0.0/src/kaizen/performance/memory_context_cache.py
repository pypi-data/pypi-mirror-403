"""
Memory Context Cache with Incremental Updates (TODO-199.3.2).

Provides intelligent caching for memory context that supports
incremental updates to avoid full context rebuilds on each cycle.

Features:
- Tracks memory segments (conversation, knowledge, facts, etc.)
- Hash-based change detection for each segment
- Incremental context assembly from cached segments
- Thread-safe operations
- Metrics for cache hit rates and rebuild savings

Usage:
    from kaizen.performance import MemoryContextCache

    cache = MemoryContextCache()

    # Build context incrementally
    context = cache.build_context_incremental(
        session_id="session-123",
        segments={
            "conversation": conversation_history,
            "knowledge": relevant_knowledge,
            "facts": extracted_facts,
        },
        build_segment_fn=render_segment
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
class MemoryContextConfig:
    """Configuration for memory context cache."""

    max_sessions: int = 100  # Maximum concurrent sessions to cache
    max_segments_per_session: int = 20  # Maximum segments per session
    ttl_seconds: Optional[float] = 1800.0  # 30 minutes, None = no expiration
    enable_metrics: bool = True
    enable_compression: bool = False  # Future: compress large segments


@dataclass
class SegmentEntry:
    """Cached segment entry."""

    content: str
    content_hash: str
    created_at: float
    accessed_at: float
    access_count: int = 0
    size_bytes: int = 0


@dataclass
class SessionContext:
    """Cached session context with segments."""

    session_id: str
    segments: Dict[str, SegmentEntry]
    cached_full_context: Optional[str] = None
    full_context_hash: Optional[str] = None
    created_at: float = 0.0
    accessed_at: float = 0.0
    segment_order: List[str] = field(default_factory=list)


@dataclass
class MemoryContextMetrics:
    """Metrics for memory context cache performance."""

    context_builds: int = 0
    incremental_updates: int = 0
    full_rebuilds: int = 0
    segment_cache_hits: int = 0
    segment_cache_misses: int = 0
    sessions_cached: int = 0
    sessions_evicted: int = 0
    total_rebuild_time_saved_ms: float = 0.0
    avg_segment_build_time_ms: float = 0.0

    @property
    def incremental_rate(self) -> float:
        """Calculate rate of incremental updates vs full rebuilds."""
        total = self.incremental_updates + self.full_rebuilds
        return self.incremental_updates / total if total > 0 else 0.0

    @property
    def segment_hit_rate(self) -> float:
        """Calculate segment cache hit rate."""
        total = self.segment_cache_hits + self.segment_cache_misses
        return self.segment_cache_hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "context_builds": self.context_builds,
            "incremental_updates": self.incremental_updates,
            "full_rebuilds": self.full_rebuilds,
            "segment_cache_hits": self.segment_cache_hits,
            "segment_cache_misses": self.segment_cache_misses,
            "sessions_cached": self.sessions_cached,
            "sessions_evicted": self.sessions_evicted,
            "incremental_rate": self.incremental_rate,
            "segment_hit_rate": self.segment_hit_rate,
            "total_rebuild_time_saved_ms": self.total_rebuild_time_saved_ms,
            "avg_segment_build_time_ms": self.avg_segment_build_time_ms,
        }


class MemoryContextCache:
    """
    Cache for memory context with incremental update support.

    This cache avoids rebuilding the full memory context on each
    TAOD cycle by tracking individual segments and only rebuilding
    segments that have changed.
    """

    def __init__(self, config: Optional[MemoryContextConfig] = None):
        """
        Initialize memory context cache.

        Args:
            config: Cache configuration
        """
        self.config = config or MemoryContextConfig()
        self._sessions: OrderedDict[str, SessionContext] = OrderedDict()
        self._lock = threading.RLock()
        self._metrics = MemoryContextMetrics()
        self._total_build_time_ms: float = 0.0
        self._build_count: int = 0

    def _compute_segment_hash(self, content: Any) -> str:
        """
        Compute hash for segment content.

        Args:
            content: Segment content (any type)

        Returns:
            Hash string
        """
        content_str = str(content)
        return hashlib.md5(content_str.encode(), usedforsecurity=False).hexdigest()[:16]

    def _get_or_create_session(self, session_id: str) -> SessionContext:
        """
        Get existing session or create new one.

        Args:
            session_id: Session identifier

        Returns:
            SessionContext instance
        """
        now = time.time()

        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.accessed_at = now
            self._sessions.move_to_end(session_id)
            return session

        # Create new session
        session = SessionContext(
            session_id=session_id,
            segments={},
            created_at=now,
            accessed_at=now,
        )
        self._sessions[session_id] = session

        if self.config.enable_metrics:
            self._metrics.sessions_cached += 1

        # Evict if over capacity
        while len(self._sessions) > self.config.max_sessions:
            self._evict_oldest_session()

        return session

    def _evict_oldest_session(self) -> None:
        """Evict the oldest session."""
        if self._sessions:
            self._sessions.popitem(last=False)
            if self.config.enable_metrics:
                self._metrics.sessions_evicted += 1

    def get_cached_segment(
        self,
        session_id: str,
        segment_name: str,
    ) -> Optional[str]:
        """
        Get cached segment content.

        Args:
            session_id: Session identifier
            segment_name: Segment name

        Returns:
            Cached content or None if not found/expired
        """
        with self._lock:
            if session_id not in self._sessions:
                return None

            session = self._sessions[session_id]

            # Check TTL
            if self.config.ttl_seconds is not None:
                if time.time() - session.accessed_at > self.config.ttl_seconds:
                    del self._sessions[session_id]
                    return None

            if segment_name not in session.segments:
                return None

            entry = session.segments[segment_name]
            now = time.time()
            entry.accessed_at = now
            entry.access_count += 1

            # Update session LRU order
            session.accessed_at = now
            self._sessions.move_to_end(session_id)

            return entry.content

    def update_segment(
        self,
        session_id: str,
        segment_name: str,
        content: str,
        source_hash: Optional[str] = None,
    ) -> bool:
        """
        Update a segment in the cache.

        Args:
            session_id: Session identifier
            segment_name: Segment name
            content: Segment content
            source_hash: Optional pre-computed hash of source data

        Returns:
            True if segment was updated (changed), False if unchanged
        """
        content_hash = source_hash or self._compute_segment_hash(content)

        with self._lock:
            session = self._get_or_create_session(session_id)
            now = time.time()

            # Check if segment already exists and is unchanged
            if segment_name in session.segments:
                existing = session.segments[segment_name]
                if existing.content_hash == content_hash:
                    # Unchanged, just update access time
                    existing.accessed_at = now
                    existing.access_count += 1
                    if self.config.enable_metrics:
                        self._metrics.segment_cache_hits += 1
                    return False

            # Create or update entry
            session.segments[segment_name] = SegmentEntry(
                content=content,
                content_hash=content_hash,
                created_at=now,
                accessed_at=now,
                access_count=1,
                size_bytes=len(content.encode()),
            )

            # Invalidate full context cache
            session.cached_full_context = None
            session.full_context_hash = None

            # Update segment order if new
            if segment_name not in session.segment_order:
                session.segment_order.append(segment_name)

            # Enforce max segments
            while len(session.segments) > self.config.max_segments_per_session:
                # Remove oldest segment
                if session.segment_order:
                    oldest = session.segment_order.pop(0)
                    if oldest in session.segments:
                        del session.segments[oldest]

            if self.config.enable_metrics:
                self._metrics.segment_cache_misses += 1

            return True

    def build_context_incremental(
        self,
        session_id: str,
        segments: Dict[str, Any],
        build_segment_fn: Callable[[str, Any], str],
        separator: str = "\n\n",
        segment_order: Optional[List[str]] = None,
    ) -> Tuple[str, bool]:
        """
        Build memory context incrementally.

        Only rebuilds segments that have changed since last call.

        Args:
            session_id: Session identifier
            segments: Dictionary of segment name -> source data
            build_segment_fn: Function to render segment (name, data) -> string
            separator: Separator between segments
            segment_order: Optional explicit segment ordering

        Returns:
            Tuple of (context_string, was_incremental)
            was_incremental is True if any cached segments were reused
        """
        if self.config.enable_metrics:
            self._metrics.context_builds += 1

        with self._lock:
            session = self._get_or_create_session(session_id)

            # Determine order
            order = segment_order or list(segments.keys())

            # Track changes
            changed_segments: Set[str] = set()
            segment_contents: Dict[str, str] = {}

            for name in order:
                if name not in segments:
                    continue

                source_data = segments[name]
                source_hash = self._compute_segment_hash(source_data)

                # Check if cached and unchanged
                if name in session.segments:
                    cached = session.segments[name]
                    if cached.content_hash == source_hash:
                        # Reuse cached content
                        segment_contents[name] = cached.content
                        cached.accessed_at = time.time()
                        cached.access_count += 1
                        continue

                # Need to rebuild this segment
                changed_segments.add(name)

                start_time = time.perf_counter()
                content = build_segment_fn(name, source_data)
                build_time_ms = (time.perf_counter() - start_time) * 1000

                # Track build time for metrics
                self._total_build_time_ms += build_time_ms
                self._build_count += 1

                segment_contents[name] = content

                # Update cache
                self.update_segment(session_id, name, content, source_hash)

            # Assemble full context
            ordered_contents = [
                segment_contents[name] for name in order if name in segment_contents
            ]
            full_context = separator.join(ordered_contents)

            # Update metrics
            was_incremental = len(changed_segments) < len(segments)
            if self.config.enable_metrics:
                if was_incremental:
                    self._metrics.incremental_updates += 1
                    # Estimate time saved
                    reused_count = len(segments) - len(changed_segments)
                    if self._build_count > 0:
                        avg_build = self._total_build_time_ms / self._build_count
                        self._metrics.total_rebuild_time_saved_ms += (
                            avg_build * reused_count
                        )
                        self._metrics.avg_segment_build_time_ms = avg_build
                else:
                    self._metrics.full_rebuilds += 1

            # Cache full context
            session.cached_full_context = full_context
            session.full_context_hash = self._compute_segment_hash(full_context)
            session.segment_order = order.copy()

            return full_context, was_incremental

    def get_cached_context(self, session_id: str) -> Optional[str]:
        """
        Get the full cached context for a session.

        Args:
            session_id: Session identifier

        Returns:
            Cached context or None if not available
        """
        with self._lock:
            if session_id not in self._sessions:
                return None

            session = self._sessions[session_id]

            # Check TTL
            if self.config.ttl_seconds is not None:
                if time.time() - session.accessed_at > self.config.ttl_seconds:
                    del self._sessions[session_id]
                    return None

            return session.cached_full_context

    def get_changed_segments(
        self,
        session_id: str,
        segments: Dict[str, Any],
    ) -> List[str]:
        """
        Identify which segments have changed.

        Args:
            session_id: Session identifier
            segments: Dictionary of segment name -> source data

        Returns:
            List of segment names that have changed
        """
        with self._lock:
            if session_id not in self._sessions:
                return list(segments.keys())

            session = self._sessions[session_id]
            changed = []

            for name, data in segments.items():
                source_hash = self._compute_segment_hash(data)

                if name not in session.segments:
                    changed.append(name)
                elif session.segments[name].content_hash != source_hash:
                    changed.append(name)

            return changed

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate all cached data for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was invalidated
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def invalidate_segment(self, session_id: str, segment_name: str) -> bool:
        """
        Invalidate a specific segment.

        Args:
            session_id: Session identifier
            segment_name: Segment name

        Returns:
            True if segment was invalidated
        """
        with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]

            if segment_name in session.segments:
                del session.segments[segment_name]
                if segment_name in session.segment_order:
                    session.segment_order.remove(segment_name)
                session.cached_full_context = None
                session.full_context_hash = None
                return True

            return False

    def invalidate_all(self) -> int:
        """
        Clear all cached sessions.

        Returns:
            Number of sessions cleared
        """
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            if self.config.enable_metrics:
                self._metrics.sessions_cached = 0
            return count

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a cached session.

        Args:
            session_id: Session identifier

        Returns:
            Session info dictionary or None
        """
        with self._lock:
            if session_id not in self._sessions:
                return None

            session = self._sessions[session_id]
            return {
                "session_id": session.session_id,
                "segment_count": len(session.segments),
                "segments": list(session.segments.keys()),
                "has_cached_context": session.cached_full_context is not None,
                "created_at": session.created_at,
                "accessed_at": session.accessed_at,
                "total_size_bytes": sum(
                    s.size_bytes for s in session.segments.values()
                ),
            }

    def size(self) -> int:
        """Get number of cached sessions."""
        with self._lock:
            return len(self._sessions)

    def get_metrics(self) -> MemoryContextMetrics:
        """Get cache metrics."""
        with self._lock:
            self._metrics.sessions_cached = len(self._sessions)
            if self._build_count > 0:
                self._metrics.avg_segment_build_time_ms = (
                    self._total_build_time_ms / self._build_count
                )
            return MemoryContextMetrics(
                context_builds=self._metrics.context_builds,
                incremental_updates=self._metrics.incremental_updates,
                full_rebuilds=self._metrics.full_rebuilds,
                segment_cache_hits=self._metrics.segment_cache_hits,
                segment_cache_misses=self._metrics.segment_cache_misses,
                sessions_cached=self._metrics.sessions_cached,
                sessions_evicted=self._metrics.sessions_evicted,
                total_rebuild_time_saved_ms=self._metrics.total_rebuild_time_saved_ms,
                avg_segment_build_time_ms=self._metrics.avg_segment_build_time_ms,
            )

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        with self._lock:
            self._metrics = MemoryContextMetrics()
            self._total_build_time_ms = 0.0
            self._build_count = 0


# Global singleton instance
_global_memory_context_cache: Optional[MemoryContextCache] = None
_global_cache_lock = threading.Lock()


def get_memory_context_cache() -> MemoryContextCache:
    """Get the global memory context cache instance."""
    global _global_memory_context_cache
    with _global_cache_lock:
        if _global_memory_context_cache is None:
            _global_memory_context_cache = MemoryContextCache()
        return _global_memory_context_cache


def set_memory_context_cache(cache: Optional[MemoryContextCache]) -> None:
    """Set the global memory context cache instance."""
    global _global_memory_context_cache
    with _global_cache_lock:
        _global_memory_context_cache = cache
