from __future__ import annotations

from typing import TYPE_CHECKING, Any

from webresearch.pipeline.runner import Pipeline
from webresearch.pipeline.step import Loop
from webresearch.workflows.technical_due_diligence import agents

if TYPE_CHECKING:
    from webresearch.workflows.technical_due_diligence.models import (
        TechnicalSubstanceReview,
    )


def _all_resolved(state: Any) -> bool:
    review: TechnicalSubstanceReview | None = state.outputs.get(
        "technical_substance_reviewer"
    )
    if review is None:
        return False
    return not review.unresolved_claims


PIPELINE = Pipeline(
    steps=[
        agents.intake_planner,
        agents.url_selector,
        agents.claim_extractor,
        agents.evidence_researcher,
        Loop(
            steps=[agents.technical_substance_reviewer, agents.gap_researcher],
            until=_all_resolved,
        ),
        agents.final_memo,
    ],
    final_output_key="final_memo",
    workflow_id="technical_due_diligence",
)
