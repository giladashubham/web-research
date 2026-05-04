# P8-02 — `deep.py` workflow

**Phase:** 8 — Variants
**Depends on:** P4-01

## Goal
Higher-budget workflow for thorough research.

## Scope
- `webresearch/workflows/deep.py` exporting `run_deep(input)`:
  - Same shape as standard (planner → parallel research → reviewer → gap loop → output).
  - Differences: depth preset is `deep` (`max_rounds=2`, `max_sources=20`), and the prompts injected for researchers via the prompt files are extended with extra "be thorough" guidance — but use the **same prompt files**, not separate ones. The depth-aware adjustments come from prompt template variables (introduced minimally here): the `{depth_extras}` placeholder in shared prompts is replaced with `quick`/`standard`/`deep`-specific snippets.
- Register as `"deep"` in `workflows/registry.py`.

## Out of scope
- Adding new step kinds — `deep` is a budget tweak, not a new shape.

## Files
- `webresearch/workflows/deep.py`
- modify `webresearch/workflows/registry.py`
- modify `webresearch/agents/prompts.py` (add `{depth_extras}` substitution)
- `prompts/depth_extras/{quick,standard,deep}.md`  (small inserts)
- `tests/workflows/test_deep.py`

## Acceptance
- [ ] Loads via `workflows.registry["deep"]`.
- [ ] With a mock that always reports gaps, hits `max_rounds=2` and stops.
- [ ] Uses the same step kinds as standard (no new ones).
