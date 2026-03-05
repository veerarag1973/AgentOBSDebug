"""
conftest.py — Shared pytest fixtures for agentobs-debug tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Trace constants
# ---------------------------------------------------------------------------

SAMPLE_TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
UNKNOWN_TRACE_ID = "ffffffffffffffffffffffffffffffff"


# ---------------------------------------------------------------------------
# Path fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_jsonl_path() -> Path:
    """Path to the canonical 10-event test fixture file."""
    return FIXTURES_DIR / "sample_events.jsonl"


@pytest.fixture
def sample_trace_id() -> str:
    """Trace ID present in sample_events.jsonl."""
    return SAMPLE_TRACE_ID


@pytest.fixture
def unknown_trace_id() -> str:
    """A trace ID that does NOT exist in any fixture file."""
    return UNKNOWN_TRACE_ID


@pytest.fixture
def corrupt_jsonl_path(tmp_path: Path) -> Path:
    """A JSONL file containing a single malformed (non-JSON) line."""
    p = tmp_path / "corrupt.jsonl"
    p.write_text("THIS IS NOT JSON\n", encoding="utf-8")
    return p


@pytest.fixture
def empty_jsonl_path(tmp_path: Path) -> Path:
    """A JSONL file that is completely empty."""
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    return p
