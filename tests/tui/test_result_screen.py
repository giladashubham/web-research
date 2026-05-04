from __future__ import annotations

from textual.widgets import Markdown

from tests.tui.helpers import make_result
from webresearch.tui.app import WebResearchApp
from webresearch.tui.screens.result import ResultScreen
from webresearch.tui.widgets.export_dialog import ExportDialog


class _ExportButton:
    id = "export-confirm"


class _ExportEvent:
    button = _ExportButton()


async def test_result_tabs_render_data() -> None:
    app = WebResearchApp()
    async with app.run_test():
        await app.push_screen(ResultScreen(make_result()))
        assert "Answer" in app.screen.query_one("#answer-markdown", Markdown).source


async def test_live_deltas_replace_with_canonical_answer() -> None:
    app = WebResearchApp()
    async with app.run_test():
        await app.push_screen(ResultScreen(make_result(), deltas_replay="draft"))
        assert "Answer" in app.screen.query_one("#answer-markdown", Markdown).source


async def test_export_writes_json(tmp_path) -> None:
    app = WebResearchApp()
    async with app.run_test():
        dialog = ExportDialog(make_result())
        await app.push_screen(dialog)
        path = tmp_path / "result.json"
        dialog.query_one("#export-path").value = str(path)
        await dialog.on_button_pressed(_ExportEvent())
        assert path.exists()


async def test_export_refuses_overwrite(tmp_path) -> None:
    app = WebResearchApp()
    async with app.run_test():
        dialog = ExportDialog(make_result())
        await app.push_screen(dialog)
        path = tmp_path / "result.json"
        path.write_text("existing")
        dialog.query_one("#export-path").value = str(path)
        await dialog.on_button_pressed(_ExportEvent())
        assert "refusing" in str(dialog.query_one("#export-error").render())
