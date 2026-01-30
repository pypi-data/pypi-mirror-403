"""Tool that reads a file."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _read_file(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    target = None
    if call_args and isinstance(call_args, dict):
        target = call_args.get("path")
    if args:
        target = target or args[0]
    if not target:
        return ToolResult(status="error", message="Usage: /tool run read.file <path>")

    path = Path(str(target)).expanduser()
    if not path.exists():
        return ToolResult(status="error", message=f"File '{path}' not found.")

    text = path.read_text()
    return ToolResult(status="success", message=text, data={"path": str(path)})


tool_spec = ToolSpec(
    name="read.file",
    description="Read file contents and print to the shell.",
    handler=_read_file,
    usage="/tool run read.file notes.txt",
    package="builtin",
    function={
        "name": "read_file",
        "description": "Read the contents of a text file.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to read."}},
            "required": ["path"],
        },
    },
)
