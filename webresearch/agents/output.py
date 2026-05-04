from __future__ import annotations

from agents import Agent

from webresearch.agents.models import FinalAnswer
from webresearch.agents.prompts import load_prompt


def output_agent(output_schema: dict[str, object] | None = None) -> Agent:
    _ = output_schema
    return Agent(
        name="Output",
        instructions=load_prompt("output.md"),
        output_type=FinalAnswer,
    )
