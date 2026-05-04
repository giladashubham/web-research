from __future__ import annotations

from typing import Any

import pytest
from agents import Agent, RunConfig, Runner

from tests._helpers.mock_model import MockModel
from webresearch.agents.gap import gap_researcher_agent
from webresearch.agents.models import (
    FinalAnswer,
    GapResearchOutput,
    ResearcherOutput,
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
from webresearch.context import WorkflowContext
from webresearch.types import SourceInput

RESEARCH_TOOL_NAMES = [
    "search_web_tool",
    "fetch_url_tool",
    "extract_content_tool",
    "rank_sources_tool",
]


@pytest.mark.parametrize(
    ("agent", "final_output"),
    [
        (
            planner_agent(),
            {
                "questions": ["What is the answer?"],
                "risks": ["Stale information"],
                "search_strategy": "Search authoritative sources.",
            },
        ),
        (
            reviewer_agent(),
            {
                "coverage": [{"topic": "answer", "status": "covered", "notes": "Supported."}],
                "conflicts": [],
                "has_critical_gaps": False,
                "follow_up_queries": [],
            },
        ),
        (
            output_agent(),
            {
                "answer_markdown": "Answer citing src_1.",
                "findings": [
                    {
                        "claim": "Claim",
                        "evidence_ids": [],
                        "source_ids": ["src_1"],
                        "confidence": "high",
                    }
                ],
                "sources_cited": ["src_1"],
                "structured_data": None,
            },
        ),
    ],
)
async def test_no_tool_agents_expose_zero_tools(
    agent: Agent[Any],
    final_output: dict[str, object],
) -> None:
    agent.model = MockModel([{"expected_tools": [], "final_output": final_output}])

    result = await Runner.run(
        agent,
        "Canned context with registered source src_1.",
        run_config=RunConfig(tracing_disabled=True),
    )

    assert result.final_output is not None


@pytest.mark.parametrize(
    ("agent", "output_type"),
    [
        (official_researcher_agent(), ResearcherOutput),
        (recent_researcher_agent(), ResearcherOutput),
        (broad_researcher_agent(), ResearcherOutput),
        (gap_researcher_agent(), GapResearchOutput),
    ],
)
async def test_research_agents_emit_search_call_and_only_declared_tools(
    agent: Agent[Any],
    output_type: type[ResearcherOutput],
) -> None:
    _ = output_type
    agent.model = MockModel(
        [
            {
                "expected_tools": RESEARCH_TOOL_NAMES,
                "tool_calls": [
                    {
                        "name": "search_web_tool",
                        "arguments": {"query": "official answer", "limit": 1},
                    }
                ],
            },
            {
                "expected_tools": RESEARCH_TOOL_NAMES,
                "final_output": {
                    "summary": "Found one relevant source.",
                    "source_ids": ["src_1"],
                    "evidence_ids": [],
                    "confidence": "medium",
                },
            },
        ]
    )

    result = await Runner.run(
        agent,
        "Canned research context.",
        context=WorkflowContext(),
        run_config=RunConfig(tracing_disabled=True),
    )

    assert isinstance(result.final_output, output_type)


async def test_output_cites_only_registered_source_ids() -> None:
    ctx = WorkflowContext()
    source = ctx.sources.add(SourceInput(url="https://example.com/report"))
    agent = output_agent()
    agent.model = MockModel(
        [
            {
                "expected_tools": [],
                "final_output": {
                    "answer_markdown": f"Answer citing {source.id}.",
                    "findings": [
                        {
                            "claim": "Claim",
                            "evidence_ids": [],
                            "source_ids": [source.id],
                            "confidence": "high",
                        }
                    ],
                    "sources_cited": [source.id],
                    "structured_data": None,
                },
            }
        ]
    )

    result = await Runner.run(
        agent,
        f"Registered sources: {source.id}",
        context=ctx,
        run_config=RunConfig(tracing_disabled=True),
    )

    assert isinstance(result.final_output, FinalAnswer)
    registered_source_ids = {record.id for record in ctx.sources.list()}
    assert set(result.final_output.sources_cited) <= registered_source_ids
    for finding in result.final_output.findings:
        assert set(finding.source_ids) <= registered_source_ids


def test_final_prompts_replace_placeholders_and_keep_depth_hook() -> None:
    prompt_names = [
        "planner.md",
        "official.md",
        "recent.md",
        "broad.md",
        "reviewer.md",
        "gap.md",
        "output.md",
    ]

    for prompt_name in prompt_names:
        prompt = load_prompt(prompt_name)
        assert "placeholder prompt" not in prompt.lower()
        assert "{depth_extras}" not in prompt
        assert "Use a balanced amount of source coverage and evidence." in prompt


def test_prompt_output_models_are_named_in_boundary_prompts() -> None:
    assert "PlanOutput" in load_prompt("planner.md")
    assert "ResearcherOutput" in load_prompt("official.md")
    assert "ResearcherOutput" in load_prompt("recent.md")
    assert "ResearcherOutput" in load_prompt("broad.md")
    assert "ReviewOutput" in load_prompt("reviewer.md")
    assert "GapResearchOutput" in load_prompt("gap.md")
    assert "FinalAnswer" in load_prompt("output.md")
