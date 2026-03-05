"""
cli.py — Command-line interface for agentobs-debug.

Entry point: agentobs-debug (registered in pyproject.toml)
Implemented in Phase 4.

All AgentOBSDebugError subclasses are caught at this boundary and converted to
a clean error message on stderr + sys.exit(1).  Python tracebacks are NEVER
shown to end users.

Commands
--------
replay      Replay an agent run step-by-step.
inspect     Print a trace summary.
tree        Print the span hierarchy.
timeline    Print the execution timeline.
tools       List tool calls.
decisions   List decision points.
cost        Print cost summary.
attribution Per-step cost/latency breakdown with percentiles.
report      Batch summary across all traces in a file.
diff        Compare two traces.
"""

from __future__ import annotations

import argparse


def _add_format(
    sub: argparse.ArgumentParser,
    choices: tuple[str, ...] = ("text", "json", "csv"),
) -> None:
    sub.add_argument(
        "--format",
        dest="output_format",
        choices=choices,
        default="text",
        metavar="FORMAT",
        help="Output format: " + ", ".join(choices) + " (default: text).",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentobs-debug",
        description="Developer tools for inspecting and debugging AgentOBS traces.",
    )
    parser.add_argument("--version", action="version", version="agentobs-debug 1.0.0")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # Shared positional + --trace factory
    def _add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("events_file", metavar="EVENTS_FILE", help="Path to a .jsonl events file.")
        sub.add_argument(
            "--trace", required=True, metavar="TRACE_ID", help="32-char hex trace ID."
        )

    # replay
    sub_replay = subparsers.add_parser("replay", help="Replay an agent run step-by-step.")
    _add_common(sub_replay)
    sub_replay.add_argument(
        "--step", dest="step_name", metavar="STEP_NAME",
        help="Filter to a single step.",
    )
    _add_format(sub_replay, ("text", "json"))

    # inspect
    sub_inspect = subparsers.add_parser("inspect", help="Print a trace summary.")
    _add_common(sub_inspect)
    _add_format(sub_inspect)

    # tree
    sub_tree = subparsers.add_parser("tree", help="Print the span hierarchy tree.")
    _add_common(sub_tree)

    # timeline
    sub_timeline = subparsers.add_parser("timeline", help="Print the execution timeline.")
    _add_common(sub_timeline)
    sub_timeline.add_argument("--event-type", dest="event_type", metavar="EVENT_TYPE",
                               help="Filter to spans whose event_type starts with this prefix.")
    sub_timeline.add_argument("--from-ms", dest="from_ms", type=float, metavar="MS",
                               help="Show only rows at or after this ms offset from trace start.")
    sub_timeline.add_argument("--to-ms", dest="to_ms", type=float, metavar="MS",
                               help="Show only rows at or before this ms offset from trace start.")
    _add_format(sub_timeline)

    # tools
    sub_tools = subparsers.add_parser("tools", help="List tool calls.")
    _add_common(sub_tools)
    sub_tools.add_argument("--tool-name", dest="tool_name", metavar="TOOL_NAME",
                            help="Filter to a specific tool by name.")
    _add_format(sub_tools)

    # decisions
    sub_decisions = subparsers.add_parser("decisions", help="List decision points.")
    _add_common(sub_decisions)
    sub_decisions.add_argument("--decision-name", dest="decision_name", metavar="DECISION_NAME",
                                help="Filter to a specific decision by name.")
    _add_format(sub_decisions)

    # cost
    sub_cost = subparsers.add_parser("cost", help="Print cost summary.")
    _add_common(sub_cost)
    _add_format(sub_cost)

    # attribution (new)
    sub_attr = subparsers.add_parser(
        "attribution",
        help="Per-step cost/latency breakdown with percentiles.",
    )
    _add_common(sub_attr)
    _add_format(sub_attr)

    # report (new — no --trace required, accepts multiple)
    sub_report = subparsers.add_parser("report", help="Batch summary report across all traces.")
    sub_report.add_argument(
        "events_file", metavar="EVENTS_FILE",
        help="Path to a .jsonl events file.",
    )
    sub_report.add_argument(
        "--trace", dest="trace_ids", action="append", metavar="TRACE_ID",
        help="Restrict to these trace IDs (repeatable). Omit to report all.",
    )
    _add_format(sub_report)

    # diff (new)
    sub_diff = subparsers.add_parser("diff", help="Compare two traces.")
    sub_diff.add_argument(
        "events_file", metavar="EVENTS_FILE",
        help="Path to a .jsonl events file.",
    )
    sub_diff.add_argument(
        "--trace-a", required=True, metavar="TRACE_ID",
        help="First (before) trace ID.",
    )
    sub_diff.add_argument(
        "--trace-b", required=True, metavar="TRACE_ID",
        help="Second (after) trace ID.",
    )
    _add_format(sub_diff, ("text", "json"))

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    import sys

    from agentobs_debug import (
        cost_summary,
        inspect_trace,
        print_trace_tree,
        replay,
        show_decisions,
        show_tools,
        timeline,
    )
    from agentobs_debug.attribution import cost_attribution
    from agentobs_debug.diff import diff_traces
    from agentobs_debug.errors import AgentOBSDebugError
    from agentobs_debug.loader import load_events
    from agentobs_debug.report import batch_report

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        cmd = args.command
        fmt = getattr(args, "output_format", "text")

        if cmd == "report":
            batch_report(args.events_file, trace_ids=args.trace_ids, output_format=fmt)
        elif cmd == "diff":
            stream = load_events(args.events_file)
            diff_traces(args.trace_a, args.trace_b, stream=stream, output_format=fmt)
        else:
            stream = load_events(args.events_file)
            if cmd == "replay":
                replay(
                    args.trace, stream=stream,
                    step_name=getattr(args, "step_name", None),
                    output_format=fmt,
                )
            elif cmd == "inspect":
                inspect_trace(args.trace, stream=stream, output_format=fmt)
            elif cmd == "tree":
                print_trace_tree(args.trace, stream=stream)
            elif cmd == "timeline":
                timeline(
                    args.trace,
                    stream=stream,
                    from_ms=getattr(args, "from_ms", None),
                    to_ms=getattr(args, "to_ms", None),
                    event_type=getattr(args, "event_type", None),
                    output_format=fmt,
                )
            elif cmd == "tools":
                show_tools(
                    args.trace, stream=stream,
                    tool_name=getattr(args, "tool_name", None),
                    output_format=fmt,
                )
            elif cmd == "decisions":
                show_decisions(
                    args.trace, stream=stream,
                    decision_name=getattr(args, "decision_name", None),
                    output_format=fmt,
                )
            elif cmd == "cost":
                cost_summary(args.trace, stream=stream, output_format=fmt)
            elif cmd == "attribution":
                cost_attribution(args.trace, stream=stream, output_format=fmt)
    except AgentOBSDebugError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
