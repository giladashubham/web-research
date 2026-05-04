# P1-04 — Source registry

**Phase:** 1 — Skeleton & primitives
**Depends on:** P1-02, P1-03

## Goal
Per-run registry that owns source identity, dedup, and citation IDs.

## Scope
- `SourceRegistry` (regular Python class, not Pydantic):
  - `add(input: SourceInput) -> SourceRecord` — normalizes URL, dedups, returns existing on dup; first-writer wins for `title`/`publisher`.
  - `get(source_id) -> SourceRecord | None`.
  - `get_by_url(url) -> SourceRecord | None`.
  - `list() -> Sequence[SourceRecord]` — insertion order.
  - `mark_fetch_status(source_id, status)`.
- IDs are `src_<n>` — short, stable per run.
- Optional: emits a `source_added` callback on first registration (used later by event stream P5-02).
- Constructed per run; **not** a singleton.

## Out of scope
- Persistence across runs.

## Files
- `webresearch/sources/registry.py`
- `tests/sources/test_registry.py`

## Acceptance
- [ ] Same normalized URL added twice returns the same record.
- [ ] First writer wins for title/publisher.
- [ ] Source IDs are stable and sequential within a registry instance.
- [ ] `mark_fetch_status` updates the status without losing other fields.
