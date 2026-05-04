# WF-02 — Move shared prompt assets

## Goal

Move generic research workflow prompts from the global `webresearch/prompts/` directory into the shared workflow package.

## Rationale

Prompts are workflow assets. Generic prompts used by `standard`, `quick`, and `deep` should live with shared workflow machinery instead of at package root.

## Depends On

- WF-01

## Scope

Move:

```text
webresearch/prompts/planner.md
webresearch/prompts/official.md
webresearch/prompts/recent.md
webresearch/prompts/broad.md
webresearch/prompts/reviewer.md
webresearch/prompts/gap.md
webresearch/prompts/output.md
```

To:

```text
webresearch/workflows/shared/prompts/
  planner.md
  official.md
  recent.md
  broad.md
  reviewer.md
  gap.md
  output.md
```

Update the shared prompt loader to load from `webresearch.workflows.shared/prompts`.

Keep old `webresearch/prompts/` only if needed during migration, but no runtime code should depend on it after this task.

## Out of Scope

- Moving depth extras.
- Duplicating prompts into each workflow.
- Changing prompt content.
- Moving workflow Python modules.

## Acceptance Criteria

- All existing agent factories still load the same prompt content.
- Tests that assert prompt content and factory instructions pass.
- No runtime code reads generic prompts from `webresearch/prompts/`.
- Full test suite passes.

## Suggested Verification

```sh
uv run pytest tests/agents/test_factories.py tests/agents/test_prompt_boundaries.py
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
```
