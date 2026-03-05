"""
filter.py — Internal filtering utilities shared across analysis modules.

Not exported in the public API; imported directly by replay, timeline,
tools, decisions, and attribution.
"""

from __future__ import annotations

from tracium.event import Event


def filter_by_step_name(
    events: list[Event],
    step_name: str | None,
) -> list[Event]:
    """Return only agent-step events whose step_name matches *step_name*.

    Matching is case-insensitive exact.  When *step_name* is ``None`` the
    original list is returned unchanged.
    """
    if step_name is None:
        return events
    lower = step_name.lower()
    return [
        e
        for e in events
        if e.event_type == "llm.trace.agent.step.completed"
        and e.payload.get("step_name", "").lower() == lower
    ]


def filter_timeline_rows(
    rows: list[tuple[int, str]],
    epoch_ns: int,
    from_ms: float | None,
    to_ms: float | None,
) -> list[tuple[int, str]]:
    """Keep only rows whose offset (ms) from *epoch_ns* lies within [from_ms, to_ms].

    Either bound may be ``None`` (meaning open-ended).
    """
    if from_ms is None and to_ms is None:
        return rows
    result = []
    for time_ns, lbl in rows:
        offset = (time_ns - epoch_ns) / 1_000_000
        if from_ms is not None and offset < from_ms:
            continue
        if to_ms is not None and offset > to_ms:
            continue
        result.append((time_ns, lbl))
    return result


def filter_spans_by_event_type(
    spans: list[Event],
    event_type: str | None,
) -> list[Event]:
    """Keep spans whose ``event_type`` starts with *event_type* (case-insensitive prefix match).

    When *event_type* is ``None`` the original list is returned unchanged.
    """
    if event_type is None:
        return spans
    lower = event_type.lower()
    return [e for e in spans if e.event_type.lower().startswith(lower)]
