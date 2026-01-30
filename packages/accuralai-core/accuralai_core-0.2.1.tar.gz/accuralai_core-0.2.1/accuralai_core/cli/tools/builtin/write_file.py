"""Tool that writes text to a file."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _write_file(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    target = None
    content = None
    if call_args and isinstance(call_args, dict):
        target = call_args.get("path")
        content = call_args.get("text")
    if len(args) >= 2:
        target = target or args[0]
        content = content or " ".join(args[1:])
    if not target or content is None:
        return ToolResult(status="error", message="Usage: /tool run write.file <path> <text>")

    path = Path(str(target)).expanduser()
    text = str(content)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)

    return ToolResult(status="success", message=f"Wrote {path}")


tool_spec = ToolSpec(
    name="write.file",
    description="Write the given text to a file.",
    handler=_write_file,
    usage="/tool run write.file notes.txt 'Hello world'",
    package="builtin",
    function={
        "name": "write_file",
        "description": "Write text content to a file on disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Destination file path."},
                "text": {"type": "string", "description": "Text to write."},
            },
            "required": ["path", "text"],
        },
    },
)
