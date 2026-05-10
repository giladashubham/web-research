from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Literal

import typer

from webresearch.cli.formats import format_result, write_output
from webresearch.cli.progress import ProgressRenderer
from webresearch.events.jsonc_writer import JSONCWriter
from webresearch.events.stream import stream_workflow
from webresearch.events.types import WorkflowFailed, WorkflowStarted
from webresearch.types import Depth, WorkflowInput, WorkflowResult
from webresearch.workflows import load_workflows

OutputFormat = Literal["json", "md"]


def run_command(  # noqa: PLR0913
    query: Annotated[str, typer.Argument(help="Research query.")],
    workflow: Annotated[str, typer.Argument(help="Workflow id.")] = "deep",
    depth: Annotated[str, typer.Option("--depth", help="Depth preset.")] = "standard",
    instructions: Annotated[str | None, typer.Option("--instructions")] = None,
    max_sources: Annotated[int | None, typer.Option("--max-sources")] = None,
    out: Annotated[str | None, typer.Option("--out")] = None,
    events_out: Annotated[str | None, typer.Option("--events-out")] = None,
    output_format: Annotated[OutputFormat, typer.Option("--format")] = "json",
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    try:
        result = asyncio.run(
            _run(
                workflow=workflow,
                query=query,
                depth=depth,
                instructions=instructions,
                max_sources=max_sources,
                quiet=quiet,
                events_out=events_out,
            )
        )
    except KeyError:
        typer.echo(f"Unknown workflow: {workflow}", err=True)
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except OSError as exc:
        typer.echo(f"IO error: {exc}", err=True)
        raise typer.Exit(3) from None

    try:
        write_output(format_result(result, output_format), out)
    except OSError as exc:
        typer.echo(f"IO error: {exc}", err=True)
        raise typer.Exit(3) from None


async def _run(  # noqa: PLR0913
    *,
    workflow: str,
    query: str,
    depth: str,
    instructions: str | None,
    max_sources: int | None,
    quiet: bool,
    events_out: str | None,
) -> WorkflowResult:
    workflow_fn = load_workflows()[workflow]
    workflow_input = WorkflowInput(
        query=query,
        depth=Depth.for_preset(depth),
        instructions=instructions,
        max_sources=max_sources,
    )
    renderer = ProgressRenderer(quiet=quiet)
    writer: JSONCWriter | None = None
    result: WorkflowResult | None = None

    async def capturing_workflow(input_: WorkflowInput) -> WorkflowResult:
        nonlocal result
        result = await workflow_fn(input_)
        return result

    try:
        async for event in stream_workflow(capturing_workflow, workflow_input):
            if isinstance(event, WorkflowStarted):
                writer = JSONCWriter(_resolve_events_path(events_out, event.run_id))
                writer.open(event.run_id, event.workflow_id, query)

            if writer:
                writer.write_event(event)

            renderer.render(event)
            if isinstance(event, WorkflowFailed):
                raise typer.Exit(1)
    finally:
        if writer:
            writer.close()

    if result is None:
        msg = "Workflow did not produce a result"
        raise RuntimeError(msg)
    return result


def _resolve_events_path(events_out: str | None, run_id: str) -> Path:
    if events_out is None:
        return Path(".web-research/logs") / f"{run_id}.jsonc"
    path = Path(events_out)
    if path.suffix == ".jsonc":
        return path
    return path / f"{run_id}.jsonc"
