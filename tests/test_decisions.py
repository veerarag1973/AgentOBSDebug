"""\ntest_decisions.py — Tests for agentobs_debug.decisions\n\nPhase 3 implementation tests.\n"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug import load_events, show_decisions
from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError

_EMPTY_TRACE_ID = "bbbb0000000000000000000000000000"


@pytest.fixture
def no_decision_jsonl(tmp_path: Path) -> Path:
    """JSONL with a span event only — no decision events."""
    evt = {
        "event_id": "1",
        "event_type": "llm.trace.span.completed",
        "payload": {"span_name": "test", "start_time_unix_nano": 1000, "end_time_unix_nano": 2000},
        "schema_version": "2.0",
        "source": "test",
        "span_id": "aaa",
        "timestamp": "2023-01-01T00:00:00Z",
        "trace_id": _EMPTY_TRACE_ID,
    }
    p = tmp_path / "no_decisions.jsonl"
    p.write_text(json.dumps(evt) + "\n", encoding="utf-8")
    return p


class TestShowDecisions:
    def test_decisions_requires_stream(self, sample_trace_id: str) -> None:
        """show_decisions() raises AgentOBSDebugError when stream is None."""
        with pytest.raises(AgentOBSDebugError):
            show_decisions(sample_trace_id, stream=None)

    def test_show_decisions_output(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """show_decisions() renders decision name, options, and chosen value."""
        stream = load_events(str(sample_jsonl_path))
        show_decisions(sample_trace_id, stream=stream)
        out = capsys.readouterr().out
        assert "Decision: tool_selection" in out
        assert "Options: search_api, knowledge_base" in out
        assert "Chosen: search_api" in out

    def test_show_decisions_empty(
        self,
        capsys: pytest.CaptureFixture,
        no_decision_jsonl: Path,
    ) -> None:
        """show_decisions() prints fallback message when no decisions exist."""
        stream = load_events(str(no_decision_jsonl))
        show_decisions(_EMPTY_TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        assert "No decision points recorded." in out

    def test_show_decisions_missing_trace(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """show_decisions() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            show_decisions(unknown_trace_id, stream=stream)

