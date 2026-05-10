from __future__ import annotations

from typing import TYPE_CHECKING

from webresearch.workflows.deep.pipeline import PIPELINE

if TYPE_CHECKING:
    from webresearch.types import WorkflowInput, WorkflowResult


async def run_deep(input: WorkflowInput) -> WorkflowResult:
    return await PIPELINE.run(input)
