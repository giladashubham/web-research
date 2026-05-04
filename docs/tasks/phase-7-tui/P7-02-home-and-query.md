# P7-02 — Home + Query screens

**Phase:** 7 — TUI
**Depends on:** P7-01

## Goal
Two entry screens: pick a workflow, then enter the query.

## Scope
- `HomeScreen`:
  - Title.
  - `ListView` (Textual built-in) of workflows with id + name + description.
  - Footer: "↑/↓ select  Enter run  s settings  q quit".
  - Enter pushes `QueryScreen(workflow_id)`.
  - `s` pushes `SettingsScreen` (P7-05).
  - Empty state when no workflows registered (shouldn't happen in v1).
- `QueryScreen(workflow_id)`:
  - `TextArea` for the query (multi-line).
  - `Input` for instructions.
  - `Select` for depth: quick / standard (default) / deep.
  - "Run" button (or Ctrl-Enter) → push `RunScreen(workflow_id, input)`.
  - Esc pops back to Home.
  - Remembers typed text in app-level state when navigating back.

## Out of scope
- Run / Result / Settings (separate tasks).

## Files
- `webresearch/tui/screens/home.py`
- `webresearch/tui/screens/query.py`
- `tests/tui/test_home_screen.py`
- `tests/tui/test_query_screen.py`

## Acceptance
- [ ] Home shows all workflows from the registry.
- [ ] Selecting a workflow pushes Query.
- [ ] Empty query disables Run.
- [ ] Esc returns to Home preserving typed text in this session.
