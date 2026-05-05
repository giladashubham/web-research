# WF-10 — Final layout cleanup

## Goal

Remove any leftover legacy workflow layout artifacts after the package migration and technical due-diligence workflow implementation.

## Rationale

The final tree should look like the project was designed with workflow packages from the start. Do not keep backwards-compatibility files, transitional wrappers, unused prompt directories, or stale tests.

## Depends On

- WF-09

## Scope

Verify and clean the final layout.

Expected final shape:

```text
webresearch/workflows/
  __init__.py
  registry.py
  shared/
    __init__.py
    state.py
    result.py
    prompt_loader.py
    prompts/
      planner.md
      official.md
      recent.md
      broad.md
      reviewer.md
      gap.md
      output.md
  standard/
    __init__.py
    workflow.py
    config.py
    README.md
    prompts/depth_extras.md
  quick/
    __init__.py
    workflow.py
    config.py
    README.md
    prompts/depth_extras.md
  deep/
    __init__.py
    workflow.py
    config.py
    README.md
    prompts/depth_extras.md
  technical_due_diligence/
    __init__.py
    workflow.py
    models.py
    schema.json
    README.md
    prompts/
    examples/
```

Remove if present:

```text
webresearch/workflows/standard.py
webresearch/workflows/quick.py
webresearch/workflows/deep.py
webresearch/workflows/state.py
webresearch/workflows/result.py
webresearch/agents/prompts.py
webresearch/prompts/
```

Clean stale references in:

- tests
- README
- docs
- imports
- registry
- type-checking imports

## Out of Scope

- New workflow behavior.
- New prompt content.
- Additional product features.

## Acceptance Criteria

- No compatibility shims remain.
- No old flat workflow modules remain.
- No global prompt directory remains.
- No imports reference deleted modules.
- `WORKFLOWS` exposes only package-based workflows.
- `README.md` documents the final workflow list and package layout accurately.
- Full test suite passes.
- Ruff, format check, mypy, and pre-commit pass.

## Suggested Verification

```sh
test ! -e webresearch/workflows/standard.py
test ! -e webresearch/workflows/quick.py
test ! -e webresearch/workflows/deep.py
test ! -e webresearch/workflows/state.py
test ! -e webresearch/workflows/result.py
test ! -e webresearch/agents/prompts.py
test ! -e webresearch/prompts
rg "webresearch\\.workflows\\.(state|result)|webresearch\\.agents\\.prompts|joinpath\\(\"prompts\"" webresearch tests docs README.md
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
uv run pre-commit run -a
```
