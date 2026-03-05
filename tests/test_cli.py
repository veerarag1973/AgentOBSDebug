"""
test_cli.py — Tests for agentobs_debug.cli

Phase 4 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.cli import main


class TestCLIReplay:
    def test_cli_replay(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug replay produces expected step output."""
        pytest.skip("Phase 4 — not yet implemented")

    def test_cli_replay_missing_trace_exits_1(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """CLI replay exits with code 1 and prints error to stderr on missing trace."""
        pytest.skip("Phase 4 — not yet implemented")


class TestCLIInspect:
    def test_cli_inspect(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug inspect produces expected summary output."""
        pytest.skip("Phase 4 — not yet implemented")


class TestCLITree:
    def test_cli_tree(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug tree produces expected hierarchy output."""
        pytest.skip("Phase 4 — not yet implemented")


class TestCLITimeline:
    def test_cli_timeline(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug timeline produces expected chronological output."""
        pytest.skip("Phase 4 — not yet implemented")


class TestCLITools:
    def test_cli_tools(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug tools lists tool calls."""
        pytest.skip("Phase 4 — not yet implemented")


class TestCLIDecisions:
    def test_cli_decisions(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug decisions lists decision points."""
        pytest.skip("Phase 4 — not yet implemented")


class TestCLICost:
    def test_cli_cost(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug cost prints cost summary."""
        pytest.skip("Phase 4 — not yet implemented")


class TestCLIErrorHandling:
    def test_cli_missing_file_exits_1(self, tmp_path: Path, sample_trace_id: str) -> None:
        """CLI exits with code 1 and prints error to stderr for a missing file."""
        pytest.skip("Phase 4 — not yet implemented")

    def test_cli_no_traceback_on_error(
        self, capsys: pytest.CaptureFixture, tmp_path: Path, sample_trace_id: str
    ) -> None:
        """CLI never emits a Python traceback to stderr on a handled error."""
        pytest.skip("Phase 4 — not yet implemented")

    def test_cli_unknown_trace_exits_1(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """CLI exits with code 1 for every command when trace_id is not found."""
        pytest.skip("Phase 4 — not yet implemented")
