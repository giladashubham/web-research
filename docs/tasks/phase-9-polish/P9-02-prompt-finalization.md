# P9-02 — Prompt finalization + golden tests

**Phase:** 9 — Polish
**Depends on:** P3-03, P4-01, P3-04

## Goal
Replace the placeholder prompt files from P3-03 with real prompts that honor the boundaries from the plan, and lock them in with golden tests via the mock model.

## Scope
- Write final content for:
  - `prompts/planner.md` — produces `PlanOutput`; no tools; restates query, decomposes into questions, identifies risks.
  - `prompts/official.md` — biases toward official sources; uses search/fetch/extract; emits `ResearcherOutput`.
  - `prompts/recent.md` — biases toward recency; same shape.
  - `prompts/broad.md` — community/expert blogs; avoids re-fetching; same shape.
  - `prompts/reviewer.md` — produces `ReviewOutput`; sets `has_critical_gaps` correctly; no tools.
  - `prompts/gap.md` — runs only the queries from the latest review's `follow_up_queries`.
  - `prompts/output.md` — produces `FinalAnswer`; cites only registered source IDs; surfaces gap warnings; no tools by default.
- Boundary tests with the mock model: feed each agent its prompt and a canned context, assert the agent's tool calls (or lack thereof) match the boundary.
- Each prompt < ~80 lines; concrete > abstract; show one short example inline where it helps.

## Out of scope
- Live LLM tuning — once these pass golden tests, P9-01 catches any drift end-to-end.

## Files
- `prompts/{planner,official,recent,broad,reviewer,gap,output}.md`
- `tests/agents/test_prompt_boundaries.py`

## Acceptance
- [ ] Each agent's mock-model boundary test passes.
- [ ] Planner / reviewer / output emit zero tool calls.
- [ ] Researchers emit at least one `search_web` call and never an undeclared tool.
- [ ] Output cites only source IDs present in the test's `SourceRegistry`.
