# P3-01 — Install `openai-agents` + smoke test

**Phase:** 3 — Agents
**Depends on:** P1-01

## Goal
Add the SDK and confirm imports work.

## Scope
- Add `openai-agents` to runtime deps. Pin a known-good version.
- Smoke test:
  - `from agents import Agent, Runner, function_tool, RunContextWrapper`.
  - Construct a trivial `Agent(name="smoke", instructions="say hi")` (no model call).
- Document required env var: `OPENAI_API_KEY` for live runs; not needed for unit tests using a mock.

## Out of scope
- Pydantic output models (P3-02).
- Agent factories (P3-03).

## Files
- `pyproject.toml` (deps update)
- `tests/agents/test_smoke.py`

## Acceptance
- [ ] `uv sync` resolves with the SDK.
- [ ] Smoke test imports compile and the trivial Agent constructs without error.
- [ ] Tracing dashboard env var documented in README.
