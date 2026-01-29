"""
Kaizen Profiling Infrastructure (TODO-199).

Provides detailed profiling capabilities for performance optimization,
including TAOD loop timing, memory analysis, and bottleneck identification.

Modules:
- taod_profiler: TAOD loop phase-by-phase timing and analysis
- memory_analyzer: Memory usage tracking and leak detection
- benchmark_runner: Automated benchmark execution

Example:
    >>> from kaizen.profiling import TAODProfiler
    >>>
    >>> async with TAODProfiler() as profiler:
    ...     result = await adapter.execute(context)
    ...     metrics = profiler.get_metrics()
    ...     print(f"Think phase p95: {metrics['think']['p95_ms']}ms")
"""

from kaizen.profiling.taod_profiler import (
    PhaseMetrics,
    TAODMetrics,
    TAODProfiler,
    CycleMetrics,
)

__all__ = [
    "TAODProfiler",
    "TAODMetrics",
    "PhaseMetrics",
    "CycleMetrics",
]
