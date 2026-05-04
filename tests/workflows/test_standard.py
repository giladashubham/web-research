from __future__ import annotations

import asyncio
from time import perf_counter

from agents import Agent
from agents.agent_output import AgentOutputSchema

from tests._helpers.mock_model import MockModel
from webresearch.agents.models import (
    FinalAnswer,
    GapResearchOutput,
    PlanOutput,
    ResearcherOutput,
    ReviewOutput,
)
from webresearch.agents.tools import RESEARCH_TOOLS
from webresearch.types import Depth, WorkflowInput
from webresearch.workflows import standard
from webresearch.workflows.registry import WORKFLOWS


def _agent(name: str, output_type: type[object], script: list[dict[str, object]]) -> Agent:
    agent_output_type = (
        AgentOutputSchema(output_type, strict_json_schema=False)
        if output_type is FinalAnswer
        else output_type
    )
    return Agent(name=name, output_type=agent_output_type, model=MockModel(script))


def _research_script(summary: str, query: str) -> list[dict[str, object]]:
    return [
        {
            "expected_tools": [
                "search_web_tool",
                "fetch_url_tool",
                "extract_content_tool",
                "rank_sources_tool",
            ],
            "tool_calls": [
                {"name": "search_web_tool", "arguments": {"query": query, "limit": 1}},
            ],
        },
        {
            "expected_tools": [
                "search_web_tool",
                "fetch_url_tool",
                "extract_content_tool",
                "rank_sources_tool",
            ],
            "final_output": {
                "summary": summary,
                "source_ids": ["src_1"],
                "evidence_ids": [],
                "confidence": "medium",
            },
        },
    ]


def _patch_common_agents(
    monkeypatch,
    *,
    review_scripts: list[list[dict[str, object]]] | None = None,
    gap_script: list[dict[str, object]] | None = None,
) -> None:
    monkeypatch.setattr(
        standard,
        "planner_agent",
        lambda: _agent(
            "planner",
            PlanOutput,
            [
                {
                    "final_output": {
                        "questions": ["Q"],
                        "risks": [],
                        "search_strategy": "Search.",
                    }
                }
            ],
        ),
    )
    monkeypatch.setattr(
        standard,
        "official_researcher_agent",
        lambda: Agent(
            name="official",
            tools=list(RESEARCH_TOOLS),
            output_type=ResearcherOutput,
            model=MockModel(_research_script("official", "web research")),
        ),
    )
    monkeypatch.setattr(
        standard,
        "recent_researcher_agent",
        lambda: Agent(
            name="recent",
            tools=list(RESEARCH_TOOLS),
            output_type=ResearcherOutput,
            model=MockModel(_research_script("recent", "web research")),
        ),
    )
    monkeypatch.setattr(
        standard,
        "broad_researcher_agent",
        lambda: Agent(
            name="broad",
            tools=list(RESEARCH_TOOLS),
            output_type=ResearcherOutput,
            model=MockModel(_research_script("broad", "source reliability")),
        ),
    )

    scripts = review_scripts or [
        [
            {
                "final_output": {
                    "coverage": [],
                    "conflicts": [],
                    "has_critical_gaps": False,
                    "follow_up_queries": [],
                }
            }
        ]
    ]

    def reviewer_factory() -> Agent:
        return _agent("reviewer", ReviewOutput, scripts.pop(0))

    monkeypatch.setattr(standard, "reviewer_agent", reviewer_factory)
    monkeypatch.setattr(
        standard,
        "gap_researcher_agent",
        lambda: _agent(
            "gap",
            GapResearchOutput,
            gap_script
            or [
                {
                    "final_output": {
                        "summary": "gap",
                        "source_ids": [],
                        "evidence_ids": [],
                        "confidence": "low",
                    }
                }
            ],
        ),
    )
    monkeypatch.setattr(
        standard,
        "output_agent",
        lambda _schema=None: _agent(
            "output",
            FinalAnswer,
            [
                {
                    "final_output": {
                        "answer_markdown": "Final answer",
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
                    }
                }
            ],
        ),
    )


async def test_standard_workflow_runs_with_mock_model_and_returns_result(monkeypatch) -> None:
    _patch_common_agents(monkeypatch)

    result = await standard.run_standard(WorkflowInput(query="query"))

    assert result.answer_markdown == "Final answer"
    assert result.findings[0].claim == "Claim"
    assert result.metadata.workflow_id == "standard"
    assert WORKFLOWS["standard"] is standard.run_standard


async def test_loop_skips_when_reviewer_has_no_critical_gaps(monkeypatch) -> None:
    gap_called = False
    _patch_common_agents(monkeypatch)

    def gap_factory() -> Agent:
        nonlocal gap_called
        gap_called = True
        return _agent("gap", GapResearchOutput, [])

    monkeypatch.setattr(standard, "gap_researcher_agent", gap_factory)

    await standard.run_standard(WorkflowInput(query="query"))

    assert gap_called is False


async def test_loop_fires_when_reviewer_reports_gaps(monkeypatch) -> None:
    _patch_common_agents(
        monkeypatch,
        review_scripts=[
            [
                {
                    "final_output": {
                        "coverage": [],
                        "conflicts": [],
                        "has_critical_gaps": True,
                        "follow_up_queries": ["gap"],
                    }
                }
            ],
            [
                {
                    "final_output": {
                        "coverage": [],
                        "conflicts": [],
                        "has_critical_gaps": False,
                        "follow_up_queries": [],
                    }
                }
            ],
        ],
    )

    result = await standard.run_standard(
        WorkflowInput(query="query", depth=Depth.for_preset("standard"))
    )

    assert "gap" in result.summary


async def test_researchers_run_concurrently(monkeypatch) -> None:
    _patch_common_agents(monkeypatch)

    async def slow_run(agent, input, *, context=None):
        _ = input, context
        if agent.name in {"official", "recent", "broad"}:
            await asyncio.sleep(0.05)
            return type(
                "RunResult",
                (),
                {
                    "final_output": agent.output_type(
                        summary=agent.name,
                        source_ids=[],
                        evidence_ids=[],
                        confidence="medium",
                    )
                },
            )()
        return await original_run(agent, input, context=context)

    original_run = standard.Runner.run
    monkeypatch.setattr(standard.Runner, "run", slow_run)

    started = perf_counter()
    await standard.run_standard(WorkflowInput(query="query"))
    elapsed = perf_counter() - started

    assert elapsed < 0.12


async def test_sources_collected_from_research_are_deduplicated(monkeypatch) -> None:
    _patch_common_agents(monkeypatch)

    result = await standard.run_standard(WorkflowInput(query="query"))

    assert len(result.sources) == 2
