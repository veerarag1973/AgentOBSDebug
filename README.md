# agentobs-debug

Developer tools for inspecting, replaying, and visualising [AgentOBS](https://github.com/agentobs) traces.

## Installation

```bash
pip install agentobs-debug
```

Requires Python ≥ 3.10 and `agentobs >= 1.0.5`.

---

## Quickstart — Programmatic API

```python
import agentobs_debug as aod

# Load events from a JSONL file
stream = aod.load_events("events.jsonl")
trace  = "4bf92f3577b34da6a3ce929d0e0e4736"

aod.replay(trace, stream=stream)          # step-by-step replay
aod.inspect_trace(trace, stream=stream)   # trace summary
aod.print_trace_tree(trace, stream=stream) # span hierarchy
aod.timeline(trace, stream=stream)        # execution timeline

aod.show_tools(trace, stream=stream)      # tool calls
aod.show_decisions(trace, stream=stream)  # decision points
aod.cost_summary(trace, stream=stream)    # token usage + cost
aod.cost_attribution(trace, stream=stream) # per-step cost/latency table

# Multi-trace
from agentobs_debug.report import batch_report
from agentobs_debug.diff import diff_traces

batch_report("events.jsonl")               # summarise all traces in a file
diff_traces(trace_a, trace_b, stream=stream)  # compare two traces
```

---

## Quickstart — CLI

```bash
# Replay an agent run step-by-step
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6

# Print a trace summary
agentobs-debug inspect events.jsonl --trace 4bf92f3577b34da6

# Print the span hierarchy tree
agentobs-debug tree events.jsonl --trace 4bf92f3577b34da6

# Print the execution timeline
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6

# List all tool calls
agentobs-debug tools events.jsonl --trace 4bf92f3577b34da6

# List all decision points
agentobs-debug decisions events.jsonl --trace 4bf92f3577b34da6

# Print cost summary
agentobs-debug cost events.jsonl --trace 4bf92f3577b34da6

# Per-step cost/latency breakdown with percentiles
agentobs-debug attribution events.jsonl --trace 4bf92f3577b34da6

# Batch summary across all traces in a file
agentobs-debug report events.jsonl

# Diff two traces
agentobs-debug diff events.jsonl --trace-a 4bf92f3577b34da6a3ce929d0e0e4736 --trace-b aaaa0000000000000000000000000001
```

---

## Public API

### `load_events(path: str) -> EventStream`

Load events from a JSONL file using the AgentOBS SDK.

- **Raises** `CorruptEventError` if the file is missing or malformed.

### `replay(trace_id: str, stream: EventStream) -> None`

Print a step-by-step replay of an agent run.

Example output:
```
Agent Run: research_agent
Trace: 4bf92f3577b34da6

Step 0 — search
Model: gpt-4o
Tokens: 530
Duration: 330 ms
```

### `inspect_trace(trace_id: str, stream: EventStream) -> None`

Print an aggregated summary of a trace.

Example output:
```
Trace Summary
-------------
Trace ID: 4bf92f3577b34da6
Spans: 2
Tokens: 740
Cost: $0.0030
Duration: 1.1s
Status: ok
```

### `print_trace_tree(trace_id: str, stream: EventStream) -> None`

Print the span hierarchy using box-drawing characters.

Example output:
```
agent_run research_agent
 ├── step search
 │    └── span chat:gpt-4o
 └── step summarize
      └── span chat:gpt-4o
```

### `timeline(trace_id: str, stream: EventStream) -> None`

Print the execution timeline with millisecond offsets.

Example output:
```
0 ms      agent_run started
120 ms    step search started
450 ms    step search completed
700 ms    step summarize started
900 ms    step summarize completed
1100 ms   agent_run completed
```

### `show_tools(trace_id: str, stream: EventStream) -> None`

Print all tool calls recorded in a trace.

Example output:
```
Tool Calls
----------
search_api(query="LLM observability")
web_fetch(url="example.com")
```

### `show_decisions(trace_id: str, stream: EventStream) -> None`

Print all decision points recorded in a trace.

Example output:
```
Decision: tool_selection
Options: search_api, knowledge_base
Chosen: search_api
```

### `cost_summary(trace_id: str, stream: EventStream) -> None`

Print aggregated token usage and cost for a trace.

Example output:
```
Cost Summary
------------
Input tokens: 570
Output tokens: 170
Total cost: $0.0030
```

### `cost_attribution(trace_id: str, stream: EventStream, output_format: str = "text") -> None`

Print a per-step cost and latency breakdown table with p50/p90/p99 duration percentiles.

Import: `from agentobs_debug.attribution import cost_attribution`

### `batch_report(path: str, trace_ids: list[str] | None = None, output_format: str = "text") -> None`

Run `inspect_trace()` for every trace (or a given subset) in a JSONL file and print a summary table. Does not require a pre-loaded stream.

Import: `from agentobs_debug.report import batch_report`

### `diff_traces(trace_id_a: str, trace_id_b: str, stream: EventStream, output_format: str = "text") -> None`

Compare two traces side by side: spans, tokens, cost, duration, status, and per-step breakdown.

Import: `from agentobs_debug.diff import diff_traces`

---

## Error Handling

All errors are typed exceptions that subclass `AgentOBSDebugError`:

| Exception | Raised when |
|---|---|
| `CorruptEventError` | JSONL file missing or malformed |
| `TraceNotFoundError` | `trace_id` not found in stream |
| `InvalidSpanHierarchyError` | Reserved for future use |

In the CLI, all exceptions are caught and printed as `Error: <message>` to stderr with `exit code 1`. Python tracebacks are never shown.

---

## API Reference

See [docs/api-reference.md](docs/api-reference.md) for the full reference: all function signatures, parameters, output formats, exception hierarchy, and complete CLI flag documentation.

---

## Dependencies

- `agentobs >= 1.0.5` — AgentOBS SDK (provides `EventStream`, event types)
- Python ≥ 3.10
