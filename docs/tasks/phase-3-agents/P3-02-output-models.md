# P3-02 — Pydantic output models

**Phase:** 3 — Agents
**Depends on:** P3-01, P1-02

## Goal
Define the `output_type` Pydantic models each agent uses. These double as the inter-step contract.

## Scope
- `PlanOutput` — `questions: list[str]`, `risks: list[str]`, `search_strategy: str`.
- `ResearcherOutput` — `summary: str`, `source_ids: list[str]`, `evidence_ids: list[str]`, `confidence: Literal["high","medium","low"]`.
- `Coverage`, `Conflict` — supporting models.
- `ReviewOutput` — `coverage: list[Coverage]`, `conflicts: list[Conflict]`, `has_critical_gaps: bool`, `follow_up_queries: list[str]`.
- `GapResearchOutput` — same shape as `ResearcherOutput`.
- `FinalAnswer` — `answer_markdown: str`, `findings: list[ResearchFindingRef]`, `sources_cited: list[str]`, `structured_data: dict | None`.

All models live in one place and are imported by the agent factories.

## Out of scope
- Validation against user-supplied `output_schema` — that lives in the output agent's logic; raw dict is acceptable for `structured_data` here.

## Files
- `webresearch/agents/models.py`
- `tests/agents/test_models.py`

## Acceptance
- [ ] All models validate via `mypy --strict`.
- [ ] Round-trip: `Model.model_validate(m.model_dump())` is identical for each.
- [ ] `ReviewOutput.has_critical_gaps` is a plain `bool` (no string variants), so the loop check is unambiguous.
