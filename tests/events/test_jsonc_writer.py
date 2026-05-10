from __future__ import annotations

import json
from webresearch.events.jsonc_writer import JSONCWriter
from webresearch.events.types import (
    WorkflowStarted,
    ToolCall,
)

def test_jsonc_writer_creates_valid_file(tmp_path) -> None:
    path = tmp_path / "run_1.jsonc"
    writer = JSONCWriter(path)
    
    writer.open("run_1", "standard", "query")
    writer.write_event(WorkflowStarted(run_id="run_1", workflow_id="standard"))
    writer.write_event(
        ToolCall(
            run_id="run_1",
            step="s1",
            tool_name="t1",
            call_id="c1",
            arguments={"key": "val"},
        )
    )
    writer.close()
    
    content = path.read_text()
    assert content.startswith("//")
    # Strip comments for simple json parsing
    json_lines = [line for line in content.splitlines() if not line.strip().startswith("//")]
    data = json.loads("\n".join(json_lines))
    
    assert data["run_id"] == "run_1"
    assert len(data["events"]) == 2
    assert data["events"][0]["kind"] == "workflow_started"
    assert data["events"][1]["arguments"]["key"] == "val"

def test_jsonc_writer_redacts_secrets(tmp_path) -> None:
    path = tmp_path / "run_1.jsonc"
    writer = JSONCWriter(path)
    
    writer.open("run_1", "standard", "query")
    writer.write_event(
        ToolCall(
            run_id="run_1",
            step="s1",
            tool_name="t1",
            call_id="c1",
            arguments={"api_key": "secret-123", "normal": "val"},
        )
    )
    writer.close()
    
    json_lines = [line for line in content.splitlines() if not line.strip().startswith("//")] if 'content' in locals() else []
    # Re-read
    content = path.read_text()
    json_lines = [line for line in content.splitlines() if not line.strip().startswith("//")]
    data = json.loads("\n".join(json_lines))
    
    args = data["events"][0]["arguments"]
    assert args["api_key"] == "[REDACTED]"
    assert args["normal"] == "val"

def test_jsonc_writer_truncates_large_values(tmp_path) -> None:
    path = tmp_path / "run_1.jsonc"
    writer = JSONCWriter(path)
    
    writer.open("run_1", "standard", "query")
    writer.write_event(
        ToolCall(
            run_id="run_1",
            step="s1",
            tool_name="t1",
            call_id="c1",
            arguments={"large": "a" * 2000},
        )
    )
    writer.close()
    
    content = path.read_text()
    json_lines = [line for line in content.splitlines() if not line.strip().startswith("//")]
    data = json.loads("\n".join(json_lines))
    
    val = data["events"][0]["arguments"]["large"]
    assert len(val) < 2000
    assert "[TRUNCATED]" in val
