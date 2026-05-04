# Implementation Tasks

Granular task breakdown of [agent-workflow-runtime-implementation-plan.md](../agent-workflow-runtime-implementation-plan.md).

One file per task. Each task is a single focused PR.

## Conventions

- File name: `P{phase}-{seq}-{slug}.md`.
- Source files use Python conventions: snake_case modules, PascalCase classes.
- Tests live under top-level `tests/` mirroring the source layout.
- A task with `Depends on: none` can start immediately.

## Phases

### Phase 1 — Project skeleton & primitives
- [P1-01](phase-1-skeleton/P1-01-project-init.md) — Project init (uv, ruff, mypy, pytest)
- [P1-02](phase-1-skeleton/P1-02-core-types.md) — Core Pydantic types
- [P1-03](phase-1-skeleton/P1-03-url-normalize.md) — URL normalization
- [P1-04](phase-1-skeleton/P1-04-source-registry.md) — Source registry

### Phase 2 — Tools
- [P2-01](phase-2-tools/P2-01-search-provider-mock.md) — `SearchProvider` protocol + `MockSearchProvider`
- [P2-02](phase-2-tools/P2-02-tavily-provider.md) — `TavilySearchProvider`
- [P2-03](phase-2-tools/P2-03-search-web-tool.md) — `search_web` tool
- [P2-04](phase-2-tools/P2-04-fetch-url-tool.md) — `fetch_url` tool
- [P2-05](phase-2-tools/P2-05-extract-content-tool.md) — `extract_content` tool
- [P2-06](phase-2-tools/P2-06-rank-sources-tool.md) — `rank_sources` tool

### Phase 3 — Agents
- [P3-01](phase-3-agents/P3-01-install-agents-sdk.md) — Install `openai-agents` + smoke
- [P3-02](phase-3-agents/P3-02-output-models.md) — Pydantic output models
- [P3-03](phase-3-agents/P3-03-agent-factories.md) — Agent factories + prompt loading
- [P3-04](phase-3-agents/P3-04-mock-model.md) — Mock-model harness

### Phase 4 — Standard workflow
- [P4-01](phase-4-standard-workflow/P4-01-standard-workflow.md) — `run_standard` function
- [P4-02](phase-4-standard-workflow/P4-02-result-aggregator.md) — `WorkflowState` + result aggregator

### Phase 5 — Event stream
- [P5-01](phase-5-events/P5-01-event-types.md) — `WorkflowEvent` types
- [P5-02](phase-5-events/P5-02-stream-workflow.md) — `stream_workflow` async generator

### Phase 6 — CLI
- [P6-01](phase-6-cli/P6-01-typer-app-list.md) — Typer app + `list` command
- [P6-02](phase-6-cli/P6-02-run-command.md) — `run` command + stderr progress
- [P6-03](phase-6-cli/P6-03-output-formats.md) — JSON + Markdown output

### Phase 7 — TUI
- [P7-01](phase-7-tui/P7-01-textual-shell.md) — Textual app shell + screen routing
- [P7-02](phase-7-tui/P7-02-home-and-query.md) — Home + Query screens
- [P7-03](phase-7-tui/P7-03-run-screen.md) — Run screen (timeline + artifacts)
- [P7-04](phase-7-tui/P7-04-result-screen.md) — Result screen + export
- [P7-05](phase-7-tui/P7-05-cancel-and-settings.md) — Cancellation + Settings

### Phase 8 — Variants
- [P8-01](phase-8-variants/P8-01-quick-workflow.md) — `quick.py` workflow
- [P8-02](phase-8-variants/P8-02-deep-workflow.md) — `deep.py` workflow

### Phase 9 — Polish
- [P9-01](phase-9-polish/P9-01-live-integration-test.md) — Live LLM integration test (gated)
- [P9-02](phase-9-polish/P9-02-prompt-finalization.md) — Prompt finalization + golden tests

## Dependency map (rough)

```
P1-01 -> all
P1-02 -> P1-04, P2-*, P3-02, P4-*
P1-03 -> P1-04, P2-04
P1-04 -> P2-03, P2-04

P2-01 -> P2-02, P2-03
P2-03..P2-06 -> P3-03

P3-01 -> P3-02, P3-03, P3-04
P3-02..P3-04 -> P4-01

P4-01 -> P4-02 -> P5-02
P5-01 -> P5-02

P5-02 -> P6-*, P7-*
P6-01 -> P6-02 -> P6-03
P7-01 -> P7-02 -> P7-03 -> P7-04 -> P7-05

P4-01 -> P8-* (quick/deep are simplifications/extensions of standard)
all-of-the-above -> P9-*
```
