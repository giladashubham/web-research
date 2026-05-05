from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StandardWorkflowConfig:
    workflow_id: str = "standard"
    depth_preset: str = "standard"
    max_gap_rounds: int = 1
    research_lanes: tuple[str, ...] = ("official", "recent", "broad")
    reviewer_enabled: bool = True
    gap_loop_enabled: bool = True


CONFIG = StandardWorkflowConfig()
