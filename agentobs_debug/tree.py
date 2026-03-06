"""
tree.py — Visualise the span hierarchy as an ASCII tree.

Implements the ``print_trace_tree()`` MUST function from MODULE-SPEC-0001 §9.

The tree uses ``span_id`` / ``parent_span_id`` relationships from the Event
envelope to reconstruct the hierarchy.  Siblings are sorted by
``start_time_unix_nano`` for deterministic output.
"""

from __future__ import annotations

from agentobs.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError


def print_trace_tree(trace_id: str, stream: EventStream | None = None) -> None:
    """Print the span hierarchy of a trace using box-drawing characters.

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

        agent_run research_agent
         ├── step search
         │    └── span chat:gpt-4o
         └── step summarize
              └── span chat:gpt-4o
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    from typing import Any

    from agentobs.event import Event

    from agentobs_debug.loader import _filter_by_trace

    _SPAN_TYPES = frozenset({
        "llm.trace.agent.run.completed",
        "llm.trace.agent.step.completed",
        "llm.trace.span.completed",
    })

    def _label(event: Event) -> str:
        et = event.event_type
        if et == "llm.trace.agent.run.completed":
            name = event.payload.get("agent_name") or event.payload.get("span_name", "")
            return f"agent_run {name}"
        if et == "llm.trace.agent.step.completed":
            return f"step {event.payload.get('step_name', '')}"
        if et == "llm.trace.span.completed":
            return f"span {event.payload.get('span_name', '')}"
        return event.event_type

    def _render(kids: list[Any], children_map: dict[str, list[Any]], prefix: str) -> None:
        for i, kid in enumerate(kids):
            is_last = i == len(kids) - 1
            connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
            print(prefix + connector + _label(kid))
            continuation = "     " if is_last else "\u2502    "
            sub_kids = sorted(
                children_map.get(kid.span_id, []),
                key=lambda e: e.payload.get("start_time_unix_nano", 0),
            )
            if sub_kids:
                _render(sub_kids, children_map, prefix + continuation)

    events = _filter_by_trace(stream, trace_id)
    spans = [e for e in events if e.event_type in _SPAN_TYPES]
    if not spans:
        return

    span_ids = {e.span_id for e in spans}

    # True root: span with no parent_span_id in this trace
    root = next((e for e in spans if not e.parent_span_id), None)
    if root is None:
        root = next((e for e in spans if e.parent_span_id not in span_ids), spans[0])

    # Build children map; orphans (unknown parent) attach to root
    children_map: dict[str, list[Any]] = {}
    for e in spans:
        if e is root:
            continue
        if e.parent_span_id in span_ids:
            parent_id: str = e.parent_span_id  # type: ignore[assignment]
        else:
            import sys
            print(
                f"Warning: orphan span {e.span_id} — attached to root",
                file=sys.stderr,
            )
            parent_id = root.span_id  # type: ignore[assignment]
        children_map.setdefault(parent_id, []).append(e)

    print(_label(root))
    root_kids = sorted(
        children_map.get(root.span_id, []),  # type: ignore[arg-type]
        key=lambda e: e.payload.get("start_time_unix_nano", 0),
    )
    if root_kids:
        _render(root_kids, children_map, " ")
