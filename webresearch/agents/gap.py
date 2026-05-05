from __future__ import annotations

from agents import Agent

from webresearch.agents.models import GapResearchOutput
from webresearch.agents.tools import RESEARCH_TOOLS
from webresearch.workflows.shared.prompt_loader import load_shared_prompt


def gap_researcher_agent(workflow_id: str = "standard") -> Agent:
    return Agent(
        name="Gap Researcher",
        instructions=load_shared_prompt("gap.md", workflow_id),
        tools=list(RESEARCH_TOOLS),
        output_type=GapResearchOutput,
    )
