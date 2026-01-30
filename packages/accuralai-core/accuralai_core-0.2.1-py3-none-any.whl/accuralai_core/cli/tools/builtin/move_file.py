"""Tool that moves/renames files and directories."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _move_file(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    source = None
    destination = None
    
    if call_args and isinstance(call_args, dict):
        source = call_args.get("source")
        destination = call_args.get("destination")
    
    if args:
        source = source or args[0]
        if len(args) > 1:
            destination = args[1]
    
    if not source or not destination:
        return ToolResult(status="error", message="Usage: /tool run move.file <source> <destination>")
    
    source_path = Path(str(source)).expanduser().resolve()
    dest_path = Path(str(destination)).expanduser().resolve()
    
    try:
        if not source_path.exists():
            return ToolResult(status="error", message=f"Source path '{source_path}' does not exist")
        
        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(source_path), str(dest_path))
        
        if source_path.is_dir():
            return ToolResult(status="success", message=f"Moved directory '{source_path}' to '{dest_path}'")
        else:
            return ToolResult(status="success", message=f"Moved file '{source_path}' to '{dest_path}'")
        
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied moving '{source_path}'")
    except Exception as e:
        return ToolResult(status="error", message=f"Error moving '{source_path}': {e}")


tool_spec = ToolSpec(
    name="move.file",
    description="Move/rename files and directories.",
    handler=_move_file,
    usage="/tool run move.file <source> <destination>",
    package="builtin",
    function={
        "name": "move_file",
        "description": "Move or rename a file or directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file or directory path."},
                "destination": {"type": "string", "description": "Destination file or directory path."}
            },
            "required": ["source", "destination"],
        },
    },
)
