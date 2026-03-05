"""
test_public_api.py — Regression tests for Phase 0.

Covers:
  - Exception hierarchy contracts (errors.py)
  - Public API surface (__init__.py __all__, __version__)
  - Test fixture file integrity (sample_events.jsonl)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentobs_debug.errors import (
    AgentOBSDebugError,
    CorruptEventError,
    InvalidSpanHierarchyError,
    TraceNotFoundError,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
# Must match conftest.SAMPLE_TRACE_ID — checked explicitly in TestFixtureIntegrity
_SAMPLE_TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"


# ---------------------------------------------------------------------------
# Phase 0.4 — Error hierarchy
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    def test_base_is_exception_subclass(self) -> None:
        """AgentOBSDebugError must root at Exception."""
        assert issubclass(AgentOBSDebugError, Exception)

    @pytest.mark.parametrize(
        "cls",
        [TraceNotFoundError, CorruptEventError, InvalidSpanHierarchyError],
    )
    def test_subclasses_inherit_base(self, cls: type) -> None:
        """Every error subclass must inherit AgentOBSDebugError."""
        assert issubclass(cls, AgentOBSDebugError)

    def test_all_subclasses_caught_by_base(self) -> None:
        """A bare `except AgentOBSDebugError` catches every subclass."""
        for cls in (TraceNotFoundError, CorruptEventError, InvalidSpanHierarchyError):
            with pytest.raises(AgentOBSDebugError):
                raise cls("caught by base")

    def test_exception_message_preserved(self) -> None:
        """The string passed to the constructor is retrievable via str()."""
        for cls in (AgentOBSDebugError, TraceNotFoundError, CorruptEventError):
            exc = cls("unique-marker-string")
            assert "unique-marker-string" in str(exc)

    def test_subclass_types_are_distinct(self) -> None:
        """None of the three leaf classes are the same object."""
        assert TraceNotFoundError is not CorruptEventError
        assert TraceNotFoundError is not InvalidSpanHierarchyError
        assert CorruptEventError is not InvalidSpanHierarchyError

    def test_base_not_caught_as_subclass(self) -> None:
        """Raising AgentOBSDebugError must NOT be caught by TraceNotFoundError."""
        reached = False
        with pytest.raises(AgentOBSDebugError):
            try:
                raise AgentOBSDebugError("base")
            except TraceNotFoundError:
                reached = True
        assert not reached, "Base class was incorrectly caught as TraceNotFoundError"

    def test_exceptions_are_instantiable_without_args(self) -> None:
        """All error classes must be constructable with zero arguments."""
        for cls in (
            AgentOBSDebugError,
            TraceNotFoundError,
            CorruptEventError,
            InvalidSpanHierarchyError,
        ):
            exc = cls()
            assert isinstance(exc, cls)


# ---------------------------------------------------------------------------
# Phase 0.3 — Public API surface
# ---------------------------------------------------------------------------


class TestPublicAPIExports:
    EXPECTED_EXPORTS = frozenset(
        {
            # Phase 1
            "load_events",
            # Phase 2 MUST
            "replay",
            "inspect_trace",
            "print_trace_tree",
            "timeline",
            # Phase 3 SHOULD
            "show_tools",
            "show_decisions",
            "cost_summary",
            # Exceptions (Phase 0)
            "AgentOBSDebugError",
            "TraceNotFoundError",
            "CorruptEventError",
            "InvalidSpanHierarchyError",
        }
    )

    def test_all_names_accessible_from_package(self) -> None:
        """Every name in EXPECTED_EXPORTS must be reachable via `import agentobs_debug`."""
        import agentobs_debug

        for name in self.EXPECTED_EXPORTS:
            assert hasattr(agentobs_debug, name), f"Missing from package: {name!r}"

    def test_dunder_all_is_exactly_expected_set(self) -> None:
        """__all__ must contain exactly the expected names — no extras, no omissions."""
        import agentobs_debug

        assert set(agentobs_debug.__all__) == self.EXPECTED_EXPORTS

    def test_version_is_nonempty_string(self) -> None:
        """__version__ must be a non-empty string."""
        import agentobs_debug

        assert isinstance(agentobs_debug.__version__, str)
        assert len(agentobs_debug.__version__) > 0

    def test_internal_helper_not_exported(self) -> None:
        """_filter_by_trace is internal and must not appear in __all__ or the package namespace."""
        import agentobs_debug

        assert "_filter_by_trace" not in agentobs_debug.__all__
        assert not hasattr(agentobs_debug, "_filter_by_trace")

    def test_imports_do_not_raise(self) -> None:
        """Importing the package must not raise any exception."""
        import importlib

        importlib.import_module("agentobs_debug")  # must not raise


# ---------------------------------------------------------------------------
# Phase 0.5 — Test fixture integrity
# ---------------------------------------------------------------------------


class TestFixtureIntegrity:
    @property
    def _fixture_lines(self) -> list[str]:
        return [
            ln
            for ln in (FIXTURES_DIR / "sample_events.jsonl").read_text().splitlines()
            if ln.strip()
        ]

    def test_fixture_file_exists(self) -> None:
        assert (FIXTURES_DIR / "sample_events.jsonl").exists()

    def test_fixture_has_exactly_ten_events(self) -> None:
        assert len(self._fixture_lines) == 10

    def test_fixture_has_exactly_one_trace_id(self) -> None:
        trace_ids = {json.loads(ln)["trace_id"] for ln in self._fixture_lines}
        assert len(trace_ids) == 1

    def test_fixture_trace_id_matches_constant(self) -> None:
        """Trace ID in file must match the constant used by all test fixtures."""
        trace_ids = {json.loads(ln)["trace_id"] for ln in self._fixture_lines}
        assert _SAMPLE_TRACE_ID in trace_ids

    def test_fixture_contains_all_required_event_types(self) -> None:
        event_types = {json.loads(ln)["event_type"] for ln in self._fixture_lines}
        required = {
            "llm.trace.agent.run.completed",
            "llm.trace.agent.step.completed",
            "llm.trace.span.completed",
            "x.agentobs.decision.recorded",
            "x.agentobs.tool.called",
            "llm.cost.token.recorded",
        }
        assert required <= event_types, f"Missing types: {required - event_types}"

    def test_fixture_has_five_span_events(self) -> None:
        """1 agent_run + 2 steps + 2 chat spans = 5 span-type events."""
        span_types = {
            "llm.trace.agent.run.completed",
            "llm.trace.agent.step.completed",
            "llm.trace.span.completed",
        }
        span_events = [
            ln for ln in self._fixture_lines
            if json.loads(ln)["event_type"] in span_types
        ]
        assert len(span_events) == 5

    def test_fixture_events_are_valid_json(self) -> None:
        """Every line in the fixture must parse as valid JSON."""
        for line in self._fixture_lines:
            obj = json.loads(line)
            assert "event_id" in obj
            assert "event_type" in obj
            assert "trace_id" in obj
