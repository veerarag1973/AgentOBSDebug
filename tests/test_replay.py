"""
test_replay.py — Tests for agentobs_debug.replay

Phase 2 implementation tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.loader import load_events
from agentobs_debug.replay import replay

_TRACE_NO_STEPS = "cccc000000000000cccc000000000001"
_TRACE_NO_TOKENS = "cccc000000000000cccc000000000002"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _run_event(
    trace_id: str,
    span_id: str,
    agent_name: str = "test_agent",
    eid: str = "00000000000000000000001001",
) -> dict:
    return {
        "event_id": eid,
        "event_type": "llm.trace.agent.run.completed",
        "payload": {
            "agent_name": agent_name,
            "duration_ms": 500.0,
            "end_time_unix_nano": 1700000000500000000,
            "span_name": "agent_run",
            "start_time_unix_nano": 1700000000000000000,
            "status": "ok",
        },
        "schema_version": "2.0",
        "source": "test@1.0.0",
        "span_id": span_id,
        "timestamp": "2023-11-14T22:13:20.000000Z",
        "trace_id": trace_id,
    }


def _step_event(
    trace_id: str,
    span_id: str,
    parent_id: str,
    name: str,
    idx: int,
    eid: str = "00000000000000000000001002",
) -> dict:
    return {
        "event_id": eid,
        "event_type": "llm.trace.agent.step.completed",
        "parent_span_id": parent_id,
        "payload": {
            "duration_ms": 200.0,
            "end_time_unix_nano": 1700000000200000000,
            "start_time_unix_nano": 1700000000000000000,
            "status": "ok",
            "step_index": idx,
            "step_name": name,
        },
        "schema_version": "2.0",
        "source": "test@1.0.0",
        "span_id": span_id,
        "timestamp": "2023-11-14T22:13:20.000000Z",
        "trace_id": trace_id,
    }


class TestReplay:
    def test_replay_requires_stream(self, sample_trace_id: str) -> None:
        """replay() raises AgentOBSDebugError when stream is None."""
        with pytest.raises(AgentOBSDebugError):
            replay(sample_trace_id, None)

    def test_replay_output_format(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """replay() stdout matches the expected header + step format."""
        stream = load_events(str(sample_jsonl_path))
        replay(sample_trace_id, stream)
        out = capsys.readouterr().out
        assert "Agent Run: research_agent" in out
        assert f"Trace: {sample_trace_id}" in out
        assert "Step 0 \u2014 search" in out
        assert "Model: gpt-4o" in out
        assert "Tokens: 530" in out
        assert "Duration: 330 ms" in out
        assert "Step 1 \u2014 summarize" in out
        assert "Tokens: 210" in out
        assert "Duration: 200 ms" in out

    def test_replay_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """replay() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            replay(unknown_trace_id, stream)

    def test_replay_no_steps(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        """replay() prints only the header when the agent run has no child steps."""
        p = tmp_path / "no_steps.jsonl"
        _write_jsonl(p, [_run_event(_TRACE_NO_STEPS, "cc00000000000001", agent_name="solo_agent")])
        stream = load_events(str(p))
        replay(_TRACE_NO_STEPS, stream)
        out = capsys.readouterr().out
        assert "Agent Run: solo_agent" in out
        assert f"Trace: {_TRACE_NO_STEPS}" in out
        assert "Step" not in out

    def test_replay_missing_token_data(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Steps without TokenUsage display 'N/A' gracefully."""
        p = tmp_path / "no_tokens.jsonl"
        _write_jsonl(p, [
            _run_event(_TRACE_NO_TOKENS, "cc00000000000003", eid="00000000000000000000001003"),
            _step_event(
                _TRACE_NO_TOKENS, "cc00000000000004", "cc00000000000003", "query", 0,
                eid="00000000000000000000001004",
            ),
        ])
        stream = load_events(str(p))
        replay(_TRACE_NO_TOKENS, stream)
        out = capsys.readouterr().out
        assert "Model: N/A" in out
        assert "Tokens: N/A" in out


# ---------------------------------------------------------------------------
# Regression tests — Phase 2.1
# ---------------------------------------------------------------------------

_TRACE_REVERSED_STEPS = "aaaa000000000000aaaa000000000003"
_TRACE_NO_AGENT_RUN = "aaaa000000000000aaaa000000000004"


class TestReplayRegression:
    def test_steps_sorted_by_step_index_not_file_order(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Steps appear in step_index order even when JSONL order is reversed."""
        p = tmp_path / "reversed.jsonl"
        _write_jsonl(p, [
            _run_event(_TRACE_REVERSED_STEPS, "aa00000000000010", eid="00000000000000000000009001"),
            # step_index=1 written first in file
            _step_event(
                _TRACE_REVERSED_STEPS, "aa00000000000012", "aa00000000000010", "second", 1,
                eid="00000000000000000000009003",
            ),
            # step_index=0 written second in file
            _step_event(
                _TRACE_REVERSED_STEPS, "aa00000000000011", "aa00000000000010", "first", 0,
                eid="00000000000000000000009002",
            ),
        ])
        stream = load_events(str(p))
        replay(_TRACE_REVERSED_STEPS, stream)
        out = capsys.readouterr().out
        assert out.index("Step 0") < out.index("Step 1")

    def test_step_block_count_matches_event_count(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Two step events produce exactly two Model/Tokens/Duration output blocks."""
        stream = load_events(str(sample_jsonl_path))
        replay(sample_trace_id, stream)
        out = capsys.readouterr().out
        assert out.count("Model:") == 2
        assert out.count("Tokens:") == 2
        assert out.count("Duration:") == 2

    def test_duration_values_expressed_in_ms(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Duration values from the fixture (330 ms, 200 ms) appear verbatim in output."""
        stream = load_events(str(sample_jsonl_path))
        replay(sample_trace_id, stream)
        out = capsys.readouterr().out
        assert "330 ms" in out
        assert "200 ms" in out

    def test_no_agent_run_event_raises(
        self, tmp_path: Path
    ) -> None:
        """replay() raises AgentOBSDebugError when the trace has no agent_run event."""
        p = tmp_path / "no_agent_run.jsonl"
        # Only a step event — no agent_run parent
        _write_jsonl(p, [
            _step_event(
                _TRACE_NO_AGENT_RUN, "aa00000000000020", "aa00000000000019", "step1", 0,
                eid="00000000000000000000009010",
            ),
        ])
        stream = load_events(str(p))
        with pytest.raises(AgentOBSDebugError):
            replay(_TRACE_NO_AGENT_RUN, stream)
