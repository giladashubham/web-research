from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Footer, ListItem, ListView, Markdown, Static, TabbedContent, TabPane

from webresearch.tui.screen_base import WorkflowAwareScreen
from webresearch.tui.widgets.export_dialog import ExportDialog
from webresearch.tui.widgets.sources_table import SourcesTable
from webresearch.types import WorkflowResult


class ResultScreen(WorkflowAwareScreen):
    BINDINGS = [("e", "export", "Export")]

    def __init__(self, result: WorkflowResult, deltas_replay: str | None = None) -> None:
        super().__init__()
        self.result = result
        self.deltas_replay = deltas_replay

    def compose(self) -> ComposeResult:
        with TabbedContent(id="result-tabs"):
            with TabPane("Answer", id="answer-tab"):
                yield Markdown(
                    self.deltas_replay or self.result.answer_markdown,
                    id="answer-markdown",
                )
            with TabPane("Findings", id="findings-tab"):
                findings = ListView(id="findings-list")
                for finding in self.result.findings:
                    findings.append(ListItem(Static(f"{finding.claim} ({finding.confidence})")))
                yield findings
            with TabPane("Sources", id="sources-tab"):
                table = SourcesTable(id="sources-table")
                table.load_result(self.result)
                yield table
            with TabPane("Evidence", id="evidence-tab"):
                evidence = ListView(id="evidence-list")
                for note in self.result.evidence:
                    evidence.append(ListItem(Static(f"{note.source_id}: {note.note}")))
                yield evidence
            with TabPane("Warnings", id="warnings-tab"):
                yield Static("\n".join(self.result.warnings), id="result-warnings")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#answer-markdown", Markdown).update(self.result.answer_markdown)

    def action_export(self) -> None:
        self.app.push_screen(ExportDialog(self.result))
