from __future__ import annotations

import json
from typing import Annotated, Literal

import typer

from webresearch.workflows import WorkflowEntry, load_workflow_entries

OutputFormat = Literal["table", "json"]


def list_workflows(
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format."),
    ] = "table",
) -> None:
    entries = load_workflow_entries()
    if output_format == "json":
        typer.echo(json.dumps([entry.model_dump() for entry in entries], indent=2))
        return

    typer.echo(_table(entries))


def _table(entries: list[WorkflowEntry]) -> str:
    rows = [(entry.id, entry.name, entry.description) for entry in entries]
    widths = [
        max(len("id"), *(len(row[0]) for row in rows)),
        max(len("name"), *(len(row[1]) for row in rows)),
        max(len("description"), *(len(row[2]) for row in rows)),
    ]
    lines = [
        f"{'id':<{widths[0]}}  {'name':<{widths[1]}}  {'description':<{widths[2]}}",
        f"{'-' * widths[0]}  {'-' * widths[1]}  {'-' * widths[2]}",
    ]
    lines.extend(
        f"{workflow_id:<{widths[0]}}  {name:<{widths[1]}}  {description:<{widths[2]}}"
        for workflow_id, name, description in rows
    )
    return "\n".join(lines)
