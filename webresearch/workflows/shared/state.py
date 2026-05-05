from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime

    from webresearch.agents.models import (
        FinalAnswer,
        GapResearchOutput,
        PlanOutput,
        ResearcherOutput,
        ReviewOutput,
    )
    from webresearch.types import Artifact, Depth, WorkflowInput


@dataclass
class WorkflowState:
    input: WorkflowInput
    depth: Depth
    run_id: str
    started_at: datetime
    plan: PlanOutput | None = None
    research: list[ResearcherOutput] = field(default_factory=list)
    review: ReviewOutput | None = None
    gaps: list[GapResearchOutput] = field(default_factory=list)
    final: FinalAnswer | None = None
    warnings: list[str] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)

    def research_prompt(self) -> str:
        return "\n".join(
            [
                f"Query: {self.input.query}",
                f"Instructions: {self.input.instructions or ''}",
                "Plan:",
                _json(self.plan),
            ]
        )

    def review_prompt(self) -> str:
        return "\n".join(
            [
                f"Query: {self.input.query}",
                "Plan:",
                _json(self.plan),
                "Research:",
                _json(self.research),
                "Gap research:",
                _json(self.gaps),
            ]
        )

    def gap_prompt(self) -> str:
        return "\n".join(
            [
                f"Query: {self.input.query}",
                "Review:",
                _json(self.review),
                "Prior research:",
                _json(self.research),
            ]
        )

    def output_prompt(self) -> str:
        return "\n".join(
            [
                f"Query: {self.input.query}",
                "Plan:",
                _json(self.plan),
                "Research:",
                _json(self.research),
                "Gap research:",
                _json(self.gaps),
                "Review:",
                _json(self.review),
            ]
        )

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts.append(artifact)


def _json(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, list):
        dumped: object = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in value
        ]
    elif isinstance(value, BaseModel):
        dumped = value.model_dump(mode="json")
    else:
        dumped = value
    return json.dumps(dumped, sort_keys=True, indent=2)
