from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict

from webresearch.tools.extract_content import extract_content
from webresearch.tools.fetch_url import fetch_url

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext


class FetchAndExtractResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    status: Literal["extracted", "failed", "blocked"]
    text: str = ""
    char_count: int = 0
    truncated: bool = False
    reason: str | None = None
    source_id: str | None = None
    artifact_id: str | None = None


async def fetch_and_extract(
    ctx: WorkflowContext,
    url: str,
    query: str | None = None,
) -> FetchAndExtractResult:
    fetch_result = await fetch_url(ctx, url)
    if fetch_result.status != "fetched":
        return FetchAndExtractResult(
            url=fetch_result.url,
            status=fetch_result.status,  # type: ignore[arg-type]
            reason=fetch_result.reason,
            source_id=fetch_result.source_id,
        )
    extract_result = await extract_content(ctx, fetch_result.url, query)
    return FetchAndExtractResult(
        url=fetch_result.url,
        status=extract_result.status,  # type: ignore[arg-type]
        text=extract_result.text,
        char_count=extract_result.char_count,
        truncated=extract_result.truncated,
        reason=extract_result.reason,
        source_id=fetch_result.source_id,
        artifact_id=extract_result.artifact_id,
    )
