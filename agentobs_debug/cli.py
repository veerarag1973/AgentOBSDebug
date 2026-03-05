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
"""

from __future__ import annotations

import argparse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentobs-debug",
        description="Developer tools for inspecting and debugging AgentOBS traces.",
    )
    parser.add_argument("--version", action="version", version="agentobs-debug 0.1.0")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # Shared arguments factory
    def _add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("events_file", metavar="EVENTS_FILE", help="Path to a .jsonl events file.")
        sub.add_argument(
            "--trace", required=True, metavar="TRACE_ID", help="32-char hex trace ID."
        )

    _add_common(subparsers.add_parser("replay", help="Replay an agent run step-by-step."))
    _add_common(subparsers.add_parser("inspect", help="Print a trace summary."))
    _add_common(subparsers.add_parser("tree", help="Print the span hierarchy tree."))
    _add_common(subparsers.add_parser("timeline", help="Print the execution timeline."))
    _add_common(subparsers.add_parser("tools", help="List tool calls."))
    _add_common(subparsers.add_parser("decisions", help="List decision points."))
    _add_common(subparsers.add_parser("cost", help="Print cost summary."))

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
    from agentobs_debug.errors import AgentOBSDebugError
    from agentobs_debug.loader import load_events

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        stream = load_events(args.events_file)
        cmd = args.command
        if cmd == "replay":
            replay(args.trace, stream=stream)
        elif cmd == "inspect":
            inspect_trace(args.trace, stream=stream)
        elif cmd == "tree":
            print_trace_tree(args.trace, stream=stream)
        elif cmd == "timeline":
            timeline(args.trace, stream=stream)
        elif cmd == "tools":
            show_tools(args.trace, stream=stream)
        elif cmd == "decisions":
            show_decisions(args.trace, stream=stream)
        elif cmd == "cost":
            cost_summary(args.trace, stream=stream)
    except AgentOBSDebugError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
