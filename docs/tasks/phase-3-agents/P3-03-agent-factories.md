# P3-03 — Agent factories + prompt loading

**Phase:** 3 — Agents
**Depends on:** P3-01, P3-02, P2-03..P2-06

## Goal
One factory per agent role. Each returns a configured `Agent`. Prompts loaded from markdown files.

## Scope
- `webresearch/agents/prompts.py`:
  - `load_prompt(name: str) -> str` reads from `prompts/{name}` relative to the package root, cached at import.
- Factories:
  - `planner_agent()` — instructions + `output_type=PlanOutput`, no tools.
  - `official_researcher_agent()`, `recent_researcher_agent()`, `broad_researcher_agent()` — instructions + tools + `output_type=ResearcherOutput`.
  - `reviewer_agent()` — instructions + `output_type=ReviewOutput`, no tools.
  - `gap_researcher_agent()` — instructions + tools + `output_type=GapResearchOutput`.
  - `output_agent(output_schema: dict | None = None)` — instructions + `output_type=FinalAnswer`, no tools by default.
- Tools list per agent comes from the plan's tool-access table.
- Empty-but-syntactically-valid prompt files ship with this task; final prompt content lands in P9-02.

## Out of scope
- The actual prompt text (P9-02 finalizes; placeholders are fine here).

## Files
- `webresearch/agents/prompts.py`
- `webresearch/agents/planner.py`
- `webresearch/agents/researchers.py`
- `webresearch/agents/reviewer.py`
- `webresearch/agents/gap.py`
- `webresearch/agents/output.py`
- `prompts/{planner,official,recent,broad,reviewer,gap,output}.md`  (placeholders)
- `tests/agents/test_factories.py`

## Acceptance
- [ ] Each factory returns a fresh `Agent` with the expected name, prompt, and tools.
- [ ] Output types match P3-02.
- [ ] Two consecutive calls return distinct `Agent` instances (no caching).
- [ ] Missing prompt file raises a clear `FileNotFoundError` naming the resolved path.
