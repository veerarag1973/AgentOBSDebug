"""
inspect.py — Aggregate and print a trace summary.

Implements the ``inspect_trace()`` MUST function from MODULE-SPEC-0001 §8.
"""

from __future__ import annotations

from tracium.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError


def inspect_trace(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    output_format: str = "text",
) -> None:
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
    from agentobs_debug.loader import _filter_by_trace

    _SPAN_TYPES = frozenset({
        "llm.trace.agent.run.completed",
        "llm.trace.agent.step.completed",
        "llm.trace.span.completed",
    })
    _COST_TYPE = "llm.cost.token.recorded"
    _AGENT_RUN_TYPE = "llm.trace.agent.run.completed"

    events = _filter_by_trace(stream, trace_id)

    span_events = [e for e in events if e.event_type in _SPAN_TYPES]
    total_spans = len(span_events)

    # Prefer explicit cost-token events (one logical record per billed span).
    # Fallback to span.completed token_usage when cost events are absent.
    cost_events = [e for e in events if e.event_type == _COST_TYPE]

    total_tokens = 0
    if cost_events:
        for e in cost_events:
            tu = e.payload.get("token_usage")
            if tu:
                total_tokens += tu.get("input_tokens", 0) + tu.get("output_tokens", 0)
    else:
        leaf_spans = [e for e in events if e.event_type == "llm.trace.span.completed"]
        for e in leaf_spans:
            tu = e.payload.get("token_usage")
            if tu:
                total_tokens += tu.get("input_tokens", 0) + tu.get("output_tokens", 0)

    total_cost = 0.0
    for e in cost_events:
        cost = e.payload.get("cost")
        if cost:
            total_cost += cost.get("total_cost_usd", 0.0)

    run_event = next((e for e in events if e.event_type == _AGENT_RUN_TYPE), None)
    duration_s = 0.0
    status = "ok"
    if run_event is not None:
        start = run_event.payload.get("start_time_unix_nano")
        end = run_event.payload.get("end_time_unix_nano")
        if start is not None and end is not None:
            duration_s = (end - start) / 1_000_000_000
        status = run_event.payload.get("status") or "ok"

    if output_format == "json":
        import json as _json
        print(_json.dumps({
            "trace_id": trace_id,
            "spans": total_spans,
            "tokens": total_tokens,
            "cost_usd": round(total_cost, 6),
            "duration_s": round(duration_s, 3),
            "status": status,
        }, indent=2))
        return

    if output_format == "csv":
        import csv as _csv
        import io as _io
        buf = _io.StringIO()
        writer = _csv.DictWriter(
            buf,
            fieldnames=["trace_id", "spans", "tokens", "cost_usd", "duration_s", "status"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow({
            "trace_id": trace_id,
            "spans": total_spans,
            "tokens": total_tokens,
            "cost_usd": f"{total_cost:.6f}",
            "duration_s": f"{duration_s:.3f}",
            "status": status,
        })
        print(buf.getvalue(), end="")
        return

    print("Trace Summary")
    print("-------------")
    print(f"Trace ID: {trace_id}")
    print(f"Spans: {total_spans}")
    print(f"Tokens: {total_tokens}")
    print(f"Cost: ${total_cost:.4f}")
    print(f"Duration: {duration_s:.1f}s")
    print(f"Status: {status}")
