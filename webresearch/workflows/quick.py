from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from agents import Runner

from webresearch.agents.output import output_agent
from webresearch.agents.planner import planner_agent
from webresearch.agents.researchers import broad_researcher_agent, official_researcher_agent
from webresearch.context import WorkflowContext
from webresearch.events.step import current_run_id, emit_output_text_delta, step
from webresearch.types import Depth
from webresearch.workflows.shared.result import build_result
from webresearch.workflows.shared.state import WorkflowState

if TYPE_CHECKING:
    from webresearch.agents.models import FinalAnswer, PlanOutput, ResearcherOutput
    from webresearch.types import WorkflowInput, WorkflowResult


async def run_quick(input: WorkflowInput) -> WorkflowResult:
    ctx = WorkflowContext()
    run_id = current_run_id()
    state = WorkflowState(
        input=input,
        depth=Depth.for_preset("quick"),
        run_id=run_id if run_id != "run_uninstrumented" else f"run_{uuid4().hex}",
        started_at=datetime.now(UTC),
    )

    async with step("planner"):
        plan = await Runner.run(planner_agent("quick"), input.query, context=ctx)
        state.plan = cast("PlanOutput", plan.final_output)

    async with step("research"):
        official, broad = await asyncio.gather(
            Runner.run(official_researcher_agent("quick"), state.research_prompt(), context=ctx),
            Runner.run(broad_researcher_agent("quick"), state.research_prompt(), context=ctx),
        )
        state.research = [
            cast("ResearcherOutput", official.final_output),
            cast("ResearcherOutput", broad.final_output),
        ]

    async with step("output"):
        final = await Runner.run(
            output_agent(input.output_schema, "quick"),
            state.output_prompt(),
            context=ctx,
        )
        state.final = cast("FinalAnswer", final.final_output)
        await emit_output_text_delta(state.final.answer_markdown)

    return build_result(state, ctx, workflow_id="quick")
