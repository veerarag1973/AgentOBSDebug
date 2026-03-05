"""
tree.py — Visualise the span hierarchy as an ASCII tree.

Implements the ``print_trace_tree()`` MUST function from MODULE-SPEC-0001 §9.

The tree uses ``span_id`` / ``parent_span_id`` relationships from the Event
envelope to reconstruct the hierarchy.  Siblings are sorted by
``start_time_unix_nano`` (or ``timestamp`` as fallback) for deterministic output.
"""

from __future__ import annotations

from tracium.stream import EventStream  # type: ignore[import]

from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import _filter_by_trace


def print_trace_tree(trace_id: str, stream: "EventStream | None" = None) -> None:
    """Print the span hierarchy of a trace using box-drawing characters.

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

        agent_run research_agent
         ├── step search
         │    └── span chat:gpt-4o
         └── step summarize
              └── span chat:gpt-4o
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    raise NotImplementedError("print_trace_tree() — implemented in Phase 2")
