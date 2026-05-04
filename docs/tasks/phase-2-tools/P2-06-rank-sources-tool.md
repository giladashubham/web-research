# P2-06 — `rank_sources` tool

**Phase:** 2 — Tools
**Depends on:** P1-04, P3-01

## Goal
Heuristic ranking of registered sources so the reviewer/output agents can prioritize without re-implementing it in prompts.

## Scope
- `@function_tool async def rank_sources(ctx, source_ids: list[str] | None = None, top_k: int = 10) -> RankedSources`.
- Score each source by:
  - Domain reliability heuristic (`*.gov`, `*.edu`, vendor-official > major news > blogs > unknown).
  - Recency: parse `published_at` if present, else `retrieved_at`.
  - Whether an `EvidenceArtifact` exists for the source.
- Returns sources in ranked order with scores.
- Optional `source_ids` filter; otherwise rank everything in the registry.

## Out of scope
- Cross-encoder rerank, embeddings.

## Files
- `webresearch/tools/rank_sources.py`
- `webresearch/tools/heuristics/domain_reliability.py`
- `tests/tools/test_rank_sources.py`

## Acceptance
- [ ] `.gov` / `.edu` outrank blogs by default.
- [ ] More-recent sources outrank older ones, all else equal.
- [ ] `top_k` caps the output.
- [ ] Empty source list returns an empty result, no error.
