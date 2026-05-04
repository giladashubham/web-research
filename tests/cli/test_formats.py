from __future__ import annotations

from datetime import UTC, datetime

from webresearch.agents.models import FinalAnswer
from webresearch.cli.formats import format_result, write_output
from webresearch.context import WorkflowContext
from webresearch.types import SourceInput, WorkflowInput, WorkflowResult
from webresearch.workflows.result import build_result
from webresearch.workflows.state import WorkflowState


def _result() -> WorkflowResult:
    ctx = WorkflowContext()
    ctx.sources.add(SourceInput(url="https://example.com", title="Example"))
    state = WorkflowState(
        input=WorkflowInput(query="query"),
        depth=WorkflowInput(query="query").depth,
        run_id="run_1",
        started_at=datetime(2026, 5, 4, tzinfo=UTC),
        final=FinalAnswer(
            answer_markdown="Answer",
            findings=[],
            sources_cited=["src_1"],
            structured_data=None,
        ),
    )
    result = build_result(state, ctx)
    result.warnings.append("warning")
    return result


def test_json_output_round_trips() -> None:
    content = format_result(_result(), "json")

    assert WorkflowResult.model_validate_json(content).answer_markdown == "Answer"


def test_markdown_output_starts_with_answer_and_ends_with_sources_and_warnings() -> None:
    content = format_result(_result(), "md")

    assert content.startswith("Answer\n")
    assert "## Sources" in content
    assert "1. Example - https://example.com" in content
    assert content.endswith("- warning")


def test_out_writes_file_with_no_trailing_junk(tmp_path) -> None:
    path = tmp_path / "answer.md"

    write_output("content", str(path))

    assert path.read_text() == "content"
