"""
test_diff.py — Tests for agentobs_debug.diff (diff_traces).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.diff import diff_traces
from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import load_events

TRACE_A = "4bf92f3577b34da6a3ce929d0e0e4736"
TRACE_B = "aaaabbbbccccddddeeeeffffaaaabbbb"


def _write_two_trace_file(tmp_path: Path) -> Path:
    """Write a JSONL with the sample trace A + a minimal trace B."""
    src = Path(__file__).parent / "fixtures" / "sample_events.jsonl"
    lines_a = src.read_text(encoding="utf-8").splitlines()

    # Trace B: a slightly heavier two-step run (more tokens, longer duration)
    def _ev(eid: str, etype: str, tid: str, sid: str, payload: dict,
            parent_sid: str | None = None) -> str:
        row: dict = {
            "event_id": eid,
            "event_type": etype,
            "payload": payload,
            "schema_version": "2.0",
            "source": "b@1.0",
            "span_id": sid,
            "timestamp": "2023-11-14T22:14:00.000000Z",
            "trace_id": tid,
        }
        if parent_sid:
            row["parent_span_id"] = parent_sid
        return json.dumps(row)

    lines_b = [
        _ev("bb01", "llm.trace.agent.run.completed", TRACE_B, "bb_run",
            {"agent_name": "b_agent",
             "start_time_unix_nano": 1700000010000000000,
             "end_time_unix_nano": 1700000012000000000,
             "status": "ok", "duration_ms": 2000.0}),
        _ev("bb02", "llm.trace.agent.step.completed", TRACE_B, "bb_step1",
            {"step_name": "search", "step_index": 0,
             "start_time_unix_nano": 1700000010100000000,
             "end_time_unix_nano": 1700000010700000000,
             "duration_ms": 600.0, "status": "ok"},
            parent_sid="bb_run"),
        _ev("bb03", "llm.trace.span.completed", TRACE_B, "bb_span1",
            {"model_info": {"name": "gpt-4o"}, "span_name": "chat",
             "start_time_unix_nano": 1700000010100000000,
             "end_time_unix_nano": 1700000010700000000,
             "token_usage": {"input_tokens": 500, "output_tokens": 200, "total_tokens": 700}},
            parent_sid="bb_step1"),
        _ev("bb04", "llm.trace.agent.step.completed", TRACE_B, "bb_step2",
            {"step_name": "summarize", "step_index": 1,
             "start_time_unix_nano": 1700000011000000000,
             "end_time_unix_nano": 1700000011500000000,
             "duration_ms": 500.0, "status": "ok"},
            parent_sid="bb_run"),
        _ev("bb05", "llm.trace.span.completed", TRACE_B, "bb_span2",
            {"model_info": {"name": "gpt-4o"}, "span_name": "chat",
             "start_time_unix_nano": 1700000011000000000,
             "end_time_unix_nano": 1700000011500000000,
             "token_usage": {"input_tokens": 200, "output_tokens": 80, "total_tokens": 280}},
            parent_sid="bb_step2"),
    ]

    p = tmp_path / "two_traces.jsonl"
    p.write_text("\n".join(lines_a + lines_b) + "\n", encoding="utf-8")
    return p


class TestDiffTracesErrors:
    def test_raises_without_stream(self) -> None:
        with pytest.raises(AgentOBSDebugError, match="EventStream"):
            diff_traces(TRACE_A, TRACE_B, stream=None)


class TestDiffTracesText:
    def test_same_trace_zero_deltas(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_A, stream=stream)
        out = capsys.readouterr().out
        # Duration delta should be (+0.0)
        assert "(+0.0" in out or "(+0)" in out

    def test_output_shows_trace_ids(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_B, stream=stream)
        out = capsys.readouterr().out
        assert "4bf92f3577b3" in out
        assert "aaaabbbbcccc" in out

    def test_output_contains_duration_delta(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_B, stream=stream)
        out = capsys.readouterr().out
        assert "Duration" in out

    def test_output_contains_step_section(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_B, stream=stream)
        out = capsys.readouterr().out
        assert "Steps" in out

    def test_output_contains_step_names(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_B, stream=stream)
        out = capsys.readouterr().out
        assert "search" in out
        assert "summarize" in out


class TestDiffTracesJSON:
    def test_json_output_structure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_B, stream=stream, output_format="json")
        out = capsys.readouterr().out
        doc = json.loads(out)
        assert "trace_a" in doc
        assert "trace_b" in doc
        assert "summary" in doc
        assert "steps" in doc

    def test_json_summary_has_delta_keys(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_B, stream=stream, output_format="json")
        out = capsys.readouterr().out
        summary = json.loads(out)["summary"]
        for key in ("duration_s", "tokens", "cost_usd", "spans", "status"):
            assert key in summary, f"missing {key!r} in summary"

    def test_json_steps_list(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_B, stream=stream, output_format="json")
        out = capsys.readouterr().out
        steps = json.loads(out)["steps"]
        assert isinstance(steps, list)
        assert any(s["name"] == "search" for s in steps)
        assert any(s["name"] == "summarize" for s in steps)

    def test_json_same_trace_zero_token_delta(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write_two_trace_file(tmp_path)
        stream = load_events(str(p))
        diff_traces(TRACE_A, TRACE_A, stream=stream, output_format="json")
        out = capsys.readouterr().out
        doc = json.loads(out)
        assert doc["summary"]["tokens"]["delta"] == 0
        assert doc["summary"]["duration_s"]["delta"] == 0.0
