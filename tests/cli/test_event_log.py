from __future__ import annotations

import json
from datetime import UTC, datetime

from typer.testing import CliRunner

from webresearch.cli import app
from webresearch.events.step import step
from webresearch.types import TokenUsage, WorkflowInput, WorkflowMetadata, WorkflowResult


async def fake_workflow(_input: WorkflowInput) -> WorkflowResult:
    async with step("planner"):
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


def test_run_creates_default_event_log(monkeypatch, tmp_path) -> None:
    def mock_load():
        return {"fake": fake_workflow}

    monkeypatch.setattr("webresearch.cli.run_cmd.load_workflows", mock_load)

    # Change current directory to tmp_path to check default log location
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["run", "query", "fake", "--quiet"])

    assert result.exit_code == 0
    logs_dir = tmp_path / ".web-research" / "logs"
    assert logs_dir.exists()

    log_files = list(logs_dir.glob("*.jsonc"))
    assert len(log_files) == 1

    data = json.loads(
        "\n".join(
            [
                line
                for line in log_files[0].read_text().splitlines()
                if not line.strip().startswith("//")
            ]
        )
    )
    assert data["query"] == "query"
    assert any(e["kind"] == "workflow_started" for e in data["events"])


def test_run_with_explicit_events_out_file(monkeypatch, tmp_path) -> None:
    def mock_load():
        return {"fake": fake_workflow}

    monkeypatch.setattr("webresearch.cli.run_cmd.load_workflows", mock_load)

    log_path = tmp_path / "my-run.jsonc"

    result = CliRunner().invoke(
        app, ["run", "query", "fake", "--quiet", "--events-out", str(log_path)]
    )

    assert result.exit_code == 0
    assert log_path.exists()

    data = json.loads(
        "\n".join(
            [
                line
                for line in log_path.read_text().splitlines()
                if not line.strip().startswith("//")
            ]
        )
    )
    assert data["run_id"].startswith("run_")


def test_run_with_explicit_events_out_dir(monkeypatch, tmp_path) -> None:
    def mock_load():
        return {"fake": fake_workflow}

    monkeypatch.setattr("webresearch.cli.run_cmd.load_workflows", mock_load)

    log_dir = tmp_path / "custom-logs"

    result = CliRunner().invoke(
        app, ["run", "query", "fake", "--quiet", "--events-out", str(log_dir)]
    )

    assert result.exit_code == 0
    assert log_dir.exists()
    assert len(list(log_dir.glob("*.jsonc"))) == 1
