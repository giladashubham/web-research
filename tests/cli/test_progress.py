from __future__ import annotations

from io import StringIO

from webresearch.cli.progress import ProgressRenderer
from webresearch.events.types import (
    OutputTextDelta,
    StepCompleted,
    StepSkipped,
    StepStarted,
    ToolCall,
    Warning,
)


def test_progress_renders_expected_glyph_sequence() -> None:
    stream = StringIO()
    renderer = ProgressRenderer(stream)

    renderer.render(StepStarted(run_id="run_1", step="planner"))
    renderer.render(
        ToolCall(
            run_id="run_1",
            step="planner",
            tool_name="search",
            call_id="c1",
            arguments={},
        )
    )
    renderer.render(StepCompleted(run_id="run_1", step="planner"))
    renderer.render(StepSkipped(run_id="run_1", step="gap", reason="none"))
    renderer.render(Warning(run_id="run_1", message="warn"))
    renderer.render(OutputTextDelta(run_id="run_1", delta="answer"))

    output = stream.getvalue()
    assert ">  planner" in output
    assert "✓  planner" in output
    assert "-  gap  (skipped)" in output
    assert "   · search" in output
    assert "! warn" in output
    assert output.endswith("answer")


def test_quiet_silences_progress() -> None:
    stream = StringIO()
    renderer = ProgressRenderer(stream, quiet=True)

    renderer.render(StepStarted(run_id="run_1", step="planner"))

    assert stream.getvalue() == ""


def test_no_ansi_when_stream_is_not_tty() -> None:
    stream = StringIO()
    renderer = ProgressRenderer(stream)

    renderer.render(Warning(run_id="run_1", message="warn"))

    assert "\033[" not in stream.getvalue()
