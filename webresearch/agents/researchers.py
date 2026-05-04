from __future__ import annotations

from agents import Agent

from webresearch.agents.models import ResearcherOutput
from webresearch.agents.prompts import load_prompt
from webresearch.agents.tools import RESEARCH_TOOLS


def official_researcher_agent() -> Agent:
    return _researcher_agent("Official Source Researcher", "official.md")


def recent_researcher_agent() -> Agent:
    return _researcher_agent("Recent Source Researcher", "recent.md")


def broad_researcher_agent() -> Agent:
    return _researcher_agent("Broad Source Researcher", "broad.md")


def _researcher_agent(name: str, prompt_name: str) -> Agent:
    return Agent(
        name=name,
        instructions=load_prompt(prompt_name),
        tools=list(RESEARCH_TOOLS),
        output_type=ResearcherOutput,
    )
