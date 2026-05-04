# P7-05 — Cancellation + Settings

**Phase:** 7 — TUI
**Depends on:** P7-01, P7-03

## Goal
Two small but necessary screens.

## Scope
**Cancellation:**
- On Run screen, `Ctrl-C` (or `q`) opens a confirm dialog: "Cancel running workflow? y/N".
- Confirming cancels the underlying `stream_workflow` task.
- After cancellation, the timeline marks the in-flight step as "cancelled" and offers `r` to return Home.

**Settings:**
- From Home, `s` pushes `SettingsScreen`.
- Read-only listing:
  - Resolved model (from env var or default).
  - Provider env vars: `OPENAI_API_KEY` ✓/✗, `TAVILY_API_KEY` ✓/✗.
  - Workflow registry counts.
- No editing — env vars are set in the user's shell.

## Out of scope
- Persisting settings.

## Files
- `webresearch/tui/widgets/confirm_cancel.py`
- `webresearch/tui/screens/settings.py`
- `tests/tui/test_confirm_cancel.py`
- `tests/tui/test_settings_screen.py`

## Acceptance
- [ ] Confirming cancellation cancels within ≤ 1s.
- [ ] Cancelled run shows the cancelled state in the timeline.
- [ ] Settings reports correct ✓/✗ for env vars (verified with monkeypatched env).
- [ ] Settings lists workflow counts.
