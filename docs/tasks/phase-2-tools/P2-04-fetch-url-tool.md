# P2-04 — `fetch_url` tool

**Phase:** 2 — Tools
**Depends on:** P1-03, P1-04, P3-01

## Goal
HTTP GET with polite headers and source-registry integration.

## Scope
- `@function_tool async def fetch_url(ctx, url: str) -> FetchResult`.
- Steps:
  1. `normalize_url(url)`.
  2. `httpx.AsyncClient.get(...)` with timeout 30s and `User-Agent: webresearch-agent/0.1`.
  3. Reject non-2xx; reject content-types not in `text/html`, `application/xhtml+xml`, `text/plain`, `application/json`.
  4. Body size limit 5 MB (truncate + warn).
  5. Stash body + content-type on the in-memory `ctx.context.pages: dict[str, FetchedPage]` (keyed by normalized URL) so `extract_content` can read it later in the same run.
  6. Update `SourceRecord.fetch_status` via `sources.mark_fetch_status(...)`.
- `FetchResult` reports byte size and content-type; the body stays on `ctx.context.pages` (read by `extract_content`).
- Failures attach a warning, return `FetchResult(status="failed", reason=...)`. **Do not raise.**

> No persistent cache in V1 — every call hits the network. A file-backed cache will be reintroduced in a later phase.

## Out of scope
- robots.txt, headless browser fallback.
- Persistent caching across runs.

## Files
- `webresearch/tools/fetch_url.py`
- `tests/tools/test_fetch_url.py`  # respx for httpx mocking

## Acceptance
- [ ] Successful fetch records body + content-type on `ctx.context.pages`.
- [ ] 4xx/5xx → `fetch_status = "failed"` + warning, no raise.
- [ ] Disallowed content-type → `fetch_status = "blocked"` + warning.
- [ ] Body over size limit → truncated with warning.
