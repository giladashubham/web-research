from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from uuid import uuid4

from webresearch.events.step import event_context
from webresearch.events.types import (
    WorkflowCompleted,
    WorkflowEvent,
    WorkflowFailed,
    WorkflowStarted,
)
from webresearch.pipeline.runtime import patch_runner_for_streaming
from webresearch.types import WorkflowFn, WorkflowInput, WorkflowResult


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
        async with patch_runner_for_streaming():
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
