from __future__ import annotations

from webresearch.tui.app import WebResearchApp
from webresearch.tui.screens.query import QueryScreen


async def test_home_shows_all_workflows() -> None:
    app = WebResearchApp()
    async with app.run_test():
        assert app.screen.query_one("#workflow-standard") is not None
        assert app.screen.query_one("#workflow-technical_due_diligence") is not None


async def test_selecting_workflow_pushes_query() -> None:
    app = WebResearchApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert isinstance(app.screen, QueryScreen)
