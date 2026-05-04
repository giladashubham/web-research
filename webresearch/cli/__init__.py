from __future__ import annotations

from typing import Annotated

import typer

from webresearch.cli.list_cmd import list_workflows
from webresearch.cli.run_cmd import run_command
from webresearch.tui.app import run as run_tui

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main(
    workflows_dir: Annotated[
        str | None,
        typer.Option(
            "--workflows-dir",
            help="Directory for user-defined workflows. Currently reserved for future use.",
        ),
    ] = None,
) -> None:
    _ = workflows_dir


app.command(name="list")(list_workflows)
app.command(name="run")(run_command)
app.command(name="tui")(run_tui)
