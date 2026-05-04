from __future__ import annotations

import pytest

from webresearch.agents.gap import gap_researcher_agent
from webresearch.agents.models import (
    FinalAnswer,
    GapResearchOutput,
    PlanOutput,
    ResearcherOutput,
    ReviewOutput,
)
from webresearch.agents.output import output_agent
from webresearch.agents.planner import planner_agent
from webresearch.agents.prompts import load_prompt
from webresearch.agents.researchers import (
    broad_researcher_agent,
    official_researcher_agent,
    recent_researcher_agent,
)
from webresearch.agents.reviewer import reviewer_agent


@pytest.mark.parametrize(
    ("factory", "name", "prompt", "output_type", "tool_count"),
    [
        (planner_agent, "Planner", "planner.md", PlanOutput, 0),
        (
            official_researcher_agent,
            "Official Source Researcher",
            "official.md",
            ResearcherOutput,
            4,
        ),
        (recent_researcher_agent, "Recent Source Researcher", "recent.md", ResearcherOutput, 4),
        (broad_researcher_agent, "Broad Source Researcher", "broad.md", ResearcherOutput, 4),
        (reviewer_agent, "Reviewer", "reviewer.md", ReviewOutput, 0),
        (gap_researcher_agent, "Gap Researcher", "gap.md", GapResearchOutput, 4),
        (output_agent, "Output", "output.md", FinalAnswer, 0),
    ],
)
def test_agent_factories_return_expected_agent(
    factory,
    name,
    prompt,
    output_type,
    tool_count,
) -> None:
    agent = factory()

    assert agent.name == name
    assert agent.instructions == load_prompt(prompt)
    if hasattr(agent.output_type, "output_type"):
        assert agent.output_type.output_type is output_type
    else:
        assert agent.output_type is output_type
    assert len(agent.tools) == tool_count


def test_agent_factories_return_fresh_instances() -> None:
    first = planner_agent()
    second = planner_agent()

    assert first is not second


def test_researcher_tools_have_expected_names() -> None:
    agent = official_researcher_agent()

    assert [tool.name for tool in agent.tools] == [
        "search_web_tool",
        "fetch_url_tool",
        "extract_content_tool",
        "rank_sources_tool",
    ]


def test_missing_prompt_raises_clear_file_not_found_error() -> None:
    with pytest.raises(FileNotFoundError, match=r"missing\.md"):
        load_prompt("missing.md")
