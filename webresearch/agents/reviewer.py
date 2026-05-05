from __future__ import annotations

from agents import Agent

from webresearch.agents.models import ReviewOutput
from webresearch.workflows.shared.prompt_loader import load_prompt


def reviewer_agent(depth: str = "standard") -> Agent:
    return Agent(
        name="Reviewer",
        instructions=load_prompt("reviewer.md", depth),
        output_type=ReviewOutput,
    )
