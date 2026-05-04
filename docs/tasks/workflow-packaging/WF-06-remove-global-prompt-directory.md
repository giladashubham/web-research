# WF-06 — Remove global prompt directory

## Goal

Finish the prompt asset migration by removing `webresearch/prompts/` and ensuring all prompt loading is workflow-aware.

## Rationale

After standard, quick, and deep are packaged, prompts should live either in `workflows/shared/prompts/` or inside a specific workflow package. The root-level prompt directory should no longer exist.

## Depends On

- WF-05

## Scope

Remove:

```text
webresearch/prompts/
```

Update prompt loading so callers can load:

- shared prompts from `webresearch/workflows/shared/prompts/`
- workflow-local depth extras from `webresearch/workflows/{workflow_id}/prompts/depth_extras.md`
- future workflow-local prompts from `webresearch/workflows/{workflow_id}/prompts/`

Recommended API:

```python
load_shared_prompt(name: str, workflow_id: str) -> str
load_workflow_prompt(workflow_id: str, name: str) -> str
load_depth_extras(workflow_id: str) -> str
```

Compatibility:

- Keep `webresearch.agents.prompts.load_prompt` only if needed by existing generic agent factory tests.
- Prefer updating factories to use the new shared loader explicitly.

## Out of Scope

- Implementing technical due diligence prompts.
- Changing prompt text.
- Changing output schemas.

## Acceptance Criteria

- `webresearch/prompts/` no longer exists.
- No runtime code references `webresearch.prompts` as a package resource.
- All current workflow prompts still load correctly.
- Existing prompt boundary tests pass.
- Full test suite passes.

## Suggested Verification

```sh
rg "webresearch.*prompts|joinpath\\(\"prompts\"" webresearch tests
uv run pytest tests/agents tests/workflows
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
```
