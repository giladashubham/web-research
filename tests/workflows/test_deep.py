from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

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
from webresearch.agents.prompts import load_prompt
from webresearch.types import WorkflowInput
from webresearch.workflows import deep
from webresearch.workflows.registry import WORKFLOWS

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def _agent(name: str, output_type: type[object], script: list[dict[str, object]]) -> Agent:
    agent_output_type = (
        AgentOutputSchema(output_type, strict_json_schema=False)
        if output_type is FinalAnswer
        else output_type
    )
    return Agent(name=name, output_type=agent_output_type, model=MockModel(script))


def _research_agent(name: str) -> Agent:
    return _agent(
        name,
        ResearcherOutput,
        [
            {
                "final_output": {
                    "summary": name,
                    "source_ids": [],
                    "evidence_ids": [],
                    "confidence": "medium",
                }
            }
        ],
    )


def _review_agent(has_gaps: bool = True) -> Agent:
    return _agent(
        "reviewer",
        ReviewOutput,
        [
            {
                "final_output": {
                    "coverage": [],
                    "conflicts": [],
                    "has_critical_gaps": has_gaps,
                    "follow_up_queries": ["gap"] if has_gaps else [],
                }
            }
        ],
    )


def _patch_agents(monkeypatch) -> list[str]:
    reviewer_calls: list[str] = []
    monkeypatch.setattr(
        deep,
        "planner_agent",
        lambda _depth="deep": _agent(
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
        deep,
        "official_researcher_agent",
        lambda _depth="deep": _research_agent("official"),
    )
    monkeypatch.setattr(
        deep,
        "recent_researcher_agent",
        lambda _depth="deep": _research_agent("recent"),
    )
    monkeypatch.setattr(
        deep,
        "broad_researcher_agent",
        lambda _depth="deep": _research_agent("broad"),
    )
    monkeypatch.setattr(
        deep,
        "gap_researcher_agent",
        lambda _depth="deep": _agent(
            "gap",
            GapResearchOutput,
            [
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

    def reviewer_factory(_depth: str = "deep") -> Agent:
        reviewer_calls.append("review")
        return _review_agent(True)

    monkeypatch.setattr(deep, "reviewer_agent", reviewer_factory)
    monkeypatch.setattr(
        deep,
        "output_agent",
        lambda _schema=None, _depth="deep": _agent(
            "output",
            FinalAnswer,
            [
                {
                    "final_output": {
                        "answer_markdown": "Deep answer",
                        "findings": [],
                        "sources_cited": [],
                        "structured_data": None,
                    }
                }
            ],
        ),
    )
    return reviewer_calls


async def test_deep_loads_from_registry() -> None:
    assert WORKFLOWS["deep"] is deep.run_deep


async def test_deep_hits_max_rounds_two_and_stops(monkeypatch) -> None:
    reviewer_calls = _patch_agents(monkeypatch)

    result = await deep.run_deep(WorkflowInput(query="query"))

    assert result.answer_markdown == "Deep answer"
    assert result.metadata.workflow_id == "deep"
    assert result.summary.count("gap") == 2
    assert len(reviewer_calls) == 3


async def test_deep_uses_standard_step_shape(monkeypatch) -> None:
    _patch_agents(monkeypatch)
    steps: list[str] = []

    @asynccontextmanager
    async def record_step(name: str) -> AsyncIterator[None]:
        steps.append(name)
        yield

    monkeypatch.setattr(deep, "step", record_step)

    await deep.run_deep(WorkflowInput(query="query"))

    assert steps == [
        "planner",
        "research",
        "reviewer",
        "gap",
        "reviewer",
        "gap",
        "reviewer",
        "output",
    ]


def test_deep_prompt_uses_same_prompt_with_depth_extras() -> None:
    prompt = load_prompt("official.md", "deep")

    assert "Official researcher placeholder prompt." in prompt
    assert "Be thorough" in prompt
