# Changelog

All notable changes to `agentobs-debug` are documented here.

---

## 0.1.0 — Initial Release

### Added

#### MUST Functions
- `load_events(path)` — Load AgentOBS events from a JSONL file via `EventStream`
- `replay(trace_id, stream)` — Step-by-step replay of an agent run
- `inspect_trace(trace_id, stream)` — Aggregated trace summary (spans, tokens, cost, duration, status)
- `print_trace_tree(trace_id, stream)` — ASCII span hierarchy using box-drawing characters
- `timeline(trace_id, stream)` — Millisecond-resolution chronological execution timeline

#### SHOULD Functions
- `show_tools(trace_id, stream)` — List all tool calls with formatted arguments
- `show_decisions(trace_id, stream)` — List all decision points (name, options, chosen)
- `cost_summary(trace_id, stream)` — Aggregated token usage and total cost

#### CLI (`agentobs-debug`)
- 7 subcommands: `replay`, `inspect`, `tree`, `timeline`, `tools`, `decisions`, `cost`
- Catches all `AgentOBSDebugError` subclasses → stderr message + exit code 1
- Never exposes Python tracebacks to end users

#### Error Types (`agentobs_debug.errors`)
- `AgentOBSDebugError` — base exception
- `TraceNotFoundError` — trace ID not present in stream
- `CorruptEventError` — JSONL file missing or malformed
- `InvalidSpanHierarchyError` — reserved for future hierarchy validation

#### Robustness
- Orphan spans (unknown `parent_span_id`) silently attached to root with a stderr warning
- All payload field access uses `.get()` with safe defaults — no `KeyError` or `AttributeError`
- Spans missing timing fields are skipped in timeline without crashing
