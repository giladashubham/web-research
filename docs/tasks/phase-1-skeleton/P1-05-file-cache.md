# P1-05 — File cache + Null cache

**Phase:** 1 — Skeleton & primitives
**Depends on:** P1-01

## Goal
File-backed key→JSON cache used by tools, plus a no-op variant for `--no-cache`.

## Scope
- `WorkflowCache` Protocol with async `get(namespace, key) -> T | None` and `set(namespace, key, value)`.
- `FileCache(root_dir: Path)`:
  - File layout: `{root}/{namespace}/{sha256(key)[:40]}.json`.
  - Atomic writes (temp + rename).
  - JSON serialization via Pydantic when value is a `BaseModel`, else plain `json`.
- `NullCache` — both methods are no-ops.
- Default root: `.webresearch/cache`.

## Out of scope
- TTL, LRU, in-memory layer.

## Files
- `webresearch/cache/__init__.py`
- `webresearch/cache/file_cache.py`
- `webresearch/cache/null_cache.py`
- `tests/cache/test_file_cache.py`
- `tests/cache/test_null_cache.py`

## Acceptance
- [ ] `set` then `get` returns the same value.
- [ ] Different namespaces don't collide for the same key.
- [ ] Concurrent writes don't corrupt files (atomic temp+rename).
- [ ] `NullCache.get` always returns `None`; `set` is a no-op.
- [ ] Pydantic `BaseModel` round-trips through the cache.
