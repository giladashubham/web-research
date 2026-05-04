# P7-01 — Textual app shell + screen routing

**Phase:** 7 — TUI
**Depends on:** P5-02

## Goal
Bootstrap a Textual `App` with screen routing.

## Scope
- Add `textual` to deps.
- `webresearch/tui/app.py`: `WebResearchApp(textual.App)`:
  - On launch, push `HomeScreen` (P7-02).
  - Global key bindings: `q` quit (with confirm if a run is active), `?` help overlay.
  - `webresearch tui` Typer subcommand launches the app (also: bare `webresearch` with no args launches the TUI).
- Screen base: a thin `WorkflowAwareScreen` that holds the loaded workflow registry, the configured `WorkflowContext` factory, and exposes a helper to start a streamed run.

## Out of scope
- Specific screens (P7-02..P7-04).

## Files
- `webresearch/tui/__init__.py`
- `webresearch/tui/app.py`
- `webresearch/tui/screen_base.py`
- `webresearch/cli/__init__.py`  (add `webresearch tui`)
- `tests/tui/test_app.py`  (textual `Pilot` for snapshot/interaction)

## Acceptance
- [ ] `webresearch tui` opens without crashing on a TTY.
- [ ] `q` triggers confirm dialog when a run is active, exits immediately otherwise.
- [ ] `?` toggles a help overlay.
