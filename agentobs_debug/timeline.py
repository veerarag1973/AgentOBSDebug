"""
timeline.py — Print a chronological execution timeline for a trace.

Implements the ``timeline()`` MUST function from MODULE-SPEC-0001 §10.

Timing uses ``start_time_unix_nano`` and ``end_time_unix_nano`` fields from the
event payload.
"""

from __future__ import annotations

from tracium.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError


def timeline(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    from_ms: float | None = None,
    to_ms: float | None = None,
    event_type: str | None = None,
    output_format: str = "text",
) -> None:
    """Print a millisecond-resolution execution timeline for a trace.

    Each span contributes two rows: a *started* row at its start time and a
    *completed* row at its end time.  All offsets are relative to the earliest
    ``start_time_unix_nano`` seen in the trace.

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
    from tracium.event import Event

    from agentobs_debug.loader import _filter_by_trace

    _SPAN_TYPES = frozenset({
        "llm.trace.agent.run.completed",
        "llm.trace.agent.step.completed",
        "llm.trace.span.completed",
    })

    def _label(event: Event) -> str:
        et = event.event_type
        if et == "llm.trace.agent.run.completed":
            return event.payload.get("span_name") or event.payload.get("agent_name") or "agent_run"
        if et == "llm.trace.agent.step.completed":
            return f"step {event.payload.get('step_name', '')}"
        if et == "llm.trace.span.completed":
            return f"span {event.payload.get('span_name', '')}"
        return event.event_type

    events = _filter_by_trace(stream, trace_id)
    spans = [e for e in events if e.event_type in _SPAN_TYPES]

    # Optional event_type prefix filter
    if event_type is not None:
        lower_et = event_type.lower()
        spans = [e for e in spans if e.event_type.lower().startswith(lower_et)]

    start_times = [
        int(e.payload.get("start_time_unix_nano"))  # type: ignore[arg-type]
        for e in spans
        if e.payload.get("start_time_unix_nano") is not None
    ]
    if not start_times:
        if output_format == "json":
            import json as _json
            print(_json.dumps([]))
        elif output_format == "csv":
            import csv as _csv
            import io as _io
            buf = _io.StringIO()
            writer = _csv.DictWriter(
                buf, fieldnames=["offset_ms", "label"], lineterminator="\n"
            )
            writer.writeheader()
            print(buf.getvalue(), end="")
        return
    epoch_zero = min(start_times)

    rows: list[tuple[int, str]] = []
    for e in spans:
        lbl = _label(e)
        start = e.payload.get("start_time_unix_nano")
        end = e.payload.get("end_time_unix_nano")
        if start is not None:
            rows.append((int(start), f"{lbl} started"))
        if end is not None:
            rows.append((int(end), f"{lbl} completed"))

    rows.sort(key=lambda r: r[0])

    # Optional time-range filter
    if from_ms is not None or to_ms is not None:
        filtered = []
        for time_ns, lbl in rows:
            offset = (time_ns - epoch_zero) / 1_000_000
            if from_ms is not None and offset < from_ms:
                continue
            if to_ms is not None and offset > to_ms:
                continue
            filtered.append((time_ns, lbl))
        rows = filtered

    if not rows:
        if output_format == "json":
            import json as _json
            print(_json.dumps([]))
        elif output_format == "csv":
            import csv as _csv
            import io as _io
            buf = _io.StringIO()
            writer = _csv.DictWriter(buf, fieldnames=["offset_ms", "label"], lineterminator="\n")
            writer.writeheader()
            print(buf.getvalue(), end="")
        return

    if output_format == "json":
        import json as _json
        out = [
            {"offset_ms": round((t - epoch_zero) / 1_000_000, 3), "label": lbl}
            for t, lbl in rows
        ]
        print(_json.dumps(out, indent=2))
        return

    if output_format == "csv":
        import csv as _csv
        import io as _io
        buf = _io.StringIO()
        writer = _csv.DictWriter(buf, fieldnames=["offset_ms", "label"], lineterminator="\n")
        writer.writeheader()
        for t, lbl in rows:
            writer.writerow({"offset_ms": round((t - epoch_zero) / 1_000_000, 3), "label": lbl})
        print(buf.getvalue(), end="")
        return

    max_offset = int((max(t for t, _ in rows) - epoch_zero) / 1_000_000)
    col_width = len(f"{max_offset} ms") + 2

    for time_ns, lbl in rows:
        offset_ms = int((time_ns - epoch_zero) / 1_000_000)
        offset_str = f"{offset_ms} ms"
        print(f"{offset_str:<{col_width}}{lbl}")
