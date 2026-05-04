from __future__ import annotations

import os
import re
from time import perf_counter

import pytest

from webresearch.events.stream import stream_workflow
from webresearch.types import FetchStatus, WorkflowInput, WorkflowResult
from webresearch.workflows.standard import run_standard

pytestmark = pytest.mark.live


_missing_live_env = not (
    os.getenv("LIVE_LLM") == "1" and os.getenv("OPENAI_API_KEY") and os.getenv("TAVILY_API_KEY")
)


@pytest.mark.skipif(
    _missing_live_env,
    reason="set LIVE_LLM=1, OPENAI_API_KEY, and TAVILY_API_KEY to run live integration",
)
async def test_live_standard_workflow_completes_with_real_services() -> None:
    captured: WorkflowResult | None = None

    async def workflow(input: WorkflowInput) -> WorkflowResult:
        nonlocal captured
        captured = await run_standard(input)
        return captured

    started = perf_counter()
    events = [
        event
        async for event in stream_workflow(
            workflow,
            WorkflowInput(query="What is the current Node.js LTS version?"),
        )
    ]
    elapsed = perf_counter() - started

    assert elapsed < 120
    assert any(event.kind == "workflow_completed" for event in events)
    assert not any(event.kind == "workflow_failed" for event in events)
    assert captured is not None
    assert captured.answer_markdown.strip()
    assert re.search(r"\b\d{2,3}(?:\.\d+){0,2}\b", captured.answer_markdown)

    fetched_sources = [
        source for source in captured.sources if source.fetch_status == FetchStatus.FETCHED
    ]
    assert len(fetched_sources) >= 2
    assert captured.evidence
