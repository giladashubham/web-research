from __future__ import annotations

from webresearch.types import WorkflowInput, WorkflowResult
from webresearch.workflows.company_news.pipeline import PIPELINE


async def run_company_news(input: WorkflowInput) -> WorkflowResult:
    return await PIPELINE.run(input)
