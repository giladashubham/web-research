from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from webresearch.events.types import WorkflowEvent


class JSONCWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._f = None
        self._first_event = True

    def open(self, run_id: str, workflow_id: str, query: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = self.path.open("w", encoding="utf-8")
        self._f.write("// Web Research event log\n")
        self._f.write("// This file contains observable events only.\n")
        self._f.write("{\n")
        self._f.write(f'  "run_id": {json.dumps(run_id)},\n')
        self._f.write(f'  "workflow_id": {json.dumps(workflow_id)},\n')
        self._f.write(f'  "query": {json.dumps(query)},\n')
        self._f.write(f'  "started_at": {json.dumps(datetime.now(UTC).isoformat())},\n')
        self._f.write('  "events": [\n')
        self._f.flush()

    def write_event(self, event: WorkflowEvent) -> None:
        if self._f is None:
            return

        prefix = "    " if self._first_event else ",\n    "
        self._first_event = False

        # Simple redaction and truncation (EV-06)
        data = self._prepare_event(event.model_dump(mode="json"))
        self._f.write(prefix + json.dumps(data))
        self._f.flush()

    def close(self) -> None:
        if self._f is None:
            return

        self._f.write("\n  ],\n")
        self._f.write(f'  "completed_at": {json.dumps(datetime.now(UTC).isoformat())}\n')
        self._f.write("}\n")
        self._f.close()
        self._f = None

    def _prepare_event(self, data: dict[str, Any]) -> dict[str, Any]:
        # Basic redaction and truncation
        if "arguments" in data and isinstance(data["arguments"], dict):
            data["arguments"] = self._redact_dict(data["arguments"])
        if "result" in data:
            data["result"] = self._truncate_value(data["result"])
        return data

    def _redact_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        secrets = {"api_key", "token", "password", "authorization", "secret"}
        return {
            k: "[REDACTED]" if any(s in k.lower() for s in secrets) else self._truncate_value(v)
            for k, v in d.items()
        }

    def _truncate_value(self, v: Any) -> Any:
        if isinstance(v, str) and len(v) > 1000:
            return v[:1000] + "... [TRUNCATED]"
        if isinstance(v, list) and len(v) > 20:
            return v[:20] + ["... [TRUNCATED]"]
        if isinstance(v, dict):
            return {k: self._truncate_value(val) for k, val in v.items()}
        return v
