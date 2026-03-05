"""
test_cost.py — Tests for agentobs_debug.cost

Phase 3 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.cost import cost_summary
from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError


class TestCostSummary:
    def test_cost_requires_stream(self, sample_trace_id: str) -> None:
        """cost_summary() raises AgentOBSDebugError when stream is None."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_cost_summary_output(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """cost_summary() renders input tokens, output tokens, and total cost."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_cost_summary_aggregates_spans(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Tokens and cost are summed across all spans in the trace."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_cost_summary_no_data(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        """cost_summary() displays zeros gracefully when no cost data is present."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_cost_summary_missing_trace(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """cost_summary() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 3 — not yet implemented")
