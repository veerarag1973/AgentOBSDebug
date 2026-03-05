"""
test_timeline.py — Tests for agentobs_debug.timeline

Phase 2 implementation tests.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.loader import load_events
from agentobs_debug.timeline import timeline

_TRACE_IDENTICAL = "ffff000000000000ffff000000000001"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


class TestTimeline:
    def test_timeline_requires_stream(self, sample_trace_id: str) -> None:
        """timeline() raises AgentOBSDebugError when stream is None."""
        with pytest.raises(AgentOBSDebugError):
            timeline(sample_trace_id, None)

    def test_timeline_output_format(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """timeline() output has correct ms offsets and span labels."""
        stream = load_events(str(sample_jsonl_path))
        timeline(sample_trace_id, stream)
        out = capsys.readouterr().out
        assert "0 ms" in out
        assert "agent_run started" in out
        assert "120 ms" in out
        assert "step search started" in out
        assert "450 ms" in out
        assert "700 ms" in out
        assert "step summarize started" in out
        assert "900 ms" in out
        assert "1100 ms" in out
        assert "agent_run completed" in out

    def test_timeline_ordering(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Timeline rows are always in ascending time order."""
        stream = load_events(str(sample_jsonl_path))
        timeline(sample_trace_id, stream)
        out = capsys.readouterr().out
        lines = [ln for ln in out.strip().split("\n") if ln.strip()]
        offsets = [int(ln.split("ms")[0].strip()) for ln in lines]
        assert offsets == sorted(offsets)

    def test_timeline_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """timeline() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            timeline(unknown_trace_id, stream)

    def test_timeline_first_offset_is_zero(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """The first timeline row always starts at 0 ms."""
        stream = load_events(str(sample_jsonl_path))
        timeline(sample_trace_id, stream)
        out = capsys.readouterr().out
        first_line = out.strip().split("\n")[0]
        assert first_line.startswith("0 ms")

    def test_timeline_identical_timestamps_stable_sort(self, tmp_path: Path) -> None:
        """Spans with identical timestamps produce consistent output across calls."""
        p = tmp_path / "identical.jsonl"
        _write_jsonl(p, [
            {
                "event_id": "00000000000000000000004001",
                "event_type": "llm.trace.agent.run.completed",
                "payload": {
                    "agent_name": "agent_a",
                    "duration_ms": 200.0,
                    "end_time_unix_nano": 1700000000200000000,
                    "span_name": "agent_run",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "ff00000000000001",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_IDENTICAL,
            },
            {
                "event_id": "00000000000000000000004002",
                "event_type": "llm.trace.span.completed",
                "parent_span_id": "ff00000000000001",
                "payload": {
                    "duration_ms": 200.0,
                    "end_time_unix_nano": 1700000000200000000,
                    "span_name": "twin_span",
                    "start_time_unix_nano": 1700000000000000000,
                    "status": "ok",
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "ff00000000000002",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_IDENTICAL,
            },
        ])
        stream = load_events(str(p))
        buf1, buf2 = io.StringIO(), io.StringIO()
        sys.stdout = buf1
        timeline(_TRACE_IDENTICAL, stream)
        sys.stdout = buf2
        timeline(_TRACE_IDENTICAL, stream)
        sys.stdout = sys.__stdout__
        assert buf1.getvalue() == buf2.getvalue()


# ---------------------------------------------------------------------------
# Regression tests — Phase 2.4
# ---------------------------------------------------------------------------

import re as _re  # noqa: E402 (needed for column alignment test)

_TRACE_NO_START_TIMES = "bbbb000000000000bbbb000000000020"


class TestTimelineRegression:
    def test_each_span_contributes_exactly_two_rows(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """5 span events × 2 rows (started + completed) = 10 output lines."""
        stream = load_events(str(sample_jsonl_path))
        timeline(sample_trace_id, stream)
        lines = [ln for ln in capsys.readouterr().out.strip().split("\n") if ln.strip()]
        assert len(lines) == 10

    def test_label_column_is_consistently_aligned(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Every row's label starts at the same character column (right-padded offset)."""
        stream = load_events(str(sample_jsonl_path))
        timeline(sample_trace_id, stream)
        lines = [ln for ln in capsys.readouterr().out.strip().split("\n") if ln.strip()]
        prefix_re = _re.compile(r"^(\d+ ms\s+)")
        col_positions: set[int] = set()
        for line in lines:
            m = prefix_re.match(line)
            assert m, f"Line doesn't match expected offset format: {line!r}"
            col_positions.add(len(m.group(1)))
        assert len(col_positions) == 1, f"Label column is inconsistent: {col_positions}"

    def test_no_span_events_produces_no_output(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Trace with only non-span events produces no timeline output."""
        p = tmp_path / "no_spans.jsonl"
        p.write_text(json.dumps({
            "event_id": "00000000000000000000009301",
            "event_type": "x.agentobs.decision.recorded",
            "parent_span_id": "bb00000000000030",
            "payload": {"chosen": "a", "decision_name": "d", "options": ["a", "b"]},
            "schema_version": "2.0",
            "source": "test@1.0.0",
            "span_id": "bb00000000000031",
            "timestamp": "2023-11-14T22:13:20.000000Z",
            "trace_id": _TRACE_NO_START_TIMES,
        }) + "\n", encoding="utf-8")
        stream = load_events(str(p))
        timeline(_TRACE_NO_START_TIMES, stream)
        assert capsys.readouterr().out == ""

    def test_all_rows_end_with_started_or_completed(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Every output row must end with 'started' or 'completed'."""
        stream = load_events(str(sample_jsonl_path))
        timeline(sample_trace_id, stream)
        for line in capsys.readouterr().out.strip().split("\n"):
            if line.strip():
                assert line.rstrip().endswith("started") or line.rstrip().endswith("completed"), (
                    f"Unexpected row ending: {line!r}"
                )

    def test_all_rows_contain_ms_unit(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Every output row must contain ' ms' as the offset unit."""
        stream = load_events(str(sample_jsonl_path))
        timeline(sample_trace_id, stream)
        for line in capsys.readouterr().out.strip().split("\n"):
            if line.strip():
                assert " ms" in line, f"Missing 'ms' unit in row: {line!r}"


# ---------------------------------------------------------------------------
# Phase 5 robustness tests — error hardening for timeline
# ---------------------------------------------------------------------------

_TRACE_MISSING_TIMES = "eeee000000000000eeee000000000030"
_TRACE_IDENTICAL_TS  = "eeee000000000000eeee000000000031"


class TestTimelineRobustness:
    def test_spans_missing_start_time_are_skipped(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Spans without start_time_unix_nano are silently excluded from timeline."""
        p = tmp_path / "missing_times.jsonl"
        rows = [
            {
                "event_id": "00000000000000000000009401",
                "event_type": "llm.trace.span.completed",
                "payload": {
                    "span_name": "has_times",
                    "start_time_unix_nano": 1700000000000000000,
                    "end_time_unix_nano":   1700000000100000000,
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "ee00000000000070",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_MISSING_TIMES,
            },
            {
                "event_id": "00000000000000000000009402",
                "event_type": "llm.trace.span.completed",
                "payload": {
                    "span_name": "no_times",
                    # deliberately omit start_time_unix_nano / end_time_unix_nano
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": "ee00000000000071",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_MISSING_TIMES,
            },
        ]
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        stream = load_events(str(p))
        timeline(_TRACE_MISSING_TIMES, stream)
        out = capsys.readouterr().out
        # only the span with times appears; span without times is silently skipped
        assert "has_times" in out
        assert "no_times" not in out

    def test_identical_timestamps_produces_stable_output(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Spans with identical timestamps produce output without crashing (stable sort)."""
        p = tmp_path / "identical_ts.jsonl"
        same_ns = 1700000000000000000
        rows = [
            {
                "event_id": f"0000000000000000000000940{i}",
                "event_type": "llm.trace.span.completed",
                "payload": {
                    "span_name": f"span_{i}",
                    "start_time_unix_nano": same_ns,
                    "end_time_unix_nano":   same_ns,
                },
                "schema_version": "2.0",
                "source": "test@1.0.0",
                "span_id": f"ee0000000000008{i}",
                "timestamp": "2023-11-14T22:13:20.000000Z",
                "trace_id": _TRACE_IDENTICAL_TS,
            }
            for i in range(3)
        ]
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        stream = load_events(str(p))
        timeline(_TRACE_IDENTICAL_TS, stream)  # must not raise
        lines = [ln for ln in capsys.readouterr().out.strip().split("\n") if ln.strip()]
        # 3 spans × 2 rows each = 6 lines, all at 0 ms
        assert len(lines) == 6
        assert all("0 ms" in ln for ln in lines)
