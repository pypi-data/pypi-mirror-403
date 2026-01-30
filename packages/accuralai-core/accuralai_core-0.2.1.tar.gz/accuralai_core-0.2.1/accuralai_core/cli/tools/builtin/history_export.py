"""Tool that exports conversation history to disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _history_export(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    target = None
    if call_args and isinstance(call_args, dict):
        target = call_args.get("path")
    if not target and args:
        target = args[0]
    if not target:
        return ToolResult(status="error", message="Usage: /tool run history.export <path>")

    path = Path(str(target)).expanduser()
    if not state.history:
        return ToolResult(status="error", message="No history to export.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(item) for item in state.history))

    return ToolResult(
        status="success",
        message=f"History exported to {path}",
        data={"path": str(path)},
    )


tool_spec = ToolSpec(
    name="history.export",
    description="Write session history to a JSONL file.",
    handler=_history_export,
    usage="/tool run history.export ~/transcript.jsonl",
    package="builtin",
    function={
        "name": "export_history",
        "description": "Export the current conversation history to a JSON Lines file.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path for the export."}},
            "required": ["path"],
        },
    },
)
