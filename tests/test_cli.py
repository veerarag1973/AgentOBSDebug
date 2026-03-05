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
        main(["replay", str(sample_jsonl_path), "--trace", sample_trace_id])
        out = capsys.readouterr().out
        assert "Agent Run:" in out
        assert "Step" in out

    def test_cli_replay_missing_trace_exits_1(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """CLI replay exits with code 1 and prints error to stderr on missing trace."""
        with pytest.raises(SystemExit) as exc_info:
            main(["replay", str(sample_jsonl_path), "--trace", unknown_trace_id])
        assert exc_info.value.code == 1


class TestCLIInspect:
    def test_cli_inspect(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug inspect produces expected summary output."""
        main(["inspect", str(sample_jsonl_path), "--trace", sample_trace_id])
        out = capsys.readouterr().out
        assert "Trace Summary" in out
        assert "Trace ID:" in out


class TestCLITree:
    def test_cli_tree(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug tree produces expected hierarchy output."""
        main(["tree", str(sample_jsonl_path), "--trace", sample_trace_id])
        out = capsys.readouterr().out
        assert "agent_run" in out


class TestCLITimeline:
    def test_cli_timeline(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug timeline produces expected chronological output."""
        main(["timeline", str(sample_jsonl_path), "--trace", sample_trace_id])
        out = capsys.readouterr().out
        assert "ms" in out
        assert "started" in out


class TestCLITools:
    def test_cli_tools(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug tools lists tool calls."""
        main(["tools", str(sample_jsonl_path), "--trace", sample_trace_id])
        out = capsys.readouterr().out
        assert "Tool Calls" in out
        assert "search_api" in out


class TestCLIDecisions:
    def test_cli_decisions(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug decisions lists decision points."""
        main(["decisions", str(sample_jsonl_path), "--trace", sample_trace_id])
        out = capsys.readouterr().out
        assert "Decision:" in out
        assert "tool_selection" in out


class TestCLICost:
    def test_cli_cost(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """agentobs-debug cost prints cost summary."""
        main(["cost", str(sample_jsonl_path), "--trace", sample_trace_id])
        out = capsys.readouterr().out
        assert "Cost Summary" in out
        assert "Total cost:" in out


class TestCLIErrorHandling:
    def test_cli_missing_file_exits_1(self, tmp_path: Path, sample_trace_id: str) -> None:
        """CLI exits with code 1 and prints error to stderr for a missing file."""
        missing = str(tmp_path / "nonexistent.jsonl")
        with pytest.raises(SystemExit) as exc_info:
            main(["replay", missing, "--trace", sample_trace_id])
        assert exc_info.value.code == 1

    def test_cli_no_traceback_on_error(
        self, capsys: pytest.CaptureFixture, tmp_path: Path, sample_trace_id: str
    ) -> None:
        """CLI never emits a Python traceback to stderr on a handled error."""
        missing = str(tmp_path / "nonexistent.jsonl")
        with pytest.raises(SystemExit):
            main(["replay", missing, "--trace", sample_trace_id])
        err = capsys.readouterr().err
        assert "Traceback" not in err

    def test_cli_unknown_trace_exits_1(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """CLI exits with code 1 for every command when trace_id is not found."""
        with pytest.raises(SystemExit) as exc_info:
            main(["inspect", str(sample_jsonl_path), "--trace", unknown_trace_id])
        assert exc_info.value.code == 1




