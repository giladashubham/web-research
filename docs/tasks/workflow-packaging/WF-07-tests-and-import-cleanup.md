# WF-07 — Reorganize workflow tests and imports

## Goal

Align test structure and imports with the new workflow package layout.

## Rationale

Once workflows are packages, tests should mirror that organization. This makes workflow-specific behavior easier to find and prevents generic workflow tests from becoming a dumping ground.

## Depends On

- WF-06

## Scope

Move tests:

```text
tests/workflows/test_standard.py
tests/workflows/test_quick.py
tests/workflows/test_deep.py
```

To:

```text
tests/workflows/standard/test_workflow.py
tests/workflows/quick/test_workflow.py
tests/workflows/deep/test_workflow.py
```

Keep shared workflow tests in:

```text
tests/workflows/shared/
  test_result.py
  test_state.py
```

or leave shared tests in `tests/workflows/` if that is less disruptive. The important part is that workflow-specific tests live next to the workflow name.

Update imports to package paths:

```python
from webresearch.workflows.standard import run_standard
from webresearch.workflows.quick import run_quick
from webresearch.workflows.deep import run_deep
```

Avoid importing implementation modules directly. If tests need to patch orchestration internals, patch through the package-level module that owns the workflow implementation after the migration.

## Out of Scope

- Changing workflow behavior.
- Adding new technical due-diligence tests.

## Acceptance Criteria

- Test names and paths reflect workflow package names.
- Tests still patch workflow internals cleanly where needed.
- `pytest tests/workflows` passes.
- Full test suite passes.
- No stale imports reference deleted module files.
- No tests import old flat workflow modules or deleted compatibility modules.

## Suggested Verification

```sh
rg "workflows\\.(standard|quick|deep)$|workflows/(standard|quick|deep)\\.py|workflows\\.(state|result)|agents\\.prompts" tests webresearch
uv run pytest tests/workflows
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
```
