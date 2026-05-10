from __future__ import annotations

import asyncio
import json
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
    step,
)
from webresearch.pipeline.hooks import HookSignal
from webresearch.pipeline.runtime import calculate_cost, execute
from webresearch.pipeline.state import PipelineState
from webresearch.pipeline.step import AgentStep, FanOut, Loop, Parallel
from webresearch.types import (
    ResearchFinding,
    TokenUsage,
    WorkflowMetadata,
    WorkflowResult,
)

if TYPE_CHECKING:
    from webresearch.types import WorkflowInput

PipelineStep = AgentStep | Parallel | FanOut | Loop

_jinja = Environment(
    loader=BaseLoader(),
    undefined=Undefined,
    autoescape=False,  # noqa: S701 (Prompts are plain text, not HTML)
)
_jinja.filters["tojson"] = lambda v, indent=None: json.dumps(
    _jsonable(v) if not isinstance(v, Undefined) else None, indent=indent
)


class Pipeline:
    def __init__(
        self,
        steps: list[PipelineStep],
        final_output_key: str = "output",
        workflow_id: str = "pipeline",
    ) -> None:
        self._steps = steps
        self._final_output_key = final_output_key
        self._workflow_id = workflow_id

    async def run(self, input: WorkflowInput) -> WorkflowResult:
        state = PipelineState(
            input=input,
            run_id=f"run_{uuid4().hex}",
            started_at=datetime.now(UTC),
            context=WorkflowContext(_max_sources=input.max_sources),
        )
        for step_def in self._steps:
            await self._execute(step_def, state)
        return _build_result(state, self._final_output_key, self._workflow_id)

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
        state.context.cost_usd += step_cost

        await emit_step_completed(
            step_def.name,
            cost_usd=step_cost,
            input_tokens=exec_result.input_tokens,
            output_tokens=exec_result.output_tokens,
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
                state.context.cost_usd += step_cost

            state.iteration_count[fan.step.name] = state.iteration_count.get(fan.step.name, 0) + 1

            await emit_step_completed(
                fan.step.name,
                cost_usd=step_cost,
                input_tokens=exec_result.input_tokens,
                output_tokens=exec_result.output_tokens,
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


def _build_result(
    state: PipelineState, final_output_key: str, workflow_id: str = "pipeline"
) -> WorkflowResult:
    final = state.outputs.get(final_output_key)
    if final is None:
        msg = f"Final output key '{final_output_key}' not found in state outputs"
        raise ValueError(msg)

    answer_md = getattr(final, "answer_markdown", "")
    structured = getattr(final, "structured_data", None)
    # For workflows like TDD that embed structured data in a "report" field
    if structured is None and hasattr(final, "report"):
        report = final.report
        if hasattr(report, "model_dump"):
            structured = report.model_dump(mode="json")

    findings_raw = getattr(final, "findings", [])

    findings = [
        ResearchFinding(
            id=f"finding_{index}",
            claim=finding.claim,
            evidence_ids=getattr(finding, "evidence_ids", []),
            confidence=_confidence_score(getattr(finding, "confidence", "medium")),
        )
        for index, finding in enumerate(findings_raw, 1)
    ]

    return WorkflowResult(
        answer_markdown=answer_md or "",
        structured_data=structured,
        summary=_summary_from_agents(state),
        findings=findings,
        sources=list(state.context.sources.list()),
        evidence=list(state.context.evidence),
        artifacts=[*state.context.artifacts],
        warnings=[*state.warnings, *state.context.warnings],
        metadata=WorkflowMetadata(
            run_id=state.run_id,
            workflow_id=workflow_id,
            started_at=state.started_at,
            finished_at=datetime.now(UTC),
            cost_usd=state.context.cost_usd,
            tokens=TokenUsage(
                input_tokens=state.context.input_tokens,
                output_tokens=state.context.output_tokens,
                total_tokens=state.context.input_tokens + state.context.output_tokens,
            ),
        ),
    )


def _summary_from_agents(state: PipelineState) -> str:
    summaries: list[str] = []
    # Steps whose Loop accumulated a history list — skip their final-value entry to avoid
    # double-counting the last iteration.
    keys_with_history: set[str] = {
        key[1 : -len("_history")]
        for key in state.outputs
        if key.startswith("_") and key.endswith("_history")
    }
    for key, output in state.outputs.items():
        if key.startswith("_") and key.endswith("_history"):
            if isinstance(output, list):
                for hist_output in output:
                    val = getattr(hist_output, "summary", None)
                    if val:
                        summaries.append(str(val))
        elif key not in keys_with_history:
            val = getattr(output, "summary", None)
            if val:
                summaries.append(str(val))
    return "\n".join(summaries) if summaries else ""


def _confidence_score(confidence: str) -> float:
    return {"low": 0.33, "medium": 0.66, "high": 1.0}.get(confidence, 0.5)
