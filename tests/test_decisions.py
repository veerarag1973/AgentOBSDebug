"""
test_decisions.py — Tests for agentobs_debug.decisions

Phase 3 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.decisions import show_decisions
from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError


class TestShowDecisions:
    def test_decisions_requires_stream(self, sample_trace_id: str) -> None:
        """show_decisions() raises AgentOBSDebugError when stream is None."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_show_decisions_output(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """show_decisions() renders decision name, options, and chosen value."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_show_decisions_empty(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        """show_decisions() prints fallback message when no decisions exist."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_show_decisions_missing_trace(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """show_decisions() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 3 — not yet implemented")
