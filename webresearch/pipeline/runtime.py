from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from agents import Agent, ModelSettings, Runner
from agents.agent_output import AgentOutputSchema

from webresearch.events.step import current_run_id, current_step, emit_event
from webresearch.events.translation import translate_sdk_event
from webresearch.events.types import (
    AgentCompleted,
    AgentFailed,
    AgentStarted,
    OutputTextDelta,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from webresearch.context import WorkflowContext
    from webresearch.pipeline.step import AgentStep

_COST_PER_1M: dict[str, dict[str, float]] = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "o4-mini": {"input": 1.10, "output": 4.40},
}


class ExecutionResult:
    def __init__(
        self,
        output: object,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> None:
        self.output = output
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model = model


async def execute(
    step: AgentStep,
    prompt: str,
    context: WorkflowContext,
    tools: list[Any] | None = None,
) -> ExecutionResult:
    output_type = (
        step.output_type
        if step.strict_schema
        else AgentOutputSchema(step.output_type, strict_json_schema=False)
    )
    agent = Agent(
        name=step.name,
        instructions=step.prompt,
        tools=tools or step.tools,
        output_type=output_type,
        model_settings=ModelSettings(store=False),
    )

    await emit_event(
        AgentStarted(run_id=current_run_id(), step=step.name, agent_name=step.name)
    )
    try:
        result = await Runner.run(agent, prompt, context=context, max_turns=step.max_turns)
    except Exception as exc:
        await emit_event(AgentFailed(run_id=current_run_id(), step=step.name, error=str(exc)))
        raise

    await emit_event(AgentCompleted(run_id=current_run_id(), step=step.name))

    usage = result.raw_responses[-1].usage if result.raw_responses else None
    input_tokens = usage.input_tokens if usage else 0
    output_tokens = usage.output_tokens if usage else 0

    return ExecutionResult(
        output=result.final_output,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=getattr(agent, "model", None) or "default",
    )


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    rates = _COST_PER_1M.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


@asynccontextmanager
async def patch_runner_for_streaming() -> AsyncIterator[None]:
    original_run = Runner.run
    original_run_streamed = Runner.run_streamed

    async def run_streamed_wrapper(*args: object, **kwargs: object) -> object:
        result = original_run_streamed(*args, **kwargs)  # type: ignore[arg-type]
        async for sdk_event in result.stream_events():
            await translate_sdk_event(sdk_event)
        return result

    Runner.run = run_streamed_wrapper  # type: ignore[method-assign, assignment]
    try:
        yield
    finally:
        Runner.run = original_run  # type: ignore[method-assign]
        Runner.run_streamed = original_run_streamed  # type: ignore[method-assign]


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
