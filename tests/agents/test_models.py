from __future__ import annotations

import pytest
from pydantic import ValidationError

from webresearch.agents.models import (
    Conflict,
    Coverage,
    FinalAnswer,
    GapResearchOutput,
    PlanOutput,
    ResearcherOutput,
    ResearchFindingRef,
    ReviewOutput,
)


@pytest.mark.parametrize(
    "model",
    [
        PlanOutput(
            questions=["What happened?"],
            risks=["Sparse sources"],
            search_strategy="Search official and recent sources.",
        ),
        ResearcherOutput(
            summary="Summary",
            source_ids=["src_1"],
            evidence_ids=["ev_1"],
            confidence="medium",
        ),
        Coverage(topic="scope", status="covered", notes="Complete"),
        Conflict(claim="Conflicting claim", source_ids=["src_1", "src_2"], notes="Disagrees"),
        ReviewOutput(
            coverage=[Coverage(topic="scope", status="partial", notes="Needs more")],
            conflicts=[],
            has_critical_gaps=False,
            follow_up_queries=["follow up"],
        ),
        GapResearchOutput(
            summary="Gap summary",
            source_ids=["src_2"],
            evidence_ids=["ev_2"],
            confidence="low",
        ),
        ResearchFindingRef(
            claim="Claim",
            evidence_ids=["ev_1"],
            source_ids=["src_1"],
            confidence="high",
        ),
        FinalAnswer(
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
    ],
)
def test_agent_output_models_round_trip(model) -> None:
    assert type(model).model_validate(model.model_dump()) == model


def test_review_output_has_critical_gaps_is_plain_bool() -> None:
    with pytest.raises(ValidationError):
        ReviewOutput.model_validate(
            {
                "coverage": [],
                "conflicts": [],
                "has_critical_gaps": "false",
                "follow_up_queries": [],
            }
        )
