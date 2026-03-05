"""
replay.py — Simulate and print an agent run step-by-step.

Implements the ``replay()`` MUST function from MODULE-SPEC-0001 §7.
"""

from __future__ import annotations

from tracium.stream import EventStream  # type: ignore[import]

from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import _filter_by_trace

# Event type constants used when walking the span tree
_AGENT_RUN_TYPE = "llm.trace.agent.run.completed"
_AGENT_STEP_TYPE = "llm.trace.agent.step.completed"
_SPAN_TYPE = "llm.trace.span.completed"


def replay(trace_id: str, stream: "EventStream | None" = None) -> None:
    """Print a sequential replay of an agent run.

    Locates all events for *trace_id*, reconstructs the span hierarchy, then
    prints each step with its model, token count, and duration.

    Parameters
    ----------
    trace_id:
        32-character hex OpenTelemetry trace ID to replay.
    stream:
        EventStream previously loaded with :func:`~agentobs_debug.load_events`.

    Raises
    ------
    AgentOBSDebugError
        If *stream* is ``None``.
    TraceNotFoundError
        If no events matching *trace_id* exist in the stream.
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    raise NotImplementedError("replay() — implemented in Phase 2")
