"""
test_replay.py — Tests for agentobs_debug.replay

Phase 2 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.replay import replay


class TestReplay:
    def test_replay_requires_stream(self, sample_trace_id: str) -> None:
        """replay() raises AgentOBSDebugError when stream is None."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_replay_output_format(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """replay() stdout matches the expected header + step format."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_replay_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """replay() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_replay_no_steps(self, tmp_path: Path) -> None:
        """replay() prints only the header when the agent run has no child steps."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_replay_missing_token_data(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Steps without TokenUsage display 'N/A' gracefully."""
        pytest.skip("Phase 2 — not yet implemented")
