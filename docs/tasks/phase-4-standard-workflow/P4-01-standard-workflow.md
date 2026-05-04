# P4-01 — `run_standard` workflow function

**Phase:** 4 — Standard workflow
**Depends on:** P3-03, P3-04, P2-03..P2-06

## Goal
Implement the standard pipeline as one async function, using the patterns from the plan.

## Scope
- `async def run_standard(input: WorkflowInput) -> WorkflowResult`.
- Build a `WorkflowContext` (registry, cache, search provider, artifacts list).
- Sequence:
  1. Planner — `await Runner.run(planner_agent(), input.query, context=ctx)`.
  2. Research — `asyncio.gather(...)` over Official / Recent / Broad researchers.
  3. Reviewer.
  4. Loop while `review.has_critical_gaps and round < depth.max_rounds`: gap researcher → reviewer.
  5. Output agent.
- Input prompts for each step are built from `WorkflowState` (P4-02) — concatenate prior outputs into the user message string.
- Returns the `WorkflowResult` built by the aggregator (P4-02).
- Uses `Runner.run` (non-streamed) here; streaming wrapper is added in Phase 5.

## Out of scope
- Streaming events (P5-02).
- Quick / Deep variants (Phase 8).

## Files
- `webresearch/workflows/__init__.py`
- `webresearch/workflows/standard.py`
- `webresearch/workflows/registry.py`  (`{"standard": run_standard}`)
- `tests/workflows/test_standard.py`  (uses `MockModel` end-to-end)

## Acceptance
- [ ] Workflow runs against the mock-model script and returns a populated `WorkflowResult`.
- [ ] Loop fires when reviewer reports gaps; skips when it doesn't.
- [ ] All researchers run concurrently (verify via timing assertions on the mock).
- [ ] Sources collected from research are deduplicated in the result.
