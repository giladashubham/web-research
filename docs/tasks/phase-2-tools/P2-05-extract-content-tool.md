# P2-05 — `extract_content` tool

**Phase:** 2 — Tools
**Depends on:** P2-04, P1-05, P3-01

## Goal
Turn raw HTML (from cache) into clean text the agent can read. Emits an Evidence artifact.

## Scope
- `@function_tool async def extract_content(ctx, url: str, query: str | None = None) -> ExtractResult`.
- Pull body from cache (populated by `fetch_url`); if absent, return failure.
- Use `trafilatura.extract(...)` (add `trafilatura` to deps).
- Truncate to 8000 chars by default; report truncation in the result.
- Cache extractions in namespace `extractions` keyed by normalized URL.
- Append an `EvidenceArtifact` to `ctx.context.artifacts` tied to the `SourceRecord` ID.
- Tool result echoes char count + truncation flag.

## Out of scope
- LLM-driven summarization — that's the agent's job.
- PDFs, non-HTML content — defer.

## Files
- `webresearch/tools/extract_content.py`
- `tests/tools/test_extract_content.py`
- `tests/fixtures/html/*.html`

## Acceptance
- [ ] Extracts main content from a typical article HTML fixture.
- [ ] Skips boilerplate (nav, footer).
- [ ] Cache hit on second call.
- [ ] No body in cache → returns failure result with reason; no artifact emitted.
- [ ] Truncation reported when content exceeds 8000 chars.
