# P8-01 — `quick.py` workflow

**Phase:** 8 — Variants
**Depends on:** P4-01

## Goal
Minimal workflow for fast lookups. No reviewer, no gap loop, fewer parallel researchers.

## Scope
- `webresearch/workflows/quick.py` exporting `run_quick(input)`:
  - Planner.
  - Research (parallel): Official + Broad (skip Recent — keeps it lean).
  - Output.
- Smaller per-tool budgets via the `quick` depth preset (max_rounds=0, fewer tool calls allowed in researcher prompt context — no enforcement on the SDK side, just smaller `input.max_sources` and shorter prompts).
- Register as `"quick"` in `workflows/registry.py`.

## Out of scope
- Reviewer / gap loop.

## Files
- `webresearch/workflows/quick.py`
- modify `webresearch/workflows/registry.py`
- `tests/workflows/test_quick.py`

## Acceptance
- [ ] Loads via `workflows.registry["quick"]`.
- [ ] Runs end-to-end against the mock model in < 5s.
- [ ] Returns a populated `WorkflowResult` without warnings about gaps.
