from __future__ import annotations

from agents import Agent

from webresearch.agents.models import GapResearchOutput
from webresearch.agents.tools import RESEARCH_TOOLS
from webresearch.workflows.shared.prompt_loader import load_prompt


def gap_researcher_agent(depth: str = "standard") -> Agent:
    return Agent(
        name="Gap Researcher",
        instructions=load_prompt("gap.md", depth),
        tools=list(RESEARCH_TOOLS),
        output_type=GapResearchOutput,
    )
