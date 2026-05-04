from __future__ import annotations

from agents import Agent

from webresearch.agents.models import PlanOutput
from webresearch.agents.prompts import load_prompt


def planner_agent() -> Agent:
    return Agent(
        name="Planner",
        instructions=load_prompt("planner.md"),
        output_type=PlanOutput,
    )
