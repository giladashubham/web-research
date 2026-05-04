from __future__ import annotations

from typing import Protocol

from pydantic import AwareDatetime, BaseModel, ConfigDict


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    title: str
    snippet: str
    publisher: str | None = None
    published_at: AwareDatetime | None = None


class SearchProvider(Protocol):
    id: str

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]: ...
