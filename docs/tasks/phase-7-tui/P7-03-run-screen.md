# P7-03 — Run screen (timeline + artifacts)

**Phase:** 7 — TUI
**Depends on:** P7-02, P5-02

## Goal
Live run view: step timeline on the left, artifacts + warnings on the right.

## Scope
- `RunScreen(workflow_id, input)`:
  - Subscribes to `stream_workflow(...)` for the chosen workflow.
  - Two-pane layout:
    - **Left**: `TimelineWidget` rows for each step (planner, research → sub-rows for parallel children, reviewer, gap iterations, output). Status: pending / running / done / skipped / failed. Tools currently in flight render as a faint hint under the running step.
    - **Right**: tabbed panels — `Artifacts` (list, Enter for overlay with formatted data) and `Warnings` (live-scrolling list).
  - On `WorkflowCompleted`, push `ResultScreen` (P7-04).
  - On `WorkflowFailed`, show inline error + offer retry / back.
  - `Ctrl-C` opens cancel-confirm overlay (P7-05).

## Out of scope
- Result screen (P7-04).
- Cancellation confirm dialog (P7-05).

## Files
- `webresearch/tui/screens/run.py`
- `webresearch/tui/widgets/timeline.py`
- `webresearch/tui/widgets/artifacts.py`
- `webresearch/tui/widgets/warnings.py`
- `tests/tui/test_run_screen.py`

## Acceptance
- [ ] Timeline reflects each `StepStarted` / `StepCompleted` event.
- [ ] Parallel children render indented under their group.
- [ ] Loop iterations render with their iteration number.
- [ ] Artifacts and warnings populate live.
- [ ] On completion, the screen transitions to Result.
