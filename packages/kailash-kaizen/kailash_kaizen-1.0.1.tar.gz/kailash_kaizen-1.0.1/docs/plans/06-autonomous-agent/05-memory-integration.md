# Memory Integration Architecture

**Document Status:** Architecture Specification for Kaizen Development Team
**Version:** 1.0.0
**Date:** 2026-01-21

---

## Executive Summary

Memory is a **cross-cutting concern** that applies independently of execution mode. An agent can be:
- Single-turn with persistent memory (recall past interactions)
- Multi-turn with no memory (isolated sessions)
- Autonomous with learning memory (adaptive behavior)

This document defines the memory architecture for the Coursewright AI platform.

---

## Core Principle: Memory Independence

### Anti-Pattern: Memory Tied to Execution Mode

```python
# ❌ BAD: Memory coupled to execution mode
class SingleTurnAgent:  # No memory
    pass

class MultiTurnAgent:  # Session memory
    def __init__(self):
        self.memory = SessionMemory()

class AutonomousAgent:  # Persistent memory
    def __init__(self):
        self.memory = PersistentMemory()
```

### Correct: Memory as Composition

```python
# ✅ GOOD: Memory composed independently
agent = Agent(
    execution_mode="single",
    memory_depth="persistent"  # Single-turn but with persistent memory
)

agent = Agent(
    execution_mode="autonomous",
    memory_depth="stateless"  # Autonomous but fresh each time
)
```

---

## Memory Taxonomy

### Memory Depth Levels

| Level | Scope | Persistence | Use Case |
|-------|-------|-------------|----------|
| **Stateless** | None | None | Stateless APIs, one-off queries |
| **Session** | Current conversation | Until session ends | Chat sessions |
| **Persistent** | Cross-session | Database | User preferences, history |
| **Learning** | Pattern detection | ML-enhanced | Adaptive tutoring |

### Memory Operations

| Operation | Description | All Levels |
|-----------|-------------|------------|
| **Store** | Save information | ✓ |
| **Recall** | Retrieve relevant memories | ✓ |
| **Summarize** | Compress memories | Persistent+ |
| **Forget** | Remove memories | Persistent+ |
| **Learn** | Detect patterns | Learning only |

---

## Architecture: Hierarchical Memory

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Memory Manager                                │
│  Coordinates all memory tiers, handles retrieval and storage        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────────┐  ┌─────────────────┐
│    HOT TIER     │  │     WARM TIER       │  │    COLD TIER    │
│   (In-Memory)   │  │    (Database)       │  │  (Object Store) │
├─────────────────┤  ├─────────────────────┤  ├─────────────────┤
│ • <1ms latency  │  │ • 10-50ms latency   │  │ • 100ms+ latency│
│ • Last N msgs   │  │ • Session/persist   │  │ • Archival      │
│ • Ring buffer   │  │ • SQLite/Postgres   │  │ • S3/filesystem │
│ • No persistence│  │ • Indexed search    │  │ • Compressed    │
└─────────────────┘  └─────────────────────┘  └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Context Builder                                 │
│  Assembles memories into context within token budget                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Interfaces

### MemoryEntry

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class MemorySource(Enum):
    CONVERSATION = "conversation"  # From chat
    LEARNED = "learned"            # Pattern detected
    EXTERNAL = "external"          # Injected externally
    SYSTEM = "system"              # System-generated

@dataclass
class MemoryEntry:
    """A single memory entry."""

    # Identity
    id: str
    session_id: str

    # Content
    content: str
    role: str = "assistant"  # "user", "assistant", "system", "tool"

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    source: MemorySource = MemorySource.CONVERSATION

    # Importance (0.0 to 1.0)
    importance: float = 0.5

    # Organization
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Embedding for semantic search
    embedding: Optional[List[float]] = None

    def to_message(self) -> Dict[str, str]:
        """Convert to LLM message format."""
        return {"role": self.role, "content": self.content}
```

### MemoryContext

```python
@dataclass
class MemoryContext:
    """
    Context built from memory for LLM consumption.

    This is what gets injected into prompts.
    """

    # Retrieved memories
    entries: List[MemoryEntry]

    # Summarized older memories
    summary: str = ""

    # Statistics
    total_tokens: int = 0
    entries_retrieved: int = 0
    entries_summarized: int = 0

    # Retrieval metadata
    retrieval_strategy: str = "relevance"
    retrieval_query: str = ""

    def to_system_prompt(self) -> str:
        """Format as system prompt section."""
        parts = []

        if self.summary:
            parts.append(f"## Previous Context Summary\n{self.summary}")

        if self.entries:
            parts.append("## Recent Conversation")
            for entry in self.entries:
                parts.append(f"**{entry.role.title()}**: {entry.content}")

        return "\n\n".join(parts)

    def to_messages(self) -> List[Dict[str, str]]:
        """Format as message history."""
        return [entry.to_message() for entry in self.entries]
```

### MemoryProvider Interface

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class MemoryProvider(ABC):
    """
    Abstract memory provider interface.

    Implementations:
    - BufferMemory: In-memory ring buffer (hot tier)
    - DatabaseMemory: SQLite/PostgreSQL (warm tier)
    - HierarchicalMemory: Multi-tier with promotion/demotion
    """

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        """
        Store a memory entry.

        Args:
            entry: Memory entry to store

        Returns:
            Entry ID
        """
        pass

    @abstractmethod
    async def recall(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_entries: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[MemoryEntry]:
        """
        Recall relevant memories.

        Args:
            query: Search query (semantic or keyword)
            session_id: Filter to specific session
            max_entries: Maximum entries to return
            filters: Additional filters (tags, date range, etc.)

        Returns:
            List of relevant memory entries
        """
        pass

    @abstractmethod
    async def build_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_tokens: int = 4000,
        strategy: str = "relevance"
    ) -> MemoryContext:
        """
        Build context for LLM consumption.

        Args:
            query: Current query/task
            session_id: Session to focus on
            max_tokens: Token budget for context
            strategy: "relevance", "recency", "importance", "hybrid"

        Returns:
            Memory context ready for prompt injection
        """
        pass

    @abstractmethod
    async def summarize(
        self,
        session_id: str,
        entries: Optional[List[MemoryEntry]] = None
    ) -> str:
        """
        Summarize memories for compression.

        Args:
            session_id: Session to summarize
            entries: Specific entries (or all if None)

        Returns:
            Summary text
        """
        pass

    async def forget(
        self,
        entry_id: Optional[str] = None,
        session_id: Optional[str] = None,
        before: Optional[datetime] = None
    ) -> int:
        """
        Remove memories.

        Args:
            entry_id: Specific entry to remove
            session_id: Remove all for session
            before: Remove entries before date

        Returns:
            Number of entries removed
        """
        pass
```

---

## Implementations

### BufferMemory (Hot Tier)

```python
from collections import deque
import threading

class BufferMemory(MemoryProvider):
    """
    Fast in-memory buffer for recent messages.

    Features:
    - O(1) append
    - Fixed size ring buffer
    - Thread-safe
    - No persistence
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._buffer: Dict[str, deque] = {}  # session_id -> deque
        self._lock = threading.Lock()

    async def store(self, entry: MemoryEntry) -> str:
        with self._lock:
            if entry.session_id not in self._buffer:
                self._buffer[entry.session_id] = deque(maxlen=self.max_size)
            self._buffer[entry.session_id].append(entry)
        return entry.id

    async def recall(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_entries: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[MemoryEntry]:
        with self._lock:
            if session_id and session_id in self._buffer:
                entries = list(self._buffer[session_id])
            else:
                entries = [e for buf in self._buffer.values() for e in buf]

        # Simple keyword matching for buffer
        if query:
            query_lower = query.lower()
            entries = [e for e in entries if query_lower in e.content.lower()]

        # Apply filters
        if filters:
            entries = self._apply_filters(entries, filters)

        return entries[-max_entries:]

    async def build_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_tokens: int = 4000,
        strategy: str = "recency"
    ) -> MemoryContext:
        entries = await self.recall(query, session_id, max_entries=50)

        # Sort by strategy
        if strategy == "recency":
            entries.sort(key=lambda e: e.timestamp, reverse=True)
        elif strategy == "importance":
            entries.sort(key=lambda e: e.importance, reverse=True)

        # Pack into token budget
        selected = []
        total_tokens = 0
        for entry in entries:
            entry_tokens = len(entry.content) // 4  # Rough estimate
            if total_tokens + entry_tokens <= max_tokens:
                selected.append(entry)
                total_tokens += entry_tokens
            else:
                break

        return MemoryContext(
            entries=selected,
            total_tokens=total_tokens,
            entries_retrieved=len(selected),
            retrieval_strategy=strategy,
            retrieval_query=query
        )

    async def summarize(self, session_id: str, entries=None) -> str:
        # Buffer doesn't summarize
        return ""
```

### HierarchicalMemory

```python
from typing import Optional
import asyncio

class HierarchicalMemory(MemoryProvider):
    """
    Multi-tier memory with automatic promotion/demotion.

    Hot Tier: BufferMemory (in-memory)
    Warm Tier: DatabaseMemory (SQLite/PostgreSQL)
    Cold Tier: ObjectStoreMemory (S3/filesystem)
    """

    def __init__(
        self,
        hot_size: int = 100,
        warm_backend: str = "sqlite",
        warm_path: str = ".kaizen/memory.db",
        cold_backend: Optional[str] = None,
        cold_path: Optional[str] = None,
        embedding_provider: Optional["EmbeddingProvider"] = None
    ):
        self.hot = BufferMemory(max_size=hot_size)
        self.warm = self._create_warm_backend(warm_backend, warm_path)
        self.cold = self._create_cold_backend(cold_backend, cold_path) if cold_backend else None
        self.embedder = embedding_provider

        # Promotion thresholds
        self.promote_importance_threshold = 0.7
        self.demote_age_days = 30

    async def store(self, entry: MemoryEntry) -> str:
        # Always store in hot tier
        await self.hot.store(entry)

        # Generate embedding if available
        if self.embedder and not entry.embedding:
            entry.embedding = await self.embedder.embed(entry.content)

        # Promote to warm if important
        if entry.importance >= self.promote_importance_threshold:
            await self.warm.store(entry)

        return entry.id

    async def recall(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_entries: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[MemoryEntry]:
        # Search all tiers in parallel
        hot_task = self.hot.recall(query, session_id, max_entries, filters)
        warm_task = self.warm.recall(query, session_id, max_entries, filters)

        tasks = [hot_task, warm_task]
        if self.cold:
            tasks.append(self.cold.recall(query, session_id, max_entries, filters))

        results = await asyncio.gather(*tasks)

        # Merge and deduplicate
        all_entries = []
        seen_ids = set()
        for tier_results in results:
            for entry in tier_results:
                if entry.id not in seen_ids:
                    all_entries.append(entry)
                    seen_ids.add(entry.id)

        # Sort by relevance (if semantic) or recency
        if self.embedder:
            query_embedding = await self.embedder.embed(query)
            all_entries.sort(
                key=lambda e: self._cosine_similarity(query_embedding, e.embedding or []),
                reverse=True
            )
        else:
            all_entries.sort(key=lambda e: e.timestamp, reverse=True)

        return all_entries[:max_entries]

    async def build_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_tokens: int = 4000,
        strategy: str = "hybrid"
    ) -> MemoryContext:
        # Get more entries than needed for filtering
        candidates = await self.recall(query, session_id, max_entries=100)

        # Sort by strategy
        if strategy == "recency":
            candidates.sort(key=lambda e: e.timestamp, reverse=True)
        elif strategy == "importance":
            candidates.sort(key=lambda e: e.importance, reverse=True)
        elif strategy == "relevance":
            # Already sorted by recall if embeddings available
            pass
        elif strategy == "hybrid":
            # Weighted combination
            def hybrid_score(e: MemoryEntry) -> float:
                recency = 1.0 / (1.0 + (datetime.now() - e.timestamp).total_seconds() / 3600)
                return 0.4 * e.importance + 0.3 * recency + 0.3 * getattr(e, '_relevance_score', 0.5)
            candidates.sort(key=hybrid_score, reverse=True)

        # Pack into token budget
        selected = []
        total_tokens = 0
        token_limit = max_tokens * 0.7  # Reserve 30% for summary

        for entry in candidates:
            entry_tokens = len(entry.content) // 4
            if total_tokens + entry_tokens <= token_limit:
                selected.append(entry)
                total_tokens += entry_tokens
            else:
                break

        # Summarize remaining important entries
        summary = ""
        remaining = [e for e in candidates if e not in selected and e.importance > 0.5]
        if remaining:
            summary = await self.summarize(session_id, remaining[:20])

        return MemoryContext(
            entries=selected,
            summary=summary,
            total_tokens=total_tokens + len(summary) // 4,
            entries_retrieved=len(selected),
            entries_summarized=len(remaining),
            retrieval_strategy=strategy,
            retrieval_query=query
        )

    async def summarize(
        self,
        session_id: str,
        entries: Optional[List[MemoryEntry]] = None
    ) -> str:
        if not entries:
            entries = await self.warm.recall("", session_id, max_entries=50)

        if not entries:
            return ""

        # Build summary prompt
        content_parts = [f"- {e.role}: {e.content[:200]}..." for e in entries[:20]]
        prompt = f"""Summarize the following conversation excerpts in 2-3 sentences:

{chr(10).join(content_parts)}

Summary:"""

        # Use a cheap model for summarization
        # This should be injected, but for simplicity:
        return f"Previous discussion covered: {', '.join(set(e.tags[0] for e in entries if e.tags)[:5])}"

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot / (norm_a * norm_b + 1e-8)
```

---

## Integration with Agents

### Memory-Aware Agent

```python
class Agent:
    """Agent with integrated memory."""

    def __init__(
        self,
        model: str = "gpt-4",
        memory_depth: str = "session",
        memory_backend: str = "sqlite",
        **kwargs
    ):
        # Initialize memory based on depth
        self.memory = self._init_memory(memory_depth, memory_backend, kwargs)
        # ... other initialization

    def _init_memory(
        self,
        depth: str,
        backend: str,
        config: dict
    ) -> Optional[MemoryProvider]:
        if depth == "stateless":
            return None
        elif depth == "session":
            return BufferMemory(max_size=config.get("memory_turns", 50))
        elif depth == "persistent":
            return HierarchicalMemory(
                hot_size=config.get("memory_turns", 50),
                warm_backend=backend,
                warm_path=config.get("memory_path", ".kaizen/memory.db")
            )
        elif depth == "learning":
            return LearningMemory(
                base_memory=HierarchicalMemory(...),
                pattern_detector=PatternDetector()
            )

    async def run(self, task: str, session_id: str = None, **kwargs) -> dict:
        # Build memory context
        memory_context = None
        if self.memory:
            memory_context = await self.memory.build_context(
                query=task,
                session_id=session_id,
                max_tokens=kwargs.get("memory_tokens", 4000),
                strategy=kwargs.get("memory_strategy", "hybrid")
            )

        # Build execution context with memory
        context = self._build_context(task, kwargs)
        if memory_context:
            context["memory"] = memory_context

        # Execute
        result = await self.strategy.execute(self, task, context)

        # Store interaction in memory
        if self.memory:
            await self._store_interaction(task, result, session_id)

        return result

    async def _store_interaction(
        self,
        task: str,
        result: dict,
        session_id: str
    ):
        # Store user message
        await self.memory.store(MemoryEntry(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content=task,
            role="user",
            importance=0.5,
            tags=self._extract_tags(task)
        ))

        # Store assistant response
        await self.memory.store(MemoryEntry(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content=result.get("output", ""),
            role="assistant",
            importance=self._calculate_importance(result),
            tags=self._extract_tags(result.get("output", ""))
        ))
```

---

## Memory Strategies

### Retrieval Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| **recency** | Most recent first | Chat continuity |
| **importance** | Highest importance first | Key facts |
| **relevance** | Semantic similarity | Topic retrieval |
| **hybrid** | Weighted combination | General use |

### Context Building

```python
async def build_context(
    self,
    query: str,
    max_tokens: int = 4000,
    strategy: str = "hybrid"
) -> MemoryContext:
    """
    Build context within token budget.

    Token allocation:
    - 70% for retrieved entries
    - 30% for summary of older entries
    """
    # ... implementation
```

---

## Usage Examples

### Basic Usage

```python
# Agent with session memory
agent = Agent(model="gpt-4", memory_depth="session")

# Memory automatically tracks conversation
await agent.run("What is covered interest parity?", session_id="user123")
await agent.run("Can you give me an example?", session_id="user123")  # Remembers context
await agent.run("How does it relate to PPP?", session_id="user123")  # Builds on history
```

### Persistent Memory

```python
# Agent with persistent memory across sessions
agent = Agent(
    model="gpt-4",
    memory_depth="persistent",
    memory_backend="postgresql",
    memory_path="postgresql://user:pass@localhost:5432/memory"
)

# Day 1
await agent.run("I'm studying for FNCE210", session_id="student_alice")
await agent.run("Help me understand hedging", session_id="student_alice")

# Day 2 (different session, same user)
await agent.run("Continue where we left off", session_id="student_alice")
# Agent recalls previous topics
```

### Learning Memory

```python
# Agent that learns patterns
agent = Agent(
    model="gpt-4",
    memory_depth="learning"
)

# Over time, agent detects:
# - User's knowledge level
# - Preferred explanation style
# - Common areas of confusion
# - Topics frequently revisited

await agent.run("Explain IRP again", session_id="student_bob")
# Agent adapts based on learned patterns
```

---

## Summary

Memory integration provides:

1. **Independence**: Memory depth is separate from execution mode
2. **Hierarchy**: Hot/warm/cold tiers for optimal performance
3. **Flexibility**: Multiple retrieval strategies
4. **Intelligence**: Semantic search and summarization
5. **Scalability**: From in-memory to distributed storage

**Key Insight**: Memory is not just "conversation history" - it's a sophisticated retrieval system that helps agents maintain context, learn patterns, and provide personalized experiences.

---

**Next Document**: [06-developer-ux-guide.md](./06-developer-ux-guide.md) - Developer experience patterns and API design.
