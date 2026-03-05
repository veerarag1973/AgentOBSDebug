"""
decisions.py — Inspect agent decision points.

Implements the ``show_decisions()`` SHOULD function from MODULE-SPEC-0001 §11.

Reads events whose ``event_type`` is ``x.agentobs.decision.recorded`` and
surfaces the ``decision_name``, ``options``, and ``chosen`` fields from the
event payload (DecisionPoint schema).
"""

from __future__ import annotations

from tracium.stream import EventStream  # type: ignore[import]

from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import _filter_by_trace

_DECISION_EVENT_TYPE = "x.agentobs.decision.recorded"


def show_decisions(trace_id: str, stream: "EventStream | None" = None) -> None:
    """Print all decision points recorded in a trace.

    Parameters
    ----------
    trace_id:
        32-character hex OpenTelemetry trace ID.
    stream:
        EventStream previously loaded with :func:`~agentobs_debug.load_events`.

    Raises
    ------
    AgentOBSDebugError
        If *stream* is ``None``.
    TraceNotFoundError
        If no events matching *trace_id* exist in the stream.

    Example output::

        Decision: tool_selection
        Options: search_api, knowledge_base
        Chosen: search_api
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    raise NotImplementedError("show_decisions() — implemented in Phase 3")
