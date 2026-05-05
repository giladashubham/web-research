# JSONC Event Capture Plan

## Goal

Add an automatic run log that captures every observable workflow event into a separate
`.jsonc` file keyed by `run_id`, without mixing it into the normal result output file.

The log should make debugging and diligence review easier by showing:

- workflow and step lifecycle events
- agent/model calls
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
      "kind": "tool_call",
      "timestamp": 124.12,
      "run_id": "run_abc123",
      "step": "evidence_researcher",
      "agent_name": "Technical Diligence Evidence Researcher",
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
    }
  ],
  "completed_at": "2026-05-05T..."
}
```

Keep final workflow output in the normal `--out` file. The event log may include output
text deltas, but should not duplicate the full final result object unless explicitly
enabled later.

## Implementation Tasks

### EV-01 - Event Model Expansion

Update `webresearch/events/types.py` with richer observable event types:

- `AgentStarted`
- `AgentCompleted`
- `AgentFailed`
- `ModelOutputItem`
- `ToolCall`
- `ToolResult`
- `ToolFailed`

Replace the existing thin `ToolStarted` / `ToolCompleted` shape if the richer tool events
make those names obsolete. Do not keep old aliases or re-export compatibility event
classes. Update the progress renderer and tests to the final event names directly.

Include common fields:

- `run_id`
- `timestamp`
- `workflow_id` when known
- `step`
- `agent_name`
- `call_id`
- `sequence`

Do not add a field called `thought` unless it contains public/visible model text. Hidden
chain-of-thought must not be requested, inferred, or logged.

### EV-02 - SDK Event Translation

Extend `webresearch/events/stream.py` so `_translate_sdk_event(...)` captures more of the
Agents SDK stream:

- agent lifecycle events if exposed by the SDK
- raw model response output items
- tool call names
- tool call arguments
- tool outputs
- tool errors
- output text deltas

Current code only translates basic tool started/completed events. This task should preserve
the existing progress renderer user experience while replacing the old thin translation
with the final richer translation. Do not emit both legacy and new tool events for the
same SDK event.

### EV-03 - JSONC Run Log Writer

Add a writer module, for example:

```text
webresearch/events/jsonc_writer.py
```

Responsibilities:

- create `.web-research/` and `.web-research/logs/` when needed
- default to `.web-research/logs/run_<run_id>.jsonc`
- derive `run_<run_id>.jsonc` when `--events-out` is a directory
- write JSONC header comments
- write a single JSON object with an `events` array
- append events incrementally and flush after each event
- close the JSON array/object in `finally`
- tolerate cancellation and workflow failure

Implementation detail: use comma-aware appends so the file remains valid JSONC after a
normal run. If a process is killed mid-run, a partial file is acceptable.

This should be the only event-log writer. Do not add a temporary NDJSON writer, debug
writer, or compatibility output mode unless a future task explicitly requires it.

### EV-04 - CLI Option

Add a CLI option in `webresearch/cli/run_cmd.py`:

```text
--events-out PATH
```

Behavior:

- omitted: write `.web-research/logs/run_<run_id>.jsonc`
- directory path: write `PATH/run_<run_id>.jsonc`
- file path ending in `.jsonc`: write exactly that file
- fail with exit code `3` on IO errors, matching existing output write behavior

The option should work with all workflows, including `technical_due_diligence`.

Add the option directly to the main `run` command surface as an override for the default
`.web-research/logs/` location. Do not add hidden legacy flags, environment-variable-only
switches, or deprecated aliases.

### EV-05 - Stream Multiplexing

Update the run command event loop so each streamed event is sent to both:

- `ProgressRenderer`
- JSONC writer

The normal result output path should remain unchanged.

Keep stream dispatch centralized. Avoid adding per-workflow event capture hooks or
workflow-specific logging branches.

### EV-06 - Redaction and Size Limits

Add conservative safeguards before logging tool arguments/results:

- redact likely secrets by key name, such as `api_key`, `authorization`, `token`, `password`
- cap large string fields
- cap large lists of search results
- mark truncated values with metadata such as `"truncated": true`

Default behavior should be useful for debugging without dumping megabytes of fetched page
content into the event log.

Apply redaction and truncation inside the shared event serialization path so all event
logs follow the same rules.

### EV-07 - Tests

Add focused tests:

```text
tests/events/test_jsonc_writer.py
tests/cli/test_event_log.py
tests/events/test_stream_workflow.py
```

Coverage:

- writer creates a valid JSONC file for a successful run
- writer finalizes on workflow failure
- CLI without `--events-out` creates `.web-research/logs/run_<run_id>.jsonc`
- CLI `--events-out logs` creates `logs/run_<run_id>.jsonc`
- CLI `--events-out file.jsonc` writes the explicit file
- final result output still goes to `--out`
- tool call arguments and tool result summaries are present
- secrets are redacted
- large values are truncated
- no deleted or legacy event names remain in runtime code unless they are still part of
  the final vocabulary

### EV-08 - Documentation

Update README with:

- `--events-out` usage
- default `.web-research/logs/run_<run_id>.jsonc` event log path
- what is captured
- explicit note that hidden chain-of-thought is not captured

## Acceptance Criteria

- `uv run webresearch run "query" standard` writes
  `.web-research/logs/run_<run_id>.jsonc`.
- `uv run webresearch run "query" standard --events-out logs` writes a `.jsonc` event log
  under the explicit directory.
- The log includes `run_id`, workflow id, step events, agent events, tool calls, arguments,
  tool results, warnings, errors, and timestamps.
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
