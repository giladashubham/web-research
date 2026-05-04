# P2-02 — `TavilySearchProvider`

**Phase:** 2 — Tools
**Depends on:** P2-01, P1-05

## Goal
Real search backend hitting Tavily's API.

## Scope
- `TavilySearchProvider(api_key: str | None = None, cache: WorkflowCache | None = None)`:
  - Reads `TAVILY_API_KEY` from env if not passed.
  - Uses `httpx.AsyncClient` to POST `https://api.tavily.com/search` with `{ query, max_results, search_depth: "basic" }`.
  - Maps response → `list[SearchResult]`.
  - Cache key: `f"{normalize(query)}::{limit}"`, namespace `searches/tavily`.
  - On non-2xx: raise `SearchProviderError(status, body_excerpt)`.
- Add `httpx` to deps.

## Out of scope
- `search_depth: "advanced"` — defer.

## Files
- `webresearch/tools/providers/tavily.py`
- `webresearch/tools/providers/errors.py`  # `SearchProviderError`
- `tests/tools/providers/test_tavily.py`  # uses `respx` or similar httpx mocking

## Acceptance
- [ ] Successful response maps to `list[SearchResult]`.
- [ ] Cache hit on second identical call (no network).
- [ ] HTTP error raises `SearchProviderError`.
- [ ] Cancellation via task cancel terminates the in-flight request.
