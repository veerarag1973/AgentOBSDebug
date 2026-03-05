"""
test_loader.py — Tests for agentobs_debug.loader

Phase 1 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.errors import CorruptEventError, TraceNotFoundError
from agentobs_debug.loader import _filter_by_trace, load_events


class TestLoadEvents:
    def test_load_valid_jsonl(self, sample_jsonl_path: Path) -> None:
        """load_events() returns an EventStream for a valid JSONL file."""
        pytest.skip("Phase 1 — not yet implemented")

    def test_load_missing_file(self, tmp_path: Path) -> None:
        """load_events() raises CorruptEventError for a non-existent path."""
        pytest.skip("Phase 1 — not yet implemented")

    def test_load_corrupt_jsonl(self, corrupt_jsonl_path: Path) -> None:
        """load_events() raises CorruptEventError for a malformed JSONL file."""
        pytest.skip("Phase 1 — not yet implemented")

    def test_load_returns_all_events(self, sample_jsonl_path: Path) -> None:
        """EventStream returned by load_events() contains the expected event count."""
        pytest.skip("Phase 1 — not yet implemented")


class TestFilterByTrace:
    def test_filter_returns_matching_events(
        self, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """_filter_by_trace() returns only events for the given trace_id."""
        pytest.skip("Phase 1 — not yet implemented")

    def test_filter_unknown_trace_raises(
        self, sample_jsonl_path: Path, unknown_trace_id: str
    ) -> None:
        """_filter_by_trace() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 1 — not yet implemented")

    def test_filter_empty_stream_raises(self, empty_jsonl_path: Path) -> None:
        """_filter_by_trace() raises TraceNotFoundError on an empty stream."""
        pytest.skip("Phase 1 — not yet implemented")
