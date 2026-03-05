"""
test_performance.py — Performance benchmarks for agentobs_debug.

Validates that core functions handle 10,000 events / 1,000 spans
within the thresholds defined in MODULE-SPEC-0001 §16.

Thresholds
----------
load_events()           < 2 s  on 10,000 events
replay()                < 1 s  on 1,000-span trace
print_trace_tree()      < 1 s  on 1,000-span trace
timeline()              < 1 s  on 1,000-span trace
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

# Allow slow machines / CI to scale thresholds: AGENTOBS_PERF_MULTIPLIER=2 doubles them.
_M = float(os.environ.get("AGENTOBS_PERF_MULTIPLIER", "1.0"))

LARGE_FIXTURE = Path(__file__).parent / "fixtures" / "large_events.jsonl"
FOCUS_TRACE   = "aaaa0000000000000000000000000001"


@pytest.fixture(scope="module")
def large_jsonl_path() -> Path:
    if not LARGE_FIXTURE.exists():
        pytest.skip("large_events.jsonl not found — run tests/generate_large_fixture.py first")
    return LARGE_FIXTURE


class TestPerformance:
    def test_load_events_10k_under_2s(self, large_jsonl_path: Path) -> None:
        """load_events() on 10,000 events completes in < 2 seconds."""
        from agentobs_debug import load_events

        t0 = time.perf_counter()
        load_events(str(large_jsonl_path))
        elapsed = time.perf_counter() - t0
        assert elapsed < 2.0 * _M, f"load_events took {elapsed:.2f}s (threshold: {2.0 * _M:.1f}s)"

    def test_replay_1k_spans_under_1s(
        self, large_jsonl_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """replay() on the 1,000-span focus trace completes in < 1 second."""
        from agentobs_debug import load_events, replay

        stream = load_events(str(large_jsonl_path))
        t0 = time.perf_counter()
        replay(FOCUS_TRACE, stream=stream)
        elapsed = time.perf_counter() - t0
        capsys.readouterr()  # discard output
        assert elapsed < 1.0 * _M, f"replay took {elapsed:.2f}s (threshold: {1.0 * _M:.1f}s)"

    def test_print_trace_tree_1k_spans_under_1s(
        self, large_jsonl_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """print_trace_tree() on the 1,000-span focus trace completes in < 1 second."""
        from agentobs_debug import load_events, print_trace_tree

        stream = load_events(str(large_jsonl_path))
        t0 = time.perf_counter()
        print_trace_tree(FOCUS_TRACE, stream=stream)
        elapsed = time.perf_counter() - t0
        capsys.readouterr()
        assert elapsed < 1.0 * _M, (
            f"print_trace_tree took {elapsed:.2f}s (threshold: {1.0 * _M:.1f}s)"
        )

    def test_timeline_1k_spans_under_1s(
        self, large_jsonl_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """timeline() on the 1,000-span focus trace completes in < 1 second."""
        from agentobs_debug import load_events, timeline

        stream = load_events(str(large_jsonl_path))
        t0 = time.perf_counter()
        timeline(FOCUS_TRACE, stream=stream)
        elapsed = time.perf_counter() - t0
        capsys.readouterr()
        assert elapsed < 1.0 * _M, f"timeline took {elapsed:.2f}s (threshold: {1.0 * _M:.1f}s)"
