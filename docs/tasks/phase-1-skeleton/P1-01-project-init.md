# P1-01 — Project init

**Phase:** 1 — Skeleton & primitives
**Depends on:** none

## Goal
Stand up the Python package skeleton and **wire in the full code-quality bar from day one**. Subsequent tasks can't slip these checks.

## Scope

### Package
- `pyproject.toml` — name `webresearch`, Python ≥ 3.12, project metadata, `[project.scripts] webresearch = "webresearch.cli:app"` (target wired in P6-01).
- `uv` for deps + venv (`uv.lock` committed).
- `webresearch/__init__.py` (empty package init).
- `.gitignore`, `.python-version` (`3.12`).

### Runtime deps
None yet — added in their phases.

### Dev deps
- `pytest`, `pytest-asyncio`, `pytest-cov`, `respx` (httpx mocking).
- `ruff`, `mypy`, `pre-commit`.

### Ruff config (in `pyproject.toml`)
- Enable rule sets: `E,F,W,I,B,UP,SIM,PL,RUF,ASYNC,TCH,ANN,RET,PTH,ARG,ERA`.
- Line length 100.
- Target `py312`.
- Per-file ignores: tests may use `ANN`-relaxed (no return annotation on test funcs), `PLR2004` (magic numbers in assertions).
- `[tool.ruff.format]` enabled (replaces black).

### Mypy config (in `pyproject.toml`)
- `strict = true`.
- `disallow_any_explicit = true` for `webresearch/` (but allow it under `tests/`).
- `warn_unreachable = true`, `warn_redundant_casts = true`, `warn_unused_ignores = true`.
- `pydantic.mypy` plugin enabled.

### Pytest config
- `[tool.pytest.ini_options]`:
  - `asyncio_mode = "auto"` (no `@pytest.mark.asyncio` boilerplate).
  - Markers declared: `live` (real network).
  - `testpaths = ["tests"]`.
  - `addopts = "-q --strict-markers"`.

### Pre-commit
- `.pre-commit-config.yaml` with `ruff`, `ruff-format`, `mypy`.
- `uv run pre-commit install` in the README setup steps.

### Make-style scripts
Document in README:
- `uv run pytest` — tests.
- `uv run pytest -m live` — live LLM tests (gated).
- `uv run ruff check` / `uv run ruff format` — lint / format.
- `uv run mypy webresearch` — type-check.
- `uv run pre-commit run -a` — full local check.

### CI placeholder
- `.github/workflows/ci.yml` (or equivalent) running the four gates: ruff check, ruff format check, mypy, pytest. Gated on PR + push to main.

## Out of scope
- Any runtime deps (Agents SDK, Pydantic-other-than-via-mypy, Textual, Typer, httpx, trafilatura) — added in their phases.
- CLI/TUI scaffolding beyond the entrypoint stub.

## Files
- `pyproject.toml`
- `uv.lock`
- `webresearch/__init__.py`
- `.gitignore`
- `.python-version`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `README.md` (minimal: install, run, dev workflow)

## Acceptance
- [ ] `uv sync` resolves cleanly.
- [ ] `uv run pytest` runs (zero tests OK).
- [ ] `uv run ruff check` exits 0.
- [ ] `uv run ruff format --check` exits 0.
- [ ] `uv run mypy webresearch` exits 0 under `strict`.
- [ ] `uv run pre-commit run -a` exits 0.
- [ ] `import webresearch` works from a fresh REPL.
- [ ] CI runs all four gates on a sample PR and blocks merge if any fails.
