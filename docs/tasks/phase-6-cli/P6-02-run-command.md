# P6-02 — `run` command + stderr progress

**Phase:** 6 — CLI
**Depends on:** P6-01, P5-02

## Goal
`webresearch run` subcommand with live progress on stderr.

## Scope
- Usage: `webresearch run [WORKFLOW] QUERY [--depth ...] [--instructions ...] [--max-sources ...] [--out PATH] [--format json|md] [--quiet]`.
- Default workflow id: `standard`.
- Resolve workflow function from `workflows.registry`; unknown id → exit 1 with a clear error.
- Build `WorkflowInput` from flags.
- Stream via `stream_workflow(...)` and render progress on stderr (P6-02 responsibility):
  - `▶  <step>` on `StepStarted`.
  - `✓  <step>  (Ns)` on `StepCompleted`.
  - `–  <step>  (skipped)` on `StepSkipped`.
  - `   · <tool>` on `ToolStarted`/`ToolCompleted` (dim).
  - `! <message>` on `Warning` (yellow).
  - Live deltas during output step: write directly to stderr without prefix.
- `--quiet` silences progress.
- Color only on TTY.

## Out of scope
- The actual `--out` / `--format` writing — P6-03.

## Files
- `webresearch/cli/run_cmd.py`
- `webresearch/cli/progress.py`
- `tests/cli/test_run_cmd.py`
- `tests/cli/test_progress.py`

## Acceptance
- [ ] Runs end-to-end against the mock model from a unit test.
- [ ] Stderr shows the expected glyph sequence; stdout receives only the result.
- [ ] `--quiet` produces no progress on stderr.
- [ ] No ANSI when stderr is not a TTY.
