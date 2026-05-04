# Web Research

Python web research runner built around agent workflows.

## Setup

```sh
uv sync
uv run pre-commit install
```

## Development

```sh
uv run pytest
uv run pytest -m live
uv run ruff check
uv run ruff format
uv run mypy webresearch
uv run pre-commit run -a
```
