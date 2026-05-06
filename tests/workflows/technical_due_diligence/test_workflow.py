from __future__ import annotations

import json
from importlib.resources import files

from agents import Agent
from jsonschema import validate

from tests._helpers.mock_model import MockModel
from webresearch.types import Depth, UrlsByCategory, WorkflowInput
from webresearch.workflows.registry import WORKFLOWS
from webresearch.workflows.technical_due_diligence import (
    ClaimExtraction,
    CompetitorMapping,
    DiligenceGapResearch,
    EvidenceResearch,
    FinalMemoOutput,
    IntakePlan,
    SelectedPriorityUrls,
    TechnicalSubstanceReview,
    UnresolvedClaim,
    run_technical_due_diligence,
)
from webresearch.workflows.technical_due_diligence.workflow import (
    _validated_priority_urls,
    claim_extractor_agent,
    competitor_mapper_agent,
    evidence_researcher_agent,
    final_memo_agent,
    gap_researcher_agent,
    intake_planner_agent,
    technical_substance_reviewer_agent,
    url_selector_agent,
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
    final_report = dict(report)
    final_report["release_activity"] = None
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
                "priority_urls_by_category": {
                    "docs": [
                        "https://example.com/docs",
                        "https://example.com/docs/deep-installation",
                    ],
                    "api": [],
                    "changelog": [
                        "https://example.com/changelog",
                        "https://example.com/changelog/v1",
                    ],
                    "pricing": [],
                    "security": [],
                    "customers": [],
                    "blog": [],
                    "careers": [],
                    "other": [],
                },
            },
        ),
    )
    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.url_selector_agent",
        lambda: _agent(
            "url_selector",
            SelectedPriorityUrls,
            {
                "priority_urls_by_category": {
                    "docs": ["https://example.com/docs"],
                    "api": [],
                    "changelog": ["https://example.com/changelog"],
                    "pricing": [],
                    "security": [],
                    "customers": [],
                    "blog": [],
                    "careers": [],
                    "other": [],
                },
                "selection_rationale": ["Use docs and changelog index pages."],
                "rejected_patterns": ["deep installation pages"],
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
                        "id": "claim_1",
                        "claim": claim["claim"],
                        "source_urls": claim["claim_source_urls"],
                        "category": "architecture",
                        "diligence_relevance": "high",
                    }
                ],
                "unknowns": ["Implementation details are not public."],
                "release_activity": {
                    "source_urls": ["https://example.com/changelog"],
                    "last_release_date": "2025-03-28",
                    "releases_last_12_months": 24,
                    "notable_releases": ["v2.1: added webhook support"],
                    "cadence_description": "approximately bi-weekly",
                },
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

    unresolved: list[dict[str, object]] = (
        [
            {
                "claim_id": "claim_1",
                "claim_text": claim["claim"],
                "reason_unresolved": (
                    "Docs describe the API but do not explain the retrieval mechanism."
                ),
                "artefact_types_to_chase": ["docs", "changelog"],
                "follow_up_queries": ["Find architecture evidence"],
            }
        ]
        if has_gaps
        else []
    )

    monkeypatch.setattr(
        f"{WORKFLOW_MODULE}.technical_substance_reviewer_agent",
        lambda: _agent(
            "review",
            TechnicalSubstanceReview,
            {
                "code_review_follow_ups": report["code_review_follow_ups"],
                "unresolved_claims": unresolved,
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
                "report": final_report,
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
    assert result.structured_data is not None
    assert result.structured_data["target"]["company_name"] == "Example Robotics"
    assert result.findings[0].claim == "The product provides autonomous workflow planning."
    assert "Public evidence:" in result.answer_markdown
    assert "Inference:" in result.answer_markdown
    assert "Unknowns:" in result.answer_markdown

    schema = json.loads(files(PACKAGE).joinpath("schema.json").read_text(encoding="utf-8"))
    validate(instance=result.structured_data, schema=schema)


async def test_diligence_gap_loop_runs_when_review_reports_unresolved(monkeypatch) -> None:
    _patch_agents(monkeypatch, has_gaps=True)

    result = await run_technical_due_diligence(
        WorkflowInput(
            query="Evaluate Example Robotics",
            depth=Depth.for_preset("standard"),
        )
    )

    assert "Public gap research" in result.summary


async def test_intake_plan_carries_categorised_urls(monkeypatch) -> None:
    _patch_agents(monkeypatch)

    result = await run_technical_due_diligence(WorkflowInput(query="Evaluate Example Robotics"))

    assert result.metadata.workflow_id == "technical_due_diligence"


async def test_unresolved_claim_model_round_trips() -> None:
    claim = UnresolvedClaim(
        claim_id="claim_1",
        claim_text="The product provides autonomous workflow planning.",
        reason_unresolved="Docs describe the API but do not explain the retrieval mechanism.",
        artefact_types_to_chase=["docs", "changelog"],
        follow_up_queries=["Search for architecture details"],
    )
    assert claim.claim_id == "claim_1"
    assert "docs" in claim.artefact_types_to_chase


async def test_priority_urls_by_category_is_categorised() -> None:
    cat = UrlsByCategory(
        docs=["https://example.com/docs"],
        changelog=["https://example.com/changelog"],
    )
    assert cat.docs == ["https://example.com/docs"]
    assert cat.api == []


async def test_url_selection_guardrails_reject_unknown_urls_and_fill_minimum_coverage() -> None:
    candidates = UrlsByCategory(
        docs=["https://example.com/docs", "https://example.com/docs/architecture"],
        api=["https://example.com/api/reference"],
        changelog=["https://example.com/release-notes", "https://example.com/release-notes/v2"],
        security=["https://example.com/security"],
    )
    selected = SelectedPriorityUrls(
        priority_urls_by_category=UrlsByCategory(
            docs=[
                "https://example.com/docs/architecture",
                "https://attacker.example/docs",
            ],
            changelog=["https://example.com/release-notes/v2"],
        )
    )

    guarded = _validated_priority_urls(candidates, selected)

    assert guarded.docs == ["https://example.com/docs/architecture"]
    assert guarded.api == ["https://example.com/api/reference"]
    assert guarded.changelog == ["https://example.com/release-notes/v2"]
    assert guarded.security == ["https://example.com/security"]


async def test_url_selection_guardrails_enforce_category_budgets() -> None:
    candidates = UrlsByCategory(
        docs=[f"https://example.com/docs/page-{index}" for index in range(12)],
        changelog=[f"https://example.com/release-notes/v{index}" for index in range(8)],
    )
    selected = SelectedPriorityUrls(priority_urls_by_category=candidates)

    guarded = _validated_priority_urls(candidates, selected)

    assert guarded.docs == candidates.docs[:8]
    assert guarded.changelog == candidates.changelog[:5]


def test_diligence_agents_disable_openai_response_storage() -> None:
    agents = [
        intake_planner_agent(),
        url_selector_agent(),
        claim_extractor_agent(),
        evidence_researcher_agent(),
        competitor_mapper_agent(),
        technical_substance_reviewer_agent(),
        gap_researcher_agent(),
        final_memo_agent(),
    ]

    assert all(agent.model_settings.store is False for agent in agents)


def test_url_selector_agent_uses_selector_model_env(monkeypatch) -> None:
    monkeypatch.setenv("WEBRESEARCH_URL_SELECTOR_MODEL", "gpt-test-selector")

    assert url_selector_agent().model == "gpt-test-selector"
