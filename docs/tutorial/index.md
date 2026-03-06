# agentobs-debug Tutorial

**Version:** 1.0.1  
**Audience:** Developers who build or operate AI agents with the AgentOBS SDK and need to inspect, debug, and understand trace data.

---

## Table of Contents

1. [What is agentobs-debug?](#1-what-is-agentobs-debug)
2. [What problem does it solve?](#2-what-problem-does-it-solve)
3. [How AgentOBS traces work](#3-how-agentobs-traces-work)
4. [Installation](#4-installation)
5. [Your first trace file](#5-your-first-trace-file)
6. [Loading events](#6-loading-events)
7. [Replaying an agent run](#7-replaying-an-agent-run)
8. [Inspecting a trace summary](#8-inspecting-a-trace-summary)
9. [Visualising the span tree](#9-visualising-the-span-tree)
10. [Reading the execution timeline](#10-reading-the-execution-timeline)
11. [Inspecting tool calls](#11-inspecting-tool-calls)
12. [Inspecting decision points](#12-inspecting-decision-points)
13. [Understanding cost](#13-understanding-cost)
14. [Using the CLI](#14-using-the-cli)
15. [Error handling](#15-error-handling)
16. [Working with multiple traces in one file](#16-working-with-multiple-traces-in-one-file)
17. [Putting it all together — a debugging workflow](#17-putting-it-all-together--a-debugging-workflow)
18. [Next steps](#18-next-steps)

---

## 1. What is agentobs-debug?

`agentobs-debug` is a Python developer toolkit for reading, visualising, and understanding traces produced by the [AgentOBS](https://github.com/agentobs) observability SDK.

It gives you seven focused views of what happened inside a single agent run:

| View | What it shows |
|---|---|
| **replay** | Each step in order — model, tokens, duration |
| **inspect** | A one-page summary — span count, total tokens, cost, duration, status |
| **tree** | The full span hierarchy as an ASCII tree |
| **timeline** | Every span start/end laid out on a millisecond ruler |
| **tools** | Every tool call with its arguments |
| **decisions** | Every recorded decision point and the option that was chosen |
| **cost** | Aggregated input/output token counts and USD cost |

All seven views are available both as a **Python API** and as a **command-line interface (CLI)**.

---

## 2. What problem does it solve?

When an AI agent misbehaves — wrong answer, unexpected tool call, high cost, slow response — you need to understand exactly what happened inside the run. AgentOBS writes every significant event to a JSONL file, but that raw file is not readable by humans.

`agentobs-debug` bridges that gap:

```
┌────────────────────────────────────────────────────────────────────┐
│  Your agent (powered by AgentOBS)                                  │
│                                                                    │
│  agent run → step → LLM call → tool call → decision → step → ...  │
│                       │                                            │
│            AgentOBS writes events.jsonl                            │
└───────────────────────┬────────────────────────────────────────────┘
                        │
                agentobs-debug reads it
                        │
                        ▼
   ┌──────────────────────────────────────────┐
   │  Human-readable views:                   │
   │   • step-by-step replay                  │
   │   • span tree                            │
   │   • timeline                             │
   │   • tool call list                       │
   │   • decision point list                  │
   │   • cost summary                         │
   └──────────────────────────────────────────┘
```

**When does this matter?**

- **Debugging wrong outputs** — walk through each step and LLM call in order to find where reasoning went wrong.
- **Diagnosing slow runs** — use the timeline to identify which span took the most time.
- **Cost control** — use the cost summary to see which steps are expensive and by how much.
- **Auditing tool behaviour** — see exactly what arguments were passed to every tool call.
- **Understanding agent logic** — read the decision points to understand why the agent chose a particular path.

---

## 3. How AgentOBS traces work

Before using `agentobs-debug` it helps to understand the three layers of an AgentOBS trace.

### Trace

A **trace** represents one complete agent run. It is identified by a **trace ID** — a 32-character hex string like `4bf92f3577b34da6a3ce929d0e0e4736`. Every event in a JSONL file carries this ID so that events from multiple runs can coexist in a single file.

### Spans

A trace is made of **spans**, each representing a unit of work:

```
agent_run          ← root span: the whole run
  step (search)    ← one reasoning step
    span (LLM)     ← the actual model call inside the step
  step (summarize)
    span (LLM)
```

Each span has a `span_id` and an optional `parent_span_id` to indicate nesting.

### Event types

AgentOBS records the following event types (used by `agentobs-debug`):

| Event type | What it represents |
|---|---|
| `llm.trace.agent.run.completed` | The whole agent run finished |
| `llm.trace.agent.step.completed` | One reasoning step finished |
| `llm.trace.span.completed` | One LLM call (chat/completion) finished |
| `llm.cost.token.recorded` | Token usage and cost billing record |
| `x.agentobs.tool.called` | An external tool was called |
| `x.agentobs.decision.recorded` | The agent recorded a decision point |

### JSONL file format

Each line in the file is a self-contained JSON object. Example (compressed):

```json
{
  "event_id": "00000000000000000000000001",
  "event_type": "llm.trace.agent.run.completed",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "a1b2c3d4e5f60001",
  "timestamp": "2023-11-14T22:13:20.000000Z",
  "payload": {
    "agent_name": "research_agent",
    "status": "ok",
    "start_time_unix_nano": 1700000000000000000,
    "end_time_unix_nano":   1700000001100000000,
    "duration_ms": 1100.0
  }
}
```

---

## 4. Installation

```bash
pip install agentobs-debug
```

**Requirements:**
- Python ≥ 3.10
- `agentobs >= 1.0.5` (installed automatically as a dependency)

Verify the install:

```bash
agentobs-debug --version
# agentobs-debug 1.0.1

agentobs-debug --help
```

---

## 5. Your first trace file

Create a minimal JSONL file called `events.jsonl` to follow along with the rest of this tutorial. Copy the contents below exactly (each block is one line):

```jsonl
{"event_id":"00000000000000000000000001","event_type":"llm.trace.agent.run.completed","payload":{"agent_name":"research_agent","duration_ms":1100.0,"end_time_unix_nano":1700000001100000000,"span_name":"agent_run","start_time_unix_nano":1700000000000000000,"status":"ok"},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60001","timestamp":"2023-11-14T22:13:20.000000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000002","event_type":"llm.trace.agent.step.completed","parent_span_id":"a1b2c3d4e5f60001","payload":{"duration_ms":330.0,"end_time_unix_nano":1700000000450000000,"start_time_unix_nano":1700000000120000000,"status":"ok","step_index":0,"step_name":"search"},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60002","timestamp":"2023-11-14T22:13:20.120000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000003","event_type":"llm.trace.span.completed","parent_span_id":"a1b2c3d4e5f60002","payload":{"duration_ms":330.0,"end_time_unix_nano":1700000000450000000,"model_info":{"name":"gpt-4o","system":"openai"},"span_name":"chat:gpt-4o","start_time_unix_nano":1700000000120000000,"status":"ok","token_usage":{"input_tokens":400,"output_tokens":130,"total_tokens":530}},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60003","timestamp":"2023-11-14T22:13:20.120000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000004","event_type":"x.agentobs.decision.recorded","parent_span_id":"a1b2c3d4e5f60002","payload":{"chosen":"search_api","decision_name":"tool_selection","options":["search_api","knowledge_base"]},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60006","timestamp":"2023-11-14T22:13:20.300000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000005","event_type":"x.agentobs.tool.called","parent_span_id":"a1b2c3d4e5f60002","payload":{"arguments":{"query":"LLM observability"},"tool_name":"search_api"},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60007","timestamp":"2023-11-14T22:13:20.150000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000006","event_type":"x.agentobs.tool.called","parent_span_id":"a1b2c3d4e5f60004","payload":{"arguments":{"url":"example.com"},"tool_name":"web_fetch"},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60008","timestamp":"2023-11-14T22:13:20.200000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000007","event_type":"llm.trace.agent.step.completed","parent_span_id":"a1b2c3d4e5f60001","payload":{"duration_ms":200.0,"end_time_unix_nano":1700000000900000000,"start_time_unix_nano":1700000000700000000,"status":"ok","step_index":1,"step_name":"summarize"},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60004","timestamp":"2023-11-14T22:13:20.700000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000008","event_type":"llm.trace.span.completed","parent_span_id":"a1b2c3d4e5f60004","payload":{"duration_ms":200.0,"end_time_unix_nano":1700000000900000000,"model_info":{"name":"gpt-4o","system":"openai"},"span_name":"chat:gpt-4o","start_time_unix_nano":1700000000700000000,"status":"ok","token_usage":{"input_tokens":170,"output_tokens":40,"total_tokens":210}},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60005","timestamp":"2023-11-14T22:13:20.700000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000009","event_type":"llm.cost.token.recorded","parent_span_id":"a1b2c3d4e5f60003","payload":{"cost":{"input_cost_usd":0.0016,"output_cost_usd":0.0007,"total_cost_usd":0.0023},"model":{"name":"gpt-4o","system":"openai"},"span_id":"a1b2c3d4e5f60003","token_usage":{"input_tokens":400,"output_tokens":130,"total_tokens":530}},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60009","timestamp":"2023-11-14T22:13:20.450000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
{"event_id":"00000000000000000000000010","event_type":"llm.cost.token.recorded","parent_span_id":"a1b2c3d4e5f60005","payload":{"cost":{"input_cost_usd":0.0005,"output_cost_usd":0.0002,"total_cost_usd":0.0007},"model":{"name":"gpt-4o","system":"openai"},"span_id":"a1b2c3d4e5f60005","token_usage":{"input_tokens":170,"output_tokens":40,"total_tokens":210}},"schema_version":"2.0","source":"research-agent@1.0.0","span_id":"a1b2c3d4e5f60010","timestamp":"2023-11-14T22:13:20.900000Z","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736"}
```

This represents a `research_agent` that:
1. Ran a **search** step — decided to use `search_api`, called it, then asked `gpt-4o` to process the result (400 input + 130 output tokens).
2. Ran a **summarize** step — fetched a URL with `web_fetch`, then asked `gpt-4o` to summarize (170 input + 40 output tokens).

Total run time: **1.1 seconds**. Total cost: **$0.0030**.

The trace ID for all examples below is:

```
4bf92f3577b34da6a3ce929d0e0e4736
```

---

## 6. Loading events

Every `agentobs-debug` function starts from an `EventStream` object. You load one with `load_events()`.

```python
import agentobs_debug as aod

stream = aod.load_events("events.jsonl")
```

`load_events()` delegates all parsing to the AgentOBS SDK. It raises typed errors if something goes wrong:

```python
from agentobs_debug.errors import CorruptEventError

try:
    stream = aod.load_events("events.jsonl")
except CorruptEventError as e:
    print(f"Could not load file: {e}")
```

**Key point:** `stream` is reusable. You load the file once and pass the same `stream` object to as many functions as you need. The file is not re-read on each call.

```python
stream = aod.load_events("events.jsonl")
trace  = "4bf92f3577b34da6a3ce929d0e0e4736"

# Reuse the same stream for every view
aod.replay(trace, stream=stream)
aod.inspect_trace(trace, stream=stream)
aod.print_trace_tree(trace, stream=stream)
```

---

## 7. Replaying an agent run

`replay()` walks through the agent's steps in order, showing what model was used, how many tokens were consumed, and how long each step took.

```python
aod.replay("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

**Output:**

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

**How to read this:**

- **Agent Run / Trace** — the name of your agent and the trace ID you looked up.
- **Step N — name** — steps are numbered by `step_index` and named by `step_name`.
- **Model** — the model name from the `model_info.name` field of the child LLM span.
- **Tokens** — total tokens (`input + output`) for the LLM call inside this step.
- **Duration** — wall-clock time the step took, from `duration_ms`.

**When to use this:** Start here when debugging. Replay gives you a narrative of the run in execution order.

---

## 8. Inspecting a trace summary

`inspect_trace()` gives you a one-page overview of the entire trace.

```python
aod.inspect_trace("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

**Output:**

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

**How to read this:**

- **Spans** — count of all span events (`agent_run` + `step` + `llm span`). Does not include tool calls, decisions, or cost events.
- **Tokens** — aggregated from `llm.cost.token.recorded` events (authoritative billing records). Falls back to `llm.trace.span.completed` token counts when no cost events are present.
- **Cost** — sum of `total_cost_usd` across all `llm.cost.token.recorded` events.
- **Duration** — wall-clock time of the root `agent_run` span in seconds.
- **Status** — the `status` field of the root `agent_run` event (`ok`, `error`, etc.).

**When to use this:** Use inspect as a health check. A `status: error`, unexpectedly high token count, or very long duration are signals that warrant deeper investigation.

---

## 9. Visualising the span tree

`print_trace_tree()` renders the parent–child hierarchy of all spans using box-drawing characters.

```python
aod.print_trace_tree("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

**Output:**

```
agent_run research_agent
 ├── step search
 │    └── span chat:gpt-4o
 └── step summarize
      └── span chat:gpt-4o
```

**How to read this:**

- The root span (`agent_run`) is always at the top.
- `├──` means there are more siblings below.
- `└──` means this is the last child at this level.
- `│` is a vertical continuation bar.
- Siblings at each level are sorted by `start_time_unix_nano`.

**Deeper trees** look like this when there are nested sub-spans:

```
agent_run product_researcher
 ├── step plan
 │    └── span chat:gpt-4o
 ├── step search
 │    ├── span chat:gpt-4o
 │    └── span tool:search_api
 └── step synthesis
      ├── span chat:gpt-4o
      │    └── span reflection
      └── span tool:write_report
```

**When to use this:** Use the tree to verify that your agent's span structure matches your expectations — catches cases where a tool span is accidentally orphaned, or nesting is wrong.

> **Note:** If a span has no matching parent in the trace, agentobs-debug will print a warning to stderr and attach it to the root:
> ```
> Warning: orphan span a1b2c3d4e5f60099 — attached to root
> ```

---

## 10. Reading the execution timeline

`timeline()` lays out every span start and end on a shared time axis, with offsets in milliseconds from the start of the run.

```python
aod.timeline("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

**Output:**

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

**How to read this:**

- `0 ms` is the start of the root `agent_run` span. All other offsets are relative to this.
- Rows are sorted strictly by nanosecond timestamp.
- Two rows at the same millisecond offset means they started/ended within the same millisecond.

**When to use this:** Use the timeline to diagnose latency. Identify which span or gap between spans is consuming the most wall-clock time.

**Common patterns to look for:**

| Pattern | What it means |
|---|---|
| Large gap between a step completing and the next starting | Overhead in your agent orchestration code |
| LLM span takes 80%+ of the step duration | Model latency is the bottleneck — consider a faster model |
| Steps overlapping in time | Parallel step execution — verify this is intentional |

---

## 11. Inspecting tool calls

`show_tools()` lists every recorded tool call with its name and arguments.

```python
aod.show_tools("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

**Output:**

```
Tool Calls
----------
search_api(query="LLM observability")
web_fetch(url="example.com")
```

Each line shows: `tool_name(arg_name="arg_value", ...)`.

**When no tool calls were recorded:**

```
No tool calls recorded.
```

**When to use this:** Use tool inspection when the agent's output is wrong and you suspect it called the wrong tool or passed bad arguments. This is the fastest way to verify that `tool_name` and `arguments` payload fields match your expectations.

---

## 12. Inspecting decision points

`show_decisions()` prints every `x.agentobs.decision.recorded` event — the options the agent considered and which it chose.

```python
aod.show_decisions("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

**Output:**

```
Decision: tool_selection
Options: search_api, knowledge_base
Chosen: search_api
```

If multiple decisions were recorded they are printed separated by a blank line:

```
Decision: tool_selection
Options: search_api, knowledge_base
Chosen: search_api

Decision: output_format
Options: markdown, plain_text, json
Chosen: markdown
```

**When no decisions were recorded:**

```
No decision points recorded.
```

**When to use this:** Use decision inspection to audit agent logic — verify that the agent chose the expected option and that the full set of candidate options is what you intended to expose.

---

## 13. Understanding cost

`cost_summary()` aggregates token usage and USD cost from all `llm.cost.token.recorded` events in the trace.

```python
aod.cost_summary("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
```

**Output:**

```
Cost Summary
------------
Input tokens: 570
Output tokens: 170
Total cost: $0.0030
```

**How to read this:**

- **Input tokens** — sum of all `token_usage.input_tokens` across cost events.
- **Output tokens** — sum of all `token_usage.output_tokens` across cost events.
- **Total cost** — sum of `cost.total_cost_usd` across cost events, formatted to 4 decimal places.

**When to use this:** Use cost summary to track per-run spend and to identify which trace is responsible for unexpectedly high billing. For per-step cost attribution, combine this with `replay()` which shows per-step token counts.

---

## 14. Using the CLI

Every function described above is also available as a CLI subcommand. The CLI is useful for quick inspection without writing any Python.

### General syntax

```bash
agentobs-debug COMMAND EVENTS_FILE [OPTIONS]
```

`--trace` is required for single-trace commands (`replay`, `inspect`, `tree`, `timeline`, `tools`, `decisions`, `cost`, `attribution`).

`report` does not require `--trace` (it can report all traces), and `diff` uses `--trace-a` and `--trace-b`.

### All subcommands

```bash
# Step-by-step replay
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# One-page trace summary
agentobs-debug inspect events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# Span hierarchy tree
agentobs-debug tree events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# Execution timeline
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# Tool call list
agentobs-debug tools events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# Decision point list
agentobs-debug decisions events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# Cost summary
agentobs-debug cost events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# Per-step cost and latency attribution
agentobs-debug attribution events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736

# Batch report across all traces in a file
agentobs-debug report events.jsonl

# Batch report for selected traces only (repeat --trace)
agentobs-debug report events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --trace aaaa0000000000000000000000000001

# Compare two traces side by side
agentobs-debug diff events.jsonl --trace-a 4bf92f3577b34da6a3ce929d0e0e4736 --trace-b aaaa0000000000000000000000000001

# Machine-readable output (supported by most commands)
agentobs-debug inspect events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --format json
agentobs-debug cost events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --format csv

# Additional filters
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --step search
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --from-ms 100 --to-ms 500 --event-type llm.trace.span
agentobs-debug tools events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --tool-name search_api
agentobs-debug decisions events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 --decision-name tool_selection
```

### CLI tips

**Save output to a file:**

```bash
agentobs-debug tree events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 > tree.txt
```

**Check the version:**

```bash
agentobs-debug --version
# agentobs-debug 1.0.1
```

**Pipe into a pager for long timelines:**

```bash
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736 | less
```

---

## 15. Error handling

### Possible exceptions

All errors are subclasses of `AgentOBSDebugError`:

| Exception | When raised |
|---|---|
| `CorruptEventError` | The JSONL file cannot be found (`FileNotFoundError`), cannot be read (`OSError`), or contains unparseable content |
| `TraceNotFoundError` | The `trace_id` you specified does not exist in the loaded stream |
| `InvalidSpanHierarchyError` | Reserved for future structural validation errors |

### Handling errors in Python

```python
from agentobs_debug.errors import (
    AgentOBSDebugError,
    CorruptEventError,
    TraceNotFoundError,
)
import agentobs_debug as aod

try:
    stream = aod.load_events("events.jsonl")
except CorruptEventError as e:
    print(f"File problem: {e}")
    raise SystemExit(1)

try:
    aod.replay("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)
except TraceNotFoundError as e:
    print(f"Trace not found: {e}")
except AgentOBSDebugError as e:
    # Catch-all for any other library error
    print(f"Unexpected error: {e}")
```

### CLI behaviour

In the CLI, all `AgentOBSDebugError` subclasses are caught and printed cleanly:

```
Error: No events found for trace_id='bad-trace-id'. Check that the correct JSONL file is loaded.
```

Exit code is `1` on any error. Python tracebacks are never shown.

---

## 16. Working with multiple traces in one file

A single JSONL file can contain events from many different agent runs. Most commands use `--trace` / `trace_id` to filter down to one run at a time, while `report` can summarize all traces and `diff` compares two selected traces.

**Example — two traces in one file:**

```python
stream = aod.load_events("production_events.jsonl")

# inspect the first run
aod.inspect_trace("4bf92f3577b34da6a3ce929d0e0e4736", stream=stream)

# inspect the second run
aod.inspect_trace("aaaa0000000000000000000000000001", stream=stream)
```

**Finding trace IDs in a JSONL file (bash):**

```bash
# Print all unique trace IDs in an events file
python -c "
import json, sys
ids = set()
for line in open('events.jsonl'):
    obj = json.loads(line)
    ids.add(obj.get('trace_id', ''))
for tid in sorted(ids):
    print(tid)
"
```

**Iterating over all traces in Python:**

```python
import json

trace_ids = set()
with open("events.jsonl") as f:
    for line in f:
        obj = json.loads(line)
        trace_ids.add(obj["trace_id"])

stream = aod.load_events("events.jsonl")
for trace_id in trace_ids:
    print(f"\n{'='*60}")
    print(f"TRACE: {trace_id}")
    print('='*60)
    aod.inspect_trace(trace_id, stream=stream)
```

---

## 17. Putting it all together — a debugging workflow

This section walks through a realistic debugging session using an events file where the agent produced an unexpected output.

### Step 1 — Get the big picture

```bash
agentobs-debug inspect events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
```

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

Status is `ok` and duration looks reasonable. Token count is moderate. No obvious red flags at this level.

### Step 2 — Replay the run step by step

```bash
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
```

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

Two steps ran. The search step consumed significantly more tokens than the summarize step. Investigating the search step further.

### Step 3 — Check what the agent decided

```bash
agentobs-debug decisions events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
```

```
Decision: tool_selection
Options: search_api, knowledge_base
Chosen: search_api
```

The agent chose `search_api` over `knowledge_base`. If the correct answer already existed in the knowledge base, this decision is the root cause — the knowledge base path would use fewer tokens.

### Step 4 — Verify tool arguments

```bash
agentobs-debug tools events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
```

```
Tool Calls
----------
search_api(query="LLM observability")
web_fetch(url="example.com")
```

`search_api` was called with `query="LLM observability"`. This looks correct for the task, so the problem is the decision, not the arguments.

### Step 5 — Check the span structure

```bash
agentobs-debug tree events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
```

```
agent_run research_agent
 ├── step search
 │    └── span chat:gpt-4o
 └── step summarize
      └── span chat:gpt-4o
```

Both steps have exactly one child LLM span. The tree is clean — no unexpected extra calls, no orphaned spans.

### Step 6 — Pinpoint the latency

```bash
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6a3ce929d0e0e4736
```

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

- Search step ran from `120 ms` to `450 ms` (330 ms).
- There is a **250 ms gap** between search completing (`450 ms`) and summarize starting (`700 ms`). This gap is agent orchestration overhead — something to investigate in the agent code.
- The remaining 200 ms after step summarize completes at `900 ms` until the run ends at `1100 ms` is also overhead — likely post-processing or cleanup.

### Conclusion

The debugging session revealed:

1. **Decision issue** — agent chose `search_api` over the cheaper `knowledge_base`.
2. **Latency issue** — 450 ms of the 1.1 s run is agent orchestration overhead, not model time.

Both are actionable improvements in the agent code, not in `agentobs-debug`.

---

## 18. Next steps

You now know how to use every feature of `agentobs-debug` to understand and debug an agent run.

**Further reading:**

- [AgentOBS SDK documentation](https://github.com/agentobs) — how to instrument your agent and produce JSONL traces.
- [AgentOBS event schema](https://github.com/agentobs) — full reference for every event type and payload field.

**Python API reference:** see `README.md` in the package root for a concise reference of all public functions and exceptions.

**Filing issues / contributing:** see `CONTRIBUTING.md` (if present) or open an issue in the repository.
