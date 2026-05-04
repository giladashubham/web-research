from __future__ import annotations

from argparse import ArgumentParser


def app() -> None:
    parser = ArgumentParser(
        prog="webresearch",
        description="Web research runner. CLI commands are added in Phase 6.",
    )
    parser.parse_args()
