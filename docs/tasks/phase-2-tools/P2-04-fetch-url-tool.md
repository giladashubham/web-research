# P2-04 — `fetch_url` tool

**Phase:** 2 — Tools
**Depends on:** P1-03, P1-04, P1-05, P3-01

## Goal
HTTP GET with caching, polite headers, and source-registry integration.

## Scope
- `@function_tool async def fetch_url(ctx, url: str) -> FetchResult`.
- Steps:
  1. `normalize_url(url)`.
  2. Cache check (namespace `fetches`, key = normalized URL).
  3. On miss: `httpx.AsyncClient.get(...)` with timeout 30s and `User-Agent: webresearch-agent/0.1`.
  4. Reject non-2xx; reject content-types not in `text/html`, `application/xhtml+xml`, `text/plain`, `application/json`.
  5. Body size limit 5 MB (truncate + warn).
  6. Cache body + content-type.
  7. Update `SourceRecord.fetch_status` via `sources.mark_fetch_status(...)`.
- `FetchResult` reports byte size and content-type; the body itself stays in cache (read by `extract_content`).
- Failures attach a warning, return `FetchResult(status="failed", reason=...)`. **Do not raise.**

## Out of scope
- robots.txt, headless browser fallback.

## Files
- `webresearch/tools/fetch_url.py`
- `tests/tools/test_fetch_url.py`  # respx for httpx mocking

## Acceptance
- [ ] Successful fetch caches body + content-type.
- [ ] Cache hit on second call (no network).
- [ ] 4xx/5xx → `fetch_status = "failed"` + warning, no raise.
- [ ] Disallowed content-type → `fetch_status = "blocked"` + warning.
- [ ] Body over size limit → truncated with warning.
