# Web Research

A Python CLI and library for running LLM-powered web research workflows. Built on the
[OpenAI Agents SDK](https://github.com/openai/openai-agents-python) with a clean
abstraction layer so the underlying runtime can be swapped without touching workflow code.

## Features

- **Declarative pipeline** — Workflows are defined as sequences of `AgentStep`, `Parallel`,
  `FanOut`, and `Loop` steps. The pipeline owns all execution mechanics (hooks, parallelism,
  loop control, event emission, cost tracking).
- **Entry-point workflow discovery** — Workflows are registered via Python entry points.
  Adding a new workflow requires zero changes outside the workflow's own folder.
- **Two built-in workflows:**
  - **`deep`** — Planner → parallel research (official/recent/broad) → review → gap loop → answer.
  - **`technical_due_diligence`** — Intake planning, URL selection, claim extraction, evidence
    research, substance review with gap loop, final memo with structured report validated
    against a JSON Schema.
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

## CLI

List available workflows:

```sh
uv run webresearch list
```

Run the deep workflow:

```sh
uv run webresearch run "What is the current Node.js LTS version?"
```

Choose a workflow and depth:

```sh
uv run webresearch run "Compare Python 3.13 migration risks" deep --depth deep
uv run webresearch run "Summarize the latest Django release" quick --depth quick
```

Run technical due diligence:

```sh
uv run webresearch run \
  "Evaluate ProductX for technical diligence. URLs: https://productx.com/docs. Competitors: ACME, Contoso." \
  technical_due_diligence \
  --format json \
  --out diligence.json
```

Output formats:

```sh
uv run webresearch run "What changed in Python 3.13?" --format md --out answer.md
uv run webresearch run "What changed in Python 3.13?" --format json --out answer.json
```

Useful options:

```sh
--instructions "Prefer official release notes"
--max-sources 8
--quiet
--events-out logs/my-run.jsonc
```

### Event Logs

Every run automatically captures observable events (agent calls, tool interactions, warnings, etc.)
into a `.jsonc` file. This is useful for debugging and diligence review without cluttering
the final result output.

- **Default location:** `.web-research/logs/run_<id>.jsonc`
- **What is captured:** Workflow/Step/Agent lifecycle, Tool calls (redacted), Tool results (truncated), output deltas.
- **Privacy:** Hidden model chain-of-thought is **not** captured.

## Python API

```python
import asyncio
from webresearch import run_workflow
from webresearch.types import WorkflowInput
from webresearch.workflows.deep import run_deep

async def main() -> None:
    result = await run_workflow(
        run_deep,
        WorkflowInput(query="What is the current Node.js LTS version?"),
    )
    print(result.answer_markdown)

asyncio.run(main())
```

For streaming progress:

```python
from webresearch import stream_workflow
from webresearch.workflows.deep import run_deep
from webresearch.types import WorkflowInput

async for event in stream_workflow(run_deep, WorkflowInput(query="Research query")):
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

  cli/                 ← Typer CLI
    __init__.py        ← app, commands
    run_cmd.py         ← run command
    list_cmd.py        ← list command
    progress.py        ← ProgressRenderer
    formats.py         ← Output formatting (JSON, Markdown)

  context.py           ← WorkflowContext (pages, sources, evidence, cost)
  types.py             ← Core contracts (WorkflowInput, WorkflowResult, Depth, etc.)
  env.py               ← Environment / .env loading

  workflows/           ← Workflow packages, discovered via entry points
    __init__.py        ← load_workflows(), load_workflow_entries()
    deep/              ← Deep research workflow
      agents.py        ← AgentStep definitions
      tools.py         ← function_tool wrappers
      pipeline.py      ← Pipeline declaration
      models.py        ← Output models
      config.py        ← Workflow config
      workflow.py      ← run_deep() entry point
      prompts/         ← .j2 Jinja2 templates
    technical_due_diligence/
      agents.py        ← AgentStep definitions + hooks
      tools.py         ← function_tool wrappers
      pipeline.py      ← Pipeline declaration
      models.py        ← Output models + UrlsByCategory
      config.py        ← Workflow config
      workflow.py      ← run_technical_due_diligence() entry point
      prompts/         ← .j2 Jinja2 templates
      schema.json      ← JSON Schema for structured report output
      examples/        ← Example input/output
```

## Architecture

### Layered design

| Layer | Owns | Never touches |
|-------|------|---------------|
| `providers/` | Raw HTTP calls, API responses, HTML extraction | LLM concepts, tools, prompts |
| `pipeline/` | Step execution, hooks, loops, events, cost, result build | Workflow logic, prompt content |
| `pipeline/runtime.py` | LLM framework imports, agent construction | Everything else |
| `events/` | Event types, sink, streaming to CLI | Workflow logic |
| `context.py` | Page cache, source registry, evidence list | Execution, providers, LLM |
| `types.py` | `WorkflowInput` / `WorkflowResult` contract | Workflow-specific types |
| `workflow/*/tools.py` | function_tool wrappers + workflow-tuned docstrings | Provider implementation |
| `workflow/*/agents.py` | AgentStep definitions + hook logic | LLM framework, Runner |
| `workflow/*/pipeline.py` | Step sequence declaration | Hook logic, execution |
| `workflow/*/workflow.py` | `run()` entry point | Everything (delegates to Pipeline) |
| `cli/` | Workflow discovery, input parsing, output formatting | Workflow internals |

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
   `output_tokens` for real-time CLI display.

### Adding a new workflow

1. Create `webresearch/workflows/my_workflow/` with `workflow.py`, `agents.py`,
   `tools.py`, `pipeline.py`, `models.py`, `config.py`, and `prompts/`.
2. In `workflow.py`, expose an async `run_my_workflow(input: WorkflowInput) -> WorkflowResult`.
3. Add an entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."webresearch.workflows"]
   my_workflow = "webresearch.workflows.my_workflow.workflow:run_my_workflow"
   ```
No other changes needed. The CLI discovers it automatically.

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
- `typer` — CLI framework
- `python-dotenv` — Environment file loading
- `defusedxml` — Safe XML parsing for sitemaps
