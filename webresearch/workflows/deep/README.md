# Deep Workflow

Registered as `deep`. A higher-budget, multi-lane research workflow with a review-and-gap
loop for thorough source coverage.

## Pipeline

```
planner ──────────────────────────────────────────────────
                                                            │
              ┌──────────────┬───────────────┐              │
              ▼              ▼               ▼              │
    official_researcher  recent_researcher  broad_researcher │
    (official sources,   (≤6 months,        (broad web       │
     docs, releases)      blog, news)        search)         │
              │              │               │              │
              └──────────────┴───────────────┘              │
                                                            │
                              ▼                              │
                     ┌─── reviewer ───┐                     │
                     │  (no tools)    │                     │
                     │                │                     │
                     ▼                │                     │
              has_critical_gaps?      │                     │
              YES ─► gap_researcher ──┘──► repeat loop      │
              NO  ─► output_writer ◄────── (max 2 rounds)   │
                                                            │
                              ▼                              │
                        FinalAnswer                          │
```

## Agents

| Step | Tools | Output | Notes |
|------|-------|--------|-------|
| `planner` | None | `PlanOutput` | Decomposes query into questions, risks, search strategy |
| `official_researcher` | All | `ResearcherOutput` | Prefers official domains, docs, releases, filings |
| `recent_researcher` | All | `ResearcherOutput` | Focuses on sources from last 6 months |
| `broad_researcher` | All | `ResearcherOutput` | Broad web search for diverse perspectives |
| `reviewer` | None | `ReviewOutput` | Assesses coverage, conflicts, critical gaps |
| `gap_researcher` | All | `GapResearchOutput` | Fills gaps identified by reviewer |
| `output` | None | `FinalAnswer` | Synthesises everything into final answer |

## Config

`config.py` exposes `DeepWorkflowConfig`:

| Field | Default | Description |
|-------|---------|-------------|
| `workflow_id` | `"deep"` | Workflow identifier |
| `researcher_max_turns` | `35` | Max turns for research agents |
| `max_gap_rounds` | `2` | Max gap loop iterations |
| `research_lanes` | `("official", "recent", "broad")` | Parallel research lanes |
| `reviewer_enabled` | `True` | Whether to run the reviewer step |
| `gap_loop_enabled` | `True` | Whether to run the gap loop |

## Prompts

All prompts are Jinja2 `.j2` templates rendered with the full pipeline state.
Available variables:

- `{{ input.query }}` — The original research query
- `{{ input.instructions }}` — Optional user instructions
- `{{ outputs.planner }}` — Plan output (or any prior step)
- `{{ outputs.reviewer }}` — Review output (gap loop agents)

Template: `webresearch/workflows/deep/prompts/*.j2`
