from __future__ import annotations


class SearchProviderError(Exception):
    def __init__(self, status: int, body_excerpt: str) -> None:
        self.status = status
        self.body_excerpt = body_excerpt
        super().__init__(f"Search provider request failed with status {status}: {body_excerpt}")
