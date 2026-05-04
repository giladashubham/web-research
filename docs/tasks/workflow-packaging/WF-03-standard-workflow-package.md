# WF-03 — Package the standard workflow

## Goal

Move the `standard` workflow into a self-contained package.

## Rationale

The standard workflow is the baseline research workflow. Packaging it first proves the migration pattern before moving quick and deep variants.

## Depends On

- WF-01
- WF-02

## Scope

Replace:

```text
webresearch/workflows/standard.py
```

With:

```text
webresearch/workflows/standard/
  __init__.py
  workflow.py
  README.md
  config.py
  prompts/
    depth_extras.md
```

Expected exports:

```python
from webresearch.workflows.standard import run_standard
```

`workflow.py` owns the orchestration.

`config.py` owns standard-specific settings:

- workflow ID: `standard`
- depth preset: `standard`
- max gap rounds: current standard behavior
- enabled research lanes: official, recent, broad
- reviewer enabled: true
- gap loop enabled: true

`prompts/depth_extras.md` owns the standard depth text currently in `webresearch/prompts/depth_extras/standard.md`.

## Out of Scope

- Changing standard workflow behavior.
- Moving quick/deep workflows.
- Adding technical due diligence.

## Acceptance Criteria

- `WORKFLOWS["standard"]` still points to `run_standard`.
- Existing standard workflow tests pass without weakening assertions.
- CLI `webresearch run "query" standard` still works.
- TUI workflow listing still includes Standard.
- `result.metadata.workflow_id == "standard"` remains true.
- The old `webresearch/workflows/standard.py` file is removed.

## Suggested Verification

```sh
uv run pytest tests/workflows/test_standard.py tests/cli tests/tui
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
```
