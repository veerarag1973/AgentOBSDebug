# agentobs-debug API Reference

**Version:** 1.0.1

This document is the complete reference for the `agentobs-debug` package. The package exposes a **Python API** for programmatic use and a **CLI** for shell-based inspection. Both surfaces provide identical capabilities.

---

## Table of Contents

1. [Python API — Overview](#1-python-api--overview)
2. [Loading events](#2-loading-events)
   - [load_events()](#load_eventspath-str--eventstream)
3. [Trace analysis functions](#3-trace-analysis-functions)
   - [replay()](#replaytrace_id-stream-step_name-output_format)
   - [inspect_trace()](#inspect_tracetrace_id-stream-output_format)
   - [print_trace_tree()](#print_trace_treetrace_id-stream)
   - [timeline()](#timelinetrace_id-stream-from_ms-to_ms-event_type-output_format)
   - [show_tools()](#show_toolstrace_id-stream-tool_name-output_format)
   - [show_decisions()](#show_decisionstrace_id-stream-decision_name-output_format)
   - [cost_summary()](#cost_summarytrace_id-stream-output_format)
4. [Multi-trace functions](#4-multi-trace-functions)
   - [batch_report()](#batch_reportpath-trace_ids-output_format)
   - [diff_traces()](#diff_tracestrace_id_a-trace_id_b-stream-output_format)
   - [cost_attribution()](#cost_attributiontrace_id-stream-output_format)
5. [Exceptions](#5-exceptions)
6. [Output formats](#6-output-formats)
7. [CLI Reference](#7-cli-reference)
   - [replay](#replay-1)
   - [inspect](#inspect)
   - [tree](#tree)
   - [timeline](#timeline-1)
   - [tools](#tools)
   - [decisions](#decisions)
   - [cost](#cost)
   - [attribution](#attribution)
   - [report](#report)
   - [diff](#diff)
8. [Importing the package](#8-importing-the-package)

---

## 1. Python API — Overview

All functions are importable from `agentobs_debug`:

```python
import agentobs_debug as aod

stream = aod.load_events("events.jsonl")
trace  = "4bf92f3577b34da6a3ce929d0e0e4736"

# Single-trace views
aod.replay(trace, stream=stream)
aod.inspect_trace(trace, stream=stream)
aod.print_trace_tree(trace, stream=stream)
aod.timeline(trace, stream=stream)
aod.show_tools(trace, stream=stream)
aod.show_decisions(trace, stream=stream)
aod.cost_summary(trace, stream=stream)
aod.cost_attribution(trace, stream=stream)

# Multi-trace
aod.batch_report("events.jsonl")
aod.diff_traces(trace_a, trace_b, stream=stream)
```

The three newer multi-trace functions (`batch_report`, `diff_traces`, `cost_attribution`) can also be imported directly from their modules:

```python
from agentobs_debug.report import batch_report
from agentobs_debug.diff import diff_traces
from agentobs_debug.attribution import cost_attribution
```

**Pattern — load once, query many times:**

```python
stream = aod.load_events("production_events.jsonl")

for trace_id in my_trace_ids:
    aod.inspect_trace(trace_id, stream=stream)
    aod.cost_summary(trace_id, stream=stream)
```

The `EventStream` object is immutable and reusable. The file is read only once.

---

## 2. Loading events

### `load_events(path: str) -> EventStream`

Load a JSONL events file into an `EventStream` using the AgentOBS SDK.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `path` | `str` | Path to a `.jsonl` file produced by an AgentOBS exporter. |

#### Returns

`agentobs.stream.EventStream` — an immutable, iterable sequence of `Event` objects.

#### Raises

| Exception | When |
|---|---|
| `CorruptEventError` | File not found, cannot be read (`OSError`), or a line fails to deserialise. |

#### Example

```python
import agentobs_debug as aod
from agentobs_debug.errors import CorruptEventError

try:
    stream = aod.load_events("events.jsonl")
except CorruptEventError as e:
    print(f"Cannot load file: {e}")
    raise SystemExit(1)
```

---

## 3. Trace analysis functions

All single-trace functions share these conventions:

- `trace_id` — the 32-character hex OpenTelemetry trace identifier.
- `stream` — an `EventStream` returned by `load_events()`. Passing `None` raises `AgentOBSDebugError`.
- `output_format` — controls the output representation (see [Output formats](#6-output-formats)).
- Functions write to **stdout** and return `None`.
- `TraceNotFoundError` is raised if `trace_id` does not exist in `stream`.

---

### `replay(trace_id, stream, *, step_name, output_format)`

Print a sequential step-by-step replay of an agent run.

#### Signature

```python
def replay(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    step_name: str | None = None,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to replay. |
| `stream` | `EventStream` | required | Loaded event stream. |
| `step_name` | `str \| None` | `None` | When set, only the step matching this name (case-insensitive exact match) is shown. |
| `output_format` | `str` | `"text"` | `"text"` or `"json"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

#### Example — Python

```python
stream = aod.load_events("events.jsonl")

# Full replay
aod.replay("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)

# Filtered to one step
aod.replay("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, step_name="search")

# JSON output
aod.replay("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, output_format="json")
```

#### Text output

```
Agent Run: research_agent
Trace: 4bf92f3577b34da6a3ce929d0e0e4736

Step 0 — search
Model: gpt-4o
Tokens: 530
Duration: 330 ms

Step 1 — summarize
Model: gpt-4o
Tokens: 210
Duration: 200 ms
```

#### JSON output

```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "agent_name": "research_agent",
  "steps": [
    {"step_index": 0, "step_name": "search", "model": "gpt-4o", "tokens": 530, "duration_ms": 330.0},
    {"step_index": 1, "step_name": "summarize", "model": "gpt-4o", "tokens": 210, "duration_ms": 200.0}
  ]
}
```

---

### `inspect_trace(trace_id, stream, *, output_format)`

Print a one-page summary of a trace: span count, total tokens, USD cost, duration, and status.

#### Signature

```python
def inspect_trace(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to summarise. |
| `stream` | `EventStream` | required | Loaded event stream. |
| `output_format` | `str` | `"text"` | `"text"`, `"json"`, or `"csv"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

#### Example — Python

```python
aod.inspect_trace("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
aod.inspect_trace("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, output_format="json")
```

#### Text output

```
Trace Summary
-------------
Trace ID: 4bf92f3577b34da6a3ce929d0e0e4736
Spans: 5
Tokens: 740
Cost: $0.0030
Duration: 1.1s
Status: ok
```

#### JSON output

```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spans": 5,
  "tokens": 740,
  "cost_usd": 0.003,
  "duration_s": 1.1,
  "status": "ok"
}
```

---

### `print_trace_tree(trace_id, stream)`

Print the span parent–child hierarchy as an ASCII tree.

#### Signature

```python
def print_trace_tree(
    trace_id: str,
    stream: EventStream | None = None,
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to visualise. |
| `stream` | `EventStream` | required | Loaded event stream. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

> **Note:** Orphan spans (those with a `parent_span_id` not found in the trace) are attached to the root with a warning printed to stderr: `Warning: orphan span <span_id> — attached to root`.

#### Example — Python

```python
aod.print_trace_tree("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

#### Output

```
agent_run research_agent
 ├── step search
 │    └── span chat:gpt-4o
 └── step summarize
      └── span chat:gpt-4o
```

---

### `timeline(trace_id, stream, *, from_ms, to_ms, event_type, output_format)`

Print a millisecond-resolution timeline of every span start and end event, with offsets relative to the trace start.

#### Signature

```python
def timeline(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    from_ms: float | None = None,
    to_ms: float | None = None,
    event_type: str | None = None,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to display. |
| `stream` | `EventStream` | required | Loaded event stream. |
| `from_ms` | `float \| None` | `None` | Show only rows at or after this millisecond offset from trace start. |
| `to_ms` | `float \| None` | `None` | Show only rows at or before this millisecond offset from trace start. |
| `event_type` | `str \| None` | `None` | Prefix filter on `event_type` (case-insensitive). E.g. `"llm.trace.span"` matches all LLM spans. |
| `output_format` | `str` | `"text"` | `"text"`, `"json"`, or `"csv"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

#### Example — Python

```python
# Full timeline
aod.timeline("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)

# Only show events between 100 ms and 500 ms
aod.timeline("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, from_ms=100, to_ms=500)

# Only LLM span events
aod.timeline("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, event_type="llm.trace.span")
```

#### Text output

```
0 ms     agent_run started
120 ms   step search started
120 ms   span chat:gpt-4o started
450 ms   span chat:gpt-4o completed
450 ms   step search completed
700 ms   step summarize started
700 ms   span chat:gpt-4o started
900 ms   span chat:gpt-4o completed
900 ms   step summarize completed
1100 ms  agent_run completed
```

---

### `show_tools(trace_id, stream, *, tool_name, output_format)`

Print all `x.agentobs.tool.called` events recorded in a trace.

#### Signature

```python
def show_tools(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    tool_name: str | None = None,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to inspect. |
| `stream` | `EventStream` | required | Loaded event stream. |
| `tool_name` | `str \| None` | `None` | When set, only calls to this tool are shown (case-insensitive exact match). |
| `output_format` | `str` | `"text"` | `"text"`, `"json"`, or `"csv"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

#### Example — Python

```python
# All tool calls
aod.show_tools("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)

# Only calls to search_api
aod.show_tools("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, tool_name="search_api")
```

#### Text output

```
Tool Calls
----------
search_api(query="LLM observability")
web_fetch(url="example.com")
```

When no tool calls match: `No tool calls recorded.`

---

### `show_decisions(trace_id, stream, *, decision_name, output_format)`

Print all `x.agentobs.decision.recorded` events recorded in a trace.

#### Signature

```python
def show_decisions(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    decision_name: str | None = None,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to inspect. |
| `stream` | `EventStream` | required | Loaded event stream. |
| `decision_name` | `str \| None` | `None` | When set, only the decision matching this name is shown (case-insensitive exact match). |
| `output_format` | `str` | `"text"` | `"text"`, `"json"`, or `"csv"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

#### Example — Python

```python
aod.show_decisions("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
aod.show_decisions("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, decision_name="tool_selection")
```

#### Text output

```
Decision: tool_selection
Options: search_api, knowledge_base
Chosen: search_api
```

When no decisions match: `No decision points recorded.`

---

### `cost_summary(trace_id, stream, *, output_format)`

Print aggregated token usage and USD cost from all `llm.cost.token.recorded` events in a trace.

#### Signature

```python
def cost_summary(
    trace_id: str,
    stream: EventStream | None = None,
    *,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to summarise. |
| `stream` | `EventStream` | required | Loaded event stream. |
| `output_format` | `str` | `"text"` | `"text"`, `"json"`, or `"csv"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

#### Example — Python

```python
aod.cost_summary("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

#### Text output

```
Cost Summary
------------
Input tokens: 570
Output tokens: 170
Total cost: $0.0030
```

---

## 4. Multi-trace functions

These functions operate across more than one trace. `batch_report` takes a file path directly (no pre-loaded stream needed). `diff_traces` and `cost_attribution` take a pre-loaded stream.

---

### `batch_report(path, trace_ids, output_format)`

Run `inspect_trace()` for every trace (or a specified subset) in a JSONL file and print a summary table.

#### Signature

```python
def batch_report(
    path: str,
    trace_ids: list[str] | None = None,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str` | required | Path to a `.jsonl` events file. |
| `trace_ids` | `list[str] \| None` | `None` | Restrict to these trace IDs. When `None`, every trace found in the file is reported. |
| `output_format` | `str` | `"text"` | `"text"`, `"json"`, or `"csv"`. |

#### Raises

| Exception | When |
|---|---|
| `CorruptEventError` | File not found or malformed. |

#### Example — Python

```python
from agentobs_debug.report import batch_report

# Report all traces in a file
batch_report("production_events.jsonl")

# Report only selected traces
batch_report(
    "production_events.jsonl",
    trace_ids=["4bf92f3577b34da6a3ce929d0e0e4736", "aaaa0000000000000000000000000001"],
)

# Machine-readable output
batch_report("production_events.jsonl", output_format="json")
```

#### Text output

```
Trace ID: 4bf92f3577b34da6a3ce929d0e0e4736
Spans: 5  Tokens: 740  Cost: $0.0030  Duration: 1.1s  Status: ok
---
Trace ID: aaaa0000000000000000000000000001
Spans: 3  Tokens: 210  Cost: $0.0007  Duration: 0.5s  Status: ok
```

#### CSV output

```
trace_id,spans,tokens,cost_usd,duration_s,status
4bf92f3577b34da6a3ce929d0e0e4736,5,740,0.003,1.1,ok
aaaa0000000000000000000000000001,3,210,0.0007,0.5,ok
```

---

### `diff_traces(trace_id_a, trace_id_b, stream, output_format)`

Compare two traces side by side: spans, tokens, cost, duration, status, and per-step breakdown.

#### Signature

```python
def diff_traces(
    trace_id_a: str,
    trace_id_b: str,
    stream: EventStream | None = None,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id_a` | `str` | required | The *before* (baseline) trace ID. |
| `trace_id_b` | `str` | required | The *after* (comparison) trace ID. |
| `stream` | `EventStream` | required | Loaded event stream (must contain both trace IDs). |
| `output_format` | `str` | `"text"` | `"text"` or `"json"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | Either trace ID not found in stream. |

#### Example — Python

```python
from agentobs_debug.diff import diff_traces

stream = aod.load_events("ab_test_events.jsonl")

diff_traces(
    "4bf92f3577b34da6a3ce929d0e0e4736",  # baseline
    "aaaa0000000000000000000000000001",  # candidate
    stream=stream,
)
```

#### Text output

```
Diff: 4bf92f35... → aaaa0000...
─────────────────────────────────────────────
  Duration:  1.1s → 2.3s  (+1.2s)
  Tokens:    740 → 980  (+240)
  Cost:      $0.0030 → $0.0041  (+$0.0011)
  Spans:     5 → 7  (+2)
  Status:    ok → ok

Steps:
  = search     tokens 530→610 (+80),  duration 330→410 ms (+80ms)
  = summarize  tokens 210→370 (+160), duration 200→310 ms (+110ms)
```

Step prefix legend:

| Prefix | Meaning |
|---|---|
| `=` | Step present in both traces |
| `+` | Step only in the *after* trace |
| `-` | Step only in the *before* trace |

---

### `cost_attribution(trace_id, stream, output_format)`

Print a per-step cost and latency breakdown table, with totals and duration percentiles (p50, p90, p99) across all steps.

#### Signature

```python
def cost_attribution(
    trace_id: str,
    stream: EventStream | None = None,
    output_format: str = "text",
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trace_id` | `str` | required | Trace to analyse. |
| `stream` | `EventStream` | required | Loaded event stream. |
| `output_format` | `str` | `"text"` | `"text"`, `"json"`, or `"csv"`. |

#### Raises

| Exception | When |
|---|---|
| `AgentOBSDebugError` | `stream` is `None`. |
| `TraceNotFoundError` | `trace_id` not in stream. |

#### Example — Python

```python
from agentobs_debug.attribution import cost_attribution

cost_attribution("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
cost_attribution("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream, output_format="csv")
```

#### Text output

```
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
```

---

## 5. Exceptions

All exceptions are importable from `agentobs_debug.errors` (or from `agentobs_debug` directly for the base class and the two most common subclasses).

```python
from agentobs_debug.errors import (
    AgentOBSDebugError,
    CorruptEventError,
    TraceNotFoundError,
    InvalidSpanHierarchyError,
)
```

| Exception | Base | Description |
|---|---|---|
| `AgentOBSDebugError` | `Exception` | Base class for all library errors. Catch this to handle any error from `agentobs_debug`. |
| `CorruptEventError` | `AgentOBSDebugError` | Raised by `load_events()` and `batch_report()` when the JSONL file is missing, unreadable, or contains a malformed event line. |
| `TraceNotFoundError` | `AgentOBSDebugError` | Raised by all single-trace analysis functions when `trace_id` is not present in the loaded stream. |
| `InvalidSpanHierarchyError` | `AgentOBSDebugError` | Reserved for future structural validation. Not currently raised. |

#### Recommended error-handling pattern

```python
import agentobs_debug as aod
from agentobs_debug.errors import (
    AgentOBSDebugError,
    CorruptEventError,
    TraceNotFoundError,
)

try:
    stream = aod.load_events("events.jsonl")
except CorruptEventError as e:
    print(f"File problem: {e}", file=sys.stderr)
    raise SystemExit(1)

try:
    aod.replay("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
except TraceNotFoundError as e:
    print(f"Trace not found: {e}", file=sys.stderr)
except AgentOBSDebugError as e:
    # Safety net for any other library error
    print(f"Unexpected error: {e}", file=sys.stderr)
```

---

## 6. Output formats

Most functions accept an `output_format` keyword argument. The supported values vary per function:

| Format | Description | Functions that support it |
|---|---|---|
| `"text"` | Human-readable text (**default** for all functions) | All functions |
| `"json"` | Structured JSON, printed to stdout | All except `print_trace_tree` |
| `"csv"` | RFC 4180 CSV with a header row, printed to stdout | `inspect_trace`, `cost_summary`, `show_tools`, `show_decisions`, `timeline`, `batch_report`, `cost_attribution` |

**JSON output** is suitable for piping into `jq` or loading with `json.loads()`:

```bash
agentobs-debug inspect events.jsonl --trace 4bf92f35... --format json | jq .cost_usd
```

**CSV output** is suitable for import into spreadsheets or further processing:

```bash
agentobs-debug cost events.jsonl --trace 4bf92f35... --format csv > cost.csv
```

---

## 7. CLI Reference

### General syntax

```
agentobs-debug COMMAND EVENTS_FILE [OPTIONS]
```

- `EVENTS_FILE` — path to a `.jsonl` file produced by AgentOBS.
- `--trace TRACE_ID` — 32-character hex trace ID. Required for single-trace commands.
- `--format FORMAT` — output format (`text`, `json`, or `csv`). Default: `text`.

```bash
agentobs-debug --version   # agentobs-debug 1.0.1
agentobs-debug --help
agentobs-debug COMMAND --help
```

All errors are printed to **stderr** as `Error: <message>` and exit with **code 1**. Python tracebacks are never shown.

---

### `replay`

Replay an agent run step-by-step.

```
agentobs-debug replay EVENTS_FILE --trace TRACE_ID [--step STEP_NAME] [--format text|json]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** Trace to replay. |
| `--step STEP_NAME` | Filter output to a single step name (case-insensitive). |
| `--format FORMAT` | `text` (default) or `json`. |

```bash
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --step search
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --format json
```

---

### `inspect`

Print a one-page trace summary.

```
agentobs-debug inspect EVENTS_FILE --trace TRACE_ID [--format text|json|csv]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** |
| `--format FORMAT` | `text` (default), `json`, or `csv`. |

```bash
agentobs-debug inspect events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug inspect events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --format json
```

---

### `tree`

Print the span hierarchy as an ASCII tree.

```
agentobs-debug tree EVENTS_FILE --trace TRACE_ID
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** |

```bash
agentobs-debug tree events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug tree events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 > tree.txt
```

---

### `timeline`

Print the millisecond-resolution execution timeline.

```
agentobs-debug timeline EVENTS_FILE --trace TRACE_ID
    [--from-ms MS] [--to-ms MS] [--event-type PREFIX]
    [--format text|json|csv]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** |
| `--from-ms MS` | Show only rows at or after this ms offset from trace start. |
| `--to-ms MS` | Show only rows at or before this ms offset from trace start. |
| `--event-type PREFIX` | Case-insensitive prefix filter on event type (e.g. `llm.trace.span`). |
| `--format FORMAT` | `text` (default), `json`, or `csv`. |

```bash
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --from-ms 100 --to-ms 500
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --event-type llm.trace.span
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 | less
```

---

### `tools`

List all tool calls in a trace.

```
agentobs-debug tools EVENTS_FILE --trace TRACE_ID [--tool-name NAME] [--format text|json|csv]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** |
| `--tool-name NAME` | Filter to a specific tool (case-insensitive exact match). |
| `--format FORMAT` | `text` (default), `json`, or `csv`. |

```bash
agentobs-debug tools events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug tools events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --tool-name search_api
```

---

### `decisions`

List all decision points in a trace.

```
agentobs-debug decisions EVENTS_FILE --trace TRACE_ID [--decision-name NAME] [--format text|json|csv]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** |
| `--decision-name NAME` | Filter to a specific decision (case-insensitive exact match). |
| `--format FORMAT` | `text` (default), `json`, or `csv`. |

```bash
agentobs-debug decisions events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug decisions events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --decision-name tool_selection
```

---

### `cost`

Print aggregated token usage and cost.

```
agentobs-debug cost EVENTS_FILE --trace TRACE_ID [--format text|json|csv]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** |
| `--format FORMAT` | `text` (default), `json`, or `csv`. |

```bash
agentobs-debug cost events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug cost events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --format csv
```

---

### `attribution`

Print per-step cost and latency breakdown with duration percentiles.

```
agentobs-debug attribution EVENTS_FILE --trace TRACE_ID [--format text|json|csv]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | **(required)** |
| `--format FORMAT` | `text` (default), `json`, or `csv`. |

```bash
agentobs-debug attribution events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
agentobs-debug attribution events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --format csv > attr.csv
```

---

### `report`

Print a batch summary across all (or selected) traces in a file. Does not require `--trace`.

```
agentobs-debug report EVENTS_FILE [--trace TRACE_ID ...] [--format text|json|csv]
```

| Flag | Description |
|---|---|
| `--trace TRACE_ID` | Restrict to this trace ID. Repeatable to include multiple. Omit to report all traces. |
| `--format FORMAT` | `text` (default), `json`, or `csv`. |

```bash
# Report all traces
agentobs-debug report production_events.jsonl

# Report only two specific traces
agentobs-debug report production_events.jsonl \
  --trace 4bf92f3577b34da6a3ce929d0e0e4736 \
  --trace aaaa0000000000000000000000000001

# Export as CSV for a spreadsheet
agentobs-debug report production_events.jsonl --format csv > traces.csv
```

---

### `diff`

Compare two traces side by side.

```
agentobs-debug diff EVENTS_FILE --trace-a TRACE_ID --trace-b TRACE_ID [--format text|json]
```

| Flag | Description |
|---|---|
| `--trace-a TRACE_ID` | **(required)** Baseline (before) trace ID. |
| `--trace-b TRACE_ID` | **(required)** Comparison (after) trace ID. |
| `--format FORMAT` | `text` (default) or `json`. |

```bash
agentobs-debug diff events.jsonl \
  --trace-a 4bf92f3577b34da6a3ce929d0e0e4736 \
  --trace-b aaaa0000000000000000000000000001

agentobs-debug diff events.jsonl \
  --trace-a 4bf92f3577b34da6a3ce929d0e0e4736 \
  --trace-b aaaa0000000000000000000000000001 \
    --format json | jq .summary.tokens
```

---

## 8. Importing the package

```python
# Recommended: import the package and use the aod. prefix
import agentobs_debug as aod

stream = aod.load_events("events.jsonl")
aod.replay("...", stream=stream)

# Alternative: import individual functions
from agentobs_debug import load_events, replay, inspect_trace
from agentobs_debug import cost_summary, show_tools, show_decisions
from agentobs_debug import print_trace_tree, timeline

# Multi-trace functions (not in __all__, import from modules directly)
from agentobs_debug.report import batch_report
from agentobs_debug.diff import diff_traces
from agentobs_debug.attribution import cost_attribution

# Exceptions
from agentobs_debug.errors import (
    AgentOBSDebugError,
    CorruptEventError,
    TraceNotFoundError,
    InvalidSpanHierarchyError,
)

# Version
import agentobs_debug
print(agentobs_debug.__version__)  # 1.0.1
```

### What's in `__all__`

The following names are exported in the package's `__all__` and can be relied upon as the stable public API:

```python
__all__ = [
    # Exceptions
    "AgentOBSDebugError",
    "CorruptEventError",
    "InvalidSpanHierarchyError",
    "TraceNotFoundError",
    # Functions
    "cost_summary",
    "inspect_trace",
    "load_events",
    "print_trace_tree",
    "replay",
    "show_decisions",
    "show_tools",
    "timeline",
]
```

`batch_report`, `diff_traces`, and `cost_attribution` are available in the package namespace (and importable from their respective modules) but are not yet in `__all__`.
