"""
test_attribution.py — Tests for agentobs_debug.attribution (cost_attribution).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.attribution import cost_attribution
from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import load_events

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"


class TestCostAttributionErrors:
    def test_raises_without_stream(self) -> None:
        with pytest.raises(AgentOBSDebugError, match="EventStream"):
            cost_attribution(TRACE_ID, stream=None)


class TestCostAttributionText:
    def test_shows_step_names(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        assert "search" in out
        assert "summarize" in out

    def test_shows_model(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        assert "gpt-4o" in out

    def test_shows_total_row(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        assert "TOTAL" in out

    def test_shows_percentiles(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        assert "p50" in out
        assert "p90" in out
        assert "p99" in out

    def test_shows_cost(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        # Total cost is $0.0030
        assert "0.0030" in out

    def test_shows_duration_ms(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        # search step is 330 ms
        assert "330" in out


class TestCostAttributionJSON:
    def test_json_structure(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="json")
        out = capsys.readouterr().out
        doc = json.loads(out)
        assert "trace_id" in doc
        assert "steps" in doc
        assert "totals" in doc
        assert "percentiles" in doc

    def test_json_steps_list(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="json")
        out = capsys.readouterr().out
        steps = json.loads(out)["steps"]
        assert isinstance(steps, list)
        assert len(steps) == 2
        names = {s["step_name"] for s in steps}
        assert "search" in names
        assert "summarize" in names

    def test_json_step_has_required_keys(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="json")
        out = capsys.readouterr().out
        step = json.loads(out)["steps"][0]
        for key in ("step_name", "model", "input_tokens", "output_tokens",
                    "cost_usd", "duration_ms", "pct_duration"):
            assert key in step, f"missing key {key!r}"

    def test_json_totals(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="json")
        out = capsys.readouterr().out
        totals = json.loads(out)["totals"]
        assert totals["total_tokens"] == totals["input_tokens"] + totals["output_tokens"]

    def test_json_percentiles_present(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="json")
        out = capsys.readouterr().out
        pct = json.loads(out)["percentiles"]
        for key in ("p50", "p90", "p99"):
            assert key in pct, f"missing {key!r} in percentiles"
            assert pct[key] is not None

    def test_json_pct_duration_sums_to_100(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="json")
        out = capsys.readouterr().out
        steps = json.loads(out)["steps"]
        total_pct = sum(s["pct_duration"] for s in steps if s["pct_duration"] is not None)
        assert abs(total_pct - 100.0) < 0.2


class TestCostAttributionCSV:
    def test_csv_header(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="csv")
        out = capsys.readouterr().out
        first = out.splitlines()[0]
        assert "step_name" in first
        assert "cost_usd" in first
        assert "duration_ms" in first

    def test_csv_row_count(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="csv")
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if line.strip()]
        # header + 2 steps
        assert len(lines) == 3

    def test_csv_step_names_in_output(
        self, sample_jsonl_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stream = load_events(str(sample_jsonl_path))
        cost_attribution(TRACE_ID, stream=stream, output_format="csv")
        out = capsys.readouterr().out
        assert "search" in out
        assert "summarize" in out
