# P9-01 — Live LLM integration test (gated)

**Phase:** 9 — Polish
**Depends on:** P4-01, P5-02, P6-02

## Goal
End-to-end smoke against real OpenAI + Tavily, gated by env so CI doesn't burn credits.

## Scope
- A single test in `tests/integration/test_live_standard.py`.
- Skipped unless `LIVE_LLM=1` and both `OPENAI_API_KEY` and `TAVILY_API_KEY` are set (use pytest's `skipif`).
- Query: a stable, low-controversy research question (e.g. "What is the current Node.js LTS version?").
- Assertions:
  - `WorkflowCompleted` reached without `WorkflowFailed`.
  - `result.answer_markdown` non-empty and mentions a Node.js version.
  - At least 2 sources, all with `fetch_status = "success"`.
  - At least 1 evidence note.
  - Wall-clock under 2 minutes.
- An npm-equivalent script: `uv run pytest -m live` (configure pytest marker `live`).

## Out of scope
- Determinism — temperature is non-zero, that's expected.
- Cost benchmarks.

## Files
- `tests/integration/test_live_standard.py`
- `pyproject.toml`  (pytest marker config)

## Acceptance
- [ ] Skips cleanly when env vars are missing.
- [ ] Passes on a fresh machine with valid keys.
- [ ] Run shows up in the OpenAI tracing dashboard (manual verify on first run).
