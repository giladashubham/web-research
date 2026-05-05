from __future__ import annotations

from agents import Agent

from webresearch.agents.models import ReviewOutput
from webresearch.agents.settings import no_store_model_settings
from webresearch.workflows.shared.prompt_loader import load_shared_prompt


def reviewer_agent(workflow_id: str = "standard") -> Agent:
    return Agent(
        name="Reviewer",
        instructions=load_shared_prompt("reviewer.md", workflow_id),
        model_settings=no_store_model_settings(),
        output_type=ReviewOutput,
    )
