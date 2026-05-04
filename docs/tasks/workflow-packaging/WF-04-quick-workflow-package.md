# WF-04 — Package the quick workflow

## Goal

Move the `quick` workflow into a self-contained package.

## Rationale

Quick is a lean workflow variant. It should clearly declare which standard research behavior it disables: no recent lane, no reviewer, and no gap loop.

## Depends On

- WF-03

## Scope

Replace:

```text
webresearch/workflows/quick.py
```

With:

```text
webresearch/workflows/quick/
  __init__.py
  workflow.py
  README.md
  config.py
  prompts/
    depth_extras.md
```

Expected exports:

```python
from webresearch.workflows.quick import run_quick
```

`config.py` owns quick-specific settings:

- workflow ID: `quick`
- depth preset: `quick`
- enabled research lanes: official, broad
- recent lane enabled: false
- reviewer enabled: false
- gap loop enabled: false

`prompts/depth_extras.md` owns the quick depth text currently in `webresearch/prompts/depth_extras/quick.md`.

## Out of Scope

- Changing quick behavior.
- Adding reviewer or gap loop to quick.
- Moving deep workflow.

## Acceptance Criteria

- `WORKFLOWS["quick"]` still points to `run_quick`.
- Quick workflow tests pass.
- Quick still emits only planner, research, and output steps.
- Quick result metadata remains `workflow_id == "quick"`.
- CLI and TUI can still select `quick`.
- The old `webresearch/workflows/quick.py` file is removed.

## Suggested Verification

```sh
uv run pytest tests/workflows/test_quick.py tests/cli tests/tui
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
```
