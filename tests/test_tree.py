"""
test_tree.py — Tests for agentobs_debug.tree

Phase 2 implementation tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.loader import load_events
from agentobs_debug.tree import print_trace_tree

_TRACE_SINGLE = "eeee000000000000eeee000000000001"
_TRACE_ORPHAN = "eeee000000000000eeee000000000002"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


class TestPrintTraceTree:
    def test_tree_requires_stream(self, sample_trace_id: str) -> None:
        """print_trace_tree() raises AgentOBSDebugError when stream is None."""
        with pytest.raises(AgentOBSDebugError):
            print_trace_tree(sample_trace_id, None)

    def test_tree_renders_hierarchy(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """print_trace_tree() output matches the expected tree structure."""
        stream = load_events(str(sample_jsonl_path))
        print_trace_tree(sample_trace_id, stream)
        out = capsys.readouterr().out
        assert "agent_run research_agent" in out
        assert "\u251c\u2500\u2500 step search" in out
        assert "\u2514\u2500\u2500 step summarize" in out
        assert "span chat:gpt-4o" in out
        lines = out.strip().split("\n")
        search_idx = next(i for i, ln in enumerate(lines) if "step search" in ln)
        summarize_idx = next(i for i, ln in enumerate(lines) if "step summarize" in ln)
        assert search_idx < summarize_idx

    def test_tree_single_span(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        """Single root span renders without tree connectors."""
        p = tmp_path / "single.jsonl"
        _write_jsonl(p, [{
            "event_id": "00000000000000000000003001",
            "event_type": "llm.trace.agent.run.completed",
            "payload": {
                "agent_name": "solo",
                "duration_ms": 100.0,
                "end_time_unix_nano": 1700000000100000000,
                "span_name": "agent_run",
                "start_time_unix_nano": 1700000000000000000,
                "status": "ok",
            },
            "schema_version": "2.0",
            "source": "test@1.0.0",
            "span_id": "ee00000000000001",
            "timestamp": "2023-11-14T22:13:20.000000Z",
            "trace_id": _TRACE_SINGLE,
        }])
        stream = load_events(str(p))
        print_trace_tree(_TRACE_SINGLE, stream)
        out = capsys.readouterr().out
        assert out.strip() == "agent_run solo"
        assert "\u251c" not in out
        assert "\u2514" not in out

    def test_tree_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """print_trace_tree() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            print_trace_tree(unknown_trace_id, stream)

    def test_tree_orphan_spans_attached_to_root(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Spans with an unknown parent_span_id are attached under the root."""
        p = tmp_path / "orphan.jsonl"
        _write_jsonl(p, [
            {
                "event_id": "00000000000000000000003002",
                "event_type": "llm.trace.agent.run.completed",
                "payload": {
                    "agent_name": "parent_agent",
                    "duration_ms": 500.0,
                    "end_time_unix_nano": 1700000000500000000,
                    "span_name": "agent_run",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "ee00000000000002",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_ORPHAN,
            },
            {
                "event_id": "00000000000000000000003003",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "ee0000000000ffff",
                "payload": {
                    "duration_ms": 100.0,
                    "end_time_unix_nano": 1700000000100000000,
                    "span_name": "orphan_span",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "ee00000000000003",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_ORPHAN,
            },
        ])
        stream = load_events(str(p))
        print_trace_tree(_TRACE_ORPHAN, stream)
        out = capsys.readouterr().out
        assert "agent_run parent_agent" in out
        assert "span orphan_span" in out
        lines = out.strip().split("\n")
        assert lines[0] == "agent_run parent_agent"
        assert "span orphan_span" in lines[1]

    def test_tree_siblings_sorted_by_start_time(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Sibling spans appear in ascending start_time order."""
        stream = load_events(str(sample_jsonl_path))
        print_trace_tree(sample_trace_id, stream)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        search_idx = next(i for i, ln in enumerate(lines) if "step search" in ln)
        summarize_idx = next(i for i, ln in enumerate(lines) if "step summarize" in ln)
        assert search_idx < summarize_idx


# ---------------------------------------------------------------------------
# Regression tests — Phase 2.3
# ---------------------------------------------------------------------------

_TRACE_NO_SPANS_TREE = "cccc000000000000cccc000000000020"
_TRACE_ALL_PARENTS = "cccc000000000000cccc000000000021"
_TRACE_DEEP = "cccc000000000000cccc000000000022"


class TestTreeRegression:
    def test_non_last_sibling_uses_t_connector(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Non-last children must use the \u251c\u2500\u2500 connector."""
        stream = load_events(str(sample_jsonl_path))
        print_trace_tree(sample_trace_id, stream)
        assert "\u251c\u2500\u2500 step search" in capsys.readouterr().out

    def test_last_sibling_uses_corner_connector(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Last child must use the \u2514\u2500\u2500 connector."""
        stream = load_events(str(sample_jsonl_path))
        print_trace_tree(sample_trace_id, stream)
        assert "\u2514\u2500\u2500 step summarize" in capsys.readouterr().out

    def test_root_node_is_first_output_line(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Root span label must always appear on the first output line."""
        stream = load_events(str(sample_jsonl_path))
        print_trace_tree(sample_trace_id, stream)
        first_line = capsys.readouterr().out.strip().split("\n")[0]
        assert first_line == "agent_run research_agent"

    def test_no_span_events_produces_no_output(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Trace whose events are all non-span types silently produces no output."""
        p = tmp_path / "no_spans.jsonl"
        p.write_text(json.dumps({
            "event_id": "00000000000000000000009201",
            "event_type": "x.agentobs.decision.recorded",
            "parent_span_id": "cc00000000000099",
            "payload": {"chosen": "a", "decision_name": "d", "options": ["a", "b"]},
            "schema_version": "2.0",
            "source": "test@1.0.0",
            "span_id": "cc00000000000100",
            "timestamp": "2023-11-14T22:13:20.000000Z",
            "trace_id": _TRACE_NO_SPANS_TREE,
        }) + "\n", encoding="utf-8")
        stream = load_events(str(p))
        print_trace_tree(_TRACE_NO_SPANS_TREE, stream)
        assert capsys.readouterr().out == ""

    def test_all_spans_with_parents_root_detected_by_dangling_ref(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """When every span has a parent_span_id, the one with a dangling ref becomes root."""
        p = tmp_path / "all_parents.jsonl"
        _write_jsonl(p, [
            {
                "event_id": "00000000000000000000009202",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "cc0000000000dead",  # dangling — not in span_ids
                "payload": {
                    "duration_ms": 200.0,
                    "end_time_unix_nano": 1700000000200000000,
                    "span_name": "orphan_root",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000030",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_ALL_PARENTS,
            },
            {
                "event_id": "00000000000000000000009203",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "cc00000000000030",
                "payload": {
                    "duration_ms": 100.0,
                    "end_time_unix_nano": 1700000000100000000,
                    "span_name": "child_span",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000031",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_ALL_PARENTS,
            },
        ])
        stream = load_events(str(p))
        print_trace_tree(_TRACE_ALL_PARENTS, stream)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert lines[0] == "span orphan_root"  # dangling-ref span is detected as root
        assert any("span child_span" in ln for ln in lines)

    def test_three_level_deep_nesting_renders_all_nodes(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """A 3-level chain (agent_run > step > span) renders all three lines."""
        p = tmp_path / "deep.jsonl"
        _write_jsonl(p, [
            {
                "event_id": "00000000000000000000009204",
                "event_type": "llm.trace.agent.run.completed",
                "payload": {
                    "agent_name": "deep_agent",
                    "duration_ms": 300.0,
                    "end_time_unix_nano": 1700000000300000000,
                    "span_name": "agent_run",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000040",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_DEEP,
            },
            {
                "event_id": "00000000000000000000009205",
                "event_type": "llm.trace.agent.step.completed",
                "parent_span_id": "cc00000000000040",
                "payload": {
                    "duration_ms": 200.0,
                    "end_time_unix_nano": 1700000000200000000,
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                    "step_index": 0,
                    "step_name": "level_two",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000041",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_DEEP,
            },
            {
                "event_id": "00000000000000000000009206",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "cc00000000000041",
                "payload": {
                    "duration_ms": 100.0,
                    "end_time_unix_nano": 1700000000100000000,
                    "span_name": "level_three",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "cc00000000000042",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_DEEP,
            },
        ])
        stream = load_events(str(p))
        print_trace_tree(_TRACE_DEEP, stream)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "agent_run deep_agent"
        assert "step level_two" in lines[1]
        assert "span level_three" in lines[2]


# ---------------------------------------------------------------------------
# Phase 5 robustness tests — error hardening for tree
# ---------------------------------------------------------------------------

_TRACE_ORPHAN_WARN = "dddd000000000000dddd000000000030"


class TestTreeRobustness:
    def test_orphan_span_prints_warning_to_stderr(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Orphan spans (unknown parent) emit a Warning to stderr."""
        p = tmp_path / "orphan_warn.jsonl"
        _write_jsonl(p, [
            {
                "event_id": "00000000000000000000009301",
                "event_type": "llm.trace.agent.run.completed",
                "payload": {
                    "agent_name": "root_agent",
                    "duration_ms": 200.0,
                    "end_time_unix_nano": 1700000000200000000,
                    "span_name": "agent_run",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "dd00000000000050",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_ORPHAN_WARN,
            },
            {
                "event_id": "00000000000000000000009302",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "dd0000000000dead",  # dangling reference
                "payload": {
                    "duration_ms": 100.0,
                    "end_time_unix_nano": 1700000000100000000,
                    "span_name": "orphan",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "dd00000000000051",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_ORPHAN_WARN,
            },
        ])
        stream = load_events(str(p))
        print_trace_tree(_TRACE_ORPHAN_WARN, stream)
        captured = capsys.readouterr()
        assert "Warning: orphan span" in captured.err
        assert "dd00000000000051" in captured.err
        # orphan still rendered in stdout under root
        assert "span orphan" in captured.out

    def test_orphan_span_still_appears_in_tree(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Orphan spans are attached under root and appear in output despite bad parent."""
        p = tmp_path / "orphan_output.jsonl"
        _write_jsonl(p, [
            {
                "event_id": "00000000000000000000009303",
                "event_type": "llm.trace.agent.run.completed",
                "payload": {
                    "agent_name": "root_agent2",
                    "duration_ms": 200.0,
                    "end_time_unix_nano": 1700000000200000000,
                    "span_name": "agent_run",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "dd00000000000060",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": "dddd000000000000dddd000000000031",
            },
            {
                "event_id": "00000000000000000000009304",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "dd0000000000ffff",  # unknown parent
                "payload": {
                    "duration_ms": 50.0,
                    "end_time_unix_nano": 1700000000050000000,
                    "span_name": "attached_orphan",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "dd00000000000061",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": "dddd000000000000dddd000000000031",
            },
        ])
        stream = load_events(str(p))
        print_trace_tree("dddd000000000000dddd000000000031", stream)
        out = capsys.readouterr().out
        assert "span attached_orphan" in out
