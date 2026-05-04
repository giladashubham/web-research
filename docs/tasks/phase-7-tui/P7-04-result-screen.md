# P7-04 — Result screen + export

**Phase:** 7 — TUI
**Depends on:** P7-03, P6-03

## Goal
Tabbed result view with answer (live deltas), sources, findings, evidence; plus export.

## Scope
- `ResultScreen(result, deltas_replay?)`:
  - Tabs: Answer | Findings | Sources | Evidence | Warnings.
  - Tab 1 — `Markdown` widget rendering `result.answer_markdown`. If the screen was constructed from a still-streaming run, render `OutputTextDelta` events live; on completion, replace with the canonical answer.
  - Tab 2 — Findings: list of claims with confidence; Enter shows linked evidence in an overlay.
  - Tab 3 — Sources: `DataTable` with id, publisher, title, URL, fetch status. Enter on a row opens an overlay with the cached extract.
  - Tab 4 — Evidence: list grouped by source; summary + relevance.
  - Tab 5 — Warnings.
  - `e` opens the Export overlay (format selector + path); reuses the formatters from P6-03.
  - On successful export, replace overlay with a 2-second toast.

## Out of scope
- Saved-runs browsing — defer.

## Files
- `webresearch/tui/screens/result.py`
- `webresearch/tui/widgets/sources_table.py`
- `webresearch/tui/widgets/export_dialog.py`
- `tests/tui/test_result_screen.py`

## Acceptance
- [ ] Each tab renders with correct data from `WorkflowResult`.
- [ ] Live deltas render before completion; canonical text replaces them on completion.
- [ ] Export writes JSON or Markdown with the same content as the CLI.
- [ ] Refusing to overwrite an existing file shows a clear error.
