"""
agentobs-debug — Developer tools for inspecting and debugging AgentOBS traces.

Public API
----------
load_events     Load events from a JSONL file into an EventStream.
replay          Print a sequential replay of an agent run.
inspect_trace   Print a summary of a trace (spans, tokens, cost, duration).
print_trace_tree  Print the span hierarchy as a tree.
timeline        Print an execution timeline for a trace.
show_tools      Print all tool calls recorded in a trace.
show_decisions  Print all decision points recorded in a trace.
cost_summary    Print aggregated token and cost information for a trace.
batch_report    Print a batch summary report across all traces in a file.
diff_traces     Compare two traces and print a diff.
cost_attribution  Print per-step cost/latency breakdown with percentiles.
"""

from agentobs_debug.attribution import cost_attribution  # noqa: F401
from agentobs_debug.cost import cost_summary
from agentobs_debug.decisions import show_decisions
from agentobs_debug.diff import diff_traces  # noqa: F401
from agentobs_debug.errors import (
    AgentOBSDebugError,
    CorruptEventError,
    InvalidSpanHierarchyError,
    TraceNotFoundError,
)
from agentobs_debug.inspect import inspect_trace
from agentobs_debug.loader import load_events
from agentobs_debug.replay import replay
from agentobs_debug.report import batch_report  # noqa: F401
from agentobs_debug.timeline import timeline
from agentobs_debug.tools import show_tools
from agentobs_debug.tree import print_trace_tree

__all__ = [
    "AgentOBSDebugError",
    "CorruptEventError",
    "InvalidSpanHierarchyError",
    "TraceNotFoundError",
    "cost_summary",
    "inspect_trace",
    "load_events",
    "print_trace_tree",
    "replay",
    "show_decisions",
    "show_tools",
    "timeline",
]

__version__ = "1.0.0"
