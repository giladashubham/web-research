from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from webresearch.types import (
    AnswerArtifact,
    Depth,
    DepthPreset,
    EvidenceNote,
    ResearchFinding,
    SourceRecord,
    WorkflowInput,
    WorkflowMetadata,
    WorkflowResult,
)


def test_depth_presets_return_expected_config():
    quick = Depth.for_preset("quick")
    standard = Depth.for_preset("standard")
    deep = Depth.for_preset("deep")

    assert quick.preset == DepthPreset.QUICK
    assert quick.max_rounds == 0
    assert quick.max_sources == 5
    assert quick.tool_budgets.search_queries == 2

    assert standard.preset == DepthPreset.STANDARD
    assert standard.max_rounds == 1
    assert standard.max_sources == 10
    assert standard.tool_budgets.search_queries == 5

    assert deep.preset == DepthPreset.DEEP
    assert deep.max_rounds == 3
    assert deep.max_sources == 20
    assert deep.tool_budgets.search_queries == 10


def test_workflow_input_requires_query():
    with pytest.raises(ValidationError):
        WorkflowInput.model_validate({})


def test_workflow_result_round_trips_from_dump():
    now = datetime(2026, 5, 4, 7, 30, tzinfo=UTC)
    result = WorkflowResult(
        answer_markdown="Answer",
        structured_data={"status": "ok"},
        summary="Summary",
        findings=[
            ResearchFinding(
                id="finding-1",
                claim="The claim is supported.",
                evidence_ids=["evidence-1"],
                confidence=0.9,
            )
        ],
        sources=[
            SourceRecord(
                id="source-1",
                url="https://example.com/report",
                title="Report",
                accessed_at=now,
                is_primary=True,
            )
        ],
        evidence=[
            EvidenceNote(
                id="evidence-1",
                source_id="source-1",
                quote="Short quote",
                note="Supports the claim.",
            )
        ],
        artifacts=[
            AnswerArtifact(
                id="artifact-1",
                title="Final answer",
                created_at=now,
                answer_markdown="Answer",
            )
        ],
        warnings=["Limited source coverage."],
        metadata=WorkflowMetadata(
            run_id="run-1",
            workflow_id="standard",
            started_at=now,
            finished_at=now,
            cost_usd=0.01,
        ),
    )

    assert WorkflowResult.model_validate(result.model_dump()) == result
