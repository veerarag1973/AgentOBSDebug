"""
attribution.py — Per-step cost/latency attribution with percentiles.

Implements the ``cost_attribution()`` function from MODULE-SPEC-0001 §Phase-9.
"""

from __future__ import annotations

import statistics
from typing import Any

from tracium.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError

_RUN_TYPE = "llm.trace.agent.run.completed"
_STEP_TYPE = "llm.trace.agent.step.completed"
_SPAN_TYPE = "llm.trace.span.completed"
_COST_TYPE = "llm.cost.token.recorded"


def cost_attribution(
    trace_id: str,
    stream: EventStream | None = None,
    output_format: str = "text",
) -> None:
    """Print per-step cost and latency breakdown with totals and duration percentiles.

    Parameters
    ----------
    trace_id:
        Trace to analyse.
    stream:
        EventStream previously loaded with :func:`~agentobs_debug.load_events`.
    output_format:
        ``"text"`` (default), ``"json"``, or ``"csv"``.

    Raises
    ------
    AgentOBSDebugError
        If *stream* is ``None``.

    Example output (text)::

        Cost & Latency Attribution  (trace 4bf92f35...)
        ─────────────────────────────────────────────────────────────────────────────
        Step            Model     In Toks  Out Toks  Cost       Duration  % Total
        ─────────────────────────────────────────────────────────────────────────────
        search          gpt-4o    400      130       $0.0023    330 ms    62.3%
        summarize       gpt-4o    170       40       $0.0007    200 ms    37.7%
        ─────────────────────────────────────────────────────────────────────────────
        TOTAL                     570      170       $0.0030    530 ms
        ─────────────────────────────────────────────────────────────────────────────

        Latency percentiles across 2 step(s):
          p50:  265 ms
          p90:  315 ms
          p99:  329 ms
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )

    import csv as _csv
    import io as _io
    import json as _json

    from agentobs_debug.loader import _filter_by_trace

    events = _filter_by_trace(stream, trace_id)

    # Index cost events by the span they are billing (payload.span_id or parent_span_id)
    cost_by_span: dict[str, dict[str, Any]] = {}
    for e in events:
        if e.event_type == _COST_TYPE:
            billed_sid = e.payload.get("span_id") or e.parent_span_id
            if billed_sid:
                tu = e.payload.get("token_usage") or {}
                cost_info = e.payload.get("cost") or {}
                cost_by_span[billed_sid] = {
                    "input_tokens": tu.get("input_tokens", 0),
                    "output_tokens": tu.get("output_tokens", 0),
                    "total_cost_usd": cost_info.get("total_cost_usd", 0.0),
                }

    # Index llm spans by their parent_span_id (step span_id → child span details)
    child_spans: dict[str, dict[str, Any]] = {}
    for e in events:
        if e.event_type == _SPAN_TYPE and e.parent_span_id and e.span_id:
            tu = e.payload.get("token_usage") or {}
            mi = e.payload.get("model_info") or {}
            child_spans[e.parent_span_id] = {
                "span_id": e.span_id,
                "model": mi.get("name") or e.payload.get("model") or "unknown",
                "input_tokens": tu.get("input_tokens", 0),
                "output_tokens": tu.get("output_tokens", 0),
            }

    rows: list[dict[str, Any]] = []
    for e in events:
        if e.event_type != _STEP_TYPE:
            continue
        name = e.payload.get("step_name") or "unknown"
        dur_ms: float | None = e.payload.get("duration_ms")
        if dur_ms is None:
            s = e.payload.get("start_time_unix_nano")
            en = e.payload.get("end_time_unix_nano")
            if s is not None and en is not None:
                dur_ms = (float(en) - float(s)) / 1_000_000

        model = "unknown"
        in_tok = 0
        out_tok = 0
        cost = 0.0

        child = child_spans.get(e.span_id) if e.span_id else None
        if child:
            model = child["model"]
            child_sid = child.get("span_id")
            if child_sid and child_sid in cost_by_span:
                ci = cost_by_span[child_sid]
                in_tok = ci["input_tokens"]
                out_tok = ci["output_tokens"]
                cost = ci["total_cost_usd"]
            else:
                # Fall back to token_usage on the span itself
                in_tok = child["input_tokens"]
                out_tok = child["output_tokens"]

        rows.append({
            "step_name": name,
            "model": model,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": cost,
            "duration_ms": dur_ms,
        })

    total_dur = sum(r["duration_ms"] for r in rows if r["duration_ms"] is not None)
    total_in = sum(r["input_tokens"] for r in rows)
    total_out = sum(r["output_tokens"] for r in rows)
    total_cost = sum(r["cost_usd"] for r in rows)

    durations: list[float] = [
        float(r["duration_ms"]) for r in rows if r["duration_ms"] is not None
    ]

    percentiles: dict[str, float | None]
    if len(durations) >= 2:
        sorted_d = sorted(durations)
        p50 = statistics.median(sorted_d)
        p90 = sorted_d[max(0, round(0.90 * len(sorted_d)) - 1)]
        p99 = sorted_d[max(0, round(0.99 * len(sorted_d)) - 1)]
        percentiles = {"p50": round(p50, 1), "p90": round(p90, 1), "p99": round(p99, 1)}
    elif len(durations) == 1:
        p50 = durations[0]
        percentiles = {"p50": round(p50, 1), "p90": round(p50, 1), "p99": round(p50, 1)}
    else:
        percentiles = {"p50": None, "p90": None, "p99": None}

    # Compute duration pct per row
    for r in rows:
        if total_dur > 0 and r["duration_ms"] is not None:
            r["pct_duration"] = round(100 * r["duration_ms"] / total_dur, 1)
        else:
            r["pct_duration"] = None

    # ---- JSON ----
    if output_format == "json":
        out_rows = [
            {
                "step_name": r["step_name"],
                "model": r["model"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cost_usd": round(r["cost_usd"], 6),
                "duration_ms": r["duration_ms"],
                "pct_duration": r["pct_duration"],
            }
            for r in rows
        ]
        doc = {
            "trace_id": trace_id,
            "steps": out_rows,
            "totals": {
                "input_tokens": total_in,
                "output_tokens": total_out,
                "total_tokens": total_in + total_out,
                "cost_usd": round(total_cost, 6),
                "duration_ms": round(total_dur, 1),
            },
            "percentiles": percentiles,
        }
        print(_json.dumps(doc, indent=2))
        return

    # ---- CSV ----
    if output_format == "csv":
        buf = _io.StringIO()
        fieldnames = [
            "step_name", "model", "input_tokens", "output_tokens",
            "cost_usd", "duration_ms", "pct_duration",
        ]
        writer = _csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "step_name": r["step_name"],
                "model": r["model"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cost_usd": f"{r['cost_usd']:.6f}",
                "duration_ms": r["duration_ms"],
                "pct_duration": r["pct_duration"],
            })
        print(buf.getvalue(), end="")
        return

    # ---- text ----
    bar = "\u2500" * 79
    hdr = f"Cost & Latency Attribution  (trace {trace_id[:12]}...)"
    print(hdr)
    print(bar)
    col = "{:<20} {:<10} {:>8} {:>8}  {:>10}  {:>10}  {:>7}"
    print(col.format("Step", "Model", "In Toks", "Out Toks", "Cost", "Duration", "% Total"))
    print(bar)
    for r in rows:
        dur_str = f"{r['duration_ms']:.0f} ms" if r["duration_ms"] is not None else "n/a"
        pct_str = f"{r['pct_duration']:.1f}%" if r["pct_duration"] is not None else "n/a"
        print(col.format(
            r["step_name"][:20],
            r["model"][:10],
            r["input_tokens"],
            r["output_tokens"],
            f"${r['cost_usd']:.4f}",
            dur_str,
            pct_str,
        ))
    print(bar)
    total_dur_str = f"{total_dur:.0f} ms" if total_dur else "n/a"
    print(col.format("TOTAL", "", total_in, total_out, f"${total_cost:.4f}", total_dur_str, ""))
    print(bar)
    print()
    n = len(durations)
    print(f"Latency percentiles across {n} step(s):")
    if percentiles["p50"] is not None:
        print(f"  p50:  {percentiles['p50']:.1f} ms")
        print(f"  p90:  {percentiles['p90']:.1f} ms")
        print(f"  p99:  {percentiles['p99']:.1f} ms")
    else:
        print("  (not enough data)")
