from __future__ import annotations

import pytest
from agents import Agent, RunConfig, Runner, function_tool

from tests._helpers.mock_model import MockModel, load_script, run_with_mock
from webresearch.agents.models import PlanOutput


def test_scripts_load_from_fixture_json() -> None:
    script = load_script("standard_happy_path.json")

    assert script[0]["expected_tools"] == []


async def test_scripted_exchange_drives_runner_to_final_output() -> None:
    agent = Agent(name="planner", output_type=PlanOutput)

    output = await run_with_mock(agent, "plan", load_script("standard_happy_path.json"))

    assert isinstance(output, PlanOutput)
    assert output.search_strategy == "Use deterministic fixture searches."


async def test_mismatched_tool_call_fails_with_clear_diff() -> None:
    @function_tool
    async def echo(value: str) -> str:
        """Echo a value."""
        return value

    model = MockModel([{"expected_tools": ["missing_tool"], "text": "done"}])
    agent = Agent(name="tool-agent", tools=[echo], model=model)

    with pytest.raises(AssertionError, match="Tool list mismatch"):
        await Runner.run(agent, "hi", run_config=RunConfig(tracing_disabled=True))


async def test_mock_model_reusable_across_multiple_runner_calls() -> None:
    model = MockModel(
        [
            {"text": "first"},
            {"text": "second"},
        ]
    )
    agent = Agent(name="reusable", model=model)

    run_config = RunConfig(tracing_disabled=True)
    first = await Runner.run(agent, "one", run_config=run_config)
    second = await Runner.run(agent, "two", run_config=run_config)

    assert first.final_output == "first"
    assert second.final_output == "second"
    assert model.calls == 2
