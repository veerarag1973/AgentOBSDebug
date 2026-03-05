"""
test_output_formats.py — Tests for --format (json/csv) and filter parameters
across all updated modules (replay, timeline, inspect, tools, decisions, cost).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.cost import cost_summary
from agentobs_debug.decisions import show_decisions
from agentobs_debug.inspect import inspect_trace
from agentobs_debug.loader import load_events
from agentobs_debug.replay import replay
from agentobs_debug.timeline import timeline
from agentobs_debug.tools import show_tools

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"


@pytest.fixture
def stream(sample_jsonl_path: Path):  # type: ignore[return]
    return load_events(str(sample_jsonl_path))


# ---------------------------------------------------------------------------
# inspect_trace
# ---------------------------------------------------------------------------

class TestInspectJSON:
    def test_json_keys(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        inspect_trace(TRACE_ID, stream=stream, output_format="json")
        doc = json.loads(capsys.readouterr().out)
        for k in ("trace_id", "spans", "tokens", "cost_usd", "duration_s", "status"):
            assert k in doc

    def test_json_trace_id(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        inspect_trace(TRACE_ID, stream=stream, output_format="json")
        assert json.loads(capsys.readouterr().out)["trace_id"] == TRACE_ID

    def test_json_tokens(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        inspect_trace(TRACE_ID, stream=stream, output_format="json")
        assert json.loads(capsys.readouterr().out)["tokens"] == 740


class TestInspectCSV:
    def test_csv_header(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        inspect_trace(TRACE_ID, stream=stream, output_format="csv")
        first = capsys.readouterr().out.splitlines()[0]
        assert "trace_id" in first and "tokens" in first

    def test_csv_two_lines(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        inspect_trace(TRACE_ID, stream=stream, output_format="csv")
        lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert len(lines) == 2

# ---------------------------------------------------------------------------
# cost_summary
# ---------------------------------------------------------------------------

class TestCostJSON:
    def test_json_keys(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        cost_summary(TRACE_ID, stream=stream, output_format="json")
        doc = json.loads(capsys.readouterr().out)
        for k in ("input_tokens", "output_tokens", "total_tokens", "total_cost_usd"):
            assert k in doc

    def test_json_total_tokens(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        cost_summary(TRACE_ID, stream=stream, output_format="json")
        doc = json.loads(capsys.readouterr().out)
        assert doc["total_tokens"] == doc["input_tokens"] + doc["output_tokens"]

    def test_json_cost_value(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        cost_summary(TRACE_ID, stream=stream, output_format="json")
        doc = json.loads(capsys.readouterr().out)
        assert abs(doc["total_cost_usd"] - 0.003) < 1e-6


class TestCostCSV:
    def test_csv_header(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        cost_summary(TRACE_ID, stream=stream, output_format="csv")
        first = capsys.readouterr().out.splitlines()[0]
        assert "input_tokens" in first and "total_cost_usd" in first

    def test_csv_data_row(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        cost_summary(TRACE_ID, stream=stream, output_format="csv")
        lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert len(lines) == 2  # header + 1 row


# ---------------------------------------------------------------------------
# replay
# ---------------------------------------------------------------------------

class TestReplayJSON:
    def test_json_structure(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        replay(TRACE_ID, stream=stream, output_format="json")
        doc = json.loads(capsys.readouterr().out)
        assert "agent_name" in doc
        assert "trace_id" in doc
        assert "steps" in doc

    def test_json_two_steps(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        replay(TRACE_ID, stream=stream, output_format="json")
        assert len(json.loads(capsys.readouterr().out)["steps"]) == 2

    def test_json_step_has_keys(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        replay(TRACE_ID, stream=stream, output_format="json")
        step = json.loads(capsys.readouterr().out)["steps"][0]
        for k in ("step_index", "step_name", "model", "tokens", "duration_ms"):
            assert k in step


class TestReplayStepFilter:
    def test_filter_search_step(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        replay(TRACE_ID, stream=stream, step_name="search", output_format="json")
        steps = json.loads(capsys.readouterr().out)["steps"]
        assert len(steps) == 1
        assert steps[0]["step_name"] == "search"

    def test_filter_nonexistent_step(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        replay(TRACE_ID, stream=stream, step_name="nonexistent", output_format="json")
        steps = json.loads(capsys.readouterr().out)["steps"]
        assert steps == []

    def test_filter_case_insensitive(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        replay(TRACE_ID, stream=stream, step_name="SEARCH", output_format="json")
        steps = json.loads(capsys.readouterr().out)["steps"]
        assert len(steps) == 1


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------

class TestTimelineJSON:
    def test_json_is_list(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_json_row_keys(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, output_format="json")
        row = json.loads(capsys.readouterr().out)[0]
        assert "offset_ms" in row and "label" in row

    def test_json_offsets_sorted(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, output_format="json")
        offsets = [r["offset_ms"] for r in json.loads(capsys.readouterr().out)]
        assert offsets == sorted(offsets)


class TestTimelineCSV:
    def test_csv_header(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, output_format="csv")
        first = capsys.readouterr().out.splitlines()[0]
        assert "offset_ms" in first and "label" in first

    def test_csv_multiple_rows(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, output_format="csv")
        lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert len(lines) > 1


class TestTimelineFilters:
    def test_event_type_filter(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, event_type="llm.trace.agent.run", output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert all("agent_run" in r["label"] or "agent" in r["label"] for r in data)

    def test_from_ms_excludes_early(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, from_ms=500.0, output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert all(r["offset_ms"] >= 500.0 for r in data)

    def test_to_ms_excludes_late(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, to_ms=500.0, output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert all(r["offset_ms"] <= 500.0 for r in data)

    def test_range_filter(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, from_ms=100.0, to_ms=500.0, output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert all(100.0 <= r["offset_ms"] <= 500.0 for r in data)

    def test_narrow_range_returns_empty(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        # A range that should exclude all rows from this trace
        timeline(TRACE_ID, stream=stream, from_ms=9999.0, to_ms=9999.0, output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert data == []

    def test_event_type_no_match_empty(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        timeline(TRACE_ID, stream=stream, event_type="x.nonexistent", output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert data == []


# ---------------------------------------------------------------------------
# show_tools
# ---------------------------------------------------------------------------

class TestToolsJSON:
    def test_json_is_list(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_json_row_keys(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, output_format="json")
        row = json.loads(capsys.readouterr().out)[0]
        assert "tool_name" in row and "arguments" in row


class TestToolsCSV:
    def test_csv_header(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, output_format="csv")
        first = capsys.readouterr().out.splitlines()[0]
        assert "tool_name" in first and "arguments" in first

    def test_csv_two_rows(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, output_format="csv")
        lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert len(lines) == 3  # header + 2 tools


class TestToolsFilter:
    def test_filter_by_tool_name(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, tool_name="search_api", output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 1
        assert data[0]["tool_name"] == "search_api"

    def test_filter_case_insensitive(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, tool_name="SEARCH_API", output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 1

    def test_filter_no_match_json(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, tool_name="nonexistent", output_format="json")
        assert json.loads(capsys.readouterr().out) == []

    def test_filter_no_match_csv(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, tool_name="nonexistent", output_format="csv")
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if line.strip()]
        assert len(lines) == 1  # only header

    def test_filter_no_match_text(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_tools(TRACE_ID, stream=stream, tool_name="nonexistent", output_format="text")
        out = capsys.readouterr().out
        assert "No tool calls recorded" in out


# ---------------------------------------------------------------------------
# show_decisions
# ---------------------------------------------------------------------------

class TestDecisionsJSON:
    def test_json_is_list(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, output_format="json")
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_json_row_keys(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, output_format="json")
        row = json.loads(capsys.readouterr().out)[0]
        assert "decision_name" in row and "options" in row and "chosen" in row

    def test_json_options_is_list(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, output_format="json")
        row = json.loads(capsys.readouterr().out)[0]
        assert isinstance(row["options"], list)


class TestDecisionsCSV:
    def test_csv_header(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, output_format="csv")
        first = capsys.readouterr().out.splitlines()[0]
        assert "decision_name" in first and "chosen" in first

    def test_csv_one_data_row(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, output_format="csv")
        lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert len(lines) == 2


class TestDecisionsFilter:
    def test_filter_by_decision_name(
        self, stream, capsys: pytest.CaptureFixture[str]  # type: ignore[no-untyped-def]
    ) -> None:
        show_decisions(
            TRACE_ID, stream=stream,
            decision_name="tool_selection", output_format="json",
        )
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 1

    def test_filter_case_insensitive(
        self, stream, capsys: pytest.CaptureFixture[str]  # type: ignore[no-untyped-def]
    ) -> None:
        show_decisions(
            TRACE_ID, stream=stream,
            decision_name="TOOL_SELECTION", output_format="json",
        )
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 1

    def test_filter_no_match_json(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, decision_name="nonexistent", output_format="json")
        assert json.loads(capsys.readouterr().out) == []

    def test_filter_no_match_csv(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, decision_name="nonexistent", output_format="csv")
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if line.strip()]
        assert len(lines) == 1  # only header

    def test_filter_no_match_text(self, stream, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[no-untyped-def]
        show_decisions(TRACE_ID, stream=stream, decision_name="nonexistent", output_format="text")
        out = capsys.readouterr().out
        assert "No decision points recorded" in out
