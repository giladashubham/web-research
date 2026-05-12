from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from jinja2 import BaseLoader, Environment, Undefined
from pydantic import BaseModel

from webresearch.context import WorkflowContext
from webresearch.events.step import (
    emit_loop_iteration,
    emit_step_completed,
    emit_step_skipped,
    get_active_run_id,
    step,
)
from webresearch.pipeline.hooks import HookSignal
from webresearch.pipeline.runtime import calculate_cost, execute
from webresearch.pipeline.state import PipelineState
from webresearch.pipeline.step import AgentStep, FanOut, Loop, Parallel
from webresearch.types import WorkflowResult

if TYPE_CHECKING:
    from webresearch.types import WorkflowInput

PipelineStep = AgentStep | Parallel | FanOut | Loop

ResultBuilder = Callable[[PipelineState], WorkflowResult]
"""Callable that constructs a :class:`WorkflowResult` from pipeline state.

Each workflow provides its own result builder, giving it full control over
how step outputs, sources, evidence, artifacts, and warnings are mapped into
the final result contract."""

_jinja = Environment(
    loader=BaseLoader(),
    undefined=Undefined,
    autoescape=False,  # noqa: S701 (Prompts are plain text, not HTML)
)
_jinja.filters["tojson"] = lambda v, indent=None: json.dumps(
    _jsonable(v) if not isinstance(v, Undefined) else None, indent=indent
)


class Pipeline:
    """Orchestrates a sequence of pipeline steps against a :class:`WorkflowInput`.

    Steps can be :class:`AgentStep`, :class:`Parallel`, :class:`FanOut`, or
    :class:`Loop`.  The pipeline renders Jinja2 prompts, manages hooks,
    accumulates cost/tokens, and emits lifecycle events.

    The pipeline itself knows nothing about the output shape — it delegates
    result construction entirely to the caller-supplied ``result_builder``.

    Parameters:
        steps: Ordered list of step definitions.
        result_builder: Callable that maps :class:`PipelineState` to a
            :class:`WorkflowResult`.  Each workflow provides its own.
    """

    def __init__(
        self,
        steps: list[PipelineStep],
        result_builder: ResultBuilder,
    ) -> None:
        self._steps = steps
        self._result_builder = result_builder

    async def run(self, input: WorkflowInput) -> WorkflowResult:
        run_id = get_active_run_id() or f"run_{uuid4().hex}"
        state = PipelineState(
            input=input,
            run_id=run_id,
            started_at=datetime.now(UTC),
            context=WorkflowContext(_max_sources=input.max_sources),
        )
        for step_def in self._steps:
            await self._execute(step_def, state)
        return self._result_builder(state)

    async def _execute(self, step_def: PipelineStep, state: PipelineState) -> None:
        if isinstance(step_def, Parallel):
            await self._execute_parallel(step_def, state)
        elif isinstance(step_def, FanOut):
            await self._execute_fanout(step_def, state)
        elif isinstance(step_def, Loop):
            await self._execute_loop(step_def, state)
        else:
            await self._execute_agent(step_def, state)

    async def _execute_agent(
        self, step_def: AgentStep, state: PipelineState, item: object = None
    ) -> None:
        if step_def.pre_hook:
            signal = await step_def.pre_hook(state)
            if signal == HookSignal.SKIP:
                await emit_step_skipped(step_def.name, "pre_hook returned SKIP")
                return

        async with step(step_def.name):
            prompt = _build_prompt(step_def, state, item=item)
            exec_result = await execute(step_def, prompt, state.context)

        state.outputs[step_def.name] = exec_result.output
        state.iteration_count[step_def.name] = state.iteration_count.get(step_def.name, 0) + 1
        step_cost = calculate_cost(
            exec_result.input_tokens, exec_result.output_tokens, exec_result.model
        )
        state.context.input_tokens += exec_result.input_tokens
        state.context.output_tokens += exec_result.output_tokens
        state.context.cached_tokens += exec_result.cached_tokens
        state.context.cost_usd += step_cost

        await emit_step_completed(
            step_def.name,
            cost_usd=step_cost,
            input_tokens=exec_result.input_tokens,
            output_tokens=exec_result.output_tokens,
            cached_tokens=exec_result.cached_tokens,
            model=exec_result.model,
        )

        if step_def.post_hook:
            signal = await step_def.post_hook(state)
            if signal == HookSignal.REPEAT:
                max_rounds = state.input.depth.max_rounds
                if state.iteration_count[step_def.name] < max_rounds:
                    await self._execute_agent(step_def, state, item=item)

    async def _execute_parallel(self, par: Parallel, state: PipelineState) -> None:
        await asyncio.gather(*[self._execute_agent(s, state) for s in par.steps])

    async def _execute_fanout(self, fan: FanOut, state: PipelineState) -> None:
        items = fan.over(state)
        results: list[Any] = []

        async def _fan_item(item: object) -> None:
            # pre_hook
            if fan.step.pre_hook:
                signal = await fan.step.pre_hook(state)
                if signal == HookSignal.SKIP:
                    return

            # execute with step context (events, error isolation)
            async with step(fan.step.name):
                prompt = _build_prompt(fan.step, state, item=item)
                exec_result = await execute(fan.step, prompt, state.context)
                results.append(exec_result.output)

                step_cost = calculate_cost(
                    exec_result.input_tokens,
                    exec_result.output_tokens,
                    exec_result.model,
                )
                state.context.input_tokens += exec_result.input_tokens
                state.context.output_tokens += exec_result.output_tokens
                state.context.cached_tokens += exec_result.cached_tokens
                state.context.cost_usd += step_cost

            state.iteration_count[fan.step.name] = state.iteration_count.get(fan.step.name, 0) + 1

            await emit_step_completed(
                fan.step.name,
                cost_usd=step_cost,
                input_tokens=exec_result.input_tokens,
                output_tokens=exec_result.output_tokens,
                cached_tokens=exec_result.cached_tokens,
                model=exec_result.model,
            )

            # post_hook with REPEAT support
            if fan.step.post_hook:
                signal = await fan.step.post_hook(state)
                if signal == HookSignal.REPEAT:
                    max_rounds = state.input.depth.max_rounds
                    if state.iteration_count.get(fan.step.name, 0) < max_rounds:
                        await _fan_item(item)

        await asyncio.gather(*[_fan_item(item) for item in items])
        state.outputs[fan.step.name] = results

    async def _execute_loop(self, loop: Loop, state: PipelineState) -> None:
        max_iter = loop.max_iterations or state.input.depth.max_rounds
        iteration = 0
        while not loop.until(state) and iteration < max_iter:
            iteration += 1
            await emit_loop_iteration(loop.steps[0].name, iteration)
            for loop_step in loop.steps:
                await self._execute_agent(loop_step, state)
                acc_key = f"_{loop_step.name}_history"
                if acc_key not in state.outputs:
                    state.outputs[acc_key] = []
                state.outputs[acc_key].append(state.outputs[loop_step.name])


def _build_prompt(step: AgentStep, state: PipelineState, item: object = None) -> str:
    return _jinja.from_string(step.prompt).render(
        input=state.input,
        outputs=state.outputs,
        item=item,
    )


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(val) for key, val in value.items()}
    return value
