# P6-01 — Typer app + `list` command

**Phase:** 6 — CLI
**Depends on:** P4-01, P5-02

## Goal
The CLI entrypoint and `webresearch list`.

## Scope
- Add `typer` to deps.
- `webresearch/cli/__init__.py` exports `app = typer.Typer()`.
- `pyproject.toml` adds the entrypoint: `webresearch = "webresearch.cli:app"`.
- Global flags (parent app): `--workflows-dir` (currently a no-op since workflows are Python-defined; kept for symmetry and future user workflows), `--no-cache`.
- `webresearch list`:
  - Prints a table: `id`, `name`, `description`.
  - Reads from `webresearch.workflows.registry`.
  - `--format json` outputs JSON instead of the table.
  - Exit 0 when at least one workflow is registered.

## Out of scope
- `run` (P6-02), output formats (P6-03), TUI launch (P7).

## Files
- `pyproject.toml`  (add typer + entrypoint)
- `webresearch/cli/__init__.py`
- `webresearch/cli/list_cmd.py`
- `tests/cli/test_list_cmd.py`

## Acceptance
- [ ] `webresearch --help` shows subcommands.
- [ ] `webresearch list` prints a non-empty table after Phase 4.
- [ ] `webresearch list --format json` round-trips through `json.loads`.
