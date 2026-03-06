"""
replay.py — Simulate and print an agent run step-by-step.

Implements the ``replay()`` MUST function from MODULE-SPEC-0001 §7.
"""

from __future__ import annotations

from agentobs.event import Event
from agentobs.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError

# Event type constants used when walking the span tree
_AGENT_RUN_TYPE = "llm.trace.agent.run.completed"
_AGENT_STEP_TYPE = "llm.trace.agent.step.completed"
_SPAN_TYPE = "llm.trace.span.completed"


def replay(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    step_name: str | None = None,
    output_format: str = "text",
) -> None:
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
    from agentobs_debug.loader import _filter_by_trace

    events = _filter_by_trace(stream, trace_id)

    run_event = next((e for e in events if e.event_type == _AGENT_RUN_TYPE), None)
    if run_event is None:
        raise AgentOBSDebugError(f"No agent_run event found in trace {trace_id!r}")

    agent_name = run_event.payload.get("agent_name", "unknown")

    step_events = sorted(
        [e for e in events if e.event_type == _AGENT_STEP_TYPE],
        key=lambda e: e.payload.get("step_index", 0),
    )

    # filter by step name if requested
    if step_name is not None:
        lower = step_name.lower()
        step_events = [
            s for s in step_events
            if s.payload.get("step_name", "").lower() == lower
        ]

    # Pre-index child spans by parent_span_id for O(1) lookup per step
    span_by_parent: dict[str, Event] = {
        e.parent_span_id: e
        for e in events
        if e.event_type == _SPAN_TYPE and e.parent_span_id is not None
    }

    if output_format == "json":
        import json as _json

        steps_out = []
        for step in step_events:
            si = step.payload.get("step_index")
            sn = step.payload.get("step_name", "unknown")
            dur = step.payload.get("duration_ms")
            chat = span_by_parent.get(step.span_id) if step.span_id is not None else None
            mdl = None
            total_tok = None
            if chat is not None:
                mi = chat.payload.get("model_info")
                if mi:
                    mdl = mi.get("name")
                tu = chat.payload.get("token_usage")
                if tu:
                    total_tok = tu.get("total_tokens")
            steps_out.append({
                "step_index": si,
                "step_name": sn,
                "model": mdl,
                "tokens": total_tok,
                "duration_ms": dur,
            })
        print(_json.dumps(
            {"agent_name": agent_name, "trace_id": trace_id, "steps": steps_out},
            indent=2,
        ))
        return

    print(f"Agent Run: {agent_name}")
    print(f"Trace: {trace_id}")

    for step in step_events:
        sname = step.payload.get("step_name", "unknown")
        step_index = step.payload.get("step_index", "?")
        duration_ms = step.payload.get("duration_ms")

        chat_event = span_by_parent.get(step.span_id) if step.span_id is not None else None

        model = "N/A"
        tokens = "N/A"
        if chat_event is not None:
            model_info = chat_event.payload.get("model_info")
            if model_info:
                model = model_info.get("name", "N/A")
            token_usage = chat_event.payload.get("token_usage")
            if token_usage:
                tokens = str(token_usage.get("total_tokens", "N/A"))

        dur_str = f"{int(duration_ms)} ms" if duration_ms is not None else "N/A"
        print(f"\nStep {step_index} \u2014 {sname}")
        print(f"Model: {model}")
        print(f"Tokens: {tokens}")
        print(f"Duration: {dur_str}")
