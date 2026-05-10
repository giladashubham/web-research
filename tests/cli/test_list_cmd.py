from __future__ import annotations

import json

from typer.testing import CliRunner

from webresearch.cli import app


def test_webresearch_help_shows_subcommands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "list" in result.output


def test_list_prints_non_empty_table() -> None:
    result = CliRunner().invoke(app, ["list"])

    assert result.exit_code == 0
    assert "deep" in result.output
    assert "technical_due_diligence" in result.output
    assert "description" in result.output


def test_list_json_round_trips() -> None:
    result = CliRunner().invoke(app, ["list", "--format", "json"])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    ids = {entry["id"] for entry in parsed}
    assert "deep" in ids
    assert "technical_due_diligence" in ids
    assert "company_news" in ids
