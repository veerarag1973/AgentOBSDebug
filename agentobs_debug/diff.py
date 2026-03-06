"""
diff.py — Compare two traces from the same (or different) EventStream.

Implements the ``diff_traces()`` function from MODULE-SPEC-0001 §Phase-9.
"""

from __future__ import annotations

from typing import Any

from agentobs.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError

_RUN_TYPE = "llm.trace.agent.run.completed"
_STEP_TYPE = "llm.trace.agent.step.completed"
_SPAN_TYPE = "llm.trace.span.completed"
_COST_TYPE = "llm.cost.token.recorded"

_SPAN_TYPES = frozenset({_RUN_TYPE, _STEP_TYPE, _SPAN_TYPE})


def diff_traces(
    trace_id_a: str,
    trace_id_b: str,
    stream: EventStream | None = None,
    output_format: str = "text",
) -> None:
    """Compare two traces and print a diff of spans, tokens, cost, and duration.

    Parameters
    ----------
    trace_id_a:
        The *before* trace ID (left side of the diff).
    trace_id_b:
        The *after* trace ID (right side of the diff).
    stream:
        EventStream previously loaded with :func:`~agentobs_debug.load_events`.
    output_format:
        ``"text"`` (default) or ``"json"``.

    Raises
    ------
    AgentOBSDebugError
        If *stream* is ``None``.
    TraceNotFoundError
        If either trace ID is not found in the stream.

    Example output (text)::

        Diff: 4bf92f35... → aaaa0000...
        ─────────────────────────────────────
          Duration:  1.1s → 2.3s  (+1.2s)
          Tokens:    740 → 980  (+240)
          Cost:      $0.0030 → $0.0041  (+$0.0011)
          Spans:     5 → 7  (+2)
          Status:    ok → ok

        Steps:
          = search     tokens 530→610 (+80),  duration 330→410 ms (+80ms)
          = summarize  tokens 210→370 (+160), duration 200→310 ms (+110ms)
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )

    import json as _json

    from agentobs_debug.loader import _filter_by_trace

    def _build_summary(tid: str) -> dict[str, Any]:
        events = _filter_by_trace(stream, tid)
        span_events = [e for e in events if e.event_type in _SPAN_TYPES]
        cost_events = [e for e in events if e.event_type == _COST_TYPE]

        total_tokens = 0
        if cost_events:
            for e in cost_events:
                tu = e.payload.get("token_usage") or {}
                total_tokens += tu.get("input_tokens", 0) + tu.get("output_tokens", 0)
        else:
            for e in events:
                if e.event_type == _SPAN_TYPE:
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
            "cost_usd": total_cost,
            "duration_s": duration_s,
            "status": status,
        }

    def _build_steps(tid: str) -> dict[str, dict[str, Any]]:
        events = _filter_by_trace(stream, tid)
        span_by_parent = {
            e.parent_span_id: e
            for e in events
            if e.event_type == _SPAN_TYPE and e.parent_span_id is not None
        }
        result = {}
        for e in events:
            if e.event_type != _STEP_TYPE:
                continue
            name = e.payload.get("step_name", "unknown")
            child = span_by_parent.get(e.span_id) if e.span_id else None
            tokens = 0
            if child:
                tu = child.payload.get("token_usage") or {}
                tokens = tu.get("total_tokens", 0)
            result[name] = {
                "tokens": tokens,
                "duration_ms": e.payload.get("duration_ms"),
            }
        return result

    a = _build_summary(trace_id_a)
    b = _build_summary(trace_id_b)
    steps_a = _build_steps(trace_id_a)
    steps_b = _build_steps(trace_id_b)

    all_step_names = list(steps_a.keys()) + [k for k in steps_b if k not in steps_a]

    step_diffs = []
    for name in all_step_names:
        in_a = name in steps_a
        in_b = name in steps_b
        if in_a and in_b:
            sa, sb = steps_a[name], steps_b[name]
            tok_delta = sb["tokens"] - sa["tokens"]
            dur_a = sa["duration_ms"]
            dur_b = sb["duration_ms"]
            dur_delta = (
                (dur_b - dur_a) if dur_a is not None and dur_b is not None else None
            )
            step_diffs.append({
                "status": "changed",
                "name": name,
                "tokens_a": sa["tokens"],
                "tokens_b": sb["tokens"],
                "tokens_delta": tok_delta,
                "duration_ms_a": dur_a,
                "duration_ms_b": dur_b,
                "duration_ms_delta": dur_delta,
            })
        elif in_a:
            step_diffs.append({
                "status": "removed",
                "name": name,
                "tokens_a": steps_a[name]["tokens"],
                "tokens_b": None,
                "tokens_delta": None,
                "duration_ms_a": steps_a[name]["duration_ms"],
                "duration_ms_b": None,
                "duration_ms_delta": None,
            })
        else:
            step_diffs.append({
                "status": "added",
                "name": name,
                "tokens_a": None,
                "tokens_b": steps_b[name]["tokens"],
                "tokens_delta": None,
                "duration_ms_a": None,
                "duration_ms_b": steps_b[name]["duration_ms"],
                "duration_ms_delta": None,
            })

    if output_format == "json":
        diff_doc = {
            "trace_a": trace_id_a,
            "trace_b": trace_id_b,
            "summary": {
                "duration_s": {"a": round(a["duration_s"], 3), "b": round(b["duration_s"], 3),
                               "delta": round(b["duration_s"] - a["duration_s"], 3)},
                "tokens": {"a": a["tokens"], "b": b["tokens"],
                           "delta": b["tokens"] - a["tokens"]},
                "cost_usd": {"a": round(a["cost_usd"], 4), "b": round(b["cost_usd"], 4),
                             "delta": round(b["cost_usd"] - a["cost_usd"], 4)},
                "spans": {"a": a["spans"], "b": b["spans"],
                          "delta": b["spans"] - a["spans"]},
                "status": {"a": a["status"], "b": b["status"]},
            },
            "steps": step_diffs,
        }
        print(_json.dumps(diff_doc, indent=2))
        return

    # ---------- text output ----------
    def _delta(val: float, fmt: str = ".0f", prefix: str = "") -> str:
        sign = "+" if val >= 0 else ""
        return f"({sign}{prefix}{val:{fmt}})"

    short_a = trace_id_a[:12] + "..."
    short_b = trace_id_b[:12] + "..."
    bar = "\u2500" * 45

    print(f"Diff: {short_a} \u2192 {short_b}")
    print(bar)
    dur_d = b["duration_s"] - a["duration_s"]
    print(f"  Duration:  {a['duration_s']:.1f}s \u2192 {b['duration_s']:.1f}s  "
          f"{_delta(dur_d, '.1f', '')}s")
    tok_d = b["tokens"] - a["tokens"]
    print(f"  Tokens:    {a['tokens']} \u2192 {b['tokens']}  {_delta(tok_d, '.0f')}")
    cost_d = b["cost_usd"] - a["cost_usd"]
    print(f"  Cost:      ${a['cost_usd']:.4f} \u2192 ${b['cost_usd']:.4f}  "
          f"{_delta(cost_d, '.4f', '$')}")
    span_d = b["spans"] - a["spans"]
    print(f"  Spans:     {a['spans']} \u2192 {b['spans']}  {_delta(span_d)}")
    print(f"  Status:    {a['status']} \u2192 {b['status']}")

    if step_diffs:
        print()
        print("Steps:")
        for sd in step_diffs:
            marker = {"changed": "=", "added": "+", "removed": "-"}.get(sd["status"], "?")
            name = sd["name"]
            if sd["status"] == "added":
                print(f"  {marker} {name}  (added, tokens={sd['tokens_b']}, "
                      f"duration={sd['duration_ms_b']} ms)")
            elif sd["status"] == "removed":
                print(f"  {marker} {name}  (removed, tokens={sd['tokens_a']}, "
                      f"duration={sd['duration_ms_a']} ms)")
            else:
                tok_str = f"tokens {sd['tokens_a']}\u2192{sd['tokens_b']} "
                tok_str += _delta(sd["tokens_delta"])
                dur_str = ""
                if sd["duration_ms_delta"] is not None:
                    dur_str = (f",  duration {sd['duration_ms_a']:.0f}\u2192"
                               f"{sd['duration_ms_b']:.0f} ms "
                               f"{_delta(sd['duration_ms_delta'], '.0f')}ms")
                print(f"  {marker} {name:<16}{tok_str}{dur_str}")
