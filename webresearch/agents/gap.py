from __future__ import annotations

from agents import Agent

from webresearch.agents.models import GapResearchOutput
from webresearch.agents.prompts import load_prompt
from webresearch.agents.tools import RESEARCH_TOOLS


def gap_researcher_agent() -> Agent:
    return Agent(
        name="Gap Researcher",
        instructions=load_prompt("gap.md"),
        tools=list(RESEARCH_TOOLS),
        output_type=GapResearchOutput,
    )
