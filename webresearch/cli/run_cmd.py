from __future__ import annotations

import asyncio
from typing import Annotated, Literal

import typer

from webresearch.cli.formats import format_result, write_output
from webresearch.cli.progress import ProgressRenderer
from webresearch.events.stream import stream_workflow
from webresearch.events.types import WorkflowFailed
from webresearch.types import Depth, WorkflowInput, WorkflowResult
from webresearch.workflows import load_workflows

OutputFormat = Literal["json", "md"]


def run_command(
    query: Annotated[str, typer.Argument(help="Research query.")],
    workflow: Annotated[str, typer.Argument(help="Workflow id.")] = "deep",
    depth: Annotated[str, typer.Option("--depth", help="Depth preset.")] = "standard",
    instructions: Annotated[str | None, typer.Option("--instructions")] = None,
    max_sources: Annotated[int | None, typer.Option("--max-sources")] = None,
    out: Annotated[str | None, typer.Option("--out")] = None,
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


async def _run(
    *,
    workflow: str,
    query: str,
    depth: str,
    instructions: str | None,
    max_sources: int | None,
    quiet: bool,
) -> WorkflowResult:
    workflow_fn = load_workflows()[workflow]
    workflow_input = WorkflowInput(
        query=query,
        depth=Depth.for_preset(depth),
        instructions=instructions,
        max_sources=max_sources,
    )
    renderer = ProgressRenderer(quiet=quiet)
    result: WorkflowResult | None = None

    async def capturing_workflow(input_: WorkflowInput) -> WorkflowResult:
        nonlocal result
        result = await workflow_fn(input_)
        return result

    async for event in stream_workflow(capturing_workflow, workflow_input):
        renderer.render(event)
        if isinstance(event, WorkflowFailed):
            raise typer.Exit(1)

    if result is None:
        msg = "Workflow did not produce a result"
        raise RuntimeError(msg)
    return result
