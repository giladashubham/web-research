from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from webresearch.cli import app
from webresearch.events.step import step
from webresearch.types import (
    TokenUsage,
    WorkflowInput,
    WorkflowMetadata,
    WorkflowResult,
)

if TYPE_CHECKING:
    from webresearch.types import WorkflowInput


async def fake_workflow(_input: WorkflowInput) -> WorkflowResult:
    async with step("planner"):
        pass
    async with step("output"):
        pass
    return WorkflowResult(
        answer_markdown="Answer",
        structured_data=None,
        summary="Summary",
        findings=[],
        sources=[],
        evidence=[],
        artifacts=[],
        warnings=[],
        metadata=WorkflowMetadata(
            run_id="run_test",
            workflow_id="fake",
            started_at=datetime(2026, 5, 4, tzinfo=UTC),
            finished_at=datetime.now(UTC),
            tokens=TokenUsage(),
        ),
    )


def test_run_outputs_json_to_stdout_and_progress_to_stderr(monkeypatch) -> None:

    def mock_load():
        return {"fake": fake_workflow}

    monkeypatch.setattr("webresearch.cli.run_cmd.load_workflows", mock_load)

    result = CliRunner().invoke(app, ["run", "query", "fake"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["answer_markdown"] == "Answer"
    assert ">  " in result.output


def test_run_quiet_silences_stderr(monkeypatch) -> None:
    def mock_load():
        return {"fake": fake_workflow}

    monkeypatch.setattr("webresearch.cli.run_cmd.load_workflows", mock_load)

    result = CliRunner().invoke(app, ["run", "query", "fake", "--quiet"])

    assert result.exit_code == 0
    assert ">  " not in result.output


def test_unknown_workflow_exits_one() -> None:
    result = CliRunner().invoke(app, ["run", "query", "missing"])

    assert result.exit_code == 1
    assert "Unknown workflow" in result.output


def test_usage_error_exits_two() -> None:
    result = CliRunner().invoke(app, ["run"])

    assert result.exit_code == 2


def test_output_write_error_exits_three(monkeypatch, tmp_path) -> None:
    def mock_load():
        return {"fake": fake_workflow}

    monkeypatch.setattr("webresearch.cli.run_cmd.load_workflows", mock_load)

    result = CliRunner().invoke(
        app, ["run", "query", "fake", "--quiet", "--out", str(tmp_path)]
    )

    assert result.exit_code == 3
    assert "IO error" in result.output


def test_out_writes_file(monkeypatch, tmp_path) -> None:
    def mock_load():
        return {"fake": fake_workflow}

    monkeypatch.setattr("webresearch.cli.run_cmd.load_workflows", mock_load)
    path = tmp_path / "result.json"

    result = CliRunner().invoke(
        app, ["run", "query", "fake", "--quiet", "--out", str(path)]
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert json.loads(path.read_text())["answer_markdown"] == "Answer"
