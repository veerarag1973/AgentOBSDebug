"""
generate_large_fixture.py — Generate tests/fixtures/large_events.jsonl

Produces:
  - 10,000 events spread across multiple traces
  - One focus trace containing exactly 1,000 spans with realistic payloads

Usage:
    python tests/generate_large_fixture.py

Output:
    tests/fixtures/large_events.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUTPUT = Path(__file__).parent / "fixtures" / "large_events.jsonl"

FOCUS_TRACE = "aaaa0000000000000000000000000001"
OTHER_TRACE = "bbbb0000000000000000000000000002"

START_NS = 1_700_000_000_000_000_000
STEP_NS  = 1_000_000  # 1 ms per span


def _event(
    event_id: str,
    event_type: str,
    span_id: str,
    trace_id: str,
    payload: dict,
    parent_span_id: str | None = None,
) -> dict:
    e: dict = {
        "event_id": event_id,
        "event_type": event_type,
        "payload": payload,
        "schema_version": "2.0",
        "source": "bench-agent@1.0.0",
        "span_id": span_id,
        "timestamp": "2023-11-14T22:13:20.000000Z",
        "trace_id": trace_id,
    }
    if parent_span_id is not None:
        e["parent_span_id"] = parent_span_id
    return e


def build_focus_trace(events: list[dict]) -> None:
    """Build the 1,000-span focus trace (1 agent run + 999 step spans)."""
    root_span_id = f"{FOCUS_TRACE[:16]}0001"
    start = START_NS
    end = start + 999 * STEP_NS

    events.append(_event(
        event_id="focus0000000000000001",
        event_type="llm.trace.agent.run.completed",
        span_id=root_span_id,
        trace_id=FOCUS_TRACE,
        payload={
            "agent_name": "bench_agent",
            "span_name": "agent_run",
            "start_time_unix_nano": start,
            "end_time_unix_nano": end,
            "duration_ms": float((end - start) / 1_000_000),
            "status": "ok",
        },
    ))

    for i in range(1, 1000):
        span_id = f"{FOCUS_TRACE[:12]}{i:04d}"
        s = start + i * STEP_NS
        e_ns = s + STEP_NS
        events.append(_event(
            event_id=f"focus{i:016d}",
            event_type="llm.trace.agent.step.completed",
            span_id=span_id,
            trace_id=FOCUS_TRACE,
            parent_span_id=root_span_id,
            payload={
                "step_name": f"step_{i}",
                "step_index": i - 1,
                "start_time_unix_nano": s,
                "end_time_unix_nano": e_ns,
                "duration_ms": float((e_ns - s) / 1_000_000),
                "status": "ok",
                "token_usage": {
                    "input_tokens": 10 + i % 50,
                    "output_tokens": 5 + i % 20,
                    "total_tokens": 15 + i % 70,
                },
            },
        ))


def build_filler_traces(events: list[dict], target_total: int) -> None:
    """Add filler events across multiple other traces to reach target_total."""
    idx = len(events)
    trace_idx = 0
    while len(events) < target_total:
        trace_id = f"cccc{trace_idx:028d}"
        span_id = f"cccc{idx:012d}"
        events.append(_event(
            event_id=f"fill{idx:016d}",
            event_type="llm.trace.span.completed",
            span_id=span_id,
            trace_id=trace_id,
            payload={
                "span_name": f"filler_{idx}",
                "start_time_unix_nano": START_NS + idx * STEP_NS,
                "end_time_unix_nano": START_NS + idx * STEP_NS + STEP_NS,
                "duration_ms": 1.0,
                "status": "ok",
            },
        ))
        idx += 1
        trace_idx += 1


def main() -> None:
    events: list[dict] = []
    build_focus_trace(events)
    build_filler_traces(events, target_total=10_000)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n",
        encoding="utf-8",
    )
    print(f"Written {len(events)} events to {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
