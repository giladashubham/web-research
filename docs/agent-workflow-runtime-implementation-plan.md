# Web Research Agent — V1 Plan (Python)

## Goal

Build a Python web research agent: a CLI + TUI that runs a multi-agent research pipeline on top of the **OpenAI Agents SDK**. Workflows are Python modules. V1 ships three default workflows (`quick`, `standard`, `deep`) — all web research.

The product is a focused web research runner. Not a generic workflow platform.

## Stack

- **Python 3.12+**
- **`openai-agents`** — agent loop, tool calling, streaming, tracing.
- **Pydantic v2** — agent output models, tool schemas, structured outputs.
- **Textual** — terminal UI.
- **Typer** — CLI.
- **httpx** — HTTP for `fetch_url`.
- **trafilatura** — content extraction.
- **tavily-python** (or direct httpx) — search.
- **pytest + pytest-asyncio** — tests.
- **uv** — packaging and venvs.

Single-language stack. No process boundary. CLI / TUI / SDK all import from the same package.

## Conventions & Code Quality

The bar is set in P1-01 and enforced in CI from day one. Don't relax it later.

**Type discipline**
- `mypy --strict` over `webresearch/`. No `Any` except at I/O boundaries (HTTP responses, raw env).
- Every public function is fully typed. Use `from __future__ import annotations` everywhere.
- Pydantic v2 models for any data that crosses a module boundary. No dicts-as-records.
- `Protocol` over inheritance for capabilities (e.g. `SearchProvider`).

**Lint & format**
- `ruff` with `E,F,W,I,B,UP,SIM,PL,RUF,ASYNC,TCH,ANN,RET,PTH,ARG,ERA` enabled. `ruff format` is the formatter.
- 100-char line limit.
- Imports sorted by ruff. No wildcard imports.
- `__future__` annotations enforced.

**Module shape**
- One concept per module. Files over ~200 lines are a smell — split.
- No premature abstraction. Three similar lines are fine; abstract when a fourth shows up with a real reason.
- No stub functions, no `pass` placeholders left in committed code.

**Errors**
- Every `except` either handles or re-raises with context. **No bare `except: pass`.** No silent fallbacks.
- Tools that fail return a typed failure result + emit a warning. They never raise out of the SDK.
- Anything else raises a typed exception (`SearchProviderError`, `WorkflowCancelled`, etc.). Caller decides.

**Async**
- All I/O is async. No `requests`, no sync `urllib`. `httpx.AsyncClient`, `aiofiles` if needed.
- `async with asyncio.timeout(...)` for deadlines. No hand-rolled timer races.
- Every `asyncio.create_task` is tracked (assign to a name, await or cancel deterministically).

**Tests**
- Each feature task ships its tests in the same PR. `tests/` mirrors `webresearch/`.
- `pytest-asyncio` mode is `auto` — no `@pytest.mark.asyncio` boilerplate.
- Mock at boundaries (`respx` for httpx, `MockSearchProvider`, `MockModel`). Never patch deep internals.
- Live tests are gated by env vars and a `live` pytest marker; skipped by default.

**Docs in code**
- Default to no comments. Names + types do the explaining.
- Comments only when WHY is non-obvious (workaround for a known bug, an invariant a reader would otherwise miss).
- No "what" comments restating the code. No file-header banners. No version stamps.
- Public-API docstrings: one line. Detailed docstrings live on the prompts and Pydantic model `Field(description=...)` — those are seen by the LLM.

**Logging**
- `logging` module for diagnostics, namespaced `webresearch.<module>`.
- `print` and `rich.print` only inside `cli/` and `tui/` (user-facing output).
- No `print` for debugging in committed code.

**CI gates**
- `uv run ruff check`, `uv run ruff format --check`, `uv run mypy webresearch`, `uv run pytest -q` — all four must pass to merge.
- Pre-commit hook (`pre-commit` + `ruff` + `ruff-format` + `mypy`) installed by P1-01.

## Core Idea

```text
A workflow is an async function:
  -> creates Agents (openai-agents)
  -> sequences them with `await Runner.run(...)`
  -> parallelizes them with `asyncio.gather(...)`
  -> loops with plain `while` / `for`
  -> returns a typed Result
```

There is no custom workflow runtime. The SDK is the runtime. Python is the configuration.

## Product Shape

```text
SDK (importable Python package)
  -> from webresearch.workflows.standard import run_standard
  -> result = await run_standard(WorkflowInput(query="..."))

CLI
  -> webresearch list
  -> webresearch run [WORKFLOW] QUERY [--depth ...] [--out PATH] [--format json|md]

TUI
  -> webresearch tui  (or just `webresearch` with no args)
  -> pick a workflow
  -> enter query
  -> live step timeline + artifacts
  -> view answer, sources, evidence
  -> export
```

## Workflow Definition

Workflows are Python modules under `webresearch/workflows/`. Each exposes one async function returning `WorkflowResult`. Example shape:

```python
# webresearch/workflows/standard.py
import asyncio
from agents import Runner

from webresearch.agents import (
    planner_agent,
    official_researcher_agent,
    recent_researcher_agent,
    broad_researcher_agent,
    reviewer_agent,
    gap_researcher_agent,
    output_agent,
)
from webresearch.events import emit, step
from webresearch.types import WorkflowInput, WorkflowResult, Depth


async def run_standard(input: WorkflowInput) -> WorkflowResult:
    depth = Depth.for_preset("standard")
    state = WorkflowState(input=input, depth=depth)

    async with step("planner"):
        plan = await Runner.run(planner_agent(), input.query)
    state.plan = plan.final_output

    async with step("research"):
        official, recent, broad = await asyncio.gather(
            Runner.run(official_researcher_agent(), state.research_prompt()),
            Runner.run(recent_researcher_agent(),   state.research_prompt()),
            Runner.run(broad_researcher_agent(),    state.research_prompt()),
        )
    state.research = [official.final_output, recent.final_output, broad.final_output]

    async with step("reviewer"):
        review = await Runner.run(reviewer_agent(), state.review_prompt())
    state.review = review.final_output

    for round_num in range(depth.max_rounds):
        if not state.review.has_critical_gaps:
            break
        async with step(f"gap_research[{round_num + 1}]"):
            gaps = await Runner.run(gap_researcher_agent(), state.gap_prompt())
        state.add_gap_research(gaps.final_output)
        async with step(f"reviewer[{round_num + 2}]"):
            review = await Runner.run(reviewer_agent(), state.review_prompt())
        state.review = review.final_output

    async with step("output"):
        answer = await Runner.run(output_agent(input.output_schema), state.output_prompt())

    return state.build_result(answer.final_output)
```

That's the entire orchestration. ~40 lines for the most elaborate workflow. No YAML loader, no validator, no parallel runner, no loop executor.

## Agents

Each agent is a factory:

```python
# webresearch/agents/planner.py
from agents import Agent
from webresearch.agents.models import PlanOutput
from webresearch.agents.prompts import load_prompt


def planner_agent() -> Agent:
    return Agent(
        name="Planner",
        instructions=load_prompt("planner.md"),
        output_type=PlanOutput,
    )
```

Researchers add tools:

```python
def official_researcher_agent() -> Agent:
    return Agent(
        name="Official Source Researcher",
        instructions=load_prompt("official.md"),
        tools=[search_web, fetch_url, extract_content],
        output_type=ResearcherOutput,
    )
```

Tool scoping is automatic — the SDK only lets each agent see the tools listed.

## Tools

Tools are decorated async functions. The SDK infers schemas from type hints.

```python
# webresearch/tools/search_web.py
from agents import function_tool, RunContextWrapper
from webresearch.types import SearchResults
from webresearch.context import WorkflowContext


@function_tool
async def search_web(
    ctx: RunContextWrapper[WorkflowContext],
    query: str,
    limit: int = 10,
) -> SearchResults:
    """Search the web. Returns ranked results with titles, URLs, snippets."""
    results = await ctx.context.search_provider.search(query, limit)
    for r in results:
        ctx.context.sources.add(r)
    return SearchResults(items=results)
```

Shared state (source registry, search provider) lives on `WorkflowContext`, passed to each `Runner.run` via the `context=` argument.

V1 tools:
- `search_web` — Tavily, with Mock for tests.
- `fetch_url` — httpx + source-registry update.
- `extract_content` — trafilatura + emits Evidence.
- `rank_sources` — heuristic scoring.

> Caching is deliberately omitted from V1 — every fetch/extract/search hits the network. A file-backed cache will be reintroduced once the end-to-end pipeline is shaken out.

## Structured Outputs

Pydantic models. The SDK validates them automatically (`output_type=...`). No post-hoc validation, no ajv.

```python
class PlanOutput(BaseModel):
    questions: list[str]
    risks: list[str]
    search_strategy: str

class Coverage(BaseModel):
    question: str
    status: Literal["covered", "weak", "missing"]
    reason: str

class ReviewOutput(BaseModel):
    coverage: list[Coverage]
    conflicts: list[Conflict]
    has_critical_gaps: bool
    follow_up_queries: list[str]

class FinalAnswer(BaseModel):
    answer_markdown: str
    structured_data: dict | None = None  # populated only when input.output_schema is set
```

User-supplied `output_schema` is handled by injecting an `output_type` derived from the schema (or by leaving it None and asking the output agent to embed structured data in `FinalAnswer.structured_data`).

## Events

The SDK exposes `Runner.run_streamed(agent, input)` — yields fine-grained events (text deltas, tool calls). We wrap each `Runner.run` in a thin helper that:
- emits our workflow-level events (`step_started`, `step_completed`, `loop_iteration`).
- forwards SDK events: tool start/end, text deltas (re-tagged `output_text_delta` only on the output step).
- writes artifacts to the run's artifact list.

```python
type WorkflowEvent =
  | WorkflowStarted | WorkflowCompleted | WorkflowFailed
  | StepStarted | StepCompleted | StepSkipped
  | LoopIteration
  | ToolStarted | ToolCompleted
  | ArtifactAdded | SourceAdded
  | OutputTextDelta
  | Warning
```

`stream_workflow(workflow_fn, input)` is an `AsyncIterator[WorkflowEvent]`. The CLI and TUI consume it.

## Source Registry & Artifacts

Still ours, but lighter in Python:
- `SourceRegistry` — URL normalize + dedup + stable IDs.
- Artifacts — Pydantic models accumulated on `WorkflowContext`.

## Config & Auth

We don't build an auth layer. The Agents SDK reads `OPENAI_API_KEY` natively; we read `TAVILY_API_KEY` for search.

| Provider | Env var |
| --- | --- |
| OpenAI (Agents SDK)  | `OPENAI_API_KEY` |
| Tavily (search)      | `TAVILY_API_KEY` |

Tracing dashboard at platform.openai.com works automatically once `OPENAI_API_KEY` is set.

## CLI

```bash
webresearch list
webresearch run [WORKFLOW] QUERY \
  --depth quick|standard|deep \
  --instructions "..." \
  --out result.json \
  --format json|md
```

- Default workflow: `standard`.
- Streams progress to stderr; result to stdout (or `--out`).
- Exit codes: `0` ok, `1` workflow failure, `2` usage error, `3` IO error.

Built with Typer.

## TUI

```text
Home          -> Pick Workflow / Saved Runs / Settings
Query         -> Editor + depth selector + Run
Run           -> Step timeline (left) | Artifacts + warnings (right)
Result        -> Answer (Markdown, live deltas) | Sources | Findings | Evidence | Export
```

Built with Textual.

## Folder Structure

```text
webresearch-agent/
  pyproject.toml
  uv.lock
  README.md

  webresearch/
    __init__.py

    types.py                    # WorkflowInput, WorkflowResult, Depth, etc.
    context.py                  # WorkflowContext (passed via Agents SDK context=)

    sources/
      registry.py
      url_normalize.py

    tools/
      search_web.py
      fetch_url.py
      extract_content.py
      rank_sources.py
      providers/
        search_provider.py      # Protocol
        tavily.py
        mock.py

    agents/
      planner.py
      researchers.py            # official + recent + broad
      reviewer.py
      gap.py
      output.py
      models.py                 # Pydantic output_type models
      prompts.py                # load_prompt helper

    workflows/
      standard.py
      quick.py
      deep.py
      registry.py               # workflow id -> async fn

    events/
      types.py
      stream.py                 # async generator wrapping Runner.run_streamed

    cli/
      __init__.py               # Typer app + entrypoint
      list_cmd.py
      run_cmd.py
      progress.py
      formats.py

    tui/
      app.py
      screens/
        home.py
        query.py
        run.py
        result.py
        settings.py
      widgets/
        timeline.py
        artifacts.py
        sources.py

  prompts/
    planner.md
    official.md
    recent.md
    broad.md
    reviewer.md
    gap.md
    output.md

  tests/
    sources/
    tools/
    agents/
    workflows/
    events/
    cli/
    tui/
    integration/                # gated live tests
```

## Implementation Phases

### Phase 1 — Project skeleton & primitives
- Project init (uv, ruff, mypy, pytest, pytest-asyncio).
- Core Pydantic types (`WorkflowInput`, `WorkflowResult`, `Depth`, artifact models).
- `SourceRegistry` + URL normalization.

### Phase 2 — Tools
- `SearchProvider` protocol + `MockSearchProvider`.
- `TavilySearchProvider`.
- `search_web`, `fetch_url`, `extract_content`, `rank_sources` tools.

### Phase 3 — Agents
- Install `openai-agents`, smoke test.
- Pydantic output models (`PlanOutput`, `ReviewOutput`, `FinalAnswer`, etc.).
- Agent factories with prompt-file loading.
- Mock-model harness for fast offline tests.

### Phase 4 — Standard workflow
- `run_standard(input)` function.
- `WorkflowState` + result aggregator.

### Phase 5 — Event stream
- `WorkflowEvent` types.
- `stream_workflow(workflow_fn, input)` async generator wrapping `Runner.run_streamed`.

### Phase 6 — CLI
- Typer app + `list` + `run`.
- Stderr progress.
- JSON / Markdown output.

### Phase 7 — TUI
- Textual app shell + screen routing.
- Home (workflow picker) + Query screens.
- Run screen (timeline + artifacts).
- Result screen (answer + sources + export).
- Cancellation + Settings.

### Phase 8 — Quick + Deep variants
- `quick.py` (no reviewer, no loop).
- `deep.py` (higher budgets, more rounds).

### Phase 9 — Polish
- Live LLM integration test (gated by env).
- Prompt finalization + golden tests.

## V1 Success Criteria

- Standard workflow runs end-to-end against real OpenAI + Tavily.
- TUI lists workflows from the registry and runs the chosen one.
- Sequential, parallel, and loop steps work via plain Python.
- Tools are scoped per agent; sources deduplicated; citation IDs stable.
- Optional structured output works (Pydantic).
- Tracing dashboard shows the full run.
- CLI exports JSON / Markdown.

## Non-Goals

- YAML / JSON workflow definitions — Python is the config.
- User-defined custom tools loaded at runtime — closed registry.
- Plugin system / marketplace / web UI / multi-user server.
- Browser automation / PDF parsing / vector DB.
- Schema repair on structured outputs.
- Resume / saved-run replay.
