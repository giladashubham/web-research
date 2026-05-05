from __future__ import annotations

from agents import Agent

from webresearch.agents.models import ResearcherOutput
from webresearch.agents.tools import RESEARCH_TOOLS
from webresearch.workflows.shared.prompt_loader import load_prompt


def official_researcher_agent(depth: str = "standard") -> Agent:
    return _researcher_agent("Official Source Researcher", "official.md", depth)


def recent_researcher_agent(depth: str = "standard") -> Agent:
    return _researcher_agent("Recent Source Researcher", "recent.md", depth)


def broad_researcher_agent(depth: str = "standard") -> Agent:
    return _researcher_agent("Broad Source Researcher", "broad.md", depth)


def _researcher_agent(name: str, prompt_name: str, depth: str) -> Agent:
    return Agent(
        name=name,
        instructions=load_prompt(prompt_name, depth),
        tools=list(RESEARCH_TOOLS),
        output_type=ResearcherOutput,
    )
