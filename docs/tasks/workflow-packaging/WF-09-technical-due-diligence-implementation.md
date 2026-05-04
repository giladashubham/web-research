# WF-09 — Implement technical due-diligence workflow

## Goal

Implement and register the `technical_due_diligence` workflow as a runnable web-research workflow.

## Rationale

The workflow should produce a sourced public technical diligence dossier: what the company claims, what public evidence supports or weakens those claims, how competitors compare, and what later code/product review should inspect.

## Depends On

- WF-08

## Scope

Implement orchestration in:

```text
webresearch/workflows/technical_due_diligence/workflow.py
```

Recommended stages:

1. Intake planner.
2. Claim extractor.
3. Evidence researcher.
4. Competitor mapper.
5. Technical substance reviewer.
6. Gap researcher loop.
7. Final memo writer.

Register:

```python
WORKFLOWS["technical_due_diligence"] = run_technical_due_diligence
```

Add workflow entry:

```text
id: technical_due_diligence
name: Technical Due Diligence
description: Public technical substance, claims, competitors, and replicability assessment.
```

Use the workflow-local prompts and schema.

The final output should include:

- Markdown memo in `answer_markdown`.
- Structured diligence report in `structured_data`.
- Raw structured data and validation errors if schema validation fails.
- Sourced findings and source IDs where possible.
- Unresolved gaps and code-review follow-up questions.

## Out of Scope

- Private code scanning.
- Private repository analysis.
- Security audit.
- Live tuning beyond the existing gated live-test pattern.

## Acceptance Criteria

- CLI can run:

```sh
uv run webresearch run "Evaluate PRODUCT for technical diligence. URLs: ..." technical_due_diligence
```

- TUI lists the workflow.
- Mock-model workflow tests pass.
- Prompt boundary tests pass.
- Output validates against `schema.json` in happy-path tests.
- The workflow clearly labels public evidence vs inference vs unknowns.
- Full test suite passes.

## Suggested Tests

Create:

```text
tests/workflows/technical_due_diligence/
  test_models.py
  test_schema.py
  test_workflow.py
  test_prompt_boundaries.py
```

## Suggested Verification

```sh
uv run pytest tests/workflows/technical_due_diligence
uv run pytest tests/cli tests/tui
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
uv run pre-commit run -a
```
