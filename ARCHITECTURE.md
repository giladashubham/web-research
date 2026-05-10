# Architecture

This document describes the current architecture of the webresearch project — how the
layers fit together, the data flow through the pipeline, and the extension points for
adding new workflows or swapping the LLM runtime.

---

## Design Goals

1. **Runtime isolation** — Only one file (`pipeline/runtime.py`) imports from the LLM
   framework. Swapping OpenAI Agents SDK → BAML → raw Anthropic API is a single-file change
   inside the SDK.
2. **Self-contained workflows** — Adding a new workflow requires zero changes outside that
   workflow's own folder. Workflows are registered via Python entry points.
3. **Declarative pipeline** — Workflows declare their logic as sequences of `AgentStep`,
   `Parallel`, `FanOut`, and `Loop` steps. The SDK owns all execution mechanics.
4. **No prompt-building code** — Prompts are Jinja2 templates rendered with the full
   pipeline state. No Python function builds prompt strings.

---

## Directory Layout

```
webresearch/
  pipeline/             ← Execution engine
    hooks.py            ← HookSignal, PreHook, PostHook
    state.py            ← PipelineState
    step.py             ← AgentStep, Parallel, FanOut, Loop
    runner.py           ← Pipeline class (orchestrates everything)
    runtime.py          ← ONLY file that imports from the LLM framework

  providers/            ← Raw I/O adapters, no LLM opinions
    search.py           ← SearchProvider protocol + Tavily + Mock
    fetch.py            ← httpx HTTP fetcher
    extract.py          ← trafilatura content extractor
    discover.py         ← URL discovery (sitemap + links)
    services.py         ← Higher-level search service
    errors.py           ← SearchProviderError

  events/               ← Event system
    types.py            ← Event models (StepStarted, ToolCompleted, etc.)
    step.py             ← Context managers + event emission helpers
    stream.py           ← stream_workflow / run_workflow

  sources/              ← Source registry
    registry.py         ← SourceRegistry
    url_normalize.py    ← URL normalization

  workflows/            ← Entry-point loader (no workflows shipped in core)
    __init__.py         ← load_workflows(), load_workflow_entries()

  context.py            ← WorkflowContext (pages, sources, evidence, cost)
  types.py              ← Core contracts
  env.py                ← Environment / .env loading
```

---

## Data Flow

### Pipeline execution

```
User input (WorkflowInput)
       │
       ▼
Pipeline.run(input)
       │
       ▼
For each step in Pipeline.steps:
  │
  ├─ AgentStep ──► 1. pre_hook (emit SKIP or CONTINUE)
  │                 2. _build_prompt (Jinja2: state → string)
  │                 3. runtime.execute (LLM call)
  │                 4. Accumulate cost + tokens into state.context
  │                 5. Emit StepCompleted event
  │                 6. post_hook (emit REPEAT or CONTINUE)
  │
  ├─ Parallel ──► asyncio.gather(*AgentStep instances)
  │
  ├─ FanOut ──► asyncio.gather(*AgentStep instances, one per item)
  │              Results collected as list under step name
  │
  └─ Loop ──► while not until(state) and iteration < max_iterations:
                for each step: _execute_agent
       │
       ▼
_build_result(state, final_output_key) → WorkflowResult
```

### Cost tracking

```
runtime.execute()
    │
    ▼
ExecutionResult (output, input_tokens, output_tokens, model)
    │
    ├─► state.context.input_tokens  += input_tokens
    │   state.context.output_tokens += output_tokens
    │   state.context.cost_usd      += calculate_cost(...)
    │
    └─► emit StepCompleted(cost_usd=..., input_tokens=..., output_tokens=...)
```

### Event streaming

```
stream_workflow(workflow_fn, input)
    │
    ├─► patch_runner_for_streaming()  (wraps Runner.run_streamed)
    │
    ├─► Background: event_context → pipeline.run → emit events to asyncio.Queue
    │
    └─► Main: yield events from queue to caller
```

---

## Pipeline Step Types

### AgentStep

```python
@dataclass
class AgentStep:
    name: str                      # Unique step identifier
    prompt: str                    # Jinja2 template string
    output_type: type[BaseModel]   # Pydantic output model
    tools: list[Any]               # Function tools for this agent
    pre_hook: PreHook | None       # Called before execution
    post_hook: PostHook | None     # Called after execution
    max_turns: int = 50            # Max LLM turns (tool calls)
    strict_schema: bool = True     # Whether to enforce strict JSON schema
```

### Parallel

Runs multiple `AgentStep` instances concurrently. All must complete before the pipeline
continues.

### FanOut

Runs one `AgentStep` once per item in a dynamic list (returned by a callable that receives
`PipelineState`). All instances run concurrently. Results are collected into a list under
`state.outputs[step.name]`.

### Loop

Repeats a sequence of steps until `until(state)` returns `True` or `max_iterations` is
reached. `max_iterations` defaults to `state.input.depth.max_rounds`.

---

## Hooks

Hooks are async callbacks that receive `PipelineState` and return a `HookSignal`:

| Signal | Behaviour |
|--------|-----------|
| `CONTINUE` | Proceed normally |
| `SKIP` | Skip this step entirely |
| `REPEAT` | Re-run this step (increments iteration count; respects `max_rounds`) |

Hooks access prior step results via `state.outputs.get("step_name")` and iteration counts
via `state.iteration_count.get("step_name", 0)`.

---

## Jinja2 Prompt Templates

Templates are rendered with the full pipeline state as context:

```jinja
Query: {{ input.query }}
{% if input.instructions %}Instructions: {{ input.instructions }}{% endif %}
Plan: {{ outputs.planner | tojson(indent=2) }}
```

Available variables:

| Variable | Description |
|----------|-------------|
| `{{ input }}` | The `WorkflowInput` (`.query`, `.instructions`, `.depth`) |
| `{{ outputs }}` | Dict of all prior step outputs by name |
| `{{ outputs.step_name }}` | Output of a specific prior step |
| `{{ outputs.step_name.field }}` | A specific field from a prior step's output |
| `{{ item }}` | (FanOut only) The element this agent instance processes |

---

## Adding a New Workflow

Workflows ship as separate pip packages. No changes to this package are needed.

1. Create a new Python package (e.g., `webresearch-my-workflow/`).
2. Add `webresearch` as a dependency.
3. Create the workflow under `src/webresearch/workflows/my_workflow/`:
   - `workflow.py` — Async entry point `run_my_workflow(input) -> WorkflowResult`
   - `agents.py` — `AgentStep` definitions
   - `tools.py` — `function_tool` wrappers around `providers/` calls
   - `pipeline.py` — `Pipeline([...])` declaration
   - `models.py` — Pydantic output models
   - `config.py` — Workflow configuration
   - `prompts/*.j2` — Jinja2 prompt templates
4. Register in your package's `pyproject.toml`:
   ```toml
   [project.entry-points."webresearch.workflows"]
   my_workflow = "webresearch.workflows.my_workflow.workflow:run_my_workflow"

   [project.entry-points."webresearch.workflows.metadata"]
   my_workflow = "webresearch.workflows.my_workflow:get_metadata"
   ```

Once installed, `load_workflows()` discovers it via `importlib.metadata`.

---

## Swapping the LLM Runtime

Only `pipeline/runtime.py` needs to change. The file currently exports:

- `execute(step, prompt, context) -> ExecutionResult`
- `ExecutionResult` (output, input_tokens, output_tokens, model)
- `calculate_cost(input_tokens, output_tokens, model) -> float`

To swap to a different runtime:
1. Rewrite `execute()` to use the new framework
2. Update `_COST_PER_1M` pricing table
3. Update `patch_runner_for_streaming()` if the new framework has a different streaming model
4. Update `pipeline/__init__.py` re-exports if the new framework uses different tool decorators

No workflow files, providers, or events code needs to change.
