"""Tool that lists directory contents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _list_directory(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    # Default to workspace root (where accuralai-core is running)
    target = "."
    if call_args and isinstance(call_args, dict):
        target = call_args.get("path", ".")
    if args:
        target = target or args[0]

    path = Path(str(target)).expanduser().resolve()
    if not path.is_dir():
        return ToolResult(status="error", message=f"Directory '{path}' not found.")

    try:
        entries = []
        for entry in sorted(os.listdir(path)):
            entry_path = path / entry
            if entry_path.is_dir():
                entries.append(f"{entry}/")
            else:
                entries.append(entry)
        
        return ToolResult(
            status="success", 
            message=f"Contents of {path}:\n" + "\n".join(entries), 
            data={"path": str(path), "entries": entries}
        )
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied accessing '{path}'")


tool_spec = ToolSpec(
    name="list.directory",
    description="List directory contents.",
    handler=_list_directory,
    usage="/tool run list.directory <path>",
    package="builtin",
    function={
        "name": "list_directory",
        "description": "List the contents of a directory.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path to list."}},
            "required": ["path"],
        },
    },
)

