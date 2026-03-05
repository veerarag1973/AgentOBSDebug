"""
test_inspect.py — Tests for agentobs_debug.inspect

Phase 2 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.inspect import inspect_trace


class TestInspectTrace:
    def test_inspect_requires_stream(self, sample_trace_id: str) -> None:
        """inspect_trace() raises AgentOBSDebugError when stream is None."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_inspect_valid_trace(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """inspect_trace() renders all required summary fields."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_inspect_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """inspect_trace() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_inspect_missing_cost_data(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """inspect_trace() displays $0.0000 when no cost data is present."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_inspect_token_aggregation(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """inspect_trace() sums tokens across all spans."""
        pytest.skip("Phase 2 — not yet implemented")
