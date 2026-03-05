"""
decisions.py — Inspect agent decision points.

Implements the ``show_decisions()`` SHOULD function from MODULE-SPEC-0001 §11.

Reads events whose ``event_type`` is ``x.agentobs.decision.recorded`` and
surfaces the ``decision_name``, ``options``, and ``chosen`` fields from the
event payload (DecisionPoint schema).
"""

from __future__ import annotations

import re

from tracium.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError

_DECISION_EVENT_TYPE = "x.agentobs.decision.recorded"

# Compiled patterns for terminal-injection sanitisation
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_CTRL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _sanitize(value: object) -> str:
    """Strip ANSI escape sequences and control characters from user-controlled strings."""
    s = str(value)
    s = _ANSI_ESCAPE.sub("", s)
    s = _CTRL_CHARS.sub("", s)
    return s


def show_decisions(trace_id: str, stream: EventStream | None = None) -> None:
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
    from agentobs_debug.loader import _filter_by_trace

    events = _filter_by_trace(stream, trace_id)
    decisions = [e for e in events if e.event_type == _DECISION_EVENT_TYPE]

    if not decisions:
        print("No decision points recorded.")
        return

    for i, evt in enumerate(decisions):
        p = evt.payload
        name = _sanitize(p.get("decision_name", "unknown"))
        options = ", ".join(_sanitize(o) for o in (p.get("options") or []))
        chosen = _sanitize(p.get("chosen", "unknown"))
        if i > 0:
            print()
        print(f"Decision: {name}")
        print(f"Options: {options}")
        print(f"Chosen: {chosen}")
