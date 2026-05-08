from __future__ import annotations

import asyncio

from webresearch.events.step import emit_output_text_delta, emit_step_completed, step
from webresearch.events.stream import stream_workflow
from webresearch.events.types import OutputTextDelta, WorkflowCompleted
from webresearch.types import WorkflowInput


async def _ordered_workflow(_: WorkflowInput) -> object:
    async with step("planner"):
        pass
    await emit_step_completed("planner")
    async with step("output"):
        await emit_output_text_delta("hello")
        await emit_output_text_delta(" world")
    await emit_step_completed("output")
    return object()


async def test_events_arrive_in_emitted_order() -> None:
    events = [event async for event in stream_workflow(_ordered_workflow, WorkflowInput(query="q"))]

    assert [event.kind for event in events] == [
        "workflow_started",
        "step_started",
        "step_completed",
        "step_started",
        "output_text_delta",
        "output_text_delta",
        "step_completed",
        "workflow_completed",
    ]


async def test_iterator_ends_cleanly_on_workflow_completion() -> None:
    events = [event async for event in stream_workflow(_ordered_workflow, WorkflowInput(query="q"))]

    assert isinstance(events[-1], WorkflowCompleted)


async def test_cancelling_iterator_cancels_workflow_task_within_one_second() -> None:
    cancelled = asyncio.Event()

    async def slow_workflow(_: WorkflowInput) -> object:
        try:
            async with step("planner"):
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.set()
            raise
        return object()

    stream = stream_workflow(slow_workflow, WorkflowInput(query="q"))
    first = await anext(stream)
    assert first.kind == "workflow_started"

    await stream.aclose()

    await asyncio.wait_for(cancelled.wait(), timeout=1)


async def test_output_text_deltas_only_arrive_during_output_step_and_reproduce_answer() -> None:
    events = [event async for event in stream_workflow(_ordered_workflow, WorkflowInput(query="q"))]

    active_step: str | None = None
    deltas: list[str] = []
    for event in events:
        if event.kind == "step_started":
            active_step = event.step
        elif event.kind == "step_completed":
            active_step = None
        elif isinstance(event, OutputTextDelta):
            assert active_step == "output"
            deltas.append(event.delta)

    assert "".join(deltas) == "hello world"


async def test_failed_workflow_emits_failed_event() -> None:
    async def failing_workflow(_: WorkflowInput) -> object:
        async with step("planner"):
            msg = "boom"
            raise RuntimeError(msg)

    events = [event async for event in stream_workflow(failing_workflow, WorkflowInput(query="q"))]

    assert events[-1].kind == "workflow_failed"
