from __future__ import annotations

from datetime import UTC, datetime

from webresearch.agents.models import PlanOutput, ResearcherOutput, ReviewOutput
from webresearch.types import Depth, WorkflowInput
from webresearch.workflows.state import WorkflowState


def test_prompt_helpers_produce_stable_deterministic_strings() -> None:
    state = WorkflowState(
        input=WorkflowInput(query="What is the status?", instructions="Use primary sources."),
        depth=Depth.for_preset("standard"),
        run_id="run_1",
        started_at=datetime(2026, 5, 4, tzinfo=UTC),
        plan=PlanOutput(
            questions=["Q1"],
            risks=["R1"],
            search_strategy="Search official sources.",
        ),
        research=[
            ResearcherOutput(
                summary="Research summary",
                source_ids=["src_1"],
                evidence_ids=["ev_1"],
                confidence="high",
            )
        ],
        review=ReviewOutput(
            coverage=[],
            conflicts=[],
            has_critical_gaps=False,
            follow_up_queries=[],
        ),
    )

    assert state.research_prompt() == (
        "Query: What is the status?\n"
        "Instructions: Use primary sources.\n"
        "Plan:\n"
        "{\n"
        '  "questions": [\n'
        '    "Q1"\n'
        "  ],\n"
        '  "risks": [\n'
        '    "R1"\n'
        "  ],\n"
        '  "search_strategy": "Search official sources."\n'
        "}"
    )
    assert state.review_prompt() == state.review_prompt()
    assert state.gap_prompt() == state.gap_prompt()
    assert state.output_prompt() == state.output_prompt()
