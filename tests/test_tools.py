"""
test_tools.py — Tests for agentobs_debug.tools

Phase 3 implementation tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug import load_events, show_tools
from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError

_EMPTY_TRACE_ID = "cccc0000000000000000000000000000"


@pytest.fixture
def no_tool_jsonl(tmp_path: Path) -> Path:
    """JSONL with a span event only — no tool-call events."""
    evt = {
        "event_id": "1",
        "event_type": "llm.trace.span.completed",
        "payload": {"span_name": "test", "start_time_unix_nano": 1000, "end_time_unix_nano": 2000},
        "schema_version": "2.0",
        "source": "test",
        "span_id": "bbb",
        "timestamp": "2023-01-01T00:00:00Z",
        "trace_id": _EMPTY_TRACE_ID,
    }
    p = tmp_path / "no_tools.jsonl"
    p.write_text(json.dumps(evt) + "\n", encoding="utf-8")
    return p


class TestShowTools:
    def test_tools_requires_stream(self, sample_trace_id: str) -> None:
        """show_tools() raises AgentOBSDebugError when stream is None."""
        with pytest.raises(AgentOBSDebugError):
            show_tools(sample_trace_id, stream=None)

    def test_show_tools_output(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """show_tools() renders header and tool names."""
        stream = load_events(str(sample_jsonl_path))
        show_tools(sample_trace_id, stream=stream)
        out = capsys.readouterr().out
        assert "Tool Calls" in out
        assert "----------" in out
        assert "search_api" in out
        assert "web_fetch" in out

    def test_show_tools_empty(
        self,
        capsys: pytest.CaptureFixture,
        no_tool_jsonl: Path,
    ) -> None:
        """show_tools() prints fallback message when no tool calls exist."""
        stream = load_events(str(no_tool_jsonl))
        show_tools(_EMPTY_TRACE_ID, stream=stream)
        out = capsys.readouterr().out
        assert "No tool calls recorded." in out

    def test_show_tools_missing_trace(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """show_tools() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            show_tools(unknown_trace_id, stream=stream)

    def test_show_tools_argument_formatting(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Arguments are formatted as key="value" pairs joined by commas."""
        stream = load_events(str(sample_jsonl_path))
        show_tools(sample_trace_id, stream=stream)
        out = capsys.readouterr().out
        assert 'query="LLM observability"' in out
        assert 'url="example.com"' in out

