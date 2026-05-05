from __future__ import annotations

import json
from importlib.resources import files

from agents import Agent
from jsonschema import validate

from tests._helpers.mock_model import MockModel
from webresearch.types import Depth, WorkflowInput
from webresearch.workflows.registry import WORKFLOWS
from webresearch.workflows.technical_due_diligence import (
    ClaimExtraction,
    CompetitorMapping,
    DiligenceGapResearch,
    EvidenceResearch,
    FinalMemoOutput,
    IntakePlan,
    TechnicalSubstanceReview,
    run_technical_due_diligence,
)

PACKAGE = "webresearch.workflows.technical_due_diligence"
WORKFLOW_MODULE = "webresearch.workflows.technical_due_diligence.workflow"


def _example_report() -> dict[str, object]:
    return json.loads(
        files(PACKAGE).joinpath("examples", "output.example.json").read_text(encoding="utf-8")
    )


def _agent(name: str, output_type: type[object], final_output: dict[str, object]) -> Agent:
    return Agent(
        name=name, output_type=output_type, model=MockModel([{"final_output": final_output}])
    )


def _patch_agents(monkeypatch, *, has_gaps: bool = False) -> None:
    report = _example_report()
    target = report["target"]
    claim = report["claims"][0]
    competitor = report["competitors"][0]

    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.intake_planner_agent",
        lambda: _agent(
            "intake",
            IntakePlan,
            {
                "target": target,
                "research_questions": ["What is public evidence vs inference?"],
                "likely_claim_areas": ["technical substance"],
                "competitor_names": ["Competitor One"],
                "priority_urls": ["https://example.com/docs"],
            },
        ),
    )
    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.claim_extractor_agent",
        lambda: _agent(
            "claims",
            ClaimExtraction,
            {
                "claims": [
                    {
                        "claim": claim["claim"],
                        "source_urls": claim["claim_source_urls"],
                        "category": "architecture",
                        "diligence_relevance": "high",
                    }
                ],
                "unknowns": ["Implementation details are not public."],
            },
        ),
    )
    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.evidence_researcher_agent",
        lambda: _agent(
            "evidence",
            EvidenceResearch,
            {
                "claim_assessments": [claim],
                "evidence_gaps": ["No benchmark evidence."],
                "source_urls": report["source_urls"],
            },
        ),
    )
    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.competitor_mapper_agent",
        lambda: _agent(
            "competitors",
            CompetitorMapping,
            {
                "competitors": [competitor],
                "comparison_summary": "Public competitor capabilities overlap.",
            },
        ),
    )
    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.technical_substance_reviewer_agent",
        lambda: _agent(
            "review",
            TechnicalSubstanceReview,
            {
                "executive_judgment": report["executive_judgment"],
                "technical_substance": report["technical_substance"],
                "replicability": report["replicability"],
                "code_review_follow_ups": report["code_review_follow_ups"],
                "has_critical_gaps": has_gaps,
                "follow_up_queries": ["Find architecture evidence"] if has_gaps else [],
            },
        ),
    )
    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.gap_researcher_agent",
        lambda: _agent(
            "gap",
            DiligenceGapResearch,
            {
                "summary": "Public gap research found no proprietary architecture proof.",
                "additional_claim_assessments": [],
                "additional_evidence_gaps": ["Architecture remains private."],
                "source_urls": ["https://example.com/docs"],
            },
        ),
    )
    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.final_memo_agent",
        lambda: _agent(
            "final",
            FinalMemoOutput,
            {
                "answer_markdown": (
                    "## Technical Due Diligence\n\n"
                    "Public evidence: docs describe APIs.\n\n"
                    "Inference: architecture depth is unclear.\n\n"
                    "Unknowns: code review is required."
                ),
                "report": report,
                "findings": [
                    {
                        "claim": claim["claim"],
                        "evidence_ids": [],
                        "source_ids": [],
                        "confidence": "medium",
                    }
                ],
            },
        ),
    )


async def test_diligence_workflow_is_registered() -> None:
    assert WORKFLOWS["technical_due_diligence"] is run_technical_due_diligence


async def test_diligence_workflow_returns_structured_report(monkeypatch) -> None:
    _patch_agents(monkeypatch)

    result = await run_technical_due_diligence(WorkflowInput(query="Evaluate Example Robotics"))

    assert result.metadata.workflow_id == "technical_due_diligence"
    assert result.structured_data_validation is not None
    assert result.structured_data_validation.valid is True
    assert result.structured_data is not None
    assert result.structured_data["target"]["company_name"] == "Example Robotics"
    assert result.findings[0].claim == "The product provides autonomous workflow planning."
    assert "Public evidence:" in result.answer_markdown
    assert "Inference:" in result.answer_markdown
    assert "Unknowns:" in result.answer_markdown

    schema = json.loads(files(PACKAGE).joinpath("schema.json").read_text(encoding="utf-8"))
    validate(instance=result.structured_data, schema=schema)


async def test_diligence_gap_loop_runs_when_review_reports_gaps(monkeypatch) -> None:
    _patch_agents(monkeypatch, has_gaps=True)

    result = await run_technical_due_diligence(
        WorkflowInput(
            query="Evaluate Example Robotics",
            depth=Depth.for_preset("standard"),
        )
    )

    assert "Public gap research" in result.summary
