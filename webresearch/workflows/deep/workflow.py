from __future__ import annotations

from webresearch.workflows.deep.pipeline import PIPELINE


async def run_deep(input):  # type: ignore[no-untyped-def]
    return await PIPELINE.run(input)
