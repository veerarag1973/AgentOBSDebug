"""
test_timeline.py — Tests for agentobs_debug.timeline

Phase 2 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.timeline import timeline


class TestTimeline:
    def test_timeline_requires_stream(self, sample_trace_id: str) -> None:
        """timeline() raises AgentOBSDebugError when stream is None."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_timeline_output_format(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """timeline() output has correct ms offsets and span labels."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_timeline_ordering(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Timeline rows are always in ascending time order."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_timeline_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """timeline() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_timeline_first_offset_is_zero(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """The first timeline row always starts at 0 ms."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_timeline_identical_timestamps_stable_sort(self, tmp_path: Path) -> None:
        """Spans with identical timestamps appear in stable (consistent) order."""
        pytest.skip("Phase 2 — not yet implemented")
