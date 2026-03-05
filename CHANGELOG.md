# Changelog

All notable changes to `agentobs-debug` are documented here.

---

## 1.0.0 — Stable Release

### Added

- Output format support across analysis commands: `--format text|json|csv`
- Filter flags for focused analysis:
	- `replay --step`
	- `timeline --from-ms`, `--to-ms`, `--event-type`
	- `tools --tool-name`
	- `decisions --decision-name`
- New analysis modules and commands:
	- `cost_attribution()` / `agentobs-debug attribution`
	- `batch_report()` / `agentobs-debug report`
	- `diff_traces()` / `agentobs-debug diff`
- Internal filtering utilities in `agentobs_debug/filter.py`
- Expanded automated test coverage for output formats, filtering, attribution, report, and diff workflows

### Changed

- CLI surface expanded from 7 to 10 subcommands
- Documentation updated for full CLI/API parity:
	- `README.md`
	- `docs/tutorial/index.md`
	- `docs/api-reference.md`

### Quality

- Lint/type/test gates passing (`ruff`, `mypy`, `pytest`)
- Coverage remains above project threshold (`>= 90%`)

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
