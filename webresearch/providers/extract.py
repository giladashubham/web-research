from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

import trafilatura
from pydantic import BaseModel, ConfigDict

from webresearch.sources.url_normalize import normalize_url
from webresearch.types import EvidenceArtifact, EvidenceNote

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext

MAX_EXTRACTED_CHARS = 8000


class ExtractResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    status: Literal["extracted", "failed"]
    text: str = ""
    char_count: int = 0
    truncated: bool = False
    reason: str | None = None
    source_id: str | None = None
    artifact_id: str | None = None


class ExtractProvider:
    def __init__(self, max_chars: int = MAX_EXTRACTED_CHARS) -> None:
        self._max_chars = max_chars

    async def extract(
        self, ctx: WorkflowContext, url: str, query: str | None = None
    ) -> ExtractResult:
        _ = query
        normalized_url = normalize_url(url)
        page = ctx.pages.get(normalized_url)
        if page is None:
            return ExtractResult(
                url=normalized_url,
                status="failed",
                reason="No fetched page body found",
            )

        extracted = trafilatura.extract(page.body, url=normalized_url, favor_recall=True)
        if extracted is None or not extracted.strip():
            return ExtractResult(url=normalized_url, status="failed", reason="No content extracted")

        text = extracted.strip()
        truncated = len(text) > self._max_chars
        if truncated:
            text = text[: self._max_chars]

        source = ctx.sources.get_by_url(normalized_url)
        evidence_id = f"ev_{len(ctx.evidence) + 1}"
        source_id = source.id if source is not None else ""
        ctx.evidence.append(
            EvidenceNote(
                id=evidence_id,
                source_id=source_id,
                note=text,
                relevance=query,
            )
        )
        artifact_id = f"artifact_{len(ctx.artifacts) + 1}"
        ctx.artifacts.append(
            EvidenceArtifact(
                id=artifact_id,
                title=f"Extracted evidence for {normalized_url}",
                created_at=datetime.now(UTC),
                evidence_ids=[evidence_id],
            )
        )

        return ExtractResult(
            url=normalized_url,
            status="extracted",
            text=text,
            char_count=len(text),
            truncated=truncated,
            source_id=source_id if source is not None else None,
            artifact_id=artifact_id,
        )
