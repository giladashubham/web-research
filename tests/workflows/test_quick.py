from __future__ import annotations

from agents import Agent
from agents.agent_output import AgentOutputSchema

from tests._helpers.mock_model import MockModel
from webresearch.agents.models import FinalAnswer, PlanOutput, ResearcherOutput
from webresearch.types import WorkflowInput
from webresearch.workflows import quick
from webresearch.workflows.registry import WORKFLOWS


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


def _patch_agents(monkeypatch) -> None:
    monkeypatch.setattr(
        quick,
        "planner_agent",
        lambda _depth="quick": _agent(
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
        quick,
        "official_researcher_agent",
        lambda _depth="quick": _research_agent("official"),
    )
    monkeypatch.setattr(
        quick,
        "broad_researcher_agent",
        lambda _depth="quick": _research_agent("broad"),
    )
    monkeypatch.setattr(
        quick,
        "output_agent",
        lambda _schema=None, _depth="quick": _agent(
            "output",
            FinalAnswer,
            [
                {
                    "final_output": {
                        "answer_markdown": "Quick answer",
                        "findings": [],
                        "sources_cited": [],
                        "structured_data": None,
                    }
                }
            ],
        ),
    )


async def test_quick_loads_from_registry() -> None:
    assert WORKFLOWS["quick"] is quick.run_quick


async def test_quick_runs_end_to_end_against_mock_model(monkeypatch) -> None:
    _patch_agents(monkeypatch)

    result = await quick.run_quick(WorkflowInput(query="query"))

    assert result.answer_markdown == "Quick answer"
    assert result.metadata.workflow_id == "quick"
    assert "official" in result.summary
    assert "broad" in result.summary


async def test_quick_returns_without_gap_warnings(monkeypatch) -> None:
    _patch_agents(monkeypatch)

    result = await quick.run_quick(WorkflowInput(query="query"))

    assert not any("gap" in warning.lower() for warning in result.warnings)
