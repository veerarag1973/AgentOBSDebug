"""
test_inspect.py — Tests for agentobs_debug.inspect

Phase 2 implementation tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.inspect import inspect_trace
from agentobs_debug.loader import load_events

_TRACE_NO_COST = "dddd000000000000dddd000000000001"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


class TestInspectTrace:
    def test_inspect_requires_stream(self, sample_trace_id: str) -> None:
        """inspect_trace() raises AgentOBSDebugError when stream is None."""
        with pytest.raises(AgentOBSDebugError):
            inspect_trace(sample_trace_id, None)

    def test_inspect_valid_trace(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """inspect_trace() renders all required summary fields."""
        stream = load_events(str(sample_jsonl_path))
        inspect_trace(sample_trace_id, stream)
        out = capsys.readouterr().out
        assert "Trace Summary" in out
        assert f"Trace ID: {sample_trace_id}" in out
        assert "Spans: 5" in out
        assert "Tokens: 740" in out
        assert "Cost: $0.0030" in out
        assert "Duration: 1.1s" in out
        assert "Status: ok" in out

    def test_inspect_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """inspect_trace() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            inspect_trace(unknown_trace_id, stream)

    def test_inspect_missing_cost_data(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """inspect_trace() displays $0.0000 when no cost data is present."""
        p = tmp_path / "no_cost.jsonl"
        _write_jsonl(p, [{
            "event_id": "00000000000000000000002001",
            "event_type": "llm.trace.agent.run.completed",
            "payload": {
                "agent_name": "no_cost_agent",
                "duration_ms": 300.0,
                "end_time_unix_nano": 1700000000300000000,
                "span_name": "agent_run",
                "start_time_unix_nano": 1700000000000000000,
                "status": "ok",
            },
            "schema_version": "2.0",
            "source": "test@1.0.0",
            "span_id": "dd00000000000001",
            "timestamp": "2023-11-14T22:13:20.000000Z",
            "trace_id": _TRACE_NO_COST,
        }])
        stream = load_events(str(p))
        inspect_trace(_TRACE_NO_COST, stream)
        out = capsys.readouterr().out
        assert "Cost: $0.0000" in out

    def test_inspect_token_aggregation(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """inspect_trace() sums tokens across all spans (400+130+170+40 = 740)."""
        stream = load_events(str(sample_jsonl_path))
        inspect_trace(sample_trace_id, stream)
        out = capsys.readouterr().out
        assert "Tokens: 740" in out


# ---------------------------------------------------------------------------
# Regression tests — Phase 2.2
# ---------------------------------------------------------------------------

_TRACE_NO_STATUS = "bbbb000000000000bbbb000000000005"


class TestInspectRegression:
    def test_output_starts_with_header_and_separator(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Output first line is 'Trace Summary', second line is the '---' separator."""
        stream = load_events(str(sample_jsonl_path))
        inspect_trace(sample_trace_id, stream)
        lines = capsys.readouterr().out.strip().split("\n")
        assert lines[0] == "Trace Summary"
        assert lines[1] == "-------------"

    def test_cost_formatted_with_four_decimal_places(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Cost value has exactly 4 decimal places (e.g. $0.0030)."""
        stream = load_events(str(sample_jsonl_path))
        inspect_trace(sample_trace_id, stream)
        out = capsys.readouterr().out
        cost_line = next(ln for ln in out.splitlines() if ln.startswith("Cost:"))
        decimal_part = cost_line.split("$")[1]
        assert "." in decimal_part
        assert len(decimal_part.split(".")[1]) == 4

    def test_missing_status_field_defaults_to_ok(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """status defaults to 'ok' when the agent_run payload has an empty status."""
        p = tmp_path / "no_status.jsonl"
        # Use empty string for status — falsy, triggers the `or 'ok'` fallback
        p.write_text(json.dumps({
            "event_id": "00000000000000000000009101",
            "event_type": "llm.trace.agent.run.completed",
            "payload": {
                "agent_name": "agent_x",
                "duration_ms": 100.0,
                "end_time_unix_nano": 1700000000100000000,
                "span_name": "agent_run",
                "start_time_unix_nano": 1700000000000000000,
                "status": "",
            },
            "schema_version": "2.0",
            "source": "test@1.0.0",
            "span_id": "bb00000000000020",
            "timestamp": "2023-11-14T22:13:20.000000Z",
            "trace_id": _TRACE_NO_STATUS,
        }) + "\n", encoding="utf-8")
        stream = load_events(str(p))
        inspect_trace(_TRACE_NO_STATUS, stream)
        assert "Status: ok" in capsys.readouterr().out

    def test_all_required_field_labels_present(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Every required field label appears in output — guards against label renames."""
        stream = load_events(str(sample_jsonl_path))
        inspect_trace(sample_trace_id, stream)
        out = capsys.readouterr().out
        for label in ("Trace ID:", "Spans:", "Tokens:", "Cost:", "Duration:", "Status:"):
            assert label in out, f"Missing label: {label!r}"

    def test_non_span_events_excluded_from_span_count(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Decision, tool-call and cost events must NOT count toward 'Spans:'."""
        # The fixture has 10 events total; only 5 are span-type → Spans: 5
        stream = load_events(str(sample_jsonl_path))
        inspect_trace(sample_trace_id, stream)
        assert "Spans: 5" in capsys.readouterr().out

    def test_tokens_do_not_double_count_parent_and_child_spans(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """When both step and child span include token_usage, only leaf-span tokens are counted."""
        trace_id = "cccc000000000000cccc000000000001"
        p = tmp_path / "token_double_count_guard.jsonl"
        rows = [
            {
                "event_id": "00000000000000000000003101",
                "event_type": "llm.trace.agent.run.completed",
                "payload": {
                    "agent_name": "agent_x",
                    "duration_ms": 200.0,
                    "end_time_unix_nano": 1700000000200000000,
                    "span_name": "agent_run",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000001",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": trace_id,
            },
            {
                "event_id": "00000000000000000000003102",
                "event_type": "llm.trace.agent.step.completed",
                "parent_span_id": "cc00000000000001",
                "payload": {
                    "step_name": "step_a",
                    "step_index": 0,
                    "start_time_unix_nano": 1700000000000000000,
                    "end_time_unix_nano": 1700000000100000000,
                    "token_usage": {"input_tokens": 100, "output_tokens": 25, "total_tokens": 125},
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000002",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": trace_id,
            },
            {
                "event_id": "00000000000000000000003103",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "cc00000000000002",
                "payload": {
                    "span_name": "chat:gpt-4o",
                    "start_time_unix_nano": 1700000000000000000,
                    "end_time_unix_nano": 1700000000100000000,
                    "token_usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100},
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000003",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": trace_id,
            },
        ]
        _write_jsonl(p, rows)

        stream = load_events(str(p))
        inspect_trace(trace_id, stream)
        out = capsys.readouterr().out
        assert "Tokens: 100" in out
