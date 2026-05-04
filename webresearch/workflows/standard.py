from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from agents import Runner

from webresearch.agents.gap import gap_researcher_agent
from webresearch.agents.output import output_agent
from webresearch.agents.planner import planner_agent
from webresearch.agents.researchers import (
    broad_researcher_agent,
    official_researcher_agent,
    recent_researcher_agent,
)
from webresearch.agents.reviewer import reviewer_agent
from webresearch.context import WorkflowContext
from webresearch.workflows.result import build_result
from webresearch.workflows.state import WorkflowState

if TYPE_CHECKING:
    from webresearch.agents.models import (
        FinalAnswer,
        GapResearchOutput,
        PlanOutput,
        ResearcherOutput,
        ReviewOutput,
    )
    from webresearch.types import WorkflowInput, WorkflowResult


async def run_standard(input: WorkflowInput) -> WorkflowResult:
    ctx = WorkflowContext()
    state = WorkflowState(
        input=input,
        depth=input.depth,
        run_id=f"run_{uuid4().hex}",
        started_at=datetime.now(UTC),
    )

    plan = await Runner.run(planner_agent(), input.query, context=ctx)
    state.plan = cast("PlanOutput", plan.final_output)

    official, recent, broad = await asyncio.gather(
        Runner.run(official_researcher_agent(), state.research_prompt(), context=ctx),
        Runner.run(recent_researcher_agent(), state.research_prompt(), context=ctx),
        Runner.run(broad_researcher_agent(), state.research_prompt(), context=ctx),
    )
    state.research = [
        cast("ResearcherOutput", official.final_output),
        cast("ResearcherOutput", recent.final_output),
        cast("ResearcherOutput", broad.final_output),
    ]

    review = await Runner.run(reviewer_agent(), state.review_prompt(), context=ctx)
    state.review = cast("ReviewOutput", review.final_output)

    round_index = 0
    while state.review.has_critical_gaps and round_index < state.depth.max_rounds:
        gap = await Runner.run(gap_researcher_agent(), state.gap_prompt(), context=ctx)
        state.gaps.append(cast("GapResearchOutput", gap.final_output))
        review = await Runner.run(reviewer_agent(), state.review_prompt(), context=ctx)
        state.review = cast("ReviewOutput", review.final_output)
        round_index += 1

    final = await Runner.run(
        output_agent(input.output_schema),
        state.output_prompt(),
        context=ctx,
    )
    state.final = cast("FinalAnswer", final.final_output)

    return build_result(state, ctx)
