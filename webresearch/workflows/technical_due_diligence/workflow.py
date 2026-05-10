from __future__ import annotations

from typing import TYPE_CHECKING

from webresearch.workflows.technical_due_diligence.pipeline import PIPELINE

if TYPE_CHECKING:
    from webresearch.types import WorkflowInput, WorkflowResult


async def run_technical_due_diligence(input: WorkflowInput) -> WorkflowResult:
    return await PIPELINE.run(input)
