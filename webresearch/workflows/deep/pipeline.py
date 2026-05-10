from __future__ import annotations

from typing import TYPE_CHECKING

from webresearch.pipeline.runner import Pipeline
from webresearch.pipeline.step import Loop, Parallel
from webresearch.workflows.deep import agents
from webresearch.workflows.deep.config import CONFIG

if TYPE_CHECKING:
    from webresearch.pipeline.state import PipelineState
    from webresearch.workflows.deep.models import ReviewOutput


def _has_gaps(state: PipelineState) -> bool:
    review: ReviewOutput | None = state.outputs.get("reviewer")
    if review is None:
        return True
    return review.has_critical_gaps


PIPELINE = Pipeline(
    steps=[
        agents.planner,
        Parallel(
            [
                agents.official_researcher,
                agents.recent_researcher,
                agents.broad_researcher,
            ]
        ),
        Loop(
            steps=[agents.reviewer, agents.gap_researcher],
            until=lambda state: not _has_gaps(state),
        ),
        agents.output_writer,
    ],
    final_output_key="output",
    workflow_id=CONFIG.workflow_id,
)
