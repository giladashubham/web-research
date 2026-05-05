from __future__ import annotations

from agents import Agent

from webresearch.agents.models import ReviewOutput
from webresearch.workflows.shared.prompt_loader import load_shared_prompt


def reviewer_agent(workflow_id: str = "standard") -> Agent:
    return Agent(
        name="Reviewer",
        instructions=load_shared_prompt("reviewer.md", workflow_id),
        output_type=ReviewOutput,
    )
