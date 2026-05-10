# Contributing

## Development Setup

```sh
uv sync
uv run pre-commit install
cp .env.example .env
```

## Running Tests

```sh
uv run pytest
```

Run with coverage:

```sh
uv run pytest --cov=webresearch
```

Run live integration tests (requires credentials):

```sh
LIVE_LLM=1 uv run pytest -m live
```

## Code Quality

```sh
uv run ruff check webresearch tests
uv run ruff format --check webresearch tests
uv run mypy webresearch
uv run pre-commit run -a
```

## Adding a Workflow

Workflows are maintained as separate pip packages. See [ARCHITECTURE.md](ARCHITECTURE.md#adding-a-new-workflow) for the structure and [`webresearch-deep`](https://github.com/kodepo-com/web-research-deep) for a complete example.

## Project Conventions

- **Imports**: Always `from __future__ import annotations` at the top.
- **Types**: Use Pydantic `BaseModel` (via `WebResearchModel` base) for data contracts.
  Use dataclasses for internal pipeline state.
- **No direct LLM imports in workflows**: Workflows import `function_tool` and `ToolContext`
  from `webresearch.pipeline`, never from `agents` directly.
- **Prompts are Jinja2**: Never build prompt strings in Python. Use `.j2` template files
  that access `{{ input }}`, `{{ outputs }}`, and `{{ item }}`.
- **Providers are stateless**: Provider classes take `WorkflowContext` as a parameter and
  register sources/evidence/pages on it. They have no LLM concepts.
- **Tests use mocks**: The `mock_execute` pattern in tests patches
  `webresearch.pipeline.runner.execute` to return predefined `ExecutionResult` objects.
  No live LLM calls in unit tests.
