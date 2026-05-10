from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyNewsConfig:
    workflow_id: str = "company_news"
    research_max_turns: int = 40
    social_max_turns: int = 30
    company_max_turns: int = 25
    default_period_days: int = 30


CONFIG = CompanyNewsConfig()
