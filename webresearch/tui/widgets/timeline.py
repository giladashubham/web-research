from __future__ import annotations

from textual.widgets import Static


class TimelineWidget(Static):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__("", *args, **kwargs)
        self.rows: list[str] = []

    @property
    def text(self) -> str:
        return "\n".join(self.rows)

    def set_status(self, step: str, status: str) -> None:
        line = f"{step}: {status}"
        self.rows.append(line)
        self.update("\n".join(self.rows))

    def add_tool(self, step: str, tool_name: str) -> None:
        self.rows.append(f"  {step} · {tool_name}")
        self.update("\n".join(self.rows))

    def add_loop(self, loop: str, iteration: int) -> None:
        self.rows.append(f"{loop} iteration {iteration}")
        self.update("\n".join(self.rows))
