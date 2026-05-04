# P2-01 — `SearchProvider` protocol + `MockSearchProvider`

**Phase:** 2 — Tools
**Depends on:** P1-02

## Goal
Internal protocol all search backends implement, plus a deterministic mock for tests.

## Scope
- `SearchProvider` Protocol:
  ```python
  class SearchProvider(Protocol):
      id: str
      async def search(self, query: str, limit: int = 10) -> list[SearchResult]: ...
  ```
- `SearchResult` Pydantic model: `url`, `title`, `snippet`, `publisher?`, `published_at?`.
- `MockSearchProvider({ fixtures })`:
  - `fixtures: dict[str, list[SearchResult]]`.
  - Exact match first; substring fallback if no exact key matches.
  - Tiny `await asyncio.sleep(0.01)` so async paths exercise.
- Default fixture set covering the prompts used in the standard workflow.

The provider lives under `webresearch/tools/providers/` — internal, not part of the public package surface.

## Out of scope
- Tavily provider (P2-02).

## Files
- `webresearch/tools/providers/search_provider.py`
- `webresearch/tools/providers/mock.py`
- `webresearch/tools/providers/fixtures/default.py`
- `tests/tools/providers/test_mock.py`

## Acceptance
- [ ] Same query returns identical results across runs.
- [ ] Substring fallback works when no exact key match.
- [ ] Default fixtures load without errors.
