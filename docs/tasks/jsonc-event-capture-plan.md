# JSONC Event Capture Plan

## Goal

Add an automatic run log that captures every observable workflow event into a separate
`.jsonc` file keyed by `run_id`, without mixing it into the normal result output file.

The log should make debugging and diligence review easier by showing:

- workflow and step lifecycle events
- agent/model calls (distinct from pipeline steps)
- tool calls with arguments
- tool responses or summarized outputs
- output text deltas when available
- warnings and errors
- timestamps, run id, workflow id, and step names

The log cannot capture private model chain-of-thought. It can capture observable agent
messages, model output items, tool requests, tool arguments, tool results, and SDK events.

## Implementation Principle

Implement this as if event capture was designed into the system from the start.

Do not add backwards-compatibility shims, transitional wrappers, duplicate legacy event
types, or alternate old/new writer paths. If an existing event model or stream translation
is too thin, replace it cleanly and update all callers and tests in the same change.

The final code should have one event vocabulary, one stream translation path, and one
JSONC writer path.

The default log location is project-local:

```text
.web-research/logs/run_<run_id>.jsonc
```

The logging system should create `.web-research/` and `.web-research/logs/` when they do
not exist. This directory is runtime state, not source code.

## Target User Experience

CLI example:

```sh
uv run webresearch run \
  "Evaluate Wazuh for technical diligence. Start with https://wazuh.com/. Find competitors too." \
  technical_due_diligence \
  --format json \
  --out diligence.json
```

Expected files:

```text
diligence.json
.web-research/logs/run_<run_id>.jsonc
```

Optional explicit log path:

```sh
uv run webresearch run "query" standard --events-out logs/my-run.jsonc
```

## JSONC File Shape

Use one JSONC document per run:

```jsonc
// Web Research event log
// This file contains observable events only, not private model reasoning.
{
  "run_id": "run_abc123",
  "workflow_id": "technical_due_diligence",
  "query": "Evaluate Wazuh...",
  "started_at": "2026-05-05T...",
  "events": [
    {
      "kind": "workflow_started",
      "timestamp": 123.45,
      "run_id": "run_abc123",
      "workflow_id": "technical_due_diligence"
    },
    {
      "kind": "step_started",
      "timestamp": 123.50,
      "run_id": "run_abc123",
      "step": "evidence_researcher"
    },
    {
      "kind": "agent_started",
      "timestamp": 124.00,
      "run_id": "run_abc123",
      "step": "evidence_researcher",
      "agent_name": "Technical Diligence Evidence Researcher"
    },
    {
      "kind": "tool_call",
      "timestamp": 124.12,
      "run_id": "run_abc123",
      "step": "evidence_researcher",
      "tool_name": "search_web_tool",
      "call_id": "call_1",
      "arguments": {
        "query": "Wazuh competitors",
        "limit": 10
      }
    },
    {
      "kind": "tool_result",
      "timestamp": 125.02,
      "run_id": "run_abc123",
      "step": "evidence_researcher",
      "tool_name": "search_web_tool",
      "call_id": "call_1",
      "result": {
        "provider_id": "tavily",
        "result_count": 10
      }
    },
    {
      "kind": "agent_completed",
      "timestamp": 126.00,
      "run_id": "run_abc123",
      "step": "evidence_researcher"
    },
    {
      "kind": "step_completed",
      "timestamp": 126.10,
      "run_id": "run_abc123",
      "step": "evidence_researcher"
    }
  ],
  "completed_at": "2026-05-05T..."
}
```

Keep final workflow output in the normal `--out` file. The event log may include output
text deltas, but should not duplicate the full final result object unless explicitly
enabled later.

## Implementation Tasks (Sequenced)

### EV-01 - Event Model Expansion
Update `webresearch/events/types.py` with richer observable event types.
- Distinguish between **Pipeline Steps** (structural) and **Agent Calls** (model interactions).
- New types: `AgentStarted`, `AgentCompleted`, `AgentFailed`, `ToolCall`, `ToolResult`, `ToolFailed`.
- Replace existing thin `ToolStarted`/`ToolCompleted` shapes.
- Update `ProgressRenderer` in `webresearch/cli/progress.py` to handle new events (e.g., map `ToolCall` to the dimmed dot UI).

### EV-02 - Run ID Synchronization
Ensure the `run_id` is consistent across the entire system.
- Update `webresearch/events/step.py` to provide a `current_run_id()` that is reliable.
- Modify `Pipeline.run` in `webresearch/pipeline/runner.py` to check for an existing `run_id` in the `event_context` before generating a new one. This ensures the final result metadata matches the event log.

### EV-03 - SDK Event Translation & Relocation
Move and extend the SDK translation logic.
- Move `_translate_sdk_event` from `webresearch/pipeline/runtime.py` to `webresearch/events/stream.py` (or a dedicated translation module).
- Extend it to capture: agent lifecycle, tool arguments, tool outputs, and tool errors.
- Ensure only one event is emitted per SDK event (no duplicates).

### EV-04 - JSONC Run Log Writer
Add `webresearch/events/jsonc_writer.py`.
- Responsibilities:
  - create `.web-research/logs/` automatically.
  - write JSONC header comments.
  - write events incrementally (stream/flush).
  - handle cancellation/failures gracefully to ensure a valid JSONC structure.

### EV-05 - CLI Integration & Multiplexing
Update `webresearch/cli/run_cmd.py`.
- Add `--events-out PATH` option.
- Default to `.web-research/logs/run_<run_id>.jsonc`.
- Update the `async for event in stream_workflow(...)` loop to send events to both the `ProgressRenderer` and the `JSONCWriter`.

### EV-06 - Redaction and Size Limits
Add safeguards to the serialization path.
- Redact secrets (`api_key`, `token`, etc.).
- Cap large string fields and long lists.
- Apply these rules inside the shared serialization logic.

### EV-07 - Tests
Add focused tests:
- `tests/events/test_jsonc_writer.py`: File creation and valid JSONC structure.
- `tests/cli/test_event_log.py`: CLI flag behavior and default path creation.
- `tests/events/test_stream_workflow.py`: End-to-end event sequence verification.

### EV-08 - Documentation
Update README with usage instructions for `--events-out` and information on what is captured in the logs.

## Acceptance Criteria

- `uv run webresearch run "query" standard` writes
  `.web-research/logs/run_<run_id>.jsonc`.
- `uv run webresearch run "query" standard --events-out logs` writes a `.jsonc` event log
  under the explicit directory.
- The log includes `run_id`, workflow id, step events, agent events, tool calls, arguments,
  tool results, warnings, errors, and timestamps.
- The `run_id` in the final result metadata matches the `run_id` in the event log.
- The normal `--out` result file is still separate.
- No hidden model chain-of-thought is requested or logged.
- JSONC output is valid after successful and failed workflow runs.
- No compatibility shims, deprecated aliases, duplicate legacy event classes, or temporary
  writer paths remain.
- Runtime code and tests use the final event names and writer APIs directly.
- Tests pass:

```sh
uv run pytest tests/events tests/cli
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
uv run pre-commit run -a
```

