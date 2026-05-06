from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate

from webresearch.types import (
    ResearchFinding,
    WorkflowMetadata,
    WorkflowResult,
)

if TYPE_CHECKING:
    from webresearch.agents.models import ResearchFindingRef
    from webresearch.context import WorkflowContext
    from webresearch.workflows.shared.state import WorkflowState


def build_result(
    state: WorkflowState,
    ctx: WorkflowContext,
    workflow_id: str = "standard",
) -> WorkflowResult:
    if state.final is None:
        msg = "Cannot build WorkflowResult before final output is set"
        raise ValueError(msg)

    warnings = [*state.warnings, *ctx.warnings]
    structured_data, validation_errors = _structured_data(state)
    warnings.extend(validation_errors)

    return WorkflowResult(
        answer_markdown=state.final.answer_markdown,
        structured_data=structured_data,
        summary=_summary(state),
        findings=[
            _finding_from_ref(index, finding)
            for index, finding in enumerate(state.final.findings, 1)
        ],
        sources=list(ctx.sources.list()),
        evidence=list(ctx.evidence),
        artifacts=[*state.artifacts, *ctx.artifacts],
        warnings=warnings,
        metadata=WorkflowMetadata(
            run_id=state.run_id,
            workflow_id=workflow_id,
            started_at=state.started_at,
            finished_at=datetime.now(UTC),
        ),
    )


def _summary(state: WorkflowState) -> str:
    research_summaries = [research.summary for research in state.research]
    gap_summaries = [gap.summary for gap in state.gaps]
    summaries = [*research_summaries, *gap_summaries]
    return "\n".join(summaries) if summaries else state.final.answer_markdown if state.final else ""


def _finding_from_ref(index: int, finding: ResearchFindingRef) -> ResearchFinding:
    confidence = {"low": 0.33, "medium": 0.66, "high": 1.0}[finding.confidence]
    return ResearchFinding(
        id=f"finding_{index}",
        claim=finding.claim,
        evidence_ids=finding.evidence_ids,
        confidence=confidence,
    )


def _structured_data(
    state: WorkflowState,
) -> tuple[dict[str, object] | None, list[str]]:
    if state.input.output_schema is None:
        return None, []

    structured_data = state.final.structured_data if state.final is not None else None
    if structured_data is None:
        return None, ["Structured data was not provided"]

    try:
        validate(instance=structured_data, schema=state.input.output_schema)
    except JsonSchemaValidationError as exc:
        return None, [f"Structured data invalid: {exc.message}"]

    return structured_data, []
