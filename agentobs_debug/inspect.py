"""
inspect.py — Aggregate and print a trace summary.

Implements the ``inspect_trace()`` MUST function from MODULE-SPEC-0001 §8.
"""

from __future__ import annotations

from tracium.stream import EventStream  # type: ignore[import]

from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import _filter_by_trace


def inspect_trace(trace_id: str, stream: "EventStream | None" = None) -> None:
    """Print a summary of a trace: span count, tokens, cost, duration, status.

    Parameters
    ----------
    trace_id:
        32-character hex OpenTelemetry trace ID to inspect.
    stream:
        EventStream previously loaded with :func:`~agentobs_debug.load_events`.

    Raises
    ------
    AgentOBSDebugError
        If *stream* is ``None``.
    TraceNotFoundError
        If no events matching *trace_id* exist in the stream.

    Example output::

        Trace Summary
        -------------
        Trace ID: 4bf92f3577b34da6
        Spans: 4
        Tokens: 812
        Cost: $0.0031
        Duration: 2.1s
        Status: ok
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    raise NotImplementedError("inspect_trace() — implemented in Phase 2")
