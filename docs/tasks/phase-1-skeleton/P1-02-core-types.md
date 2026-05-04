# P1-02 — Core Pydantic types

**Phase:** 1 — Skeleton & primitives
**Depends on:** P1-01

## Goal
Define the data model in one module. Pure Pydantic — no behavior.

## Scope
- `WorkflowInput` — `query`, `instructions`, `depth`, `max_sources`, `output_schema`.
- `Depth` — enum + per-preset config (`max_rounds`, `max_sources`, per-tool budgets); class method `for_preset(name)`.
- `WorkflowResult` — `answer_markdown`, `structured_data`, `summary`, `findings`, `sources`, `evidence`, `artifacts`, `warnings`, `metadata`.
- `WorkflowMetadata` — `run_id`, `workflow_id`, `started_at`, `finished_at`, `cost_usd`, `tokens`.
- `SourceRecord`, `EvidenceNote`, `ResearchFinding`.
- `Artifact` (base) + concrete `PlanArtifact`, `SourceArtifact`, `EvidenceArtifact`, `ReviewArtifact`, `AnswerArtifact`, `WarningArtifact`.
- `StructuredDataValidation`.

Add `Pydantic v2` to deps.

## Out of scope
- Agent-specific output models (`PlanOutput`, `ReviewOutput`, `FinalAnswer`) — those live with the agents in P3-02.

## Files
- `webresearch/types.py`
- `tests/test_types.py`

## Acceptance
- [ ] All types validate cleanly under `mypy --strict`.
- [ ] `Depth.for_preset("quick" | "standard" | "deep")` returns the expected presets.
- [ ] `WorkflowInput.query` is required; missing it raises `ValidationError`.
- [ ] Round-trip: `WorkflowResult.model_validate(result.model_dump())` is identical.
