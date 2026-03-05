"""
test_report.py — Tests for agentobs_debug.report (batch_report).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.report import batch_report

SAMPLE_TRACE = "4bf92f3577b34da6a3ce929d0e0e4736"


class TestBatchReportText:
    def test_text_includes_trace_id(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path))
        out = capsys.readouterr().out
        assert SAMPLE_TRACE in out

    def test_text_includes_token_count(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path))
        out = capsys.readouterr().out
        assert "740" in out

    def test_text_includes_cost(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path))
        out = capsys.readouterr().out
        assert "0.0030" in out

    def test_text_separator_between_traces(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Two traces in the same file → separator line
        tid2 = "aaaabbbbccccddddeeeeffffaaaabbbb"
        src = Path(__file__).parent / "fixtures" / "sample_events.jsonl"
        lines = src.read_text(encoding="utf-8").splitlines()
        extra = {
            "event_id": "ee000000000000000000000001",
            "event_type": "llm.trace.agent.run.completed",
            "payload": {"agent_name": "agent_b", "start_time_unix_nano": 1700000000000000000,
                        "end_time_unix_nano": 1700000000500000000, "status": "ok"},
            "schema_version": "2.0",
            "source": "b@1.0",
            "span_id": "bbbb000000000001",
            "timestamp": "2023-11-14T22:13:30.000000Z",
            "trace_id": tid2,
        }
        two_trace = tmp_path / "two.jsonl"
        two_trace.write_text("\n".join(lines) + "\n" + json.dumps(extra) + "\n", encoding="utf-8")
        batch_report(str(two_trace))
        out = capsys.readouterr().out
        assert "---" in out


class TestBatchReportJSON:
    def test_json_is_list(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), output_format="json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_json_has_required_keys(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), output_format="json")
        out = capsys.readouterr().out
        row = json.loads(out)[0]
        for key in ("trace_id", "spans", "tokens", "cost_usd", "duration_s", "status"):
            assert key in row, f"missing key {key!r}"

    def test_json_trace_id_correct(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), output_format="json")
        out = capsys.readouterr().out
        assert json.loads(out)[0]["trace_id"] == SAMPLE_TRACE

    def test_json_tokens(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), output_format="json")
        out = capsys.readouterr().out
        assert json.loads(out)[0]["tokens"] == 740

    def test_json_subset_of_trace_ids(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), trace_ids=[SAMPLE_TRACE], output_format="json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1

    def test_json_unknown_trace_returns_empty_entry(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tid = "ffffffffffffffffffffffffffffffff"
        batch_report(str(sample_jsonl_path), trace_ids=[tid], output_format="json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["trace_id"] == tid


class TestBatchReportCSV:
    def test_csv_has_header(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), output_format="csv")
        out = capsys.readouterr().out
        first_line = out.splitlines()[0]
        assert "trace_id" in first_line
        assert "tokens" in first_line

    def test_csv_has_data_row(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), output_format="csv")
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if line.strip()]
        assert len(lines) == 2  # header + 1 row

    def test_csv_trace_id_in_row(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        batch_report(str(sample_jsonl_path), output_format="csv")
        out = capsys.readouterr().out
        assert SAMPLE_TRACE in out
