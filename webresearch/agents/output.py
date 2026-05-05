from __future__ import annotations

from agents import Agent
from agents.agent_output import AgentOutputSchema

from webresearch.agents.models import FinalAnswer
from webresearch.workflows.shared.prompt_loader import load_prompt


def output_agent(output_schema: dict[str, object] | None = None, depth: str = "standard") -> Agent:
    _ = output_schema
    return Agent(
        name="Output",
        instructions=load_prompt("output.md", depth),
        output_type=AgentOutputSchema(FinalAnswer, strict_json_schema=False),
    )
