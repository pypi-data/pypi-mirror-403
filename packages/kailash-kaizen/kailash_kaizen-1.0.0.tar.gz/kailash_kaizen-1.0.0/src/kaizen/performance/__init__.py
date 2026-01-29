"""Performance optimization utilities for Kaizen agents."""

from kaizen.performance.parallel_tools import (
    ParallelToolExecutor,
    ToolDependencyAnalyzer,
    ParallelExecutionConfig,
    ParallelExecutionResult,
)
from kaizen.performance.schema_cache import (
    SchemaCache,
    ToolSchemaCache,
    SchemaCacheConfig,
    CacheMetrics,
    get_schema_cache,
    set_schema_cache,
)
from kaizen.performance.embedding_cache import (
    EmbeddingCache,
    EmbeddingCacheConfig,
    EmbeddingCacheMetrics,
    get_embedding_cache,
    set_embedding_cache,
)
from kaizen.performance.prompt_cache import (
    PromptCache,
    PromptCacheConfig,
    PromptCacheMetrics,
    PromptEntry,
    get_prompt_cache,
    set_prompt_cache,
)
from kaizen.performance.memory_context_cache import (
    MemoryContextCache,
    MemoryContextConfig,
    MemoryContextMetrics,
    SessionContext,
    SegmentEntry,
    get_memory_context_cache,
    set_memory_context_cache,
)
from kaizen.performance.hook_batch_executor import (
    HookBatchExecutor,
    HookBatchConfig,
    HookBatchMetrics,
    HookExecutionResult,
    BatchExecutionResult,
    BatchExecutionMode,
    create_hook_executor,
)
from kaizen.performance.background_checkpoint import (
    BackgroundCheckpointWriter,
    BackgroundCheckpointConfig,
    BackgroundCheckpointMetrics,
    CheckpointWriteResult,
    PendingCheckpoint,
    create_background_writer,
)

__all__ = [
    # Parallel execution
    "ParallelToolExecutor",
    "ToolDependencyAnalyzer",
    "ParallelExecutionConfig",
    "ParallelExecutionResult",
    # Schema caching
    "SchemaCache",
    "ToolSchemaCache",
    "SchemaCacheConfig",
    "CacheMetrics",
    "get_schema_cache",
    "set_schema_cache",
    # Embedding caching
    "EmbeddingCache",
    "EmbeddingCacheConfig",
    "EmbeddingCacheMetrics",
    "get_embedding_cache",
    "set_embedding_cache",
    # Prompt caching
    "PromptCache",
    "PromptCacheConfig",
    "PromptCacheMetrics",
    "PromptEntry",
    "get_prompt_cache",
    "set_prompt_cache",
    # Memory context caching
    "MemoryContextCache",
    "MemoryContextConfig",
    "MemoryContextMetrics",
    "SessionContext",
    "SegmentEntry",
    "get_memory_context_cache",
    "set_memory_context_cache",
    # Hook batch execution
    "HookBatchExecutor",
    "HookBatchConfig",
    "HookBatchMetrics",
    "HookExecutionResult",
    "BatchExecutionResult",
    "BatchExecutionMode",
    "create_hook_executor",
    # Background checkpoint I/O
    "BackgroundCheckpointWriter",
    "BackgroundCheckpointConfig",
    "BackgroundCheckpointMetrics",
    "CheckpointWriteResult",
    "PendingCheckpoint",
    "create_background_writer",
]
