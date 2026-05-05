from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webresearch.types import WorkflowInput, WorkflowResult


async def run_technical_due_diligence(input: WorkflowInput) -> WorkflowResult:
    _ = input
    msg = "technical_due_diligence workflow skeleton is not implemented yet"
    raise NotImplementedError(msg)
