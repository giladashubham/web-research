from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webresearch.pipeline.state import PipelineState


class HookSignal(Enum):
    CONTINUE = "continue"
    SKIP = "skip"
    REPEAT = "repeat"


PreHook = Callable[["PipelineState"], Awaitable[HookSignal]]
PostHook = Callable[["PipelineState"], Awaitable[HookSignal]]
