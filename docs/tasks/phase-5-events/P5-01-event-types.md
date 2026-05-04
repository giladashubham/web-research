# P5-01 — `WorkflowEvent` types

**Phase:** 5 — Event stream
**Depends on:** P1-02

## Goal
Discriminated-union of workflow-level events. Pydantic-tagged `kind` field for routing.

## Scope
- Event models:
  - `WorkflowStarted`, `WorkflowCompleted`, `WorkflowFailed`.
  - `StepStarted`, `StepCompleted`, `StepSkipped`.
  - `LoopIteration`.
  - `ToolStarted`, `ToolCompleted`.
  - `ArtifactAdded`, `SourceAdded`.
  - `OutputTextDelta`.
  - `Warning`.
- Discriminated union via Pydantic's `Field(discriminator="kind")`.
- All events carry `run_id` and a high-resolution timestamp.

## Out of scope
- The async generator that emits them (P5-02).

## Files
- `webresearch/events/types.py`
- `tests/events/test_types.py`

## Acceptance
- [ ] All event variants validate cleanly.
- [ ] Discriminated parsing: a JSON dict with `kind: "step_started"` parses to `StepStarted`, not the wrong variant.
- [ ] Round-trip via `model_dump_json` / `model_validate_json` is identical for each event type.
