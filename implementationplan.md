# agentobs-debug — Implementation Plan

**Module:** agentobs-debug  
**Spec:** MODULE-SPEC-0001  
**Version:** 0.1 Draft  
**Date:** March 5, 2026  

---

## Overview

This document describes the phased implementation plan for the `agentobs-debug` Python package. The module provides developer tooling for inspecting, replaying, and visualizing AgentOBS traces. It depends on the `agentobs >= 0.1` SDK and must not reimplement any SDK internals.

---

## Phase 0 — Project Scaffolding

**Goal:** Establish the repository layout, packaging configuration, and developer environment before writing any functional code.

### Tasks

#### 0.1 Repository Structure

Create the following layout:

```
agentobs-debug/
├── agentobs_debug/
│   ├── __init__.py
│   ├── loader.py
│   ├── replay.py
│   ├── inspect.py
│   ├── tree.py
│   ├── timeline.py
│   ├── decisions.py
│   ├── tools.py
│   ├── cost.py
│   ├── cli.py
│   └── errors.py
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   └── sample_events.jsonl
│   ├── test_loader.py
│   ├── test_replay.py
│   ├── test_inspect.py
│   ├── test_tree.py
│   ├── test_timeline.py
│   ├── test_decisions.py
│   ├── test_tools.py
│   ├── test_cost.py
│   └── test_cli.py
├── pyproject.toml
├── README.md
└── LICENSE
```

#### 0.2 Packaging Configuration (`pyproject.toml`)

- Package name: `agentobs-debug`
- Importable as: `agentobs_debug`
- Python requirement: `>=3.10`
- Required dependency: `agentobs >= 0.1`
- Optional CLI entry point: `agentobs-debug = agentobs_debug.cli:main`
- Dev dependencies: `pytest`, `pytest-cov`, `ruff`, `mypy`

#### 0.3 Public API Surface (`__init__.py`)

Expose the following names at the top-level module:

| Symbol | Source Module | MUST/SHOULD |
|---|---|---|
| `load_events` | `loader` | MUST |
| `replay` | `replay` | MUST |
| `inspect_trace` | `inspect` | MUST |
| `print_trace_tree` | `tree` | MUST |
| `timeline` | `timeline` | MUST |
| `show_tools` | `tools` | SHOULD |
| `show_decisions` | `decisions` | SHOULD |
| `cost_summary` | `cost` | SHOULD |

#### 0.4 Error Types (`errors.py`)

Define the module's exception hierarchy:

```python
class AgentOBSDebugError(Exception): ...
class TraceNotFoundError(AgentOBSDebugError): ...
class CorruptEventError(AgentOBSDebugError): ...
class InvalidSpanHierarchyError(AgentOBSDebugError): ...
```

#### 0.5 Test Fixtures

Create `tests/fixtures/sample_events.jsonl` with representative AgentOBS events covering:
- An `agent_run` span
- Two `step` spans (search, summarize)
- Two `chat` spans with token usage
- One `decision_point` event
- Two `tool_call` events

#### 0.6 CI Configuration

Set up a basic GitHub Actions (or equivalent) workflow:
- Lint with `ruff`
- Type-check with `mypy`
- Run `pytest` with coverage

**Deliverable:** Empty but importable package; all files present; CI passes on an empty test suite.

---

## Phase 1 — Event Loading (MUST)

**Goal:** Implement `load_events()` backed by the AgentOBS SDK's `EventStream`.

### Dependency Contract

This module MUST NOT call any JSONL parsing logic directly. All parsing is delegated to:

```python
agentobs.EventStream.from_file(path)
```

### Tasks

#### 1.1 Implement `loader.py`

```python
from agentobs import EventStream
from agentobs_debug.errors import CorruptEventError

def load_events(path: str) -> EventStream:
    """Load events from a JSONL file using AgentOBS EventStream."""
    try:
        return EventStream.from_file(path)
    except Exception as exc:
        raise CorruptEventError(f"Failed to load events from {path!r}: {exc}") from exc
```

#### 1.2 Internal Helper: `_filter_by_trace`

Add a shared utility used by all higher-level functions:

```python
def _filter_by_trace(stream: EventStream, trace_id: str) -> list[Event]:
    events = [e for e in stream if e.trace_id == trace_id]
    if not events:
        raise TraceNotFoundError(f"No events found for trace_id={trace_id!r}")
    return events
```

This helper is internal (`_` prefix) and must not be exported from `__init__.py`.

#### 1.3 Tests (`test_loader.py`)

| Test | Scenario |
|---|---|
| `test_load_valid_jsonl` | Load the fixture file; assert EventStream returned |
| `test_load_missing_file` | Non-existent path raises `CorruptEventError` |
| `test_load_corrupt_jsonl` | Malformed JSONL raises `CorruptEventError` |

**Deliverable:** `load_events()` works and is fully tested.

---

## Phase 2 — Core Read-Only Analysis (MUST)

**Goal:** Implement the four MUST functions: `replay`, `inspect_trace`, `print_trace_tree`, `timeline`.

All four functions accept a `trace_id: str` and an `EventStream`. To avoid requiring callers to always pass a stream, each function will accept an optional `stream` parameter. If not provided, a sensible error is raised directing the developer to call `load_events()` first.

### Shared Pattern

Every MUST function follows this contract:

```python
def func(trace_id: str, stream: EventStream | None = None) -> None:
    if stream is None:
        raise AgentOBSDebugError("An EventStream is required. Call load_events() first.")
    events = _filter_by_trace(stream, trace_id)
    # ... render output
```

---

### Phase 2.1 — Trace Replay (`replay.py`)

#### Behavior
- Filter events by `trace_id`
- Reconstruct span hierarchy using AgentOBS span model
- Identify the root `agent_run` span
- Walk child `step` spans in chronological order
- For each step, locate the associated `chat` span and extract model name, token count, and duration

#### Output Format
```
Agent Run: research_agent
Trace: 4bf92f3577b34da6

Step 0 — search
Model: gpt-4o
Tokens: 530
Duration: 420 ms

Step 1 — summarize
Model: gpt-4o
Tokens: 210
Duration: 190 ms
```

#### Implementation Notes
- Use `agentobs.SpanHierarchy` (or equivalent SDK type) to reconstruct parent-child relationships via `span_id` / `parent_span_id`
- Duration = `(end_time_unix_nano - start_time_unix_nano) / 1_000_000` ms
- Token count sourced from `SpanPayload.TokenUsage`

#### Tests (`test_replay.py`)

| Test | Scenario |
|---|---|
| `test_replay_output_format` | Captured stdout matches expected format |
| `test_replay_missing_trace` | Raises `TraceNotFoundError` |
| `test_replay_no_steps` | Agent run with no child steps prints header only |
| `test_replay_missing_token_data` | Steps with no TokenUsage display `N/A` gracefully |

---

### Phase 2.2 — Trace Inspection (`inspect.py`)

#### Behavior
- Aggregate across all spans in the trace
- Compute: total spans, total tokens (input + output), total cost, total duration (root span), status

#### Output Format
```
Trace Summary
-------------
Trace ID: 4bf92f3577b34da6
Spans: 4
Tokens: 812
Cost: $0.0031
Duration: 2.1s
Status: ok
```

#### Implementation Notes
- `total_spans` = count of events with `event_type == "span"`
- `total_tokens` = sum of `TokenUsage.input_tokens + TokenUsage.output_tokens` across all spans
- `total_cost` = sum of `CostBreakdown.total_cost` across all spans
- `duration` = root span's duration in seconds
- `status` = root span's `status` field; default to `"ok"` if absent

#### Tests (`test_inspect.py`)

| Test | Scenario |
|---|---|
| `test_inspect_valid_trace` | All fields rendered correctly |
| `test_inspect_missing_cost_data` | Cost displayed as `$0.0000` when absent |
| `test_inspect_missing_trace` | Raises `TraceNotFoundError` |

---

### Phase 2.3 — Span Tree Visualization (`tree.py`)

#### Behavior
- Use `span_id` and `parent_span_id` to build a tree
- Print using box-drawing characters (`├──`, `└──`, `│`)
- Root node is printed without prefix
- Depth is unlimited

#### Output Format
```
agent_run research_agent
 ├── step search
 │    └── span chat:gpt-4o
 └── step summarize
      └── span chat:gpt-4o
```

#### Implementation Notes
- Build an adjacency map: `{parent_id: [child_span, ...]}`
- Sort siblings by `start_time_unix_nano` for deterministic output
- Use a recursive render function with an `is_last` flag to select `├──` vs `└──`
- Span label format: `{span_kind} {span_name}`

#### Tests (`test_tree.py`)

| Test | Scenario |
|---|---|
| `test_tree_renders_hierarchy` | Output matches expected fixture string |
| `test_tree_single_span` | Single root span renders without connectors |
| `test_tree_missing_trace` | Raises `TraceNotFoundError` |
| `test_tree_orphan_spans` | Spans with an unknown `parent_span_id` are attached under root |

---

### Phase 2.4 — Execution Timeline (`timeline.py`)

#### Behavior
- Collect all span start/end events
- Compute offset from the earliest `start_time_unix_nano` in the trace
- Sort events chronologically and print

#### Output Format
```
0 ms      agent_run started
120 ms    step search started
450 ms    span completed
700 ms    step summarize started
900 ms    span completed
1100 ms   agent_run completed
```

#### Implementation Notes
- epoch_zero = `min(span.start_time_unix_nano for span in spans)`
- Each span contributes two rows: `{name} started` and `{name} completed`
- Offset = `(time_nano - epoch_zero) / 1_000_000`
- Column width for the offset is right-padded to align labels

#### Tests (`test_timeline.py`)

| Test | Scenario |
|---|---|
| `test_timeline_output_format` | Offsets and labels correct |
| `test_timeline_ordering` | Events are always in ascending time order |
| `test_timeline_missing_trace` | Raises `TraceNotFoundError` |

**Deliverable:** All four MUST functions implemented and tested.

---

## Phase 3 — Optional Analysis Functions (SHOULD)

**Goal:** Implement the three SHOULD functions: `show_decisions`, `show_tools`, `cost_summary`.

---

### Phase 3.1 — Decision Point Analysis (`decisions.py`)

#### Behavior
- Filter events where `event_type == "decision_point"` and `trace_id` matches
- For each decision, print: decision name, available options, and the chosen option

#### Output Format
```
Decision: tool_selection
Options: search_api, knowledge_base
Chosen: search_api
```

#### Implementation Notes
- Uses `DecisionPoint` payload from the AgentOBS schema
- If no decision events exist for a trace, print: `No decision points recorded.`

#### Tests (`test_decisions.py`)

| Test | Scenario |
|---|---|
| `test_show_decisions_output` | Renders decisions from fixture |
| `test_show_decisions_empty` | Prints fallback message when none found |
| `test_show_decisions_missing_trace` | Raises `TraceNotFoundError` |

---

### Phase 3.2 — Tool Call Inspection (`tools.py`)

#### Behavior
- Filter events where `event_type == "tool_call"` and `trace_id` matches
- Print each call as `tool_name(key="value", ...)`

#### Output Format
```
Tool Calls
----------
search_api(query="LLM observability")
web_fetch(url="example.com")
```

#### Implementation Notes
- Arguments sourced from `ToolCallPayload.arguments` (dict)
- Arguments formatted as `key="value"` pairs joined by commas
- If no tool calls, print: `No tool calls recorded.`

#### Tests (`test_tools.py`)

| Test | Scenario |
|---|---|
| `test_show_tools_output` | Renders tool calls correctly |
| `test_show_tools_empty` | Prints fallback message |
| `test_show_tools_missing_trace` | Raises `TraceNotFoundError` |

---

### Phase 3.3 — Cost Summary (`cost.py`)

#### Behavior
- Aggregate `TokenUsage` and `CostBreakdown` across all spans in the trace
- Print totals

#### Output Format
```
Cost Summary
------------
Input tokens: 640
Output tokens: 172
Total cost: $0.0032
```

#### Implementation Notes
- Sum `input_tokens` and `output_tokens` from each span's `TokenUsage`
- Sum `total_cost` from each span's `CostBreakdown`
- Format cost with 4 decimal places: `${cost:.4f}`
- If no cost data present, print each field as `0` / `$0.0000`

#### Tests (`test_cost.py`)

| Test | Scenario |
|---|---|
| `test_cost_summary_output` | Tokens and cost aggregated correctly |
| `test_cost_summary_no_data` | Displays zeros gracefully |
| `test_cost_summary_missing_trace` | Raises `TraceNotFoundError` |

**Deliverable:** All three SHOULD functions implemented and tested.

---

## Phase 4 — CLI Tool (SHOULD)

**Goal:** Implement the `agentobs-debug` command-line interface.

### Architecture

Use Python's `argparse` module. The CLI is the only code permitted to call `sys.exit()`. All other modules must raise typed exceptions.

### Entry Point

```
agentobs-debug <command> <events_file> --trace <trace_id> [options]
```

### CLI Commands

| Command | Function Called | Description |
|---|---|---|
| `replay` | `replay()` | Replay an agent run step-by-step |
| `inspect` | `inspect_trace()` | Print trace summary |
| `tree` | `print_trace_tree()` | Print span hierarchy |
| `timeline` | `timeline()` | Print execution timeline |
| `tools` | `show_tools()` | List tool calls |
| `decisions` | `show_decisions()` | List decision points |
| `cost` | `cost_summary()` | Print cost summary |

### Example Invocations

```bash
agentobs-debug replay events.jsonl --trace 4bf92f3577b34da6
agentobs-debug inspect events.jsonl --trace 4bf92f3577b34da6
agentobs-debug tree events.jsonl --trace 4bf92f3577b34da6
agentobs-debug timeline events.jsonl --trace 4bf92f3577b34da6
agentobs-debug tools events.jsonl --trace 4bf92f3577b34da6
agentobs-debug decisions events.jsonl --trace 4bf92f3577b34da6
agentobs-debug cost events.jsonl --trace 4bf92f3577b34da6
```

### Error Handling in CLI

All `AgentOBSDebugError` subclasses must be caught at the CLI boundary:

```python
except TraceNotFoundError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    sys.exit(1)
except CorruptEventError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    sys.exit(1)
except AgentOBSDebugError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    sys.exit(1)
```

The CLI MUST NOT print Python tracebacks to end users.

### `pyproject.toml` Entry Point Registration

```toml
[project.scripts]
agentobs-debug = "agentobs_debug.cli:main"
```

### Tests (`test_cli.py`)

| Test | Scenario |
|---|---|
| `test_cli_replay` | `replay` command produces expected output |
| `test_cli_inspect` | `inspect` command produces expected output |
| `test_cli_tree` | `tree` command produces expected output |
| `test_cli_timeline` | `timeline` command produces expected output |
| `test_cli_tools` | `tools` command produces expected output |
| `test_cli_decisions` | `decisions` command produces expected output |
| `test_cli_cost` | `cost` command produces expected output |
| `test_cli_missing_trace` | Exits with code 1, prints error to stderr |
| `test_cli_missing_file` | Exits with code 1, prints error to stderr |
| `test_cli_no_traceback_on_error` | No Python traceback in stderr output |

**Deliverable:** `agentobs-debug` CLI installed and all commands functional.

---

## Phase 5 — Error Handling & Robustness (MUST)

**Goal:** Harden all functions against malformed or incomplete event data.

### Tasks

#### 5.1 Missing Trace Handling

- All functions must call `_filter_by_trace` before proceeding
- `TraceNotFoundError` must be raised (not silently ignored) by all MUST functions
- SHOULD functions may print a friendly message instead of raising

#### 5.2 Corrupt Event Handling

- Wrap SDK calls in `try/except` blocks where the SDK may raise on bad data
- Re-raise as `CorruptEventError` with context
- Log the offending event index or raw line where possible

#### 5.3 Invalid Span Hierarchy Handling

- If `parent_span_id` references a non-existent span, attach the orphan span to the root
- Log a warning (not an error) to `stderr`: `Warning: orphan span {span_id} — attached to root`
- Never raise for hierarchy issues; degrade gracefully

#### 5.4 Missing Payload Fields

- Any field access on optional span payload fields (e.g., `TokenUsage`, `CostBreakdown`, `DecisionPoint`) must use `.get()` or `Optional` typing with a safe default
- Never raise `AttributeError` or `KeyError` from rendering functions

#### 5.5 Robustness Tests

Add edge-case tests to each existing test file:

| Scenario | Expected Behavior |
|---|---|
| Empty JSONL file | `CorruptEventError` or `TraceNotFoundError` |
| JSONL with only unrelated traces | `TraceNotFoundError` |
| Spans missing `start_time_unix_nano` | Timeline skips or uses `0` offset |
| Spans with no children | Tree renders root node only |
| Spans with identical timestamps | Timeline is stable-sorted |

**Deliverable:** All functions handle bad input without crashing the CLI.

---

## Phase 6 — Performance Validation

**Goal:** Verify the module meets the performance requirement of 10,000 events / 1,000 spans per trace without significant slowdown.

### Tasks

#### 6.1 Generate Synthetic Large Fixture

Write a test utility `tests/generate_large_fixture.py` that produces:
- 10,000 events across multiple traces
- One trace containing 1,000 spans with realistic payloads

Store output as `tests/fixtures/large_events.jsonl`.

#### 6.2 Performance Benchmarks

Add a benchmark test file `tests/test_performance.py` using `pytest-benchmark` or simple `time.perf_counter()` assertions:

| Benchmark | Threshold |
|---|---|
| `load_events()` on 10k events | < 2 seconds |
| `replay()` on 1000-span trace | < 1 second |
| `print_trace_tree()` on 1000-span trace | < 1 second |
| `timeline()` on 1000-span trace | < 1 second |

#### 6.3 Optimization Targets (if thresholds missed)

- Span hierarchy: build adjacency map in O(n) using a dict keyed by `parent_span_id`
- Timeline: sort once using `heapq.merge` or `sorted()` rather than re-sorting per render
- Token aggregation: single-pass accumulation over the event list

**Deliverable:** All benchmarks pass; no O(n²) algorithms in critical paths.

---

## Phase 7 — Documentation & Release Preparation

**Goal:** Prepare the package for public release as `pip install agentobs-debug`.

### Tasks

#### 7.1 README.md

Cover:
- Installation: `pip install agentobs-debug`
- Quickstart (programmatic API)
- Quickstart (CLI)
- All 8 public functions with signatures and example output
- Error handling notes
- Dependency on `agentobs >= 0.1`

#### 7.2 API Reference (Docstrings)

Add docstrings to all public functions covering:
- Parameters
- Return type (`None` for all rendering functions; `EventStream` for `load_events`)
- Exceptions raised
- Example usage

#### 7.3 CHANGELOG.md

Create initial entry:
```
## 0.1.0 — Initial Release
- load_events, replay, inspect_trace, print_trace_tree, timeline (MUST)
- show_tools, show_decisions, cost_summary (SHOULD)
- CLI: agentobs-debug with 7 subcommands
```

#### 7.4 Final Quality Gates

Before tagging `v0.1.0`:

| Gate | Requirement |
|---|---|
| Test coverage | >= 90% line coverage |
| Type checking | `mypy` passes with no errors |
| Linting | `ruff` passes with no errors |
| All MUST functions | Implemented and tested |
| CLI | All 7 commands functional |
| Error handling | No unhandled exceptions in CLI |
| Performance | Benchmarks pass |

**Deliverable:** Package ready for `pip install agentobs-debug`.

---

## Phase 8 — Filtering & Output Formats

**Goal:** Make every analysis function useful in scripts and pipelines by adding per-call filtering and machine-readable output formats.

### 8.1 Internal filter utilities (`filter.py`)

Create `agentobs_debug/filter.py` with three pure helper functions (not exported in `__init__.py`):

- `filter_by_step_name(events, step_name)` — keep only `agent.step.completed` events whose `step_name` matches (case-insensitive exact match).
- `filter_timeline_rows(rows, epoch_ns, from_ms, to_ms)` — keep `(time_ns, label)` rows within a millisecond window.
- `filter_spans_by_event_type(spans, event_type)` — keep spans whose `event_type` starts with the given prefix.

### 8.2 Filter parameters

Add optional keyword-only parameters to existing functions:

| Function | New parameter | Behaviour |
|---|---|---|
| `replay()` | `step_name: str \| None = None` | Show only the named step |
| `timeline()` | `from_ms: float \| None`, `to_ms: float \| None`, `event_type: str \| None` | Time-window and type filter |
| `show_tools()` | `tool_name: str \| None = None` | Filter to a single tool |
| `show_decisions()` | `decision_name: str \| None = None` | Filter to a single decision |

### 8.3 `output_format` parameter

Add `output_format: str = "text"` to `replay`, `inspect_trace`, `timeline`, `show_tools`, `show_decisions`, `cost_summary`.

Supported values: `"text"` (default, current behaviour), `"json"`, `"csv"`.

#### JSON schema per function

| Function | JSON shape |
|---|---|
| `inspect_trace` | `{"trace_id","spans","tokens","cost_usd","duration_s","status"}` |
| `replay` | `{"agent_name","trace_id","steps":[{"step_index","step_name","model","tokens","duration_ms"}]}` |
| `timeline` | `[{"offset_ms","label"}]` |
| `show_tools` | `[{"tool_name","arguments"}]` |
| `show_decisions` | `[{"decision_name","options","chosen"}]` |
| `cost_summary` | `{"input_tokens","output_tokens","total_tokens","total_cost_usd"}` |

#### CSV schema per function

Each function outputs a header row followed by one row per record.

### 8.4 CLI flags

Add to each existing subcommand:

- `--format {text,json,csv}` (default: `text`)
- `--step STEP_NAME` on `replay`
- `--event-type EVENT_TYPE` on `timeline`
- `--from-ms FLOAT` and `--to-ms FLOAT` on `timeline`
- `--tool-name TOOL_NAME` on `tools`
- `--decision-name DECISION_NAME` on `decisions`

**Deliverable:** All existing tests still pass; new `output_format` and filter params covered by updated tests.

---

## Phase 9 — Batch Report, Trace Diff & Per-Step Attribution

**Goal:** Add three new high-value analysis commands for multi-trace workflows.

### 9.1 Batch report (`report.py`)

New module `agentobs_debug/report.py`, new public function:

```python
def batch_report(
    path: str,
    trace_ids: list[str] | None = None,
    output_format: str = "text",
) -> None:
    """Run inspect_trace() for every trace (or the given subset) in a JSONL file."""
```

- When `trace_ids` is `None`, report on every distinct `trace_id` in the file.
- `text` format: each trace's `inspect_trace` output separated by a `---` divider.
- `json` format: a JSON list of inspect dicts.
- `csv` format: one row per trace.

CLI command: `agentobs-debug report EVENTS_FILE [--trace T1 --trace T2] [--format text|json|csv]`

### 9.2 Trace diff (`diff.py`)

New module `agentobs_debug/diff.py`, new public function:

```python
def diff_traces(
    trace_id_a: str,
    trace_id_b: str,
    stream: EventStream | None = None,
    output_format: str = "text",
) -> None:
    """Compare two traces and print a diff of spans, tokens, cost, and duration."""
```

Diff includes:
- Summary: duration delta, token delta, cost delta, span count delta, status change.
- Per-step diff: steps matched by `step_name`; shows added/removed/changed steps with `→` notation.

CLI command: `agentobs-debug diff EVENTS_FILE --trace-a T1 --trace-b T2 [--format text|json]`

### 9.3 Per-step attribution (`attribution.py`)

New module `agentobs_debug/attribution.py`, new public function:

```python
def cost_attribution(
    trace_id: str,
    stream: EventStream | None = None,
    output_format: str = "text",
) -> None:
    """Print per-step cost and latency breakdown with percentiles."""
```

Output includes:
- Table: step name, model, input tokens, output tokens, cost USD, duration ms, % of total duration.
- Latency percentiles across steps: p50, p90, p99.

CLI command: `agentobs-debug attribution EVENTS_FILE --trace T1 [--format text|json|csv]`

### 9.4 Tests

- `tests/test_report.py` — batch_report text/json/csv + unknown trace filtering.
- `tests/test_diff.py` — diff identical traces, diff traces with added/removed steps, JSON output.
- `tests/test_attribution.py` — per-step table correctness, percentile calculation, JSON/CSV output.

**Deliverable:** Three new commands functional in CLI and Python API; all tests pass; coverage ≥ 90%.

---

## Phase Summary Table

| Phase | Name | Priority | Functions / Artifacts |
|---|---|---|---|
| 0 | Project Scaffolding | Blocker | Repo layout, `pyproject.toml`, error types, fixtures, CI |
| 1 | Event Loading | MUST | `load_events()` |
| 2 | Core Analysis | MUST | `replay()`, `inspect_trace()`, `print_trace_tree()`, `timeline()` |
| 3 | Optional Analysis | SHOULD | `show_decisions()`, `show_tools()`, `cost_summary()` |
| 4 | CLI Tool | SHOULD | `agentobs-debug` with 7 subcommands |
| 5 | Error Hardening | MUST | Robustness across all functions and CLI |
| 6 | Performance | SHOULD | 10k event / 1k span benchmarks |
| 7 | Docs & Release | SHOULD | README, docstrings, CHANGELOG, final QA gates |
| 8 | Filtering & Output Formats | SHOULD | `filter.py`, `--format`, `--step`, `--event-type`, time-range flags |
| 9 | Batch Report / Diff / Attribution | SHOULD | `report.py`, `diff.py`, `attribution.py`, 3 new CLI commands |

---

## Constraints Summary

| Constraint | Source |
|---|---|
| MUST NOT generate AgentOBS events | §1 |
| MUST use `EventStream.from_file()` for JSONL loading | §6 |
| MUST NOT reimplement event parsing or trace hierarchy | §3 |
| MUST NOT generate ULIDs | §3 |
| MUST use `span_id` / `parent_span_id` for tree | §9 |
| MUST use `start_time_unix_nano` / `end_time_unix_nano` for timeline | §10 |
| Errors MUST NOT crash the CLI | §15 |
| SHOULD handle 10k events / 1k spans | §16 |

---

## Success Criteria (from §19)

- [ ] `replay()` works correctly end-to-end
- [ ] `print_trace_tree()` renders span hierarchy correctly
- [ ] `timeline()` renders chronological execution view
- [ ] CLI (`agentobs-debug`) is installed and all subcommands functional
