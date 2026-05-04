# WF-08 — Add technical due-diligence workflow skeleton

## Goal

Add the self-contained package skeleton for the future `technical_due_diligence` workflow without implementing the full workflow logic yet.

## Rationale

After the current workflows use self-contained packages, the technical due-diligence workflow should follow the same architecture from the start.

## Depends On

- WF-07

## Scope

Create:

```text
webresearch/workflows/technical_due_diligence/
  __init__.py
  README.md
  workflow.py
  models.py
  schema.json
  prompts/
    intake_planner.md
    claim_extractor.md
    evidence_researcher.md
    competitor_mapper.md
    technical_substance_reviewer.md
    gap_researcher.md
    final_memo.md
  examples/
    input.example.json
    output.example.json
```

Add a placeholder `run_technical_due_diligence` only if it can fail clearly with a `NotImplementedError` or return a minimal mock-safe result. Do not register it as a runnable workflow until the implementation task exists.

Add Pydantic models for the planned structured output:

- `DiligenceTarget`
- `ExecutiveJudgment`
- `ClaimAssessment`
- `TechnicalSubstanceAssessment`
- `CompetitorAssessment`
- `ReplicabilityAssessment`
- `CodeReviewFollowUp`
- `TechnicalDueDiligenceReport`

Add `schema.json` matching the planned report model.

## Out of Scope

- Registering the workflow as production-ready.
- Implementing web research orchestration.
- Writing final prompts beyond skeleton versions.
- Running live diligence research.

## Acceptance Criteria

- Package imports cleanly.
- `schema.json` is valid JSON Schema.
- Pydantic report model can validate the example output.
- Example input/output files are valid JSON.
- The workflow is not exposed in `WORKFLOWS` unless it is actually runnable.
- Full test suite passes.

## Suggested Verification

```sh
uv run pytest tests/workflows
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
```
