from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuickWorkflowConfig:
    workflow_id: str = "quick"
    depth_preset: str = "quick"
    research_lanes: tuple[str, ...] = ("official", "broad")
    recent_lane_enabled: bool = False
    reviewer_enabled: bool = False
    gap_loop_enabled: bool = False


CONFIG = QuickWorkflowConfig()
