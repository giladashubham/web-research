from __future__ import annotations

import json
from importlib.resources import files

from jsonschema import validate

from webresearch.pipeline.runtime import ExecutionResult
from webresearch.providers.discover import UrlsByCategory
from webresearch.types import Depth, WorkflowInput
from webresearch.workflows import load_workflows
from webresearch.workflows.technical_due_diligence import (
    ClaimExtraction,
    DiligenceGapResearch,
    EvidenceResearch,
    FinalMemoOutput,
    IntakePlan,
    SelectedPriorityUrls,
    TechnicalSubstanceReview,
    UnresolvedClaim,
    run_technical_due_diligence,
)
from webresearch.workflows.technical_due_diligence.agents import (
    _validated_priority_urls,
)

PACKAGE = "webresearch.workflows.technical_due_diligence"
RUNTIME_MODULE = "webresearch.pipeline.runner"


def _example_report() -> dict[str, object]:
    return json.loads(
        files(PACKAGE)
        .joinpath("examples", "output.example.json")
        .read_text(encoding="utf-8")
    )


def _make_exec_result(output: object) -> ExecutionResult:
    return ExecutionResult(
        output=output,
        input_tokens=100,
        output_tokens=50,
        model="gpt-4.1-mini",
    )


def _patch_runtime(monkeypatch, *, has_gaps: bool = False) -> list[str]:
    report = _example_report()
    final_report = dict(report)
    final_report["release_activity"] = None
    target = report["target"]
    claim = report["claims"][0]
    call_order: list[str] = []

    unresolvable: list[dict[str, object]] = (
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

    outputs: dict[str, object] = {
        "intake_planner": IntakePlan(
            target={
                "company_name": str(target.get("company_name", "")),
                "product_name": str(target.get("product_name", "")),
                "product_url": str(target.get("product_url", "")),
                "known_urls": [str(u) for u in target.get("known_urls", [])],
                "known_competitors": [
                    str(c) for c in target.get("known_competitors", [])
                ],
                "evaluation_prompt": str(target.get("evaluation_prompt", "")),
            },
            research_questions=["What is public evidence vs inference?"],
            likely_claim_areas=["technical substance"],
            claim_source_urls=[],
            evidence_urls_by_category=UrlsByCategory(
                docs=[
                    "https://example.com/docs",
                    "https://example.com/docs/deep-installation",
                ],
                api=[],
                changelog=[
                    "https://example.com/changelog",
                    "https://example.com/changelog/v1",
                ],
                security=[],
                customers=[],
                blog=[],
                careers=[],
                other=[],
            ),
        ),
        "url_selector": SelectedPriorityUrls(
            evidence_urls_by_category=UrlsByCategory(
                docs=["https://example.com/docs"],
                api=[],
                changelog=["https://example.com/changelog"],
                security=[],
                customers=[],
                blog=[],
                careers=[],
                other=[],
            ),
            selection_rationale=["Use docs and changelog index pages."],
            rejected_patterns=["deep installation pages"],
        ),
        "claim_extractor": ClaimExtraction(
            claims=[
                {
                    "id": "claim_1",
                    "claim": claim["claim"],
                    "source_urls": claim["claim_source_urls"],
                    "category": "architecture",
                    "diligence_relevance": "high",
                }
            ],
            unknowns=["Implementation details are not public."],
        ),
        "evidence_researcher": EvidenceResearch(
            claim_assessments=[claim],
            evidence_gaps=[
                {
                    "claim_id": "claim_1",
                    "gap_type": "documentation_gap",
                    "description": "No benchmark evidence.",
                }
            ],
            source_urls=report["source_urls"],
            release_activity=None,
        ),
        "technical_substance_reviewer": TechnicalSubstanceReview(
            code_review_follow_ups=report["code_review_follow_ups"],
            unresolved_claims=unresolvable,
        ),
        "gap_researcher": DiligenceGapResearch(
            summary="Public gap research found no proprietary architecture proof.",
            additional_claim_assessments=[],
            additional_evidence_gaps=[
                {
                    "claim_id": "claim_1",
                    "gap_type": "documentation_gap",
                    "description": "Architecture remains private.",
                }
            ],
            source_urls=["https://example.com/docs"],
        ),
        "final_memo": FinalMemoOutput(
            answer_markdown=(
                "## Technical Due Diligence\n\n"
                "Public evidence: docs describe APIs.\n\n"
                "Inference: architecture depth is unclear.\n\n"
                "Unknowns: code review is required."
            ),
            report=final_report,
            findings=[
                {
                    "claim": claim["claim"],
                    "evidence_ids": [],
                    "source_ids": [],
                    "confidence": "medium",
                }
            ],
        ),
    }

    async def mock_execute(step, _prompt, _context, _tools=None):
        call_order.append(step.name)
        out = outputs.get(step.name, {})
        return _make_exec_result(out)

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)
    return call_order


async def test_diligence_workflow_is_registered() -> None:
    assert "technical_due_diligence" in load_workflows()


async def test_diligence_workflow_returns_structured_report(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    result = await run_technical_due_diligence(
        WorkflowInput(query="Evaluate Example Robotics")
    )

    assert result.metadata.workflow_id == "technical_due_diligence"
    assert result.structured_data is not None
    assert result.structured_data["target"]["company_name"] == "Example Robotics"
    assert (
        result.findings[0].claim == "The product provides autonomous workflow planning."
    )
    assert "Public evidence:" in result.answer_markdown
    assert "Inference:" in result.answer_markdown
    assert "Unknowns:" in result.answer_markdown

    schema = json.loads(
        files(PACKAGE).joinpath("schema.json").read_text(encoding="utf-8")
    )
    validate(instance=result.structured_data, schema=schema)


async def test_diligence_gap_loop_runs_when_review_reports_unresolved(
    monkeypatch,
) -> None:
    _patch_runtime(monkeypatch, has_gaps=True)

    result = await run_technical_due_diligence(
        WorkflowInput(
            query="Evaluate Example Robotics",
            depth=Depth.for_preset("standard"),
        )
    )

    assert "Public gap research" in result.summary


async def test_intake_plan_carries_categorised_urls(monkeypatch) -> None:
    _patch_runtime(monkeypatch)

    result = await run_technical_due_diligence(
        WorkflowInput(query="Evaluate Example Robotics")
    )

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


async def test_url_selection_guardrails_reject_unknown_urls_and_fill_minimum_coverage() -> (
    None
):
    candidates = UrlsByCategory(
        docs=["https://example.com/docs", "https://example.com/docs/architecture"],
        api=["https://example.com/api/reference"],
        changelog=[
            "https://example.com/release-notes",
            "https://example.com/release-notes/v2",
        ],
        security=["https://example.com/security"],
    )
    selected = SelectedPriorityUrls(
        evidence_urls_by_category=UrlsByCategory(
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
    selected = SelectedPriorityUrls(evidence_urls_by_category=candidates)

    guarded = _validated_priority_urls(candidates, selected)

    assert guarded.docs == candidates.docs[:8]
    assert guarded.changelog == candidates.changelog[:5]
