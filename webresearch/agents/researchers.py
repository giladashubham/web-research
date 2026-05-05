from __future__ import annotations

from agents import Agent

from webresearch.agents.models import ResearcherOutput
from webresearch.agents.tools import RESEARCH_TOOLS
from webresearch.workflows.shared.prompt_loader import load_shared_prompt


def official_researcher_agent(workflow_id: str = "standard") -> Agent:
    return _researcher_agent("Official Source Researcher", "official.md", workflow_id)


def recent_researcher_agent(workflow_id: str = "standard") -> Agent:
    return _researcher_agent("Recent Source Researcher", "recent.md", workflow_id)


def broad_researcher_agent(workflow_id: str = "standard") -> Agent:
    return _researcher_agent("Broad Source Researcher", "broad.md", workflow_id)


def _researcher_agent(name: str, prompt_name: str, workflow_id: str) -> Agent:
    return Agent(
        name=name,
        instructions=load_shared_prompt(prompt_name, workflow_id),
        tools=list(RESEARCH_TOOLS),
        output_type=ResearcherOutput,
    )
