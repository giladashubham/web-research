# Architecture Rewrite Plan

## Goal

Redesign `webresearch` so the SDK owns all execution mechanics and workflows are fully
self-contained declarative definitions. Swapping the underlying LLM runtime (OpenAI Agents SDK →
BAML or anything else) is a single-file change inside the SDK. Adding a new workflow requires no
changes outside that workflow's own folder.

No backward-compatibility shims. This is a clean rewrite.

---

## Target Directory Layout

```
webresearch/
  pipeline/               ← NEW: the execution engine
    __init__.py
    step.py               ← AgentStep, Parallel, FanOut
    hooks.py              ← HookSignal, hook type aliases
    state.py              ← PipelineState (flows through all steps)
    runner.py             ← Pipeline class (orchestrates execution)
    runtime.py            ← ONLY file that imports from the LLM framework

  providers/              ← NEW: raw I/O adapters, no LLM opinions
    __init__.py
    search.py             ← SearchProvider protocol + Tavily + Mock impls
    fetch.py              ← httpx wrapper (replaces tools/fetch_url.py)
    extract.py            ← trafilatura wrapper (replaces tools/extract_content.py)
    discover.py           ← URL discovery (replaces tools/discover_urls.py)

  events/                 ← KEEP as-is (types.py, step.py, stream.py)
  sources/                ← KEEP as-is (url_normalize.py, registry.py)
  context.py              ← SIMPLIFY: remove search_provider field
  types.py                ← TRIM: remove UrlsByCategory (workflow-specific)
  env.py                  ← KEEP as-is

  cli/                    ← UPDATE: discover workflows via entry points
    __init__.py
    run_cmd.py
    list_cmd.py
    progress.py
    formats.py

  workflows/
    deep/                 ← REWRITE: fully self-contained
      tools.py            ← NEW: function_tool wrappers for this workflow
      agents.py           ← NEW: AgentStep definitions
      pipeline.py         ← NEW: Pipeline([...]) declaration
      models.py           ← NEW: PlanOutput, ResearcherOutput, etc.
      config.py           ← KEEP
      prompts/            ← RENAME *.md → *.j2
      workflow.py         ← SIMPLIFY: just calls pipeline.run(input)
      __init__.py

    technical_due_diligence/   ← REWRITE: fully self-contained
      tools.py                 ← NEW
      agents.py                ← NEW
      pipeline.py              ← NEW
      models.py                ← KEEP + add UrlsByCategory here
      config.py                ← NEW
      prompts/                 ← RENAME *.md → *.j2
      schema.json              ← KEEP
      workflow.py              ← SIMPLIFY
      __init__.py
```

### Deleted entirely

```
webresearch/agents/                    ← absorbed into each workflow
webresearch/tools/                     ← replaced by providers/ + per-workflow tools.py
webresearch/workflows/quick/           ← removed
webresearch/workflows/standard/        ← removed
webresearch/workflows/shared/          ← absorbed into SDK pipeline + each workflow
```

---

## Layer 1: `webresearch/pipeline/`

This is the new core of the SDK. Workflows never import from the LLM framework directly.

### `pipeline/hooks.py`

```python
from enum import Enum
from typing import Awaitable, Callable, TYPE_CHECKING

class HookSignal(Enum):
    CONTINUE = "continue"   # proceed to next step
    SKIP     = "skip"       # skip this step, move on
    REPEAT   = "repeat"     # re-run this step (increments iteration count)

if TYPE_CHECKING:
    from webresearch.pipeline.state import PipelineState

PreHook  = Callable[["PipelineState"], Awaitable[HookSignal]]
PostHook = Callable[["PipelineState"], Awaitable[HookSignal]]
```

### `pipeline/step.py`

Three composable step types. Workflows only use these — never `agents.Agent` directly.

```python
from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel
from webresearch.pipeline.hooks import PreHook, PostHook

@dataclass
class AgentStep:
    name: str
    prompt: str                      # Jinja2 template string (loaded from prompts/*.j2)
    output_type: type[BaseModel]
    tools: list[Any]  = field(default_factory=list)
    pre_hook:  PreHook  | None = None
    post_hook: PostHook | None = None
    max_turns: int = 50              # passed to runtime
    strict_schema: bool = True
    # strict_schema=False for agents whose output_type contains open-ended dicts
    # (e.g. structured_data: dict[str, object]) that fail OpenAI strict JSON schema.
    # runtime.py wraps output_type in AgentOutputSchema(..., strict_json_schema=False).

@dataclass
class Parallel:
    """Run multiple AgentSteps concurrently. All must complete before continuing."""
    steps: list[AgentStep]

@dataclass
class FanOut:
    """
    Run one AgentStep once per item in a state collection.
    `over` is a callable that receives PipelineState and returns the list to fan over.
    All instances run concurrently. Results collected as list under step.name.
    """
    step: AgentStep
    over: Callable[["PipelineState"], list[Any]]

@dataclass
class Loop:
    """
    Repeat a sequence of steps until `until` returns True or max_iterations is reached.
    max_iterations defaults to state.input.depth.max_rounds at runtime.
    """
    steps: list[AgentStep]
    until: Callable[["PipelineState"], bool]
    max_iterations: int | None = None
```

### `pipeline/state.py`

The single object that flows through every step. Hooks read from it; the runtime writes to it.

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from webresearch.context import WorkflowContext
from webresearch.types import WorkflowInput

@dataclass
class PipelineState:
    input:           WorkflowInput
    run_id:          str
    started_at:      datetime
    context:         WorkflowContext        # pages, sources, evidence (shared I/O state)
    outputs:         dict[str, Any]  = field(default_factory=dict)
    # outputs["step_name"] = the output_type instance produced by that step.
    # For FanOut steps, outputs["step_name"] = list[output_type].
    iteration_count: dict[str, int]  = field(default_factory=dict)
    # iteration_count["step_name"] = how many times this step has been run (starts at 0).
    warnings:        list[str]       = field(default_factory=list)
```

Hooks access prior step results like:

```python
review = state.outputs.get("technical_substance_reviewer")  # typed at callsite
iteration = state.iteration_count.get("gap_researcher", 0)
max_rounds = state.input.depth.max_rounds
```

### `pipeline/runner.py`

The Pipeline class. Owns all execution logic: hooks, looping, parallelism, event emission,
cost tracking. Workflows never call `Runner.run()` directly — they call `pipeline.run(input)`.

```python
from webresearch.pipeline.step import AgentStep, Parallel, FanOut
from webresearch.pipeline.state import PipelineState
from webresearch.pipeline.hooks import HookSignal
from webresearch.types import WorkflowInput, WorkflowResult

PipelineStep = AgentStep | Parallel | FanOut | Loop

class Pipeline:
    def __init__(self, steps: list[PipelineStep], final_output_key: str = "output") -> None:
        self._steps = steps
        self._final_output_key = final_output_key

    async def run(self, input: WorkflowInput) -> WorkflowResult:
        state = _init_state(input)
        for step_def in self._steps:
            await self._execute(step_def, state)
        return _build_result(state, self._final_output_key)

    async def _execute(self, step_def: PipelineStep, state: PipelineState) -> None:
        if isinstance(step_def, Parallel):
            await self._execute_parallel(step_def, state)
        elif isinstance(step_def, FanOut):
            await self._execute_fanout(step_def, state)
        elif isinstance(step_def, Loop):
            await self._execute_loop(step_def, state)
        else:
            await self._execute_agent(step_def, state)

    async def _execute_agent(self, step: AgentStep, state: PipelineState, item: object = None) -> None:
        # 1. pre_hook
        if step.pre_hook:
            signal = await step.pre_hook(state)
            if signal == HookSignal.SKIP:
                await emit_step_skipped(step.name, "pre_hook returned SKIP")
                return

        # 2. render prompt, run via runtime, emit events
        async with sdk_step(step.name):
            prompt = _build_prompt(step, state, item=item)
            exec_result = await runtime.execute(step, prompt, state.context)

        # 3. write output and accumulate cost
        state.outputs[step.name] = exec_result.output
        state.iteration_count[step.name] = state.iteration_count.get(step.name, 0) + 1
        state.context.input_tokens  += exec_result.input_tokens
        state.context.output_tokens += exec_result.output_tokens
        state.context.cost_usd      += runtime._cost(exec_result)

        # 4. post_hook — REPEAT re-runs only this single step
        if step.post_hook:
            signal = await step.post_hook(state)
            if signal == HookSignal.REPEAT:
                if state.iteration_count[step.name] < state.input.depth.max_rounds:
                    await self._execute_agent(step, state, item=item)

    async def _execute_parallel(self, par: Parallel, state: PipelineState) -> None:
        await asyncio.gather(*[self._execute_agent(s, state) for s in par.steps])

    async def _execute_fanout(self, fan: FanOut, state: PipelineState) -> None:
        items = fan.over(state)
        await asyncio.gather(*[self._execute_agent(fan.step, state, item=item) for item in items])
        # state.outputs[fan.step.name] = list of all results collected per item

    async def _execute_loop(self, loop: Loop, state: PipelineState) -> None:
        max_iter = loop.max_iterations or state.input.depth.max_rounds
        iteration = 0
        while not loop.until(state) and iteration < max_iter:
            await emit_loop_iteration(loop.steps[0].name, iteration + 1)
            for step in loop.steps:
                await self._execute_agent(step, state)
            iteration += 1
```

Key behaviours owned by the runner (workflows get these for free):
- Event emission: `StepStarted`, `StepCompleted`, `StepSkipped`, `StepFailed`, `LoopIteration`
- Tool events: emitted by `runtime.py` (see below)
- Cost/token tracking: accumulated from runtime responses into `state.context`
- `max_rounds` enforcement: runner checks `iteration_count` before allowing `REPEAT`

### `pipeline/runtime.py`

**The only file in the entire codebase that imports from the LLM framework.**

```python
# THIS IS THE ONLY FILE THAT KNOWS ABOUT THE LLM FRAMEWORK.
# Swapping to BAML, raw Anthropic API, etc. = rewrite this file only.

from agents import Agent, Runner, ModelSettings   # openai-agents SDK

from webresearch.pipeline.step import AgentStep
from webresearch.context import WorkflowContext

async def execute(
    step: AgentStep,
    prompt: str,
    context: WorkflowContext,
) -> object:
    output_type = (
        step.output_type
        if step.strict_schema
        else AgentOutputSchema(step.output_type, strict_json_schema=False)
    )
    agent = Agent(
        name=step.name,
        instructions=step.prompt,
        tools=step.tools,
        output_type=output_type,
        model_settings=ModelSettings(store=False),
    )
    result = await Runner.run(agent, prompt, context=context, max_turns=step.max_turns)
    return result.final_output
```

When migrating to BAML, this becomes:

```python
# future runtime_baml.py
from baml_client import b

async def execute(step: AgentStep, prompt: str, context: WorkflowContext) -> object:
    fn = getattr(b, step.name)
    return await fn(input=prompt, ...)
```

The streaming/tool-event translation currently in `events/stream.py`
(`_patch_runner_for_streaming`) also moves here, since it is framework-specific.

---

## Layer 2: `webresearch/providers/`

Raw I/O. No LLM concepts, no function_tool decorators, no docstrings for agents.
These are pure Python functions/classes called by workflow tool wrappers.

### `providers/search.py`

```python
from typing import Protocol
from pydantic import BaseModel, AwareDatetime

class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    publisher: str | None = None
    published_at: AwareDatetime | None = None

class SearchProvider(Protocol):
    id: str
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]: ...

class TavilySearchProvider:
    id = "tavily"
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]: ...

class MockSearchProvider:
    id = "mock"
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        return []

def default_search_provider() -> SearchProvider:
    match os.getenv("WEBRESEARCH_SEARCH_PROVIDER", "tavily"):
        case "tavily": return TavilySearchProvider()
        case _: return MockSearchProvider()
```

The `TavilySearchProvider` implementation is identical to the current
`tools/providers/tavily.py`. Just moved.

### `providers/fetch.py`

Direct port of `tools/fetch_url.py`. Same logic, same return type (`FetchResult`).
No `@function_tool` decorator. The decorator lives in workflow `tools.py` files.

### `providers/extract.py`

Direct port of `tools/extract_content.py`. Same logic. No decorator.

### `providers/discover.py`

Direct port of `tools/discover_urls.py`. Same logic. No decorator.

---

## Layer 3: `webresearch/context.py` (simplified)

Remove `search_provider` and `search_query_cache` — those move to `providers/` and are
injected via `PipelineState`. `WorkflowContext` becomes pure I/O state tracking only.

```python
@dataclass
class WorkflowContext:
    sources:  SourceRegistry             = field(default_factory=SourceRegistry)
    pages:    dict[str, FetchedPage]     = field(default_factory=dict)
    evidence: list[EvidenceNote]         = field(default_factory=list)
    artifacts: list[Artifact]            = field(default_factory=list)
    warnings: list[str]                  = field(default_factory=list)
    cost_usd: float                      = 0.0
    input_tokens: int                    = 0
    output_tokens: int                   = 0
```

Cost and token fields are written by `pipeline/runtime.py` after each agent call.

---

## Layer 4: `webresearch/types.py` (trimmed)

Remove `UrlsByCategory` — it is specific to `technical_due_diligence` and moves to
that workflow's `models.py`.

Everything else (`WorkflowInput`, `WorkflowResult`, `WorkflowMetadata`, `SourceRecord`,
`EvidenceNote`, `ResearchFinding`, `Depth`, `DepthPreset`, etc.) stays as the
stable contract between CLI and all workflows.

---

## Layer 5: Workflow — `workflows/deep/`

### `workflows/deep/models.py`

Move `PlanOutput`, `ResearcherOutput`, `ReviewOutput`, `GapResearchOutput`, `FinalAnswer`
here from `webresearch/agents/models.py`. These types belong to the deep workflow.

```python
class PlanOutput(BaseModel):
    questions: list[str]
    risks: list[str]
    search_strategy: str

class ResearcherOutput(BaseModel):
    summary: str
    source_ids: list[str]
    evidence_ids: list[str]
    confidence: Literal["high", "medium", "low"]

class ReviewOutput(BaseModel):
    coverage: list[Coverage]
    conflicts: list[Conflict]
    has_critical_gaps: bool
    follow_up_queries: list[str]

class GapResearchOutput(ResearcherOutput): pass

class FinalAnswer(BaseModel):
    answer_markdown: str
    findings: list[ResearchFindingRef]
    sources_cited: list[str]
    structured_data: dict[str, object] | None = None
```

### `workflows/deep/tools.py`

Wraps provider calls into tool functions with docstrings tuned for the deep research
use case. No logic — just the decorator, name, and docstring.

Workflows import `function_tool` and `ToolContext` from `webresearch.pipeline`, not
from the LLM framework directly. `pipeline/__init__.py` re-exports these so that
swapping the runtime doesn't require touching workflow tool files.

```python
from webresearch.pipeline import function_tool, ToolContext   # SDK re-exports, not framework
from webresearch.providers import fetch, search, discover

@function_tool
async def search_web_tool(ctx: ToolContext, query: str, limit: int = 10):
    """Search the web for sources relevant to the research query."""
    return await search.search_web(ctx.context, query, limit)

@function_tool
async def fetch_and_extract_tool(ctx: ToolContext, url: str, query: str | None = None):
    """Fetch a URL and return extracted text. Pass query to focus extraction."""
    return await fetch.fetch_and_extract(ctx.context, url, query)

@function_tool
async def discover_urls_tool(ctx: ToolContext, seed_url: str):
    """Expand a seed URL into high-value pages. Use before searching."""
    return await discover.discover_urls(ctx.context, seed_url)

@function_tool
async def rank_sources_tool(ctx: ToolContext, source_ids: list[str] | None = None, top_k: int = 10):
    """Rank registered sources by reliability and recency."""
    return await search.rank_sources(ctx.context, source_ids, top_k)

RESEARCH_TOOLS = [discover_urls_tool, search_web_tool, fetch_and_extract_tool, rank_sources_tool]
```

### `workflows/deep/agents.py`

Defines all agents as `AgentStep` instances. No `Runner.run()`. No `from agents import Agent`.

```python
from webresearch.pipeline.step import AgentStep
from webresearch.workflows.deep.tools import RESEARCH_TOOLS
from webresearch.workflows.deep.models import (
    PlanOutput, ResearcherOutput, ReviewOutput, GapResearchOutput, FinalAnswer
)
from importlib.resources import files

def _prompt(name: str) -> str:
    return (files("webresearch.workflows.deep") / "prompts" / name).read_text(encoding="utf-8")

planner = AgentStep(
    name="planner",
    prompt=_prompt("planner.j2"),
    output_type=PlanOutput,
)

official_researcher = AgentStep(
    name="official_researcher",
    prompt=_prompt("official.j2"),
    tools=RESEARCH_TOOLS,
    output_type=ResearcherOutput,
)

recent_researcher = AgentStep(
    name="recent_researcher",
    prompt=_prompt("recent.j2"),
    tools=RESEARCH_TOOLS,
    output_type=ResearcherOutput,
)

broad_researcher = AgentStep(
    name="broad_researcher",
    prompt=_prompt("broad.j2"),
    tools=RESEARCH_TOOLS,
    output_type=ResearcherOutput,
)

reviewer = AgentStep(
    name="reviewer",
    prompt=_prompt("reviewer.j2"),
    output_type=ReviewOutput,
)

gap_researcher = AgentStep(
    name="gap_researcher",
    prompt=_prompt("gap.j2"),
    tools=RESEARCH_TOOLS,
    output_type=GapResearchOutput,
)

output_writer = AgentStep(
    name="output",
    prompt=_prompt("output.j2"),
    output_type=FinalAnswer,
    strict_schema=False,
)

# No hooks needed on deep workflow — the Loop in pipeline.py owns the iteration logic.
```

### `workflows/deep/pipeline.py`

The sequence. One file, reads like a spec.

```python
from webresearch.pipeline.runner import Pipeline
from webresearch.pipeline.step import Parallel, Loop
from webresearch.workflows.deep import agents
from webresearch.workflows.deep.models import ReviewOutput

def _has_gaps(state) -> bool:
    review: ReviewOutput | None = state.outputs.get("reviewer")
    return review is None or review.has_critical_gaps

PIPELINE = Pipeline([
    agents.planner,
    Parallel([
        agents.official_researcher,
        agents.recent_researcher,
        agents.broad_researcher,
    ]),
    Loop(
        steps=[agents.reviewer, agents.gap_researcher],
        until=lambda state: not _has_gaps(state),
    ),
    agents.output_writer,
])
```

### `workflows/deep/workflow.py`

```python
from webresearch.workflows.deep.pipeline import PIPELINE
from webresearch.types import WorkflowInput, WorkflowResult

async def run(input: WorkflowInput) -> WorkflowResult:
    return await PIPELINE.run(input)
```

That's the entire file.

---

## Layer 6: Workflow — `workflows/technical_due_diligence/`

### `workflows/technical_due_diligence/models.py` (extended)

Add `UrlsByCategory` here (moved from `webresearch/types.py`):

```python
class UrlsByCategory(BaseModel):
    docs:      list[str] = []
    api:       list[str] = []
    changelog: list[str] = []
    security:  list[str] = []
    customers: list[str] = []
    blog:      list[str] = []
    careers:   list[str] = []
    other:     list[str] = []
```

All existing models (`IntakePlan`, `ClaimExtraction`, `EvidenceResearch`,
`TechnicalSubstanceReview`, `DiligenceGapResearch`, `SelectedPriorityUrls`,
`FinalMemoOutput`, `TechnicalDueDiligenceReport`) stay here as-is.

### `workflows/technical_due_diligence/config.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TechnicalDueDiligenceConfig:
    workflow_id: str = "technical_due_diligence"
    min_max_rounds: int = 5
    research_max_turns: int = 50
    url_selector_model: str = "gpt-4.1-mini"
    url_selector_model_env: str = "WEBRESEARCH_URL_SELECTOR_MODEL"
    url_budgets: dict[str, int] = field(default_factory=lambda: {
        "docs": 8, "api": 5, "changelog": 5, "security": 4,
        "customers": 3, "blog": 3, "careers": 2, "other": 4,
    })
    min_coverage_categories: tuple[str, ...] = ("docs", "api", "changelog", "security")

CONFIG = TechnicalDueDiligenceConfig()
```

### `workflows/technical_due_diligence/tools.py`

Same pattern as `deep/tools.py`. Docstrings tuned for due diligence context.

```python
from webresearch.pipeline import function_tool, ToolContext
from webresearch.providers import fetch, search, discover

@function_tool
async def search_web_tool(ctx: ToolContext, query: str, limit: int = 10):
    """Search the web for technical evidence. Prefer official docs, changelogs, security advisories."""
    return await search.search_web(ctx.context, query, limit)

@function_tool
async def fetch_and_extract_tool(ctx: ToolContext, url: str, query: str | None = None):
    """
    Fetch a URL and return extracted text. Pass the specific claim being investigated
    as query to focus extraction on the most relevant content.
    """
    return await fetch.fetch_and_extract(ctx.context, url, query)

@function_tool
async def discover_urls_tool(ctx: ToolContext, seed_url: str):
    """
    Discover high-value URLs from a domain: docs, API reference, changelog, security pages.
    Use this on the target company's primary domain before searching.
    """
    return await discover.discover_urls(ctx.context, seed_url)

RESEARCH_TOOLS = [search_web_tool, fetch_and_extract_tool, discover_urls_tool]
```

Note: `rank_sources_tool` is intentionally omitted here — due diligence agents navigate by
claim, not by source rank.

### `workflows/technical_due_diligence/agents.py`

All agents as `AgentStep`. Hooks drive the gap loop entirely from state.

```python
from webresearch.pipeline.step import AgentStep
from webresearch.pipeline.hooks import HookSignal, PreHook, PostHook
from webresearch.pipeline.state import PipelineState
from webresearch.workflows.technical_due_diligence.tools import RESEARCH_TOOLS
from webresearch.workflows.technical_due_diligence.models import (
    IntakePlan, ClaimExtraction, EvidenceResearch,
    TechnicalSubstanceReview, DiligenceGapResearch,
    SelectedPriorityUrls, FinalMemoOutput,
)
from webresearch.workflows.technical_due_diligence.config import CONFIG

def _prompt(name: str) -> str:
    return (files("webresearch.workflows.technical_due_diligence") / "prompts" / name).read_text()

intake_planner = AgentStep(
    name="intake_planner",
    prompt=_prompt("intake_planner.j2"),
    tools=RESEARCH_TOOLS,
    output_type=IntakePlan,
    max_turns=CONFIG.research_max_turns,
)

url_selector = AgentStep(
    name="url_selector",
    prompt=_prompt("url_selector.j2"),
    output_type=SelectedPriorityUrls,
    pre_hook=_url_selector_pre_hook,
    post_hook=_url_selector_post_hook,
)

claim_extractor = AgentStep(
    name="claim_extractor",
    prompt=_prompt("claim_extractor.j2"),
    tools=RESEARCH_TOOLS,
    output_type=ClaimExtraction,
    max_turns=CONFIG.research_max_turns,
)

evidence_researcher = AgentStep(
    name="evidence_researcher",
    prompt=_prompt("evidence_researcher.j2"),
    tools=RESEARCH_TOOLS,
    output_type=EvidenceResearch,
    max_turns=CONFIG.research_max_turns,
)

technical_substance_reviewer = AgentStep(
    name="technical_substance_reviewer",
    prompt=_prompt("technical_substance_reviewer.j2"),
    output_type=TechnicalSubstanceReview,
)

gap_researcher = AgentStep(
    name="gap_researcher",
    prompt=_prompt("gap_researcher.j2"),
    tools=RESEARCH_TOOLS,
    output_type=DiligenceGapResearch,
    max_turns=CONFIG.research_max_turns,
    post_hook=_gap_post_hook,   # merges gap results into reviewer state for next iteration
)

final_memo = AgentStep(
    name="final_memo",
    prompt=_prompt("final_memo.j2"),
    output_type=FinalMemoOutput,
)

# --- hooks ---

async def _url_selector_pre_hook(state: PipelineState) -> HookSignal:
    plan: IntakePlan | None = state.outputs.get("intake_planner")
    if not plan or not _has_any_urls(plan.evidence_urls_by_category):
        return HookSignal.SKIP
    return HookSignal.CONTINUE

async def _url_selector_post_hook(state: PipelineState) -> HookSignal:
    # Validate + budget-cap selected URLs. Falls back to deterministic slice if invalid.
    plan = state.outputs.get("intake_planner")
    selected = state.outputs.get("url_selector")
    if plan and selected:
        state.outputs["url_selector"] = _validated_priority_urls(
            plan.evidence_urls_by_category, selected
        )
    return HookSignal.CONTINUE

async def _gap_post_hook(state: PipelineState) -> HookSignal:
    # Merge gap results into reviewer output so the Loop's `until` condition
    # sees updated unresolved_claims on the next iteration.
    review = state.outputs.get("technical_substance_reviewer")
    gap = state.outputs.get("gap_researcher")
    if review and gap:
        state.outputs["technical_substance_reviewer"] = _merge_gap_into_review(review, gap)
    return HookSignal.CONTINUE

# Loop iteration logic lives in pipeline.py (_all_resolved).
# Hooks here are only for url_selector validation and gap result merging.
```

The `_validated_priority_urls`, `_merge_gap_into_review`, and `_has_any_urls` helpers move
from `workflow.py` into `agents.py` (or a private `_url_utils.py`). They are unchanged
in logic — just relocated.

### `workflows/technical_due_diligence/pipeline.py`

```python
from webresearch.pipeline.runner import Pipeline
from webresearch.pipeline.step import Loop
from webresearch.workflows.technical_due_diligence import agents
from webresearch.workflows.technical_due_diligence.models import TechnicalSubstanceReview

def _all_resolved(state) -> bool:
    review: TechnicalSubstanceReview | None = state.outputs.get("technical_substance_reviewer")
    return review is not None and not review.unresolved_claims

PIPELINE = Pipeline(
    steps=[
        agents.intake_planner,
        agents.url_selector,        # pre_hook skips if no URLs found
        agents.claim_extractor,
        agents.evidence_researcher,
        Loop(
            steps=[agents.technical_substance_reviewer, agents.gap_researcher],
            until=_all_resolved,
        ),
        agents.final_memo,
    ],
    final_output_key="final_memo",
)
```

Future: fan out evidence_researcher per claim — one line change:

```python
from webresearch.pipeline.step import Loop, FanOut
from webresearch.workflows.technical_due_diligence.models import ClaimExtraction

PIPELINE = Pipeline(
    steps=[
        agents.intake_planner,
        agents.url_selector,
        agents.claim_extractor,
        FanOut(
            agents.evidence_researcher,
            over=lambda state: state.outputs["claim_extractor"].claims,
        ),
        Loop(
            steps=[agents.technical_substance_reviewer, agents.gap_researcher],
            until=_all_resolved,
        ),
        agents.final_memo,
    ],
    final_output_key="final_memo",
)
```

### `workflows/technical_due_diligence/workflow.py`

```python
from webresearch.workflows.technical_due_diligence.pipeline import PIPELINE
from webresearch.types import WorkflowInput, WorkflowResult

async def run(input: WorkflowInput) -> WorkflowResult:
    return await PIPELINE.run(input)
```

---

## Layer 7: CLI — workflow discovery via entry points

Replace the hardcoded `WORKFLOWS` dict in `workflows/registry.py` with Python entry points.
Any installed package can register a workflow by adding to its `pyproject.toml`:

```toml
[project.entry-points."webresearch.workflows"]
deep                    = "webresearch.workflows.deep.workflow:run"
technical_due_diligence = "webresearch.workflows.technical_due_diligence.workflow:run"
```

CLI discovery in `cli/list_cmd.py` and `cli/run_cmd.py`:

```python
from importlib.metadata import entry_points

def load_workflows() -> dict[str, Callable]:
    eps = entry_points(group="webresearch.workflows")
    return {ep.name: ep.load() for ep in eps}
```

`workflows/registry.py` is deleted entirely.

---

## Cost and Token Tracking

Cost flows through two channels simultaneously: state (for the final result) and events
(for real-time CLI display). Both are written by the pipeline, never by workflows.

### Flow

```
runtime.py executes LLM call
    │
    ▼
RunResult contains usage (input_tokens, output_tokens, model)
    │
    ├─▶ runtime.py returns (output, usage) to pipeline/runner.py
    │
    ├─▶ runner accumulates into state.context
    │     context.input_tokens  += usage.input_tokens
    │     context.output_tokens += usage.output_tokens
    │     context.cost_usd      += _cost(usage, model)
    │
    └─▶ runner emits StepCompleted with per-step cost
          StepCompleted(step="claim_extractor", cost_usd=0.012, tokens=1500)
```

### `events/types.py` — extend `StepCompleted`

```python
class StepCompleted(EventModel):
    kind: Literal["step_completed"] = "step_completed"
    step: str
    cost_usd: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
```

### `pipeline/runtime.py` — return usage alongside output

```python
@dataclass
class ExecutionResult:
    output: object
    input_tokens: int
    output_tokens: int
    model: str

async def execute(step: AgentStep, prompt: str, context: WorkflowContext) -> ExecutionResult:
    ...
    result = await Runner.run(agent, prompt, ...)
    usage = result.raw_responses[-1].usage   # OpenAI Agents SDK
    return ExecutionResult(
        output=result.final_output,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        model=agent.model or "default",
    )
```

### `pipeline/runtime.py` — cost calculation

Cost calculation lives here because it is model- and framework-specific.
When swapping to BAML or another runtime, pricing updates in one place.

```python
_COST_PER_1M = {
    "gpt-4.1":       {"input": 2.00,  "output": 8.00},
    "gpt-4.1-mini":  {"input": 0.40,  "output": 1.60},
    "o4-mini":       {"input": 1.10,  "output": 4.40},
}

def _cost(input_tokens: int, output_tokens: int, model: str) -> float:
    rates = _COST_PER_1M.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
```

### `pipeline/runner.py` — accumulate and emit

```python
exec_result = await runtime.execute(step, prompt, state.context)
state.outputs[step.name] = exec_result.output
state.context.input_tokens  += exec_result.input_tokens
state.context.output_tokens += exec_result.output_tokens
state.context.cost_usd      += runtime._cost(
    exec_result.input_tokens, exec_result.output_tokens, exec_result.model
)
await emit_event(StepCompleted(
    run_id=state.run_id,
    step=step.name,
    cost_usd=...,
    input_tokens=exec_result.input_tokens,
    output_tokens=exec_result.output_tokens,
))
```

### Final result

`_build_result` reads accumulated totals from `state.context`:

```python
metadata=WorkflowMetadata(
    cost_usd=state.context.cost_usd,
    tokens=TokenUsage(
        input_tokens=state.context.input_tokens,
        output_tokens=state.context.output_tokens,
        total_tokens=state.context.input_tokens + state.context.output_tokens,
    ),
)
```

The CLI `ProgressRenderer` displays running cost per step from `StepCompleted` events
without waiting for the full run to finish.

---

## Events — what moves, what stays

`events/types.py` — keep as-is. All event types are correct and SDK-level.

`events/step.py` — keep as-is. `step()`, `emit_event()`, etc. are used by
`pipeline/runner.py`, not directly by workflows.

`events/stream.py` — split:
- `stream_workflow()` and `run_workflow()` stay here (CLI uses these)
- `_patch_runner_for_streaming()` and `_translate_sdk_event()` move into
  `pipeline/runtime.py` — they are framework-specific

---

## Prompt Context — Jinja2 Templates

Prompts are Jinja2 templates. The template itself declares what it needs from state.
The runner renders it — no Python code builds prompt strings, no `_stage_prompt()`,
no `research_prompt()`, no `output_prompt()`. All of those helpers are deleted.

### How it works

`pipeline/runner.py` renders each step's template with the full `PipelineState` as context:

```python
from jinja2 import Environment, BaseLoader

_jinja = Environment(loader=BaseLoader(), undefined=jinja2.Undefined)
_jinja.filters["tojson"] = lambda v, indent=None: json.dumps(_jsonable(v), indent=indent)

def _build_prompt(step: AgentStep, state: PipelineState, item: object = None) -> str:
    return _jinja.from_string(step.prompt).render(
        input=state.input,        # WorkflowInput — query, instructions, depth
        outputs=state.outputs,    # dict[step_name → output_type instance]
        item=item,                # FanOut only — the specific element being processed
    )
```

Template variables available in every prompt:
- `{{ input.query }}` — the original research query
- `{{ input.instructions }}` — optional user instructions
- `{{ input.depth.preset }}` — quick / standard / deep
- `{{ outputs.step_name }}` — output of any prior step by name
- `{{ outputs.step_name.field }}` — specific field from a prior step's output
- `{{ item }}` — FanOut only: the element this agent instance is processing

### Sequential step example

```jinja
{# prompts/evidence_researcher.j2 #}
Query: {{ input.query }}
{% if input.instructions %}Instructions: {{ input.instructions }}{% endif %}

Research plan:
{{ outputs.intake_planner | tojson(indent=2) }}

Claims to investigate:
{{ outputs.claim_extractor.claims | tojson(indent=2) }}

URLs already read:
{{ outputs.url_selector | tojson(indent=2) }}
```

### Parallel step example

Each agent picks only what it needs — same `outputs` passed to all:

```jinja
{# prompts/official_researcher.j2 #}
Focus on official sources: documentation, company blog, press releases.
Query: {{ input.query }}
Plan: {{ outputs.planner | tojson(indent=2) }}
```

```jinja
{# prompts/recent_researcher.j2 #}
Focus on sources from the last 6 months only.
Query: {{ input.query }}
Plan: {{ outputs.planner | tojson(indent=2) }}
```

### FanOut step example

`item` is the specific claim this instance is researching:

```jinja
{# prompts/evidence_researcher.j2 — fan-out version #}
Investigate this specific claim:
{{ item | tojson(indent=2) }}

Overall query: {{ input.query }}
Target company: {{ outputs.intake_planner.target }}
High-value URLs to check: {{ outputs.url_selector.docs | tojson }}
```

### What is deleted

- `workflows/shared/state.py` — `research_prompt()`, `review_prompt()`, `gap_prompt()`,
  `output_prompt()` all gone
- `technical_due_diligence/workflow.py` — `_stage_prompt()`, `_input_prompt()` all gone
- No Python code anywhere builds a prompt string

### Dependency

Add `jinja2` to `pyproject.toml` dependencies (it is already a transitive dep of many
packages but should be declared explicitly).

---

## `WorkflowResult` construction

`pipeline/runner.py` builds `WorkflowResult` from `PipelineState` after all steps complete.
It replaces `workflows/shared/result.py`.

```python
def _build_result(state: PipelineState, workflow_id: str) -> WorkflowResult:
    final: FinalAnswer = state.outputs["output"]   # or "final_memo" for due diligence
    return WorkflowResult(
        answer_markdown=final.answer_markdown,
        structured_data=...,
        summary=...,
        findings=...,
        sources=list(state.context.sources.list()),
        evidence=list(state.context.evidence),
        artifacts=list(state.context.artifacts),
        warnings=[*state.warnings, *state.context.warnings],
        metadata=WorkflowMetadata(
            run_id=state.run_id,
            workflow_id=workflow_id,
            started_at=state.started_at,
            finished_at=datetime.now(UTC),
            cost_usd=state.context.cost_usd,
            tokens=TokenUsage(
                input_tokens=state.context.input_tokens,
                output_tokens=state.context.output_tokens,
                total_tokens=state.context.input_tokens + state.context.output_tokens,
            ),
        ),
    )
```

The `final_output_key` (e.g. `"output"` vs `"final_memo"`) is a `Pipeline` constructor
parameter:

```python
PIPELINE = Pipeline(steps=[...], final_output_key="final_memo")
```

---

## Implementation Order

Do this in phases so the project is always runnable after each phase.

### Phase 1 — Build SDK internals, nothing breaks yet

1. Add `jinja2` to `pyproject.toml` dependencies
2. Create `webresearch/providers/` by copying from `tools/` (no deletes yet)
3. Create `webresearch/pipeline/hooks.py`
4. Create `webresearch/pipeline/state.py`
5. Create `webresearch/pipeline/step.py`
6. Create `webresearch/pipeline/runtime.py` (wraps existing `Runner.run`)
7. Create `webresearch/pipeline/runner.py` (Pipeline class + Jinja `_build_prompt`)
8. Add tests for Pipeline with mock steps — verify template rendering for sequential,
   Parallel, and FanOut cases

### Phase 2 — Migrate `deep` workflow

1. Create `workflows/deep/models.py` (from `agents/models.py`)
2. Create `workflows/deep/tools.py`
3. Create `workflows/deep/agents.py`
4. Create `workflows/deep/pipeline.py`
5. Rewrite `workflows/deep/workflow.py` to `return await PIPELINE.run(input)`
6. Verify `webresearch run deep "test query"` still works

### Phase 3 — Migrate `technical_due_diligence` workflow

1. Extend `workflows/technical_due_diligence/models.py` with `UrlsByCategory`
2. Create `workflows/technical_due_diligence/config.py`
3. Create `workflows/technical_due_diligence/tools.py`
4. Create `workflows/technical_due_diligence/agents.py` (port hooks from workflow.py)
5. Create `workflows/technical_due_diligence/pipeline.py`
6. Rewrite `workflows/technical_due_diligence/workflow.py`
7. Verify workflow produces identical output to current version

### Phase 4 — Delete old code

1. Delete `webresearch/agents/`
2. Delete `webresearch/tools/`
3. Delete `webresearch/workflows/quick/`
4. Delete `webresearch/workflows/standard/`
5. Delete `webresearch/workflows/shared/`
6. Delete `webresearch/workflows/registry.py`
7. Remove `UrlsByCategory` from `webresearch/types.py`
8. Remove search_provider from `webresearch/context.py`
9. Move streaming patch from `events/stream.py` to `pipeline/runtime.py`

### Phase 5 — Entry point discovery

1. Add `[project.entry-points."webresearch.workflows"]` to `pyproject.toml`
2. Rewrite CLI discovery to use `importlib.metadata.entry_points`
3. Verify `webresearch list` and `webresearch run` still work

---

## What Each Layer Is Responsible For

| Layer            | Owns                                                     | Never touches                          |
|------------------|----------------------------------------------------------|----------------------------------------|
| `providers/`     | Raw HTTP calls, API responses, HTML extraction           | LLM concepts, tools, prompts           |
| `pipeline/`      | Step execution, hooks, loops, events, cost, result build | Workflow logic, prompt content         |
| `pipeline/runtime.py` | LLM framework imports, agent construction          | Everything else                        |
| `events/`        | Event types, sink, streaming to CLI                      | Workflow logic                         |
| `context.py`     | Page cache, source registry, evidence list               | Execution, providers, LLM              |
| `types.py`       | WorkflowInput / WorkflowResult contract                  | Workflow-specific types                |
| `workflow/*/tools.py`  | function_tool wrappers + workflow-tuned docstrings | Provider implementation                |
| `workflow/*/agents.py` | AgentStep definitions + hook logic               | LLM framework, Runner                  |
| `workflow/*/pipeline.py` | Step sequence declaration                      | Hook logic, execution                  |
| `workflow/*/workflow.py` | `run()` entry point                            | Everything (delegates to Pipeline)     |
| `cli/`           | Workflow discovery, input parsing, output formatting     | Workflow internals                     |
