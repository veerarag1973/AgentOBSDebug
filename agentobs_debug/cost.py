"""
cost.py — Display aggregated token usage and cost for a trace.

Implements the ``cost_summary()`` SHOULD function from MODULE-SPEC-0001 §13.

Aggregates TokenUsage and CostBreakdown data from all span events in the trace.
Cost data may live in:
  - SpanPayload.token_usage  (dict with input_tokens / output_tokens / total_tokens)
  - llm.cost.token.recorded  events (CostTokenRecordedPayload.cost / .token_usage)
Both sources are consulted and summed.
"""

from __future__ import annotations

from tracium.stream import EventStream  # type: ignore[import]

from agentobs_debug.errors import AgentOBSDebugError
from agentobs_debug.loader import _filter_by_trace

_SPAN_TYPE = "llm.trace.span.completed"
_COST_TOKEN_TYPE = "llm.cost.token.recorded"


def cost_summary(trace_id: str, stream: "EventStream | None" = None) -> None:
    """Print aggregated token usage and cost for a trace.

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

        Cost Summary
        ------------
        Input tokens: 640
        Output tokens: 172
        Total cost: $0.0032
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    raise NotImplementedError("cost_summary() — implemented in Phase 3")
