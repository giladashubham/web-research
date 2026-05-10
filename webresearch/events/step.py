from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar

from webresearch.events.types import (
    LoopIteration,
    OutputTextDelta,
    StepCompleted,
    StepFailed,
    StepSkipped,
    StepStarted,
    WorkflowEvent,
)

EventSink = Callable[[WorkflowEvent], Awaitable[None]]

_event_sink: ContextVar[EventSink | None] = ContextVar("event_sink", default=None)
_run_id: ContextVar[str | None] = ContextVar("run_id", default=None)
_active_step: ContextVar[str | None] = ContextVar("active_step", default=None)


@asynccontextmanager
async def event_context(run_id: str, sink: EventSink) -> AsyncIterator[None]:
    sink_token = _event_sink.set(sink)
    run_id_token = _run_id.set(run_id)
    try:
        yield
    finally:
        _run_id.reset(run_id_token)
        _event_sink.reset(sink_token)


@asynccontextmanager
async def step(name: str) -> AsyncIterator[None]:
    token = _active_step.set(name)
    await emit_event(StepStarted(run_id=current_run_id(), step=name))
    try:
        yield
    except Exception as exc:
        await emit_event(StepFailed(run_id=current_run_id(), step=name, error=str(exc)))
        raise
    finally:
        _active_step.reset(token)


def current_run_id() -> str:
    return _run_id.get() or "run_uninstrumented"


def current_step() -> str | None:
    return _active_step.get()


async def emit_event(event: WorkflowEvent) -> None:
    sink = _event_sink.get()
    if sink is not None:
        await sink(event)


async def emit_loop_iteration(loop: str, iteration: int) -> None:
    await emit_event(
        LoopIteration(run_id=current_run_id(), loop=loop, iteration=iteration)
    )


async def emit_step_skipped(name: str, reason: str) -> None:
    await emit_event(StepSkipped(run_id=current_run_id(), step=name, reason=reason))


async def emit_output_text_delta(delta: str) -> None:
    if current_step() == "output" and delta:
        await emit_event(OutputTextDelta(run_id=current_run_id(), delta=delta))


async def emit_step_completed(
    name: str,
    cost_usd: float | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> None:
    await emit_event(
        StepCompleted(
            run_id=current_run_id(),
            step=name,
            cost_usd=cost_usd,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    )
