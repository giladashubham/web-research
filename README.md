# Web Research

Python web research runner built around agent workflows.

## Setup

```sh
uv sync
uv run pre-commit install
```

## Runtime Environment

Live OpenAI runs require `OPENAI_API_KEY`.

The Agents SDK tracing dashboard is enabled by the SDK when tracing is configured for live runs;
unit tests use mocks and do not require tracing credentials.

## Development

```sh
uv run pytest
uv run pytest -m live
uv run ruff check
uv run ruff format
uv run mypy webresearch
uv run pre-commit run -a
```
