"""
test_cost.py — Tests for agentobs_debug.cost

Phase 3 implementation tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug import cost_summary, load_events
from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError

_EMPTY_TRACE_ID = "dddd0000000000000000000000000000"


@pytest.fixture
def no_cost_jsonl(tmp_path: Path) -> Path:
    """JSONL with a span event only — no cost events."""
    evt = {
        "event_id": "1",
        "event_type": "llm.trace.span.completed",
        "payload": {"span_name": "test", "start_time_unix_nano": 1000, "end_time_unix_nano": 2000},
        "schema_version": "2.0",
        "source": "test",
        "span_id": "ccc",
        "timestamp": "2023-01-01T00:00:00Z",
        "trace_id": _EMPTY_TRACE_ID,
    }
    p = tmp_path / "no_cost.jsonl"
    p.write_text(json.dumps(evt) + "\n", encoding="utf-8")
    return p


class TestCostSummary:
    def test_cost_requires_stream(self, sample_trace_id: str) -> None:
        """cost_summary() raises AgentOBSDebugError when stream is None."""
        with pytest.raises(AgentOBSDebugError):
            cost_summary(sample_trace_id, stream=None)

    def test_cost_summary_output(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """cost_summary() renders input tokens, output tokens, and total cost."""
        stream = load_events(str(sample_jsonl_path))
        cost_summary(sample_trace_id, stream=stream)
        out = capsys.readouterr().out
        assert "Cost Summary" in out
        assert "------------" in out
        assert "Input tokens:" in out
        assert "Output tokens:" in out
        assert "Total cost:" in out

    def test_cost_summary_aggregates_spans(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Tokens and cost are summed across all cost events in the trace."""
        stream = load_events(str(sample_jsonl_path))
        cost_summary(sample_trace_id, stream=stream)
        out = capsys.readouterr().out
        # fixture has 2 cost events: 400+170=570 input, 130+40=170 output, $0.0023+$0.0007=$0.0030
        assert "Input tokens: 570" in out
        assert "Output tokens: 170" in out
        assert "Total cost: $0.0030" in out

    def test_cost_summary_no_data(
        self, capsys: pytest.CaptureFixture, no_cost_jsonl: Path
    ) -> None:
        """cost_summary() displays zeros gracefully when no cost data is present."""
        stream = load_events(str(no_cost_jsonl))
        cost_summary(_EMPTY_TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        assert "Input tokens: 0" in out
        assert "Output tokens: 0" in out
        assert "Total cost: $0.0000" in out

    def test_cost_summary_missing_trace(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """cost_summary() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            cost_summary(unknown_trace_id, stream=stream)

