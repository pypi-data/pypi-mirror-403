"""
TAOD Loop Profiler (TODO-199.1.1).

Provides detailed phase-by-phase profiling for the Think-Act-Observe-Decide
loop to identify performance bottlenecks and track optimization progress.

Features:
- Per-phase timing (Think, Act, Observe, Decide)
- Per-cycle aggregation
- Hook overhead tracking
- Tool execution breakdown
- System prompt generation timing
- Memory context building timing
- Percentile calculations (p50, p95, p99)

Usage:
    >>> from kaizen.profiling import TAODProfiler
    >>>
    >>> profiler = TAODProfiler()
    >>> profiler.start()
    >>>
    >>> # In your TAOD loop phases:
    >>> profiler.start_phase("think")
    >>> await think_phase()
    >>> profiler.end_phase("think")
    >>>
    >>> # Get metrics
    >>> metrics = profiler.get_metrics()
    >>> print(f"Think p95: {metrics.phases['think'].p95_ms:.2f}ms")

Integration with LocalKaizenAdapter:
    The profiler can be enabled via AutonomousConfig:

    >>> config = AutonomousConfig(
    ...     enable_profiling=True,
    ...     profile_output_path=Path("profiles/run.json")
    ... )
"""

import json
import logging
import statistics
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PhaseMetrics:
    """Metrics for a single TAOD phase."""

    phase_name: str
    samples: List[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of samples."""
        return len(self.samples)

    @property
    def total_ms(self) -> float:
        """Total time spent in this phase."""
        return sum(self.samples)

    @property
    def mean_ms(self) -> float:
        """Mean latency in milliseconds."""
        return statistics.mean(self.samples) if self.samples else 0.0

    @property
    def stddev_ms(self) -> float:
        """Standard deviation in milliseconds."""
        return statistics.stdev(self.samples) if len(self.samples) > 1 else 0.0

    @property
    def p50_ms(self) -> float:
        """Median latency."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        return sorted_samples[int(len(sorted_samples) * 0.50)]

    @property
    def p95_ms(self) -> float:
        """95th percentile latency."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        return sorted_samples[int(len(sorted_samples) * 0.95)]

    @property
    def p99_ms(self) -> float:
        """99th percentile latency."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        return sorted_samples[int(len(sorted_samples) * 0.99)]

    @property
    def min_ms(self) -> float:
        """Minimum latency."""
        return min(self.samples) if self.samples else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum latency."""
        return max(self.samples) if self.samples else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "phase_name": self.phase_name,
            "count": self.count,
            "total_ms": self.total_ms,
            "mean_ms": self.mean_ms,
            "stddev_ms": self.stddev_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
        }


@dataclass
class CycleMetrics:
    """Metrics for a complete TAOD cycle."""

    cycle_number: int
    think_ms: float
    act_ms: float
    observe_ms: float
    decide_ms: float
    hooks_ms: float
    checkpoint_ms: float
    total_ms: float
    tool_calls: int = 0
    llm_calls: int = 1

    @property
    def overhead_ms(self) -> float:
        """Non-core overhead (hooks + checkpoint)."""
        return self.hooks_ms + self.checkpoint_ms

    @property
    def overhead_percent(self) -> float:
        """Overhead as percentage of total."""
        return (self.overhead_ms / self.total_ms * 100) if self.total_ms > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cycle_number": self.cycle_number,
            "think_ms": self.think_ms,
            "act_ms": self.act_ms,
            "observe_ms": self.observe_ms,
            "decide_ms": self.decide_ms,
            "hooks_ms": self.hooks_ms,
            "checkpoint_ms": self.checkpoint_ms,
            "total_ms": self.total_ms,
            "tool_calls": self.tool_calls,
            "llm_calls": self.llm_calls,
            "overhead_ms": self.overhead_ms,
            "overhead_percent": self.overhead_percent,
        }


@dataclass
class TAODMetrics:
    """Complete TAOD profiling metrics."""

    # Per-phase metrics
    think: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("think"))
    act: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("act"))
    observe: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("observe"))
    decide: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("decide"))

    # Overhead metrics
    hooks: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("hooks"))
    checkpoint: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("checkpoint"))
    system_prompt: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("system_prompt"))
    memory_context: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("memory_context"))
    tool_schema: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("tool_schema"))

    # Per-cycle metrics
    cycles: List[CycleMetrics] = field(default_factory=list)

    # Metadata
    total_duration_ms: float = 0.0
    total_cycles: int = 0
    total_tool_calls: int = 0
    total_llm_calls: int = 0
    timestamp: str = ""

    @property
    def cycle_p50_ms(self) -> float:
        """Median cycle time."""
        if not self.cycles:
            return 0.0
        sorted_totals = sorted(c.total_ms for c in self.cycles)
        return sorted_totals[int(len(sorted_totals) * 0.50)]

    @property
    def cycle_p95_ms(self) -> float:
        """95th percentile cycle time."""
        if not self.cycles:
            return 0.0
        sorted_totals = sorted(c.total_ms for c in self.cycles)
        return sorted_totals[int(len(sorted_totals) * 0.95)]

    @property
    def cycle_p99_ms(self) -> float:
        """99th percentile cycle time."""
        if not self.cycles:
            return 0.0
        sorted_totals = sorted(c.total_ms for c in self.cycles)
        return sorted_totals[int(len(sorted_totals) * 0.99)]

    @property
    def phases(self) -> Dict[str, PhaseMetrics]:
        """All phases as dictionary."""
        return {
            "think": self.think,
            "act": self.act,
            "observe": self.observe,
            "decide": self.decide,
            "hooks": self.hooks,
            "checkpoint": self.checkpoint,
            "system_prompt": self.system_prompt,
            "memory_context": self.memory_context,
            "tool_schema": self.tool_schema,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "summary": {
                "total_duration_ms": self.total_duration_ms,
                "total_cycles": self.total_cycles,
                "total_tool_calls": self.total_tool_calls,
                "total_llm_calls": self.total_llm_calls,
                "cycle_p50_ms": self.cycle_p50_ms,
                "cycle_p95_ms": self.cycle_p95_ms,
                "cycle_p99_ms": self.cycle_p99_ms,
                "timestamp": self.timestamp,
            },
            "phases": {name: phase.to_dict() for name, phase in self.phases.items()},
            "cycles": [c.to_dict() for c in self.cycles],
        }


class TAODProfiler:
    """
    Profiler for TAOD loop performance analysis.

    Tracks timing for each phase of the Think-Act-Observe-Decide loop,
    including overhead from hooks, checkpoints, and context building.

    Thread-safe for use within async contexts.

    Example:
        >>> profiler = TAODProfiler()
        >>> profiler.start()
        >>>
        >>> # Profile phases
        >>> with profiler.phase("think"):
        ...     await think_phase()
        >>>
        >>> # Complete cycle
        >>> profiler.complete_cycle(tool_calls=3)
        >>>
        >>> # Get results
        >>> metrics = profiler.get_metrics()
        >>> profiler.export_json("profile.json")
    """

    # Performance targets (from TODO-199)
    TARGETS = {
        "cycle_p50_ms": 50.0,
        "cycle_p95_ms": 100.0,
        "cycle_p99_ms": 200.0,
        "tool_execution_p95_ms": 20.0,
        "memory_recall_p95_ms": 10.0,
        "checkpoint_save_p95_ms": 1000.0,
        "checkpoint_load_p95_ms": 500.0,
    }

    def __init__(self, enabled: bool = True):
        """
        Initialize the profiler.

        Args:
            enabled: Whether profiling is enabled. When False, all operations
                    are no-ops for minimal overhead.
        """
        self.enabled = enabled
        self._metrics = TAODMetrics()
        self._start_time: Optional[float] = None
        self._phase_starts: Dict[str, float] = {}
        self._current_cycle: Dict[str, float] = {}
        self._cycle_start: Optional[float] = None
        self._current_cycle_number = 0

    def start(self) -> None:
        """Start profiling session."""
        if not self.enabled:
            return

        self._start_time = time.perf_counter()
        self._metrics.timestamp = datetime.now().isoformat()
        logger.debug("TAOD profiling started")

    def stop(self) -> TAODMetrics:
        """
        Stop profiling and finalize metrics.

        Returns:
            Complete TAODMetrics with all collected data
        """
        if not self.enabled:
            return self._metrics

        if self._start_time:
            self._metrics.total_duration_ms = (
                time.perf_counter() - self._start_time
            ) * 1000

        self._metrics.total_cycles = len(self._metrics.cycles)
        self._metrics.total_tool_calls = sum(c.tool_calls for c in self._metrics.cycles)
        self._metrics.total_llm_calls = sum(c.llm_calls for c in self._metrics.cycles)

        logger.debug(
            f"TAOD profiling stopped: {self._metrics.total_cycles} cycles, "
            f"{self._metrics.total_duration_ms:.2f}ms total"
        )

        return self._metrics

    def start_cycle(self) -> None:
        """Start timing a new TAOD cycle."""
        if not self.enabled:
            return

        self._current_cycle_number += 1
        self._cycle_start = time.perf_counter()
        self._current_cycle = {
            "think_ms": 0.0,
            "act_ms": 0.0,
            "observe_ms": 0.0,
            "decide_ms": 0.0,
            "hooks_ms": 0.0,
            "checkpoint_ms": 0.0,
            "tool_calls": 0,
            "llm_calls": 0,
        }

    def complete_cycle(self, tool_calls: int = 0, llm_calls: int = 1) -> None:
        """
        Complete the current cycle and record metrics.

        Args:
            tool_calls: Number of tool calls in this cycle
            llm_calls: Number of LLM calls in this cycle
        """
        if not self.enabled or self._cycle_start is None:
            return

        total_ms = (time.perf_counter() - self._cycle_start) * 1000

        cycle = CycleMetrics(
            cycle_number=self._current_cycle_number,
            think_ms=self._current_cycle.get("think_ms", 0.0),
            act_ms=self._current_cycle.get("act_ms", 0.0),
            observe_ms=self._current_cycle.get("observe_ms", 0.0),
            decide_ms=self._current_cycle.get("decide_ms", 0.0),
            hooks_ms=self._current_cycle.get("hooks_ms", 0.0),
            checkpoint_ms=self._current_cycle.get("checkpoint_ms", 0.0),
            total_ms=total_ms,
            tool_calls=tool_calls,
            llm_calls=llm_calls,
        )

        self._metrics.cycles.append(cycle)
        self._cycle_start = None

    def start_phase(self, phase_name: str) -> None:
        """
        Start timing a phase.

        Args:
            phase_name: Name of the phase (think, act, observe, decide, hooks, etc.)
        """
        if not self.enabled:
            return

        self._phase_starts[phase_name] = time.perf_counter()

    def end_phase(self, phase_name: str) -> float:
        """
        End timing a phase and record the duration.

        Args:
            phase_name: Name of the phase

        Returns:
            Duration in milliseconds
        """
        if not self.enabled:
            return 0.0

        start_time = self._phase_starts.pop(phase_name, None)
        if start_time is None:
            logger.warning(f"Phase '{phase_name}' was never started")
            return 0.0

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Record to appropriate phase metrics
        phase_metrics = self._get_phase_metrics(phase_name)
        if phase_metrics:
            phase_metrics.samples.append(duration_ms)

        # Also record to current cycle if applicable
        cycle_key = f"{phase_name}_ms"
        if cycle_key in self._current_cycle:
            self._current_cycle[cycle_key] += duration_ms

        return duration_ms

    @contextmanager
    def phase(self, phase_name: str):
        """
        Context manager for timing a phase.

        Example:
            >>> with profiler.phase("think"):
            ...     await think_phase()

        Args:
            phase_name: Name of the phase

        Yields:
            None
        """
        self.start_phase(phase_name)
        try:
            yield
        finally:
            self.end_phase(phase_name)

    def record_tool_execution(self, duration_ms: float) -> None:
        """
        Record a tool execution duration.

        Args:
            duration_ms: Tool execution time in milliseconds
        """
        if not self.enabled:
            return

        # Tool executions are part of ACT phase
        self._metrics.act.samples.append(duration_ms)

    def record_llm_call(self, duration_ms: float) -> None:
        """
        Record an LLM API call duration.

        Args:
            duration_ms: LLM call time in milliseconds
        """
        if not self.enabled:
            return

        # LLM calls are part of THINK phase
        self._metrics.think.samples.append(duration_ms)

    def _get_phase_metrics(self, phase_name: str) -> Optional[PhaseMetrics]:
        """Get PhaseMetrics object for a phase name."""
        return self._metrics.phases.get(phase_name)

    def get_metrics(self) -> TAODMetrics:
        """
        Get current metrics snapshot.

        Returns:
            TAODMetrics with all collected data
        """
        return self._metrics

    def check_targets(self) -> Dict[str, Dict[str, Any]]:
        """
        Check metrics against performance targets.

        Returns:
            Dictionary with target name, actual value, target value, and pass/fail
        """
        results = {}

        # Cycle targets
        results["cycle_p50_ms"] = {
            "actual": self._metrics.cycle_p50_ms,
            "target": self.TARGETS["cycle_p50_ms"],
            "passed": self._metrics.cycle_p50_ms <= self.TARGETS["cycle_p50_ms"],
        }
        results["cycle_p95_ms"] = {
            "actual": self._metrics.cycle_p95_ms,
            "target": self.TARGETS["cycle_p95_ms"],
            "passed": self._metrics.cycle_p95_ms <= self.TARGETS["cycle_p95_ms"],
        }
        results["cycle_p99_ms"] = {
            "actual": self._metrics.cycle_p99_ms,
            "target": self.TARGETS["cycle_p99_ms"],
            "passed": self._metrics.cycle_p99_ms <= self.TARGETS["cycle_p99_ms"],
        }

        # Tool execution targets
        if self._metrics.act.samples:
            results["tool_execution_p95_ms"] = {
                "actual": self._metrics.act.p95_ms,
                "target": self.TARGETS["tool_execution_p95_ms"],
                "passed": self._metrics.act.p95_ms <= self.TARGETS["tool_execution_p95_ms"],
            }

        # Memory targets
        if self._metrics.memory_context.samples:
            results["memory_recall_p95_ms"] = {
                "actual": self._metrics.memory_context.p95_ms,
                "target": self.TARGETS["memory_recall_p95_ms"],
                "passed": (
                    self._metrics.memory_context.p95_ms
                    <= self.TARGETS["memory_recall_p95_ms"]
                ),
            }

        # Checkpoint targets
        if self._metrics.checkpoint.samples:
            results["checkpoint_save_p95_ms"] = {
                "actual": self._metrics.checkpoint.p95_ms,
                "target": self.TARGETS["checkpoint_save_p95_ms"],
                "passed": (
                    self._metrics.checkpoint.p95_ms
                    <= self.TARGETS["checkpoint_save_p95_ms"]
                ),
            }

        return results

    def export_json(self, path: Path) -> None:
        """
        Export metrics to JSON file.

        Args:
            path: Output file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self._metrics.to_dict()
        data["targets"] = self.check_targets()

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"TAOD profile exported to {path}")

    def print_summary(self) -> None:
        """Print human-readable summary of metrics."""
        metrics = self._metrics

        print("\n" + "=" * 70)
        print("TAOD PROFILING SUMMARY")
        print("=" * 70)
        print(f"Total Duration: {metrics.total_duration_ms:.2f}ms")
        print(f"Total Cycles: {metrics.total_cycles}")
        print(f"Total Tool Calls: {metrics.total_tool_calls}")
        print(f"Total LLM Calls: {metrics.total_llm_calls}")
        print()

        print("CYCLE LATENCY:")
        print(f"  P50: {metrics.cycle_p50_ms:.2f}ms (target: <{self.TARGETS['cycle_p50_ms']}ms)")
        print(f"  P95: {metrics.cycle_p95_ms:.2f}ms (target: <{self.TARGETS['cycle_p95_ms']}ms)")
        print(f"  P99: {metrics.cycle_p99_ms:.2f}ms (target: <{self.TARGETS['cycle_p99_ms']}ms)")
        print()

        print("PHASE BREAKDOWN:")
        for name, phase in metrics.phases.items():
            if phase.count > 0:
                print(f"  {name.upper():15s} | "
                      f"count={phase.count:4d} | "
                      f"mean={phase.mean_ms:8.2f}ms | "
                      f"p95={phase.p95_ms:8.2f}ms | "
                      f"total={phase.total_ms:10.2f}ms")
        print()

        print("TARGET CHECK:")
        targets = self.check_targets()
        for name, result in targets.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"  {name:25s}: {result['actual']:8.2f}ms vs {result['target']:8.2f}ms - {status}")

        print("=" * 70 + "\n")


# Global profiler instance for easy access
_global_profiler: Optional[TAODProfiler] = None


def get_profiler() -> TAODProfiler:
    """Get or create global profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = TAODProfiler(enabled=False)
    return _global_profiler


def set_profiler(profiler: TAODProfiler) -> None:
    """Set global profiler instance."""
    global _global_profiler
    _global_profiler = profiler


__all__ = [
    "TAODProfiler",
    "TAODMetrics",
    "PhaseMetrics",
    "CycleMetrics",
    "get_profiler",
    "set_profiler",
]
