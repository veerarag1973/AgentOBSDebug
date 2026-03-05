"""
timeline.py — Print a chronological execution timeline for a trace.

Implements the ``timeline()`` MUST function from MODULE-SPEC-0001 §10.

Timing uses ``start_time_unix_nano`` and ``end_time_unix_nano`` fields from the
event payload when present, falling back to the Event ``timestamp`` field plus
``duration_ms`` for SDK compatibility.
"""

from __future__ import annotations

from tracium.stream import EventStream  # type: ignore[import]

from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import _filter_by_trace


def timeline(trace_id: str, stream: "EventStream | None" = None) -> None:
    """Print a millisecond-resolution execution timeline for a trace.

    Each span contributes two rows: a *started* row at its start time and a
    *completed* row at its end time.  All offsets are relative to the earliest
    ``start_time_unix_nano`` (or ``timestamp``) seen in the trace.

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

        0 ms      agent_run started
        120 ms    step search started
        450 ms    span completed
        700 ms    step summarize started
        900 ms    span completed
        1100 ms   agent_run completed
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    raise NotImplementedError("timeline() — implemented in Phase 2")
