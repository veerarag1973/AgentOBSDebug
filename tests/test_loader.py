"""
test_loader.py — Tests for agentobs_debug.loader

Phase 1 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agentobs.stream import EventStream

from agentobs_debug.errors import CorruptEventError, TraceNotFoundError
from agentobs_debug.loader import _filter_by_trace, load_events

# The fixture file has exactly 10 events (all for SAMPLE_TRACE_ID).
EXPECTED_EVENT_COUNT = 10


class TestLoadEvents:
    def test_load_valid_jsonl(self, sample_jsonl_path: Path) -> None:
        """load_events() returns an EventStream for a valid JSONL file."""
        stream = load_events(str(sample_jsonl_path))
        assert isinstance(stream, EventStream)

    def test_load_missing_file(self, tmp_path: Path) -> None:
        """load_events() raises CorruptEventError for a non-existent path."""
        missing = tmp_path / "does_not_exist.jsonl"
        with pytest.raises(CorruptEventError):
            load_events(str(missing))

    def test_load_corrupt_jsonl(self, corrupt_jsonl_path: Path) -> None:
        """load_events() raises CorruptEventError for a malformed JSONL file."""
        with pytest.raises(CorruptEventError):
            load_events(str(corrupt_jsonl_path))

    def test_load_returns_all_events(self, sample_jsonl_path: Path) -> None:
        """EventStream returned by load_events() contains the expected event count."""
        stream = load_events(str(sample_jsonl_path))
        assert len(list(stream)) == EXPECTED_EVENT_COUNT


class TestFilterByTrace:
    def test_filter_returns_matching_events(
        self, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """_filter_by_trace() returns only events for the given trace_id."""
        stream = load_events(str(sample_jsonl_path))
        events = _filter_by_trace(stream, sample_trace_id)
        assert len(events) == EXPECTED_EVENT_COUNT
        assert all(e.trace_id == sample_trace_id for e in events)

    def test_filter_unknown_trace_raises(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """_filter_by_trace() raises TraceNotFoundError for an unknown trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            _filter_by_trace(stream, unknown_trace_id)

    def test_filter_empty_stream_raises(self, empty_jsonl_path: Path) -> None:
        """_filter_by_trace() raises TraceNotFoundError on an empty stream."""
        stream = load_events(str(empty_jsonl_path))
        with pytest.raises(TraceNotFoundError):
            _filter_by_trace(stream, "4bf92f3577b34da6a3ce929d0e0e4736")


# ---------------------------------------------------------------------------
# Regression tests — Phase 1
# ---------------------------------------------------------------------------


class TestLoaderRegression:
    def test_corrupt_error_chains_original_exception(self, corrupt_jsonl_path: Path) -> None:
        """CorruptEventError.__cause__ must be the original SDK exception."""
        with pytest.raises(CorruptEventError) as exc_info:
            load_events(str(corrupt_jsonl_path))
        assert exc_info.value.__cause__ is not None

    def test_corrupt_error_message_includes_path(self, corrupt_jsonl_path: Path) -> None:
        """CorruptEventError message must reference the file path (by filename at minimum)."""
        with pytest.raises(CorruptEventError) as exc_info:
            load_events(str(corrupt_jsonl_path))
        # The loader uses {path!r} which repr-escapes backslashes on Windows.
        # Checking the filename (no path separators) is unambiguous across OSes.
        assert corrupt_jsonl_path.name in str(exc_info.value)

    def test_trace_not_found_message_includes_trace_id(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """TraceNotFoundError message must contain the requested trace_id."""
        stream = load_events(str(sample_jsonl_path))
        with pytest.raises(TraceNotFoundError) as exc_info:
            _filter_by_trace(stream, unknown_trace_id)
        assert unknown_trace_id in str(exc_info.value)

    def test_stream_is_reusable(self, sample_jsonl_path: Path) -> None:
        """Iterating the same EventStream twice must yield the same event count."""
        stream = load_events(str(sample_jsonl_path))
        first_pass = len(list(stream))
        second_pass = len(list(stream))
        assert first_pass == second_pass == EXPECTED_EVENT_COUNT

    def test_filter_result_is_list(self, sample_jsonl_path: Path, sample_trace_id: str) -> None:
        """_filter_by_trace() must return a plain list, not a generator."""
        stream = load_events(str(sample_jsonl_path))
        result = _filter_by_trace(stream, sample_trace_id)
        assert isinstance(result, list)
