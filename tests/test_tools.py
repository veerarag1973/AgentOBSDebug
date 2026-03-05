"""
test_tools.py — Tests for agentobs_debug.tools

Phase 3 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.tools import show_tools


class TestShowTools:
    def test_tools_requires_stream(self, sample_trace_id: str) -> None:
        """show_tools() raises AgentOBSDebugError when stream is None."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_show_tools_output(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """show_tools() renders tool name and arguments in call syntax."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_show_tools_empty(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        """show_tools() prints fallback message when no tool calls exist."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_show_tools_missing_trace(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """show_tools() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 3 — not yet implemented")

    def test_show_tools_argument_formatting(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Arguments are formatted as key=\"value\" pairs joined by commas."""
        pytest.skip("Phase 3 — not yet implemented")
