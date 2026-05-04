# P3-04 — Mock-model harness

**Phase:** 3 — Agents
**Depends on:** P3-01, P3-03

## Goal
Drive `Runner.run` against a scripted fake model so workflow + agent tests run offline, fast, and deterministic.

## Scope
- `MockModel` implementing the SDK's model interface with a scripted response queue:
  - Accepts a list of canned responses (text + tool calls + final structured outputs).
  - Each `Runner.run(...)` call pops the next scripted exchange.
  - Asserts the agent's tool calls match the script (helps catch regressions).
- Scripts are dicts loaded from `tests/fixtures/scripts/*.json` so they can be edited without recompiling.
- A `run_with_mock(agent, input, script)` helper for tests.

## Out of scope
- Real LLM tests (P9-01).

## Files
- `tests/conftest.py`  (fixtures)
- `tests/_helpers/mock_model.py`
- `tests/_helpers/scripts/standard_happy_path.json`
- `tests/agents/test_mock_model.py`

## Acceptance
- [ ] Scripted exchange drives `Runner.run` to a final output without network.
- [ ] Mismatched tool call → test fails with a clear diff.
- [ ] One `MockModel` instance is reusable across multiple `Runner.run` calls in a single test.
