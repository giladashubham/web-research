from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from webresearch.types import WorkflowResult

OutputFormat = Literal["json", "md"]


def format_result(result: WorkflowResult, output_format: OutputFormat) -> str:
    if output_format == "json":
        return result.model_dump_json(indent=2)
    return _markdown(result)


def write_output(content: str, out: str | None) -> None:
    if out is None:
        print(content)
        return
    Path(out).write_text(content, encoding="utf-8")


def _markdown(result: WorkflowResult) -> str:
    sections = [result.answer_markdown.rstrip(), "", "## Sources"]
    if result.sources:
        sections.extend(
            f"{index}. {source.title or source.url} - {source.url}"
            for index, source in enumerate(result.sources, 1)
        )
    else:
        sections.append("No sources.")

    if result.warnings:
        sections.extend(["", "## Warnings"])
        sections.extend(f"- {warning}" for warning in result.warnings)

    return "\n".join(sections)
