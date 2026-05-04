from __future__ import annotations

from agents import Agent, RunContextWrapper, Runner, function_tool


def test_agents_sdk_smoke_imports_and_constructs_agent() -> None:
    agent = Agent(name="smoke", instructions="say hi")

    assert agent.name == "smoke"
    assert agent.instructions == "say hi"
    assert Runner is not None
    assert function_tool is not None
    assert RunContextWrapper is not None
