from __future__ import annotations

from importlib.resources import files

from webresearch.pipeline.step import AgentStep
from webresearch.workflows.deep.config import CONFIG
from webresearch.workflows.deep.models import (
    FinalAnswer,
    GapResearchOutput,
    PlanOutput,
    ResearcherOutput,
    ReviewOutput,
)
from webresearch.workflows.deep.tools import RESEARCH_TOOLS


def _prompt(name: str) -> str:
    return (files("webresearch.workflows.deep") / "prompts" / f"{name}.j2").read_text(
        encoding="utf-8"
    )


planner = AgentStep(
    name="planner",
    prompt=_prompt("planner"),
    output_type=PlanOutput,
)

official_researcher = AgentStep(
    name="official_researcher",
    prompt=_prompt("official"),
    tools=RESEARCH_TOOLS,
    output_type=ResearcherOutput,
    max_turns=CONFIG.researcher_max_turns,
)

recent_researcher = AgentStep(
    name="recent_researcher",
    prompt=_prompt("recent"),
    tools=RESEARCH_TOOLS,
    output_type=ResearcherOutput,
    max_turns=CONFIG.researcher_max_turns,
)

broad_researcher = AgentStep(
    name="broad_researcher",
    prompt=_prompt("broad"),
    tools=RESEARCH_TOOLS,
    output_type=ResearcherOutput,
    max_turns=CONFIG.researcher_max_turns,
)

reviewer = AgentStep(
    name="reviewer",
    prompt=_prompt("reviewer"),
    output_type=ReviewOutput,
)

gap_researcher = AgentStep(
    name="gap_researcher",
    prompt=_prompt("gap"),
    tools=RESEARCH_TOOLS,
    output_type=GapResearchOutput,
    max_turns=CONFIG.researcher_max_turns,
)

output_writer = AgentStep(
    name="output",
    prompt=_prompt("output"),
    output_type=FinalAnswer,
    strict_schema=False,
)
