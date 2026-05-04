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
from webresearch.events.step import (
    current_run_id,
    emit_loop_iteration,
    emit_output_text_delta,
    emit_step_skipped,
    step,
)
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
    run_id = current_run_id()
    state = WorkflowState(
        input=input,
        depth=input.depth,
        run_id=run_id if run_id != "run_uninstrumented" else f"run_{uuid4().hex}",
        started_at=datetime.now(UTC),
    )

    async with step("planner"):
        plan = await Runner.run(planner_agent(), input.query, context=ctx)
        state.plan = cast("PlanOutput", plan.final_output)

    async with step("research"):
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

    async with step("reviewer"):
        review = await Runner.run(reviewer_agent(), state.review_prompt(), context=ctx)
        state.review = cast("ReviewOutput", review.final_output)

    round_index = 0
    while state.review.has_critical_gaps and round_index < state.depth.max_rounds:
        round_index += 1
        await emit_loop_iteration("gap", round_index)
        async with step("gap"):
            gap = await Runner.run(gap_researcher_agent(), state.gap_prompt(), context=ctx)
            state.gaps.append(cast("GapResearchOutput", gap.final_output))
        async with step("reviewer"):
            review = await Runner.run(reviewer_agent(), state.review_prompt(), context=ctx)
            state.review = cast("ReviewOutput", review.final_output)

    if state.review is not None and not state.review.has_critical_gaps:
        await emit_step_skipped("gap", "Reviewer reported no critical gaps")

    async with step("output"):
        final = await Runner.run(
            output_agent(input.output_schema),
            state.output_prompt(),
            context=ctx,
        )
        state.final = cast("FinalAnswer", final.final_output)
        await emit_output_text_delta(state.final.answer_markdown)

    return build_result(state, ctx)
