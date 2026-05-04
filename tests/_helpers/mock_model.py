from __future__ import annotations

import json
from difflib import unified_diff
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from agents import Agent, RunConfig, Runner
from agents.items import ModelResponse, TResponseOutputItem
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from agents.agent_output import AgentOutputSchemaBase
    from agents.handoffs import Handoff
    from agents.items import TResponseInputItem
    from agents.model_settings import ModelSettings
    from agents.models.interface import ModelTracing
    from agents.tool import Tool
    from openai.types.responses import ResponseStreamEvent
    from openai.types.responses.response_prompt_param import ResponsePromptParam

ScriptStep = dict[str, Any]


class MockModel(Model):
    def __init__(self, script: Sequence[ScriptStep]) -> None:
        self._script = list(script)
        self.calls = 0

    @override
    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: ResponsePromptParam | None,
    ) -> ModelResponse:
        _ = (
            system_instructions,
            input,
            model_settings,
            output_schema,
            handoffs,
            tracing,
            previous_response_id,
            conversation_id,
            prompt,
        )
        if not self._script:
            raise AssertionError("MockModel script exhausted")

        self.calls += 1
        step = self._script.pop(0)
        self._assert_expected_tools(step, tools)
        return ModelResponse(
            output=_output_items(step, self.calls),
            usage=Usage(requests=1),
            response_id=f"mock_response_{self.calls}",
        )

    @override
    def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: ResponsePromptParam | None,
    ) -> AsyncIterator[ResponseStreamEvent]:
        _ = (
            system_instructions,
            input,
            model_settings,
            tools,
            output_schema,
            handoffs,
            tracing,
            previous_response_id,
            conversation_id,
            prompt,
        )

        async def _empty_stream() -> AsyncIterator[ResponseStreamEvent]:
            if False:
                yield None  # type: ignore[misc]

        return _empty_stream()

    def _assert_expected_tools(self, step: ScriptStep, tools: list[Tool]) -> None:
        expected = step.get("expected_tools")
        if expected is None:
            return

        actual_tool_names = [tool.name for tool in tools]
        expected_tool_names = [str(name) for name in expected]
        if actual_tool_names == expected_tool_names:
            return

        diff = "\n".join(
            unified_diff(
                expected_tool_names,
                actual_tool_names,
                fromfile="script",
                tofile="agent",
                lineterm="",
            )
        )
        raise AssertionError(f"Tool list mismatch:\n{diff}")


def load_script(name: str) -> list[ScriptStep]:
    path = Path(__file__).parent / "scripts" / name
    return json.loads(path.read_text())


async def run_with_mock(
    agent: Agent[Any],
    input: str,
    script: Sequence[ScriptStep],
) -> object:
    agent.model = MockModel(script)
    result = await Runner.run(
        agent,
        input,
        run_config=RunConfig(tracing_disabled=True),
    )
    return result.final_output


def _output_items(step: ScriptStep, call_index: int) -> list[TResponseOutputItem]:
    items: list[TResponseOutputItem] = []
    for tool_call in step.get("tool_calls", []):
        items.append(
            ResponseFunctionToolCall(
                type="function_call",
                name=str(tool_call["name"]),
                call_id=str(tool_call.get("call_id", f"call_{call_index}")),
                arguments=json.dumps(tool_call.get("arguments", {})),
                status="completed",
            )
        )

    if "final_output" in step:
        final_output = step["final_output"]
        text = final_output if isinstance(final_output, str) else json.dumps(final_output)
        items.append(_message(text, call_index))
    elif "text" in step:
        items.append(_message(str(step["text"]), call_index))

    return items


def _message(text: str, call_index: int) -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id=f"mock_message_{call_index}",
        role="assistant",
        status="completed",
        type="message",
        content=[
            ResponseOutputText(
                type="output_text",
                text=text,
                annotations=[],
            )
        ],
    )
