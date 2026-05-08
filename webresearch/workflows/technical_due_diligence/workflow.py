from __future__ import annotations

from webresearch.workflows.technical_due_diligence.pipeline import PIPELINE


async def run_technical_due_diligence(input):  # type: ignore[no-untyped-def]
    return await PIPELINE.run(input)
