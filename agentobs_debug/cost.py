"""
cost.py — Display aggregated token usage and cost for a trace.

Implements the ``cost_summary()`` SHOULD function from MODULE-SPEC-0001 §13.

Aggregates TokenUsage and CostBreakdown data from ``llm.cost.token.recorded``
events in the trace (CostTokenRecordedPayload.cost / .token_usage).
"""

from __future__ import annotations

from agentobs.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError

_COST_TOKEN_TYPE = "llm.cost.token.recorded"


def cost_summary(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    output_format: str = "text",
) -> None:
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
    from agentobs_debug.loader import _filter_by_trace

    events = _filter_by_trace(stream, trace_id)
    input_tokens = 0
    output_tokens = 0
    total_cost = 0.0

    for evt in events:
        if evt.event_type == _COST_TOKEN_TYPE:
            tu = evt.payload.get("token_usage") or {}
            input_tokens += tu.get("input_tokens", 0)
            output_tokens += tu.get("output_tokens", 0)
            cost = evt.payload.get("cost") or {}
            total_cost += cost.get("total_cost_usd", 0.0)

    if output_format == "json":
        import json as _json
        print(_json.dumps({
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "total_cost_usd": round(total_cost, 6),
        }, indent=2))
        return

    if output_format == "csv":
        import csv as _csv
        import io as _io
        buf = _io.StringIO()
        writer = _csv.DictWriter(
            buf,
            fieldnames=["input_tokens", "output_tokens", "total_tokens", "total_cost_usd"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow({
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "total_cost_usd": f"{total_cost:.6f}",
        })
        print(buf.getvalue(), end="")
        return

    print("Cost Summary")
    print("------------")
    print(f"Input tokens: {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Total cost: ${total_cost:.4f}")
