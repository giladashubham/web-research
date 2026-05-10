from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TechnicalDueDiligenceConfig:
    workflow_id: str = "technical_due_diligence"
    min_max_rounds: int = 5
    research_max_turns: int = 50
    url_selector_model: str = "gpt-4.1-mini"
    url_selector_model_env: str = "WEBRESEARCH_URL_SELECTOR_MODEL"
    url_budgets: dict[str, int] = field(default_factory=lambda: {
        "docs": 8, "api": 5, "changelog": 5, "security": 4,
        "customers": 3, "blog": 3, "careers": 2, "pricing": 3, "other": 4,
    })
    min_coverage_categories: tuple[str, ...] = ("docs", "api", "changelog", "security")


CONFIG = TechnicalDueDiligenceConfig()
