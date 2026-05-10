from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

    from webresearch.context import WorkflowContext
    from webresearch.types import WorkflowInput


@dataclass
class PipelineState:
    input: WorkflowInput
    run_id: str
    started_at: datetime
    context: WorkflowContext
    outputs: dict[str, Any] = field(default_factory=dict)
    iteration_count: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
