from __future__ import annotations

from textual.widgets import Static


class WarningsWidget(Static):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__("", *args, **kwargs)
        self.messages: list[str] = []

    @property
    def text(self) -> str:
        return "\n".join(self.messages)

    def add_warning(self, message: str) -> None:
        self.messages.append(message)
        self.update("\n".join(self.messages))
