# P4-02 — `WorkflowState` + result aggregator

**Phase:** 4 — Standard workflow
**Depends on:** P1-02, P1-04, P3-02

## Goal
Bundle the per-run state and build the final `WorkflowResult` from it.

## Scope
- `WorkflowState` dataclass:
  - `input: WorkflowInput`, `depth: Depth`, `run_id: str`, `started_at: datetime`.
  - `plan: PlanOutput | None`, `research: list[ResearcherOutput]`, `review: ReviewOutput | None`, `gaps: list[GapResearchOutput]`, `final: FinalAnswer | None`.
  - Helpers: `research_prompt()`, `review_prompt()`, `gap_prompt()`, `output_prompt()` — string formatters that produce the user message for the corresponding agent (replaces our old "step input composer").
  - `add_warning(msg)`, `add_artifact(artifact)`.
- `build_result(state, ctx) -> WorkflowResult`:
  - Pulls sources from `ctx.sources.list()`.
  - Pulls evidence from `ctx.artifacts` filtered to evidence type.
  - Pulls findings from `state.final.findings`.
  - Populates metadata (`run_id`, `workflow_id`, timestamps).
  - Surfaces all warnings collected on `ctx`.
- Structured-output handling: if `input.output_schema` is set, copy `state.final.structured_data` into `result.structured_data` after validating against the schema (use `jsonschema` package).

## Out of scope
- Schema repair — non-goal.

## Files
- `webresearch/workflows/state.py`
- `webresearch/workflows/result.py`
- `tests/workflows/test_state.py`
- `tests/workflows/test_result.py`

## Acceptance
- [ ] Prompt helpers produce stable, deterministic strings (golden-file friendly).
- [ ] `build_result` populates every field of `WorkflowResult`.
- [ ] Structured-output validation: valid → `structured_data`, invalid → `raw_structured_data` + warning.
- [ ] Missing `outputSchema` leaves `structured_data` undefined.
