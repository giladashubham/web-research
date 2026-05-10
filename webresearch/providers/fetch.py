from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import httpx
from pydantic import BaseModel, ConfigDict

from webresearch.context import FetchedPage
from webresearch.sources.url_normalize import normalize_url
from webresearch.types import FetchStatus, SourceInput

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext

ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/xhtml+xml",
    "application/xml",
    "text/html",
    "text/plain",
    "text/xml",
}
BODY_SIZE_LIMIT_BYTES = 5 * 1024 * 1024
USER_AGENT = "webresearch-agent/0.1"


class FetchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    status: Literal["fetched", "failed", "blocked"]
    byte_size: int = 0
    content_type: str | None = None
    truncated: bool = False
    reason: str | None = None
    source_id: str | None = None


class FetchProvider:
    def __init__(self, timeout: float = 30, body_limit_bytes: int = BODY_SIZE_LIMIT_BYTES) -> None:
        self._timeout = timeout
        self._body_limit = body_limit_bytes

    async def fetch(self, ctx: WorkflowContext, url: str) -> FetchResult:
        normalized_url = normalize_url(url)

        if normalized_url in ctx.pages:
            page = ctx.pages[normalized_url]
            source = ctx.sources.get_by_url(normalized_url) or ctx.sources.add(
                SourceInput(url=normalized_url)
            )
            return FetchResult(
                url=normalized_url,
                status="fetched",
                byte_size=len(page.body.encode("utf-8", errors="replace")),
                content_type=page.content_type,
                truncated=page.truncated,
                source_id=source.id,
            )

        source = ctx.sources.get_by_url(normalized_url) or ctx.sources.add(
            SourceInput(url=normalized_url)
        )

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                headers={"User-Agent": USER_AGENT},
            ) as client:
                response = await client.get(normalized_url)
        except httpx.HTTPError as exc:
            return _failure(ctx, normalized_url, source.id, f"HTTP request failed: {exc}")

        content_type = _content_type(response.headers.get("content-type"))
        if response.is_error:
            return _failure(
                ctx,
                normalized_url,
                source.id,
                f"HTTP status {response.status_code}",
                content_type,
            )

        if content_type not in ALLOWED_CONTENT_TYPES:
            reason = f"Blocked content type: {content_type or 'unknown'}"
            ctx.sources.mark_fetch_status(source.id, FetchStatus.BLOCKED)
            ctx.warnings.append(f"{normalized_url}: {reason}")
            return FetchResult(
                url=normalized_url,
                status="blocked",
                content_type=content_type,
                reason=reason,
                source_id=source.id,
            )

        body = response.content
        truncated = len(body) > self._body_limit
        if truncated:
            body = body[: self._body_limit]
            ctx.warnings.append(f"{normalized_url}: response body truncated to 5 MB")

        text = body.decode(response.encoding or "utf-8", errors="replace")
        ctx.pages[normalized_url] = FetchedPage(
            url=normalized_url,
            body=text,
            content_type=content_type,
            truncated=truncated,
        )
        ctx.sources.mark_fetch_status(source.id, FetchStatus.FETCHED)

        return FetchResult(
            url=normalized_url,
            status="fetched",
            byte_size=len(body),
            content_type=content_type,
            truncated=truncated,
            source_id=source.id,
        )


def _failure(
    ctx: WorkflowContext,
    normalized_url: str,
    source_id: str,
    reason: str,
    content_type: str | None = None,
) -> FetchResult:
    ctx.sources.mark_fetch_status(source_id, FetchStatus.FAILED)
    ctx.warnings.append(f"{normalized_url}: {reason}")
    return FetchResult(
        url=normalized_url,
        status="failed",
        content_type=content_type,
        reason=reason,
        source_id=source_id,
    )


def _content_type(header_value: str | None) -> str | None:
    if header_value is None:
        return None
    return header_value.split(";", maxsplit=1)[0].strip().lower()
