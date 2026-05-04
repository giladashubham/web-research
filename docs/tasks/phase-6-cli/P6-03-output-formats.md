# P6-03 — JSON + Markdown output

**Phase:** 6 — CLI
**Depends on:** P6-02

## Goal
Two formats for the run result, written to stdout or `--out`.

## Scope
- `--format json` (default): write `WorkflowResult.model_dump_json(indent=2)`.
- `--format md`: write `result.answer_markdown`, then `## Sources` (numbered, with URLs), then `## Warnings` (if any).
- `--out PATH`: write to a file; otherwise stdout.
- Exit codes:
  - `0` — workflow completed (warnings allowed).
  - `1` — `WorkflowFailed`.
  - `2` — usage error.
  - `3` — IO error (can't read workflows dir, can't write `--out`).

## Out of scope
- HTML, PDF — defer.

## Files
- `webresearch/cli/formats.py`
- `tests/cli/test_formats.py`

## Acceptance
- [ ] JSON output round-trips through `WorkflowResult.model_validate_json(...)`.
- [ ] Markdown output starts with the answer and ends with sources + warnings.
- [ ] `--out` writes the file with no trailing junk.
- [ ] Each exit code is exercised by a corresponding test scenario.
