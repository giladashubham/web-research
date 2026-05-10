from __future__ import annotations

from collections.abc import Callable, Sequence

from webresearch.sources.url_normalize import normalize_url
from webresearch.types import FetchStatus, SourceInput, SourceRecord

SourceAddedCallback = Callable[[SourceRecord], None]


class SourceRegistry:
    def __init__(
        self,
        source_added: SourceAddedCallback | None = None,
        max_sources: int | None = None,
    ) -> None:
        self._source_added = source_added
        self._max_sources = max_sources
        self._records: list[SourceRecord] = []
        self._by_id: dict[str, SourceRecord] = {}
        self._by_url: dict[str, SourceRecord] = {}

    def add(self, source_input: SourceInput) -> SourceRecord:
        normalized_url = normalize_url(source_input.url)
        existing = self._by_url.get(normalized_url)
        if existing is not None:
            return existing

        if self._max_sources is not None and len(self._records) >= self._max_sources:
            return self._records[-1] if self._records else existing  # type: ignore[return-value]

        source_id = f"src_{len(self._records) + 1}"
        record = SourceRecord(
            id=source_id,
            url=normalized_url,
            title=source_input.title,
            snippet=source_input.snippet,
            publisher=source_input.publisher,
            published_at=source_input.published_at,
            accessed_at=source_input.accessed_at,
            is_primary=source_input.is_primary,
        )
        self._records.append(record)
        self._by_id[source_id] = record
        self._by_url[normalized_url] = record

        if self._source_added is not None:
            self._source_added(record)

        return record

    def get(self, source_id: str) -> SourceRecord | None:
        return self._by_id.get(source_id)

    def get_by_url(self, url: str) -> SourceRecord | None:
        return self._by_url.get(normalize_url(url))

    def list(self) -> Sequence[SourceRecord]:
        return tuple(self._records)

    def mark_fetch_status(self, source_id: str, status: FetchStatus) -> None:
        record = self._by_id[source_id]
        record.fetch_status = status
