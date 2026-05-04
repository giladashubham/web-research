from __future__ import annotations

from textual.widgets import ListItem, ListView, Static


class ArtifactsWidget(ListView):
    async def add_artifact(self, artifact_id: str, artifact_kind: str) -> None:
        self.append(ListItem(Static(f"{artifact_id} ({artifact_kind})")))
