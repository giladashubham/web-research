from __future__ import annotations

from datetime import date
from importlib.resources import files
from typing import TYPE_CHECKING

from webresearch.pipeline.hooks import HookSignal
from webresearch.pipeline.step import AgentStep
from webresearch.workflows.company_news.config import CONFIG
from webresearch.workflows.company_news.models import (
    IntakePlan,
    OutputWriterOutput,
    ResearcherOutput,
)
from webresearch.workflows.company_news.tools import COMPANY_TOOLS, NEWS_TOOLS

if TYPE_CHECKING:
    from webresearch.pipeline.state import PipelineState


def _prompt(name: str) -> str:
    return (
        files("webresearch.workflows.company_news") / "prompts" / f"{name}.j2"
    ).read_text(encoding="utf-8")


async def _intake_planner_pre_hook(state: PipelineState) -> HookSignal:
    state.outputs["_today_date"] = date.today().isoformat()
    return HookSignal.CONTINUE


intake_planner = AgentStep(
    name="intake_planner",
    prompt=_prompt("intake_planner"),
    output_type=IntakePlan,
    pre_hook=_intake_planner_pre_hook,
)

web_news_researcher = AgentStep(
    name="web_news_researcher",
    prompt=_prompt("web_news_researcher"),
    tools=NEWS_TOOLS,
    output_type=ResearcherOutput,
    max_turns=CONFIG.research_max_turns,
)

social_researcher = AgentStep(
    name="social_researcher",
    prompt=_prompt("social_researcher"),
    tools=NEWS_TOOLS,
    output_type=ResearcherOutput,
    max_turns=CONFIG.social_max_turns,
)

company_researcher = AgentStep(
    name="company_researcher",
    prompt=_prompt("company_researcher"),
    tools=COMPANY_TOOLS,
    output_type=ResearcherOutput,
    max_turns=CONFIG.company_max_turns,
)

output_writer = AgentStep(
    name="output_writer",
    prompt=_prompt("output_writer"),
    output_type=OutputWriterOutput,
)
