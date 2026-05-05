from __future__ import annotations

from agents import Agent

from webresearch.agents.models import PlanOutput
from webresearch.agents.settings import no_store_model_settings
from webresearch.workflows.shared.prompt_loader import load_shared_prompt


def planner_agent(workflow_id: str = "standard") -> Agent:
    return Agent(
        name="Planner",
        instructions=load_shared_prompt("planner.md", workflow_id),
        model_settings=no_store_model_settings(),
        output_type=PlanOutput,
    )
