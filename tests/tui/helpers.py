from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from webresearch.agents.models import FinalAnswer
from webresearch.context import WorkflowContext
from webresearch.events.step import emit_output_text_delta, emit_step_skipped, step
from webresearch.types import WorkflowInput, WorkflowResult
from webresearch.workflows.result import build_result
from webresearch.workflows.state import WorkflowState


def make_result(query: str = "query") -> WorkflowResult:
    input_ = WorkflowInput(query=query)
    state = WorkflowState(
        input=input_,
        depth=input_.depth,
        run_id="run_tui",
        started_at=datetime(2026, 5, 4, tzinfo=UTC),
        final=FinalAnswer(
            answer_markdown="Answer",
            findings=[],
            sources_cited=[],
            structured_data=None,
        ),
    )
    return build_result(state, WorkflowContext())


async def fake_workflow(input_: WorkflowInput) -> WorkflowResult:
    async with step("planner"):
        await asyncio.sleep(0)
    await emit_step_skipped("gap", "none")
    async with step("output"):
        await emit_output_text_delta("Answer")
    return make_result(input_.query)
