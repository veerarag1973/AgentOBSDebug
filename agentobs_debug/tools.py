"""
tools.py — Inspect tool calls recorded in a trace.

Implements the ``show_tools()`` SHOULD function from MODULE-SPEC-0001 §12.

Reads events whose ``event_type`` is ``x.agentobs.tool.called`` and surfaces
the ``tool_name`` and ``arguments`` fields from the ToolCallPayload.
"""

from __future__ import annotations

from tracium.stream import EventStream  # type: ignore[import]

from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import _filter_by_trace

_TOOL_EVENT_TYPE = "x.agentobs.tool.called"


def show_tools(trace_id: str, stream: "EventStream | None" = None) -> None:
    """Print all tool calls recorded in a trace.

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

        Tool Calls
        ----------
        search_api(query="LLM observability")
        web_fetch(url="example.com")
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    raise NotImplementedError("show_tools() — implemented in Phase 3")
