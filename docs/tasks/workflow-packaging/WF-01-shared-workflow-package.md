# WF-01 — Create shared workflow package

## Goal

Introduce a `webresearch.workflows.shared` package for workflow infrastructure that is reused by multiple workflow packages.

This task should not change runtime behavior.

## Rationale

The current workflow modules share `state.py`, `result.py`, global agent factories, and global prompt loading. Before moving each workflow into a self-contained package, create a clear shared layer so generic machinery does not get duplicated.

## Scope

Create:

```text
webresearch/workflows/shared/
  __init__.py
  state.py
  result.py
  prompt_loader.py
```

Move or wrap:

- `webresearch/workflows/state.py` -> `webresearch/workflows/shared/state.py`
- `webresearch/workflows/result.py` -> `webresearch/workflows/shared/result.py`
- `webresearch/agents/prompts.py` prompt-loading behavior -> `webresearch/workflows/shared/prompt_loader.py`

Keep compatibility imports for one migration step:

```text
webresearch/workflows/state.py
webresearch/workflows/result.py
webresearch/agents/prompts.py
```

These compatibility modules should re-export the new shared implementations so existing tests and imports keep passing.

## Out of Scope

- Moving workflow files into packages.
- Moving prompt markdown files.
- Changing workflow behavior.
- Adding the technical due-diligence workflow.

## Acceptance Criteria

- Existing imports keep working:
  - `from webresearch.workflows.state import WorkflowState`
  - `from webresearch.workflows.result import build_result`
  - `from webresearch.agents.prompts import load_prompt`
- New imports work:
  - `from webresearch.workflows.shared.state import WorkflowState`
  - `from webresearch.workflows.shared.result import build_result`
  - `from webresearch.workflows.shared.prompt_loader import load_prompt`
- Full test suite passes.
- Ruff, format check, mypy, and pre-commit pass.

## Suggested Verification

```sh
uv run pytest tests/workflows tests/agents
uv run ruff check
uv run ruff format --check
uv run mypy webresearch
uv run pre-commit run -a
```
