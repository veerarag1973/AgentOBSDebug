"""
report.py — Batch report across all (or selected) traces in a JSONL file.

Implements the ``batch_report()`` function from MODULE-SPEC-0001 §Phase-9.
"""

from __future__ import annotations


def batch_report(
    path: str,
    trace_ids: list[str] | None = None,
    output_format: str = "text",
) -> None:
    """Run inspect_trace() for every trace (or a given subset) in a JSONL file.

    Parameters
    ----------
    path:
        Path to a ``.jsonl`` events file.
    trace_ids:
        Optional list of trace IDs to include.  When ``None`` every distinct
        trace ID found in the file is reported.
    output_format:
        ``"text"`` (default), ``"json"``, or ``"csv"``.

    Raises
    ------
    CorruptEventError
        If the file cannot be opened or parsed.

    Example output (text)::

        Trace ID: 4bf92f3577b34da6a3ce929d0e0e4736
        Spans: 5  Tokens: 740  Cost: $0.0030  Duration: 1.1s  Status: ok
        ---
        Trace ID: aaaa0000000000000000000000000001
        Spans: 3  Tokens: 210  Cost: $0.0007  Duration: 0.5s  Status: ok
    """
    import csv
    import io
    import json as _json
    import sys
    from typing import Any

    from agentobs_debug.loader import _filter_by_trace, load_events

    _SPAN_TYPES = frozenset({
        "llm.trace.agent.run.completed",
        "llm.trace.agent.step.completed",
        "llm.trace.span.completed",
    })
    _COST_TYPE = "llm.cost.token.recorded"
    _RUN_TYPE = "llm.trace.agent.run.completed"

    stream = load_events(path)

    # Discover all trace IDs present in the file if not supplied
    if trace_ids is None:
        seen: list[str] = []
        seen_set: set[str] = set()
        for e in stream:
            if e.trace_id is None or e.trace_id in seen_set:
                continue
            seen.append(e.trace_id)
            seen_set.add(e.trace_id)
        trace_ids = seen

    def _summarise(tid: str) -> dict[str, Any]:
        from agentobs_debug.errors import TraceNotFoundError
        try:
            events = _filter_by_trace(stream, tid)
        except TraceNotFoundError:
            return {
                "trace_id": tid,
                "spans": 0,
                "tokens": 0,
                "cost_usd": 0.0,
                "duration_s": 0.0,
                "status": "not_found",
            }
        span_events = [e for e in events if e.event_type in _SPAN_TYPES]
        cost_events = [e for e in events if e.event_type == _COST_TYPE]

        total_tokens = 0
        if cost_events:
            for e in cost_events:
                tu = e.payload.get("token_usage") or {}
                total_tokens += tu.get("input_tokens", 0) + tu.get("output_tokens", 0)
        else:
            for e in events:
                if e.event_type == "llm.trace.span.completed":
                    tu = e.payload.get("token_usage") or {}
                    total_tokens += tu.get("input_tokens", 0) + tu.get("output_tokens", 0)

        total_cost = sum(
            (e.payload.get("cost") or {}).get("total_cost_usd", 0.0) for e in cost_events
        )

        run = next((e for e in events if e.event_type == _RUN_TYPE), None)
        duration_s = 0.0
        status = "ok"
        if run is not None:
            s = run.payload.get("start_time_unix_nano")
            en = run.payload.get("end_time_unix_nano")
            if s is not None and en is not None:
                duration_s = (en - s) / 1_000_000_000
            status = run.payload.get("status") or "ok"

        return {
            "trace_id": tid,
            "spans": len(span_events),
            "tokens": total_tokens,
            "cost_usd": round(total_cost, 4),
            "duration_s": round(duration_s, 1),
            "status": status,
        }

    summaries = [_summarise(tid) for tid in trace_ids]

    if output_format == "json":
        print(_json.dumps(summaries, indent=2))
    elif output_format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["trace_id", "spans", "tokens", "cost_usd", "duration_s", "status"],
        )
        writer.writeheader()
        writer.writerows(summaries)
        print(buf.getvalue(), end="")
    else:
        for i, s in enumerate(summaries):
            if i > 0:
                print("---", file=sys.stdout)
            print(f"Trace ID: {s['trace_id']}")
            print(
                f"Spans: {s['spans']}  "
                f"Tokens: {s['tokens']}  "
                f"Cost: ${s['cost_usd']:.4f}  "
                f"Duration: {s['duration_s']:.1f}s  "
                f"Status: {s['status']}"
            )
