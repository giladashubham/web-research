from __future__ import annotations

from webresearch.types import WorkflowInput, WorkflowResult
from webresearch.workflows.technical_due_diligence.pipeline import PIPELINE


async def run_technical_due_diligence(input: WorkflowInput) -> WorkflowResult:
    return await PIPELINE.run(input)
