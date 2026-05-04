from __future__ import annotations

from agents import Agent

from webresearch.agents.models import ReviewOutput
from webresearch.agents.prompts import load_prompt


def reviewer_agent() -> Agent:
    return Agent(
        name="Reviewer",
        instructions=load_prompt("reviewer.md"),
        output_type=ReviewOutput,
    )
