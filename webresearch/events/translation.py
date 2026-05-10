from __future__ import annotations

from typing import Any

from webresearch.events.step import current_run_id, current_step, emit_event
from webresearch.events.types import (
    OutputTextDelta,
    ToolCall,
    ToolFailed,
    ToolResult,
)


async def translate_sdk_event(sdk_event: object) -> None:
    step = current_step()
    if step is None:
        return

    event_name = getattr(sdk_event, "name", None)
    item = getattr(sdk_event, "item", None)

    if event_name == "tool_called":
        raw_item = getattr(item, "raw_item", None)
        await emit_event(
            ToolCall(
                run_id=current_run_id(),
                step=step,
                tool_name=str(getattr(raw_item, "name", "tool")),
                call_id=_optional_str(getattr(raw_item, "call_id", None)) or "unknown",
                arguments=_as_dict(getattr(raw_item, "arguments", {})),
            )
        )
    elif event_name == "tool_output":
        raw_item = getattr(item, "raw_item", None)
        # item.raw_item for tool_output is usually the result object or a dict
        await emit_event(
            ToolResult(
                run_id=current_run_id(),
                step=step,
                tool_name="tool",
                call_id=_optional_str(_dict_get(raw_item, "call_id")) or "unknown",
                result=raw_item,
            )
        )
    elif event_name == "tool_error":
        raw_item = getattr(item, "raw_item", None)
        await emit_event(
            ToolFailed(
                run_id=current_run_id(),
                step=step,
                tool_name="tool",
                call_id=_optional_str(_dict_get(raw_item, "call_id")) or "unknown",
                error=str(raw_item),
            )
        )

    data = getattr(sdk_event, "data", None)
    delta = getattr(data, "delta", None)
    if step == "output" and getattr(data, "type", None) == "response.output_text.delta" and delta:
        await emit_event(OutputTextDelta(run_id=current_run_id(), delta=str(delta)))


def _dict_get(value: object, key: str) -> Any | None:
    if isinstance(value, dict):
        return value.get(key)
    return None


def _optional_str(value: Any | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_dict(value: Any) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {"raw": str(value)}
