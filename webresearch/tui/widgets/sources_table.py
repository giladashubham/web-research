from __future__ import annotations

from textual.widgets import DataTable

from webresearch.types import WorkflowResult


class SourcesTable(DataTable):
    def load_result(self, result: WorkflowResult) -> None:
        self.clear(columns=True)
        self.add_columns("id", "publisher", "title", "url", "fetch")
        for source in result.sources:
            self.add_row(
                source.id,
                source.publisher or "",
                source.title or "",
                source.url,
                source.fetch_status or "",
            )
