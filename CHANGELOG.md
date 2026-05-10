# Changelog

## 0.1.0 (unreleased)

### Major

- **Workflow extraction** — Built-in workflows moved to separate pip packages:
  - `webresearch-deep` — Deep research workflow.
  - `webresearch-tdd` — Technical due diligence (coming soon).
  - `webresearch-company-news` — Company news monitoring (coming soon).
  
  Core `webresearch` is now a pure SDK: pipeline engine, providers, events,
  and entry-point discovery. The CLI has been removed — workflow packages
  provide their own CLI. Workflows are installed as optional packages.

- **CLI removed** — `webresearch/cli/` and the `typer` dependency removed from core.
  Workflow packages (e.g., `webresearch-deep`) own their own CLI.

- **Metadata entry points** — New `webresearch.workflows.metadata` entry-point group for
  workflow descriptions. `load_workflow_entries()` discovers metadata from installed
  packages with a fallback for workflows without metadata.

- **Architecture rewrite** — The codebase was restructured following the plan in
  `ARCHITECTURE_PLAN.md`. Key changes:

  - **New `webresearch/pipeline/` layer**: `AgentStep`, `Parallel`, `FanOut`, `Loop` step
    types with `Pipeline` orchestrator, Jinja2 prompt rendering, hook system, cost
    tracking, and event emission. The only file importing the LLM framework is
    `pipeline/runtime.py`.

  - **New `webresearch/providers/` layer**: Raw I/O adapters for search (Tavily + Mock),
    HTTP fetch, HTML extraction (trafilatura), and URL discovery. No LLM concepts,
    no function_tool decorators.

  - **Self-contained workflows**: Each workflow (`deep`, `technical_due_diligence`) has its
    own `agents.py`, `tools.py`, `pipeline.py`, `models.py`, `config.py`, and `prompts/`.
    No shared workflow infrastructure.

  - **Entry-point discovery**: Workflows are registered in `pyproject.toml` under
    `[project.entry-points."webresearch.workflows"]`. The CLI discovers them via
    `importlib.metadata`.

  - **Jinja2 templates**: All prompts are `.j2` files rendered with the full pipeline
    state. No Python code builds prompt strings.

  - **Simplified `context.py`**: `WorkflowContext` is pure I/O state tracking (pages,
    sources, evidence, cost). `search_provider` and `query_cache` removed.

  - **Deleted**: `webresearch/agents/`, `webresearch/tools/`,
    `webresearch/workflows/quick/`, `webresearch/workflows/standard/`,
    `webresearch/workflows/shared/`, `webresearch/workflows/registry.py`.

### Added

- Jinja2 prompt rendering in pipeline runner.
- Event-based cost tracking per step.
- `FanOut` step type for parallel processing over dynamic collections.
- `Loop` step type with `until` condition and `max_iterations`.
- Pre-hook/Post-hook system with SKIP and REPEAT signals.
- `UrlsByCategory` moved to `providers/discover.py` and `tdd/models.py`.
- Comprehensive test suite for pipeline execution, hooks, loops, fan-out, cost tracking.

### Changed

- CLI now discovers workflows via entry points rather than hardcoded registry.
- `technical_due_diligence` workflow uses Pipeline-based execution with hook-driven gap loop.
- `deep` workflow uses Pipeline with `Parallel` and `Loop` steps.
- All prompt files renamed from `.md` to `.j2`.

### Removed

- `webresearch/agents/` — absorbed into workflow-specific `agents.py` files.
- `webresearch/tools/` — replaced by `providers/` + per-workflow `tools.py`.
- `webresearch/workflows/quick/` and `webresearch/workflows/standard/`.
- `webresearch/workflows/shared/` — replaced by pipeline SDK.
- `webresearch/workflows/registry.py` — replaced by entry points.
