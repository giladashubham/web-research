from __future__ import annotations

from textual.widgets import Static

from webresearch.tui.app import WebResearchApp
from webresearch.tui.screens.settings import SettingsScreen


async def test_settings_reports_env_vars_and_workflow_count(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "set")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    app = WebResearchApp()
    async with app.run_test():
        await app.push_screen(SettingsScreen())
        content = str(app.screen.query_one("#settings-content", Static).render())
        assert "OPENAI_API_KEY: ✓" in content
        assert "TAVILY_API_KEY: ✗" in content
        assert "Workflows:" in content
