# Web Research

A Python SDK for running LLM-powered web research workflows. Built on the
[OpenAI Agents SDK](https://github.com/openai/openai-agents-python) with a clean
abstraction layer so the underlying runtime can be swapped without touching workflow code.

## Features

- **Declarative pipeline** — Workflows are defined as sequences of `AgentStep`, `Parallel`,
  `FanOut`, and `Loop` steps. The pipeline owns all execution mechanics (hooks, parallelism,
  loop control, event emission, cost tracking).
- **Entry-point workflow discovery** — Workflows are registered via Python entry points.
  Adding a new workflow requires zero changes to this package. Just install its pip package.
- **Pluggable workflows** — Workflows ship as separate pip-installable packages:
  - [`webresearch-deep`](https://github.com/kodepo-com/web-research-deep) — Planner → parallel research (official/recent/broad) → review → gap loop → answer.
  - `webresearch-tdd` (coming soon) — Technical due diligence with claim extraction, evidence research, and structured reports.
  - `webresearch-company-news` (coming soon) — Multi-channel company news monitoring.
- **Provider layer** — Raw I/O adapters for web search (Tavily/mock), HTTP fetching, HTML
  extraction (trafilatura), and URL discovery (sitemap + link parsing). No LLM concepts.
- **Runtime isolation** — Only `pipeline/runtime.py` imports from the LLM framework.
  Swapping to BAML, raw Anthropic API, etc. means rewriting that single file.
- **Jinja2 prompt templates** — Prompts are `.j2` files rendered with the full pipeline state
  (`{{ input }}`, `{{ outputs }}`, `{{ item }}`). No Python code builds prompt strings.
- **Event streaming** — Real-time step/tool progress, output deltas, and cost tracking
  available via async event stream.
- **Cost tracking** — Per-step and cumulative token usage and cost, emitted via events and
  captured in the final `WorkflowResult.metadata`.

## Setup

```sh
uv sync
cp .env.example .env
```

Edit `.env` with your credentials:

```sh
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
OPENAI_MODEL=gpt-4.1
WEBRESEARCH_URL_SELECTOR_MODEL=gpt-4.1-mini
```

Environment variables are loaded from `.env` automatically. Values already set in your
shell take precedence.

## Usage

`webresearch` is an SDK. Workflow packages (like [`webresearch-deep`](https://github.com/kodepo-com/web-research-deep)) provide their own CLI or you call the API directly.

### Event Logs

Run observers can capture observable events (agent calls, tool interactions, warnings, etc.)
to `.jsonc` files via `webresearch.events.jsonc_writer.JSONCWriter`. Useful for
debugging and diligence review without cluttering the final result output.

- **What is captured:** Workflow/Step/Agent lifecycle, Tool calls (redacted), Tool results (truncated), output deltas.
- **Privacy:** Hidden model chain-of-thought is **not** captured.

## Python API

```python
import asyncio
from webresearch import run_workflow
from webresearch.types import WorkflowInput
from webresearch.workflows import load_workflows

async def main() -> None:
    workflows = load_workflows()
    deep = workflows["deep"]  # discovered via entry points

    result = await run_workflow(
        deep,
        WorkflowInput(query="What is the current Node.js LTS version?"),
    )
    print(result.answer_markdown)

asyncio.run(main())
```

For streaming progress:

```python
from webresearch import stream_workflow
from webresearch.workflows import load_workflows
from webresearch.types import WorkflowInput

workflows = load_workflows()

async for event in stream_workflow(workflows["deep"], WorkflowInput(query="Research query")):
    print(event.kind)
```

## Project Structure

```
webresearch/
  pipeline/            ← Execution engine (no LLM imports outside runtime.py)
    hooks.py           ← HookSignal, PreHook, PostHook
    state.py           ← PipelineState
    step.py            ← AgentStep, Parallel, FanOut, Loop
    runner.py          ← Pipeline class (orchestration + Jinja rendering)
    runtime.py         ← ONLY file importing from the LLM framework
    __init__.py        ← Re-exports function_tool, ToolContext

  providers/           ← Raw I/O adapters (no LLM concepts)
    search.py          ← SearchProvider protocol, Tavily + Mock implementations
    fetch.py           ← httpx-based HTTP fetcher
    extract.py         ← trafilatura-based HTML content extractor
    discover.py        ← URL discovery via sitemap + link parsing
    services.py        ← Higher-level search service with caching + ranking
    errors.py          ← SearchProviderError

  events/              ← Event types, streaming, context management
    types.py           ← All event models (StepStarted, ToolCompleted, etc.)
    step.py            ← event_context, step(), emit_event()
    stream.py          ← stream_workflow(), run_workflow()

  sources/             ← Source registry and URL normalization
    registry.py        ← SourceRegistry (stable src_* IDs, fetch status)
    url_normalize.py   ← URL normalization (scheme, host, port, tracking params)

  context.py           ← WorkflowContext (pages, sources, evidence, cost)
  types.py             ← Core contracts (WorkflowInput, WorkflowResult, Depth, etc.)
  env.py               ← Environment / .env loading

  workflows/           ← Entry-point loader (no workflows shipped here)
    __init__.py        ← load_workflows(), load_workflow_entries()
```

## Architecture

### Layered design

| Layer | Owns | Never touches |
|-------|------|---------------|
| `providers/` | Raw HTTP calls, API responses, HTML extraction | LLM concepts, tools, prompts |
| `pipeline/` | Step execution, hooks, loops, events, cost, result build | Workflow logic, prompt content |
| `pipeline/runtime.py` | LLM framework imports, agent construction | Everything else |
| `events/` | Event types, sink, streaming to consumers | Workflow logic |
| `context.py` | Page cache, source registry, evidence list | Execution, providers, LLM |
| `types.py` | `WorkflowInput` / `WorkflowResult` contract | Workflow-specific types |
| `workflow/*/tools.py` | function_tool wrappers + workflow-tuned docstrings (in external packages) | Provider implementation |
| `workflow/*/agents.py` | AgentStep definitions + hook logic (in external packages) | LLM framework, Runner |
| `workflow/*/pipeline.py` | Step sequence declaration (in external packages) | Hook logic, execution |
| `workflow/*/workflow.py` | `run()` entry point (in external packages) | Everything (delegates to Pipeline) |


### Pipeline step types

- **`AgentStep`** — A single agent with a Jinja2 prompt, output type, tools, and optional hooks.
- **`Parallel`** — Run multiple `AgentStep` instances concurrently. All must complete before
  the pipeline continues.
- **`FanOut`** — Run one `AgentStep` once per item in a dynamic collection (e.g. one per URL).
  All instances run concurrently. Results collected as a list.
- **`Loop`** — Repeat a sequence of steps until a condition is met or `max_iterations` is reached.

### Cost tracking

Cost flows through two channels simultaneously:

1. **State accumulation** — `pipeline/runtime.py` returns `ExecutionResult` with token
   counts. `pipeline/runner.py` accumulates these into `state.context.cost_usd`,
   `input_tokens`, `output_tokens`. Final `WorkflowResult.metadata` reads from here.
2. **Event emission** — Each `StepCompleted` event carries `cost_usd`, `input_tokens`,
   `output_tokens` for real-time display in consumers (CLI, UI, logs).

### Adding a new workflow

Workflows live in their own pip packages. To create one:

1. Create a new Python package (e.g., `webresearch-my-workflow/`).
2. Add `webresearch` as a dependency in your `pyproject.toml`.
3. Create the workflow files under your package (use `src/webresearch/workflows/my_workflow/`
   for namespace-package compatibility):
   - `workflow.py` — async `run_my_workflow(input: WorkflowInput) -> WorkflowResult`
   - `agents.py` — `AgentStep` definitions
   - `tools.py` — `function_tool` wrappers around providers
   - `pipeline.py` — `Pipeline([...])` declaration
   - `models.py` — Pydantic output models
   - `config.py` — Workflow configuration
   - `prompts/*.j2` — Jinja2 prompt templates
4. Register the workflow and its metadata via entry points:
   ```toml
   [project.entry-points."webresearch.workflows"]
   my_workflow = "webresearch.workflows.my_workflow.workflow:run_my_workflow"

   [project.entry-points."webresearch.workflows.metadata"]
   my_workflow = "webresearch.workflows.my_workflow:get_metadata"
   ```
5. Publish your package. Anyone who installs it gets the workflow auto-discovered.

See [`webresearch-deep`](https://github.com/kodepo-com/web-research-deep) for a complete example.

## Development

```sh
uv run pytest
uv run ruff check
uv run ruff format
uv run mypy webresearch
```

Live service tests (require credentials):

```sh
LIVE_LLM=1 uv run pytest -m live
```

## Dependencies

Key runtime dependencies:

- `openai-agents` — LLM agent framework
- `httpx` — Async HTTP client
- `trafilatura` — HTML content extraction
- `jinja2` — Prompt template rendering
- `pydantic` — Data validation and schema enforcement
- `python-dotenv` — Environment file loading
- `defusedxml` — Safe XML parsing for sitemaps
