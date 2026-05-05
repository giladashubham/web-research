from __future__ import annotations

from agents import Agent
from agents.agent_output import AgentOutputSchema

from webresearch.agents.models import FinalAnswer
from webresearch.workflows.shared.prompt_loader import load_shared_prompt


def output_agent(
    output_schema: dict[str, object] | None = None, workflow_id: str = "standard"
) -> Agent:
    _ = output_schema
    return Agent(
        name="Output",
        instructions=load_shared_prompt("output.md", workflow_id),
        output_type=AgentOutputSchema(FinalAnswer, strict_json_schema=False),
    )
