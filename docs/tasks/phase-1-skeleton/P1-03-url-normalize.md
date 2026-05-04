# P1-03 — URL normalization

**Phase:** 1 — Skeleton & primitives
**Depends on:** P1-01

## Goal
One function that turns a raw URL into a canonical form for dedup and cache keys.

## Scope
- `normalize_url(raw: str) -> str`.
- Lowercase scheme + host; reject non-http(s).
- Strip default ports (`:80` for http, `:443` for https).
- Drop fragment (`#...`).
- Strip common tracking params: `utm_*`, `gclid`, `fbclid`, `mc_*`, `ref`, `ref_src`, `_hsenc`, `_hsmi`.
- Sort remaining query params alphabetically.
- Trim trailing slash on path (preserve `/` for root).

## Out of scope
- IDN/punycode beyond what `urllib.parse` does.

## Files
- `webresearch/sources/url_normalize.py`
- `tests/sources/test_url_normalize.py`

## Acceptance
- [ ] Tracking-param URLs collapse to the same form.
- [ ] Trailing-slash and fragment differences collapse.
- [ ] Different schemes/hosts do **not** collapse.
- [ ] `mailto:` / `javascript:` / `file:` raise `ValueError`.
