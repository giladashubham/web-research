from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeepWorkflowConfig:
    workflow_id: str = "deep"
    depth_preset: str = "deep"
    max_gap_rounds: int = 2
    max_sources: int = 20
    researcher_max_turns: int = 35
    research_lanes: tuple[str, ...] = ("official", "recent", "broad")
    reviewer_enabled: bool = True
    gap_loop_enabled: bool = True


CONFIG = DeepWorkflowConfig()
