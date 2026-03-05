"""
test_tree.py — Tests for agentobs_debug.tree

Phase 2 implementation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentobs_debug.errors import AgentOBSDebugError, TraceNotFoundError
from agentobs_debug.tree import print_trace_tree


class TestPrintTraceTree:
    def test_tree_requires_stream(self, sample_trace_id: str) -> None:
        """print_trace_tree() raises AgentOBSDebugError when stream is None."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_tree_renders_hierarchy(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """print_trace_tree() output matches the expected tree structure."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_tree_single_span(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        """Single root span renders without tree connectors."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_tree_missing_trace(self, sample_jsonl_path: Path, unknown_trace_id: str) -> None:
        """print_trace_tree() raises TraceNotFoundError for an unknown trace_id."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_tree_orphan_spans_attached_to_root(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        """Spans with an unknown parent_span_id are attached under the root."""
        pytest.skip("Phase 2 — not yet implemented")

    def test_tree_siblings_sorted_by_start_time(
        self, capsys: pytest.CaptureFixture, sample_jsonl_path: Path, sample_trace_id: str
    ) -> None:
        """Sibling spans appear in ascending start_time order."""
        pytest.skip("Phase 2 — not yet implemented")
