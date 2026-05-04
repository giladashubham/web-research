from __future__ import annotations

from agents import Agent

from webresearch.agents.models import PlanOutput
from webresearch.agents.prompts import load_prompt


def planner_agent(depth: str = "standard") -> Agent:
    return Agent(
        name="Planner",
        instructions=load_prompt("planner.md", depth),
        output_type=PlanOutput,
    )
