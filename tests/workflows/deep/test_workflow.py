from __future__ import annotations

from contextlib import asynccontextmanager
from importlib.resources import files
from typing import TYPE_CHECKING

from webresearch.pipeline.runtime import ExecutionResult
from webresearch.types import Depth, WorkflowInput
from webresearch.workflows import load_workflows
from webresearch.workflows.deep import run_deep
from webresearch.workflows.deep.models import (
    FinalAnswer,
    GapResearchOutput,
    PlanOutput,
    ResearcherOutput,
    ReviewOutput,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

RUNTIME_MODULE = "webresearch.pipeline.runner"


def _make_exec_result(output: object) -> ExecutionResult:
    return ExecutionResult(
        output=output,
        input_tokens=100,
        output_tokens=50,
        model="gpt-4.1-mini",
    )


def _patch_runtime(monkeypatch) -> list[str]:
    reviewer_calls: list[str] = []
    call_index: list[int] = [0]

    plans = [
        PlanOutput(questions=["Q"], risks=[], search_strategy="Search."),
    ]
    research = [
        ResearcherOutput(summary="official", source_ids=[], evidence_ids=[], confidence="medium"),
    ]
    review_gapped = ReviewOutput(
        coverage=[], conflicts=[], has_critical_gaps=True, follow_up_queries=["gap"]
    )
    review_clean = ReviewOutput(
        coverage=[], conflicts=[], has_critical_gaps=False, follow_up_queries=[]
    )
    gaps = [
        GapResearchOutput(summary="gap", source_ids=[], evidence_ids=[], confidence="low"),
    ]

    async def mock_execute(step, _prompt, _context, _tools=None):
        name = step.name
        if name == "planner":
            out = plans[(call_index[0]) % len(plans)]
        elif name in ("official_researcher", "recent_researcher", "broad_researcher"):
            out = research[(call_index[0]) % len(research)]
        elif name == "reviewer":
            reviewer_calls.append("review")
            # Return has_gaps=True for first 2 calls, then clean on 3rd
            out = review_gapped if len(reviewer_calls) < 3 else review_clean
        elif name == "gap_researcher":
            out = gaps[(call_index[0]) % len(gaps)]
        elif name == "output":
            out = FinalAnswer(
                answer_markdown="Deep answer",
                findings=[],
                sources_cited=[],
                structured_data=None,
            )
        else:
            out = {}
        call_index[0] += 1
        return _make_exec_result(out)

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)
    return reviewer_calls


async def test_deep_loads_from_registry() -> None:
    assert "deep" in load_workflows()


async def test_deep_hits_max_rounds_two_and_stops(monkeypatch) -> None:
    reviewer_calls = _patch_runtime(monkeypatch)

    result = await run_deep(WorkflowInput(query="query", depth=Depth.for_preset("deep")))

    assert result.answer_markdown == "Deep answer"
    assert result.metadata.workflow_id == "deep"
    assert result.summary.count("gap") == 3
    assert len(reviewer_calls) == 3


async def test_deep_uses_standard_step_shape(monkeypatch) -> None:
    _patch_runtime(monkeypatch)
    steps: list[str] = []

    @asynccontextmanager
    async def record_step(name: str) -> AsyncIterator[None]:
        steps.append(name)
        yield

    monkeypatch.setattr("webresearch.pipeline.runner.step", record_step)

    await run_deep(WorkflowInput(query="query", depth=Depth.for_preset("deep")))

    assert steps == [
        "planner",
        "official_researcher",
        "recent_researcher",
        "broad_researcher",
        "reviewer",
        "gap_researcher",
        "reviewer",
        "gap_researcher",
        "reviewer",
        "gap_researcher",
        "output",
    ]


def test_deep_prompt_uses_jinja2_template() -> None:
    prompt = (files("webresearch.workflows.deep") / "prompts" / "official.j2").read_text(
        encoding="utf-8"
    )

    assert "official-source researcher" in prompt
    assert "ResearcherOutput" in prompt
    assert "Be thorough" in prompt
    assert "{{ input.query }}" in prompt
