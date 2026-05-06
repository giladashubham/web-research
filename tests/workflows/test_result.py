from __future__ import annotations

from datetime import UTC, datetime

import pytest

from webresearch.agents.models import FinalAnswer, ResearcherOutput, ResearchFindingRef
from webresearch.context import WorkflowContext
from webresearch.types import EvidenceNote, SourceInput, WorkflowInput
from webresearch.workflows.shared.result import build_result
from webresearch.workflows.shared.state import WorkflowState


def _state(input_: WorkflowInput) -> WorkflowState:
    return WorkflowState(
        input=input_,
        depth=input_.depth,
        run_id="run_1",
        started_at=datetime(2026, 5, 4, tzinfo=UTC),
        research=[
            ResearcherOutput(
                summary="Research summary",
                source_ids=["src_1"],
                evidence_ids=["ev_1"],
                confidence="medium",
            )
        ],
        final=FinalAnswer(
            answer_markdown="Answer",
            findings=[
                ResearchFindingRef(
                    claim="Claim",
                    evidence_ids=["ev_1"],
                    source_ids=["src_1"],
                    confidence="high",
                )
            ],
            sources_cited=["src_1"],
            structured_data={"status": "ok"},
        ),
    )


def test_build_result_populates_every_workflow_result_field() -> None:
    ctx = WorkflowContext()
    ctx.sources.add(SourceInput(url="https://example.com/report", title="Report"))
    ctx.evidence.append(EvidenceNote(id="ev_1", source_id="src_1", note="Evidence"))
    ctx.warnings.append("context warning")
    state = _state(WorkflowInput(query="Query"))
    state.add_warning("state warning")

    result = build_result(state, ctx)

    assert result.answer_markdown == "Answer"
    assert result.summary == "Research summary"
    assert result.findings[0].claim == "Claim"
    assert result.sources[0].id == "src_1"
    assert result.evidence[0].id == "ev_1"
    assert result.artifacts == []
    assert result.warnings == ["state warning", "context warning"]
    assert result.metadata.run_id == "run_1"
    assert result.metadata.workflow_id == "standard"


def test_structured_output_validates_and_sets_structured_data() -> None:
    state = _state(
        WorkflowInput(
            query="Query",
            output_schema={
                "type": "object",
                "properties": {"status": {"type": "string"}},
                "required": ["status"],
            },
        )
    )

    result = build_result(state, WorkflowContext())

    assert result.structured_data == {"status": "ok"}
    assert result.warnings == []


def test_invalid_structured_output_moves_to_raw_and_adds_warning() -> None:
    state = _state(
        WorkflowInput(
            query="Query",
            output_schema={
                "type": "object",
                "properties": {"status": {"type": "integer"}},
                "required": ["status"],
            },
        )
    )

    result = build_result(state, WorkflowContext())

    assert result.structured_data is None
    assert result.warnings


def test_missing_output_schema_leaves_structured_data_undefined() -> None:
    result = build_result(_state(WorkflowInput(query="Query")), WorkflowContext())

    assert result.structured_data is None


def test_build_result_requires_final_output() -> None:
    state = WorkflowState(
        input=WorkflowInput(query="Query"),
        depth=WorkflowInput(query="Query").depth,
        run_id="run_1",
        started_at=datetime(2026, 5, 4, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="final output"):
        build_result(state, WorkflowContext())
