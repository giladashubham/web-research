from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from agents import Runner

from webresearch.events.step import current_run_id, current_step, emit_event, event_context
from webresearch.events.types import (
    OutputTextDelta,
    ToolCompleted,
    ToolStarted,
    WorkflowCompleted,
    WorkflowEvent,
    WorkflowFailed,
    WorkflowStarted,
)
from webresearch.types import WorkflowInput, WorkflowResult

WorkflowFn = Callable[[WorkflowInput], Awaitable[WorkflowResult]]


async def stream_workflow(
    workflow_fn: WorkflowFn,
    input: WorkflowInput,
) -> AsyncIterator[WorkflowEvent]:
    run_id = f"run_{uuid4().hex}"
    workflow_id = _workflow_id(workflow_fn)
    queue: asyncio.Queue[WorkflowEvent | None] = asyncio.Queue()

    async def emit(event: WorkflowEvent) -> None:
        await queue.put(event)

    async def run_background() -> None:
        await emit(WorkflowStarted(run_id=run_id, workflow_id=workflow_id))
        try:
            async with event_context(run_id, emit):
                await workflow_fn(input)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await emit(WorkflowFailed(run_id=run_id, workflow_id=workflow_id, error=str(exc)))
        else:
            await emit(WorkflowCompleted(run_id=run_id, workflow_id=workflow_id))
        finally:
            await queue.put(None)

    task: asyncio.Task[None] | None = None
    try:
        async with _patch_runner_for_streaming():
            task = asyncio.create_task(run_background())
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
    finally:
        if task is not None and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=1)
            except asyncio.CancelledError:
                pass
            except TimeoutError:
                pass


async def run_workflow(workflow_fn: WorkflowFn, input: WorkflowInput) -> WorkflowResult:
    return await workflow_fn(input)


def _workflow_id(workflow_fn: WorkflowFn) -> str:
    name = workflow_fn.__name__
    if name.startswith("run_"):
        return name.removeprefix("run_")
    return name


@asynccontextmanager
async def _patch_runner_for_streaming() -> AsyncIterator[None]:
    original_run = Runner.run
    original_run_streamed = Runner.run_streamed

    async def run_streamed_wrapper(*args: object, **kwargs: object) -> object:
        result = original_run_streamed(*args, **kwargs)  # type: ignore[arg-type]
        async for sdk_event in result.stream_events():
            await _translate_sdk_event(sdk_event)
        return result

    Runner.run = run_streamed_wrapper  # type: ignore[method-assign, assignment]
    try:
        yield
    finally:
        Runner.run = original_run  # type: ignore[method-assign]


async def _translate_sdk_event(sdk_event: object) -> None:
    step = current_step()
    if step is None:
        return

    event_name = getattr(sdk_event, "name", None)
    item = getattr(sdk_event, "item", None)
    if event_name == "tool_called":
        raw_item = getattr(item, "raw_item", None)
        await emit_event(
            ToolStarted(
                run_id=current_run_id(),
                step=step,
                tool_name=str(getattr(raw_item, "name", "tool")),
                call_id=_optional_str(getattr(raw_item, "call_id", None)),
            )
        )
    elif event_name == "tool_output":
        raw_item = getattr(item, "raw_item", None)
        await emit_event(
            ToolCompleted(
                run_id=current_run_id(),
                step=step,
                tool_name="tool",
                call_id=_optional_str(_dict_get(raw_item, "call_id")),
            )
        )

    data = getattr(sdk_event, "data", None)
    delta = _attr(data, "delta")
    if step == "output" and _attr(data, "type") == "response.output_text.delta" and delta:
        await emit_event(OutputTextDelta(run_id=current_run_id(), delta=str(delta)))


def _dict_get(value: object, key: str) -> object | None:
    if isinstance(value, dict):
        return value.get(key)
    return None


def _attr(value: object, name: str) -> object | None:
    return getattr(value, name, None)


def _optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)
