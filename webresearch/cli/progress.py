from __future__ import annotations

import sys
from time import perf_counter
from typing import TextIO

from webresearch.events.types import (
    OutputTextDelta,
    StepCompleted,
    StepSkipped,
    StepStarted,
    ToolCompleted,
    ToolStarted,
    Warning,
    WorkflowEvent,
    WorkflowFailed,
)


class ProgressRenderer:
    def __init__(self, stream: TextIO | None = None, *, quiet: bool = False) -> None:
        self._stream = stream if stream is not None else sys.stderr
        self._quiet = quiet
        self._step_starts: dict[str, float] = {}
        self._use_color = self._stream.isatty()

    def render(self, event: WorkflowEvent) -> None:
        if self._quiet:
            return

        if isinstance(event, StepStarted):
            self._step_starts[event.step] = perf_counter()
            self._line(f">  {event.step}")
        elif isinstance(event, StepCompleted):
            elapsed = perf_counter() - self._step_starts.get(event.step, perf_counter())
            self._line(f"✓  {event.step}  ({elapsed:.0f}s)")
        elif isinstance(event, StepSkipped):
            self._line(f"-  {event.step}  (skipped)")
        elif isinstance(event, ToolStarted | ToolCompleted):
            self._line(self._dim(f"   · {event.tool_name}"))
        elif isinstance(event, Warning):
            self._line(self._yellow(f"! {event.message}"))
        elif isinstance(event, WorkflowFailed):
            self._line(self._red(f"✗  workflow failed: {event.error}"))
        elif isinstance(event, OutputTextDelta):
            self._stream.write(event.delta)
            self._stream.flush()

    def _line(self, text: str) -> None:
        self._stream.write(f"{text}\n")
        self._stream.flush()

    def _dim(self, text: str) -> str:
        if not self._use_color:
            return text
        return f"\033[2m{text}\033[0m"

    def _yellow(self, text: str) -> str:
        if not self._use_color:
            return text
        return f"\033[33m{text}\033[0m"

    def _red(self, text: str) -> str:
        if not self._use_color:
            return text
        return f"\033[31m{text}\033[0m"
