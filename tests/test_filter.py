"""
test_filter.py — Tests for agentobs_debug.filter (internal utilities).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agentobs_debug.filter import (
    filter_by_step_name,
    filter_spans_by_event_type,
    filter_timeline_rows,
)


def _make_event(event_type: str, payload: dict | None = None) -> MagicMock:
    e = MagicMock()
    e.event_type = event_type
    e.payload = payload or {}
    return e


class TestFilterByStepName:
    def test_none_returns_all(self) -> None:
        e1 = _make_event("llm.trace.agent.step.completed", {"step_name": "search"})
        e2 = _make_event("llm.trace.agent.run.completed", {})
        result = filter_by_step_name([e1, e2], None)
        assert result == [e1, e2]

    def test_matching_name_case_insensitive(self) -> None:
        e1 = _make_event("llm.trace.agent.step.completed", {"step_name": "Search"})
        e2 = _make_event("llm.trace.agent.step.completed", {"step_name": "summarize"})
        result = filter_by_step_name([e1, e2], "search")
        assert result == [e1]

    def test_no_match_returns_empty(self) -> None:
        e = _make_event("llm.trace.agent.step.completed", {"step_name": "search"})
        result = filter_by_step_name([e], "nonexistent")
        assert result == []

    def test_non_step_events_excluded(self) -> None:
        e_run = _make_event("llm.trace.agent.run.completed", {"step_name": "search"})
        result = filter_by_step_name([e_run], "search")
        assert result == []

    def test_empty_list_returns_empty(self) -> None:
        assert filter_by_step_name([], "search") == []


class TestFilterTimelineRows:
    _EPOCH = 1_000_000_000  # ns = 1 ms from epoch

    def _rows(self) -> list[tuple[int, str]]:
        return [
            (1_000_000_000, "event at 0 ms"),
            (2_000_000_000, "event at 1000 ms"),
            (1_500_000_000, "event at 500 ms"),
        ]

    def test_none_bounds_returns_all(self) -> None:
        rows = self._rows()
        result = filter_timeline_rows(rows, self._EPOCH, None, None)
        assert result == rows

    def test_from_ms_filters_early(self) -> None:
        rows = self._rows()
        result = filter_timeline_rows(rows, self._EPOCH, 400.0, None)
        offsets = [(t - self._EPOCH) / 1_000_000 for t, _ in result]
        assert all(o >= 400.0 for o in offsets)

    def test_to_ms_filters_late(self) -> None:
        rows = self._rows()
        result = filter_timeline_rows(rows, self._EPOCH, None, 600.0)
        offsets = [(t - self._EPOCH) / 1_000_000 for t, _ in result]
        assert all(o <= 600.0 for o in offsets)

    def test_range_both_bounds(self) -> None:
        rows = self._rows()
        result = filter_timeline_rows(rows, self._EPOCH, 400.0, 600.0)
        assert len(result) == 1
        assert result[0][1] == "event at 500 ms"

    def test_empty_rows(self) -> None:
        assert filter_timeline_rows([], 0, 0.0, 100.0) == []


class TestFilterSpansByEventType:
    def test_none_returns_all(self) -> None:
        e1 = _make_event("llm.trace.agent.step.completed")
        e2 = _make_event("x.agentobs.tool.called")
        result = filter_spans_by_event_type([e1, e2], None)
        assert result == [e1, e2]

    def test_prefix_match_case_insensitive(self) -> None:
        e1 = _make_event("llm.trace.agent.step.completed")
        e2 = _make_event("llm.trace.agent.run.completed")
        e3 = _make_event("x.agentobs.tool.called")
        result = filter_spans_by_event_type([e1, e2, e3], "LLM.Trace.Agent.Step")
        assert result == [e1]

    def test_broad_prefix(self) -> None:
        e1 = _make_event("llm.trace.agent.step.completed")
        e2 = _make_event("llm.trace.agent.run.completed")
        e3 = _make_event("x.agentobs.tool.called")
        result = filter_spans_by_event_type([e1, e2, e3], "llm.trace")
        assert e1 in result
        assert e2 in result
        assert e3 not in result

    def test_no_match_returns_empty(self) -> None:
        e = _make_event("llm.trace.agent.step.completed")
        result = filter_spans_by_event_type([e], "x.agentobs")
        assert result == []
