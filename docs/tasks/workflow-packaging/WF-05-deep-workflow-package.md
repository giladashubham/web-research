# WF-05 — Package the deep workflow

## Goal

Move the `deep` workflow into a self-contained package.

## Rationale

Deep is a standard-shaped workflow with higher research budget and a two-round gap cap. Packaging it makes those differences explicit and keeps deep-specific prompt extras with the workflow.

## Depends On

- WF-04

## Scope

Replace:

```text
webresearch/workflows/deep.py
```

With:

```text
webresearch/workflows/deep/
  __init__.py
  workflow.py
  README.md
  config.py
  prompts/
    depth_extras.md
```

Expected exports:

```python
from webresearch.workflows.deep import run_deep
```

`config.py` owns deep-specific settings:

- workflow ID: `deep`
- depth preset: `deep`
- max gap rounds: 2
- max sources: 20
- enabled research lanes: official, recent, broad
- reviewer enabled: true
- gap loop enabled: true

`prompts/depth_extras.md` owns the deep depth text currently in `webresearch/prompts/depth_extras/deep.md`.

## Out of Scope

- Changing the two-round gap-loop behavior.
- Adding technical due diligence.

## Acceptance Criteria

- `WORKFLOWS["deep"]` still points to `run_deep`.
- Deep workflow tests pass.
- Deep still hits max gap rounds of 2 when reviewer keeps reporting critical gaps.
- Deep result metadata remains `workflow_id == "deep"`.
- CLI and TUI can still select `deep`.
- The old `webresearch/workflows/deep.py` file is removed.

## Suggested Verification

```sh
uv run pytest tests/workflows/test_deep.py tests/cli tests/tui
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
```
