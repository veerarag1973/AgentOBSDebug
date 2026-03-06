"""
tools.py — Inspect tool calls recorded in a trace.

Implements the ``show_tools()`` SHOULD function from MODULE-SPEC-0001 §12.

Reads events whose ``event_type`` is ``x.agentobs.tool.called`` and surfaces
the ``tool_name`` and ``arguments`` fields from the ToolCallPayload.
"""

from __future__ import annotations

import re

from agentobs.stream import EventStream

from agentobs_debug.errors import AgentOBSDebugError

_TOOL_EVENT_TYPE = "x.agentobs.tool.called"

# Compiled patterns for terminal-injection sanitisation
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_CTRL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _sanitize(value: object) -> str:
    """Strip ANSI escape sequences and control characters from user-controlled strings."""
    s = str(value)
    s = _ANSI_ESCAPE.sub("", s)
    s = _CTRL_CHARS.sub("", s)
    return s


def show_tools(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    tool_name: str | None = None,
    output_format: str = "text",
) -> None:
    """Print all tool calls recorded in a trace.

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

        Tool Calls
        ----------
        search_api(query="LLM observability")
        web_fetch(url="example.com")
    """
    if stream is None:
        raise AgentOBSDebugError(
            "An EventStream is required. Call load_events() first and pass the result as `stream`."
        )
    from agentobs_debug.loader import _filter_by_trace

    events = _filter_by_trace(stream, trace_id)
    tool_events = [e for e in events if e.event_type == _TOOL_EVENT_TYPE]

    if tool_name is not None:
        lower = tool_name.lower()
        tool_events = [e for e in tool_events if e.payload.get("tool_name", "").lower() == lower]

    if not tool_events:
        if output_format == "json":
            import json as _json
            print(_json.dumps([], indent=2))
        elif output_format == "csv":
            import csv as _csv
            import io as _io
            buf = _io.StringIO()
            writer = _csv.DictWriter(
                buf, fieldnames=["tool_name", "arguments"], lineterminator="\n"
            )
            writer.writeheader()
            print(buf.getvalue(), end="")
        else:
            print("No tool calls recorded.")
        return

    if output_format == "json":
        import json as _json
        rows = [
            {"tool_name": _sanitize(e.payload.get("tool_name", "unknown")),
             "arguments": e.payload.get("arguments") or {}}
            for e in tool_events
        ]
        print(_json.dumps(rows, indent=2))
        return

    if output_format == "csv":
        import csv as _csv
        import io as _io
        import json as _json
        buf = _io.StringIO()
        writer = _csv.DictWriter(buf, fieldnames=["tool_name", "arguments"], lineterminator="\n")
        writer.writeheader()
        for e in tool_events:
            writer.writerow({
                "tool_name": _sanitize(e.payload.get("tool_name", "unknown")),
                "arguments": _json.dumps(e.payload.get("arguments") or {}),
            })
        print(buf.getvalue(), end="")
        return

    print("Tool Calls")
    print("----------")
    for evt in tool_events:
        p = evt.payload
        name = _sanitize(p.get("tool_name", "unknown"))
        args = p.get("arguments") or {}
        args_str = ", ".join(f'{k}="{_sanitize(v)}"' for k, v in args.items())
        print(f"{name}({args_str})")
