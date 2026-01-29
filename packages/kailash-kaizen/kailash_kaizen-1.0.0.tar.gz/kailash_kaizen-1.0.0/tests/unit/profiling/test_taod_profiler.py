"""
Unit tests for TAOD Profiler (TODO-199.1.1).

Tests the profiling infrastructure for TAOD loop performance analysis.
"""

import json
import tempfile
import time
from pathlib import Path

import pytest

from kaizen.profiling.taod_profiler import (
    CycleMetrics,
    PhaseMetrics,
    TAODMetrics,
    TAODProfiler,
    get_profiler,
    set_profiler,
)


# ═══════════════════════════════════════════════════════════════
# PhaseMetrics Tests
# ═══════════════════════════════════════════════════════════════


class TestPhaseMetrics:
    """Tests for PhaseMetrics data class."""

    def test_empty_metrics(self):
        """Empty metrics should return zero for all properties."""
        metrics = PhaseMetrics(phase_name="test")

        assert metrics.count == 0
        assert metrics.total_ms == 0.0
        assert metrics.mean_ms == 0.0
        assert metrics.stddev_ms == 0.0
        assert metrics.p50_ms == 0.0
        assert metrics.p95_ms == 0.0
        assert metrics.p99_ms == 0.0
        assert metrics.min_ms == 0.0
        assert metrics.max_ms == 0.0

    def test_single_sample(self):
        """Single sample should handle edge case correctly."""
        metrics = PhaseMetrics(phase_name="test", samples=[10.0])

        assert metrics.count == 1
        assert metrics.total_ms == 10.0
        assert metrics.mean_ms == 10.0
        assert metrics.stddev_ms == 0.0  # stddev needs >1 sample
        assert metrics.min_ms == 10.0
        assert metrics.max_ms == 10.0

    def test_multiple_samples(self):
        """Multiple samples should calculate correct statistics."""
        # Samples: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
        samples = [float(i * 10) for i in range(1, 11)]
        metrics = PhaseMetrics(phase_name="test", samples=samples)

        assert metrics.count == 10
        assert metrics.total_ms == 550.0
        assert metrics.mean_ms == 55.0
        assert metrics.min_ms == 10.0
        assert metrics.max_ms == 100.0

        # Percentiles (with sorted list of 10 elements: indices 0-9)
        # int(10 * 0.50) = 5 → element at index 5 = 60
        # int(10 * 0.95) = 9 → element at index 9 = 100
        assert metrics.p50_ms == 60.0  # index 5 (6th element)
        assert metrics.p95_ms == 100.0  # index 9 (10th element)

    def test_to_dict(self):
        """to_dict should return serializable dictionary."""
        metrics = PhaseMetrics(phase_name="think", samples=[5.0, 10.0, 15.0])
        result = metrics.to_dict()

        assert result["phase_name"] == "think"
        assert result["count"] == 3
        assert result["total_ms"] == 30.0
        assert result["mean_ms"] == 10.0
        assert "p50_ms" in result
        assert "p95_ms" in result
        assert "p99_ms" in result


# ═══════════════════════════════════════════════════════════════
# CycleMetrics Tests
# ═══════════════════════════════════════════════════════════════


class TestCycleMetrics:
    """Tests for CycleMetrics data class."""

    def test_cycle_metrics_creation(self):
        """CycleMetrics should store all phase timings."""
        cycle = CycleMetrics(
            cycle_number=1,
            think_ms=50.0,
            act_ms=20.0,
            observe_ms=5.0,
            decide_ms=2.0,
            hooks_ms=3.0,
            checkpoint_ms=10.0,
            total_ms=90.0,
            tool_calls=3,
            llm_calls=1,
        )

        assert cycle.cycle_number == 1
        assert cycle.think_ms == 50.0
        assert cycle.act_ms == 20.0
        assert cycle.observe_ms == 5.0
        assert cycle.decide_ms == 2.0
        assert cycle.hooks_ms == 3.0
        assert cycle.checkpoint_ms == 10.0
        assert cycle.total_ms == 90.0
        assert cycle.tool_calls == 3
        assert cycle.llm_calls == 1

    def test_overhead_calculation(self):
        """Overhead should be hooks + checkpoint."""
        cycle = CycleMetrics(
            cycle_number=1,
            think_ms=50.0,
            act_ms=20.0,
            observe_ms=5.0,
            decide_ms=2.0,
            hooks_ms=3.0,
            checkpoint_ms=10.0,
            total_ms=90.0,
        )

        assert cycle.overhead_ms == 13.0  # 3 + 10
        assert abs(cycle.overhead_percent - 14.44) < 0.1  # 13/90 * 100

    def test_to_dict(self):
        """to_dict should include computed properties."""
        cycle = CycleMetrics(
            cycle_number=1,
            think_ms=50.0,
            act_ms=20.0,
            observe_ms=5.0,
            decide_ms=2.0,
            hooks_ms=3.0,
            checkpoint_ms=10.0,
            total_ms=90.0,
        )
        result = cycle.to_dict()

        assert "overhead_ms" in result
        assert "overhead_percent" in result


# ═══════════════════════════════════════════════════════════════
# TAODMetrics Tests
# ═══════════════════════════════════════════════════════════════


class TestTAODMetrics:
    """Tests for TAODMetrics data class."""

    def test_empty_metrics(self):
        """Empty metrics should have zero percentiles."""
        metrics = TAODMetrics()

        assert metrics.cycle_p50_ms == 0.0
        assert metrics.cycle_p95_ms == 0.0
        assert metrics.cycle_p99_ms == 0.0
        assert len(metrics.cycles) == 0

    def test_phases_property(self):
        """phases property should return all phase metrics."""
        metrics = TAODMetrics()
        phases = metrics.phases

        assert "think" in phases
        assert "act" in phases
        assert "observe" in phases
        assert "decide" in phases
        assert "hooks" in phases
        assert "checkpoint" in phases
        assert "system_prompt" in phases
        assert "memory_context" in phases
        assert "tool_schema" in phases

    def test_cycle_percentiles(self):
        """Cycle percentiles should be calculated from cycles list."""
        metrics = TAODMetrics()

        # Add 10 cycles with varying total times
        for i in range(10):
            cycle = CycleMetrics(
                cycle_number=i + 1,
                think_ms=float(i * 10),
                act_ms=5.0,
                observe_ms=2.0,
                decide_ms=1.0,
                hooks_ms=1.0,
                checkpoint_ms=5.0,
                total_ms=float((i + 1) * 10),  # 10, 20, 30, ..., 100
            )
            metrics.cycles.append(cycle)

        # int(10 * 0.50) = 5 → element at index 5 = 60
        # int(10 * 0.95) = 9 → element at index 9 = 100
        assert metrics.cycle_p50_ms == 60.0  # index 5 (6th element)
        assert metrics.cycle_p95_ms == 100.0  # 95th percentile

    def test_to_dict(self):
        """to_dict should return complete serializable structure."""
        metrics = TAODMetrics()
        metrics.total_duration_ms = 1000.0
        metrics.total_cycles = 10
        metrics.timestamp = "2026-01-24T10:00:00"

        result = metrics.to_dict()

        assert "summary" in result
        assert "phases" in result
        assert "cycles" in result
        assert result["summary"]["total_duration_ms"] == 1000.0


# ═══════════════════════════════════════════════════════════════
# TAODProfiler Tests
# ═══════════════════════════════════════════════════════════════


class TestTAODProfiler:
    """Tests for TAODProfiler class."""

    def test_profiler_disabled(self):
        """Disabled profiler should be no-op."""
        profiler = TAODProfiler(enabled=False)
        profiler.start()
        profiler.start_phase("think")
        profiler.end_phase("think")
        profiler.complete_cycle()
        metrics = profiler.stop()

        assert len(metrics.cycles) == 0

    def test_profiler_basic_flow(self):
        """Basic profiling flow should record timings."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()

        # Simulate a cycle
        profiler.start_cycle()

        profiler.start_phase("think")
        time.sleep(0.01)  # 10ms
        profiler.end_phase("think")

        profiler.start_phase("decide")
        time.sleep(0.001)  # 1ms
        profiler.end_phase("decide")

        profiler.start_phase("act")
        time.sleep(0.005)  # 5ms
        profiler.end_phase("act")

        profiler.start_phase("observe")
        time.sleep(0.001)  # 1ms
        profiler.end_phase("observe")

        profiler.complete_cycle(tool_calls=1)

        metrics = profiler.stop()

        # Verify cycle was recorded
        assert len(metrics.cycles) == 1
        assert metrics.cycles[0].tool_calls == 1

        # Verify phase timings
        assert metrics.think.count == 1
        assert metrics.think.mean_ms >= 9.0  # Should be ~10ms

        assert metrics.act.count == 1
        assert metrics.act.mean_ms >= 4.0  # Should be ~5ms

    def test_phase_context_manager(self):
        """Phase context manager should record timing."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()
        profiler.start_cycle()

        with profiler.phase("think"):
            time.sleep(0.005)  # 5ms

        profiler.complete_cycle()
        metrics = profiler.stop()

        assert metrics.think.count == 1
        assert metrics.think.mean_ms >= 4.0

    def test_multiple_cycles(self):
        """Multiple cycles should all be recorded."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()

        for i in range(5):
            profiler.start_cycle()

            with profiler.phase("think"):
                time.sleep(0.001)

            profiler.complete_cycle(tool_calls=i)

        metrics = profiler.stop()

        assert len(metrics.cycles) == 5
        assert metrics.total_cycles == 5
        assert metrics.think.count == 5

    def test_check_targets(self):
        """check_targets should compare against performance targets."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()

        # Create cycles that meet targets (p50 < 50ms)
        for _ in range(10):
            profiler.start_cycle()

            with profiler.phase("think"):
                time.sleep(0.01)  # 10ms

            profiler.complete_cycle()

        profiler.stop()
        targets = profiler.check_targets()

        # Should have cycle targets checked
        assert "cycle_p50_ms" in targets
        assert "actual" in targets["cycle_p50_ms"]
        assert "target" in targets["cycle_p50_ms"]
        assert "passed" in targets["cycle_p50_ms"]

    def test_export_json(self):
        """export_json should create valid JSON file."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()

        profiler.start_cycle()
        with profiler.phase("think"):
            time.sleep(0.001)
        profiler.complete_cycle()

        profiler.stop()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "profile.json"
            profiler.export_json(output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "summary" in data
            assert "phases" in data
            assert "cycles" in data
            assert "targets" in data

    def test_print_summary(self, capsys):
        """print_summary should output formatted summary."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()

        for _ in range(3):
            profiler.start_cycle()
            with profiler.phase("think"):
                time.sleep(0.001)
            profiler.complete_cycle()

        profiler.stop()
        profiler.print_summary()

        captured = capsys.readouterr()
        assert "TAOD PROFILING SUMMARY" in captured.out
        assert "CYCLE LATENCY" in captured.out
        assert "PHASE BREAKDOWN" in captured.out
        assert "TARGET CHECK" in captured.out

    def test_end_phase_without_start(self):
        """Ending phase without starting should log warning."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()

        duration = profiler.end_phase("nonexistent")

        assert duration == 0.0


# ═══════════════════════════════════════════════════════════════
# Global Profiler Tests
# ═══════════════════════════════════════════════════════════════


class TestGlobalProfiler:
    """Tests for global profiler functions."""

    def test_get_profiler_creates_instance(self):
        """get_profiler should create instance if none exists."""
        # Reset global state
        set_profiler(None)

        profiler = get_profiler()

        assert profiler is not None
        assert isinstance(profiler, TAODProfiler)

    def test_set_profiler(self):
        """set_profiler should update global instance."""
        custom_profiler = TAODProfiler(enabled=True)
        set_profiler(custom_profiler)

        assert get_profiler() is custom_profiler


# ═══════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════


class TestProfilerIntegration:
    """Integration tests for profiler with realistic scenarios."""

    def test_realistic_taod_cycle(self):
        """Simulate realistic TAOD cycle timings."""
        profiler = TAODProfiler(enabled=True)
        profiler.start()

        for cycle_num in range(10):
            profiler.start_cycle()

            # THINK: System prompt + memory + LLM call (~20-30ms simulated)
            with profiler.phase("system_prompt"):
                time.sleep(0.001)  # 1ms

            with profiler.phase("memory_context"):
                time.sleep(0.002)  # 2ms

            with profiler.phase("think"):
                time.sleep(0.015)  # 15ms (simulated LLM)

            # DECIDE: Quick decision logic (~1ms)
            with profiler.phase("decide"):
                time.sleep(0.001)

            # ACT: Tool execution (~5-10ms)
            with profiler.phase("act"):
                time.sleep(0.005 + (cycle_num * 0.001))  # Variable

            # OBSERVE: Process results (~1ms)
            with profiler.phase("observe"):
                time.sleep(0.001)

            # Hooks (~0.5ms)
            with profiler.phase("hooks"):
                time.sleep(0.0005)

            # Checkpoint every 3 cycles (~5ms)
            if cycle_num % 3 == 0:
                with profiler.phase("checkpoint"):
                    time.sleep(0.005)

            profiler.complete_cycle(tool_calls=2, llm_calls=1)

        metrics = profiler.stop()

        # Verify all phases recorded
        assert metrics.think.count == 10
        assert metrics.act.count == 10
        assert metrics.observe.count == 10
        assert metrics.decide.count == 10
        assert metrics.hooks.count == 10
        assert metrics.checkpoint.count > 0  # At least some checkpoints

        # Verify totals
        assert metrics.total_cycles == 10
        assert metrics.total_tool_calls == 20  # 2 per cycle
        assert metrics.total_llm_calls == 10

        # Verify cycle timing (should be roughly 25-35ms per cycle)
        assert metrics.cycle_p50_ms > 20.0
        assert metrics.cycle_p95_ms < 100.0  # Should meet target
