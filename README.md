# Web Research

Web Research is a Python CLI and TUI for running OpenAI Agents SDK research workflows.
It can search the web, fetch and extract pages, rank sources, review coverage gaps, and
return sourced answers as JSON or Markdown.

## Features

- Three workflows:
  - `quick`: planner, official-source research, broad research, final answer.
  - `standard`: planner, parallel research, reviewer, one gap pass, final answer.
  - `deep`: standard workflow shape with deeper source budget and two gap passes.
- Tavily search when `TAVILY_API_KEY` is configured; mock search provider otherwise.
- Source registry with stable `src_*` IDs and fetched-page status.
- Evidence extraction with stable `ev_*` IDs.
- Event streaming for workflow progress, tool calls, output deltas, completion, and failure.
- Typer CLI and Textual TUI.
- Optional structured output validation for JSON results.

## Setup

```sh
uv sync
uv run pre-commit install
cp .env.example .env
```

Edit `.env` with the credentials you want to use:

```sh
OPENAI_API_KEY=...
TAVILY_API_KEY=...
OPENAI_MODEL=
LIVE_LLM=0
```

Environment variables are loaded from `.env` automatically. Values already set in your
shell take precedence over `.env`.

## CLI

List workflows:

```sh
uv run webresearch list
uv run webresearch list --format json
```

Run a query:

```sh
uv run webresearch run "What is the current Node.js LTS version?"
```

Choose a workflow and depth:

```sh
uv run webresearch run "Compare Python 3.13 migration risks" deep --depth deep
uv run webresearch run "Summarize the latest Django release" quick --depth quick
```

Write Markdown or JSON output:

```sh
uv run webresearch run "What changed in Python 3.13?" --format md --out answer.md
uv run webresearch run "What changed in Python 3.13?" --format json --out answer.json
```

Useful options:

```sh
--instructions "Prefer official release notes"
--max-sources 8
--quiet
```

## TUI

Start the terminal UI:

```sh
uv run webresearch tui
```

The TUI lets you choose a workflow, enter a query, watch progress, inspect sources and
artifacts, export results, cancel an active run, and view runtime settings.

## Runtime Environment

Live OpenAI runs require `OPENAI_API_KEY`.

Tavily-backed search requires `TAVILY_API_KEY`. If it is not set, the app uses the mock
search provider, which is suitable for tests and local smoke runs.

The gated live integration test requires:

```sh
LIVE_LLM=1
OPENAI_API_KEY=...
TAVILY_API_KEY=...
```

Run it with:

```sh
uv run pytest -m live
```

The OpenAI Agents SDK tracing dashboard is enabled by the SDK when tracing is configured
for live runs. Unit tests use mocks and do not require tracing credentials.

## Python API

```python
import asyncio

from webresearch import run_workflow
from webresearch.types import WorkflowInput
from webresearch.workflows.standard import run_standard


async def main() -> None:
    result = await run_workflow(
        run_standard,
        WorkflowInput(query="What is the current Node.js LTS version?"),
    )
    print(result.answer_markdown)


asyncio.run(main())
```

For streaming progress:

```python
from webresearch import stream_workflow

async for event in stream_workflow(run_standard, WorkflowInput(query="Research query")):
    print(event.kind)
```

## Development

```sh
uv run pytest
uv run ruff check
uv run ruff format
uv run mypy webresearch
uv run pre-commit run -a
```

Live service tests are skipped unless the required environment variables are set.
