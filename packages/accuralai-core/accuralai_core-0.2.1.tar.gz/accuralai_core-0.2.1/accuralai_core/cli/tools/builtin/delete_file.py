"""Tool that deletes files and directories."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _delete_file(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    path = None
    recursive = False
    
    if call_args and isinstance(call_args, dict):
        path = call_args.get("path")
        recursive = call_args.get("recursive", False)
    
    if args:
        path = path or args[0]
        if len(args) > 1:
            recursive = args[1].lower() in ("true", "yes", "1", "recursive")
    
    if not path:
        return ToolResult(status="error", message="Usage: /tool run delete.file <path> [recursive]")
    
    file_path = Path(str(path)).expanduser().resolve()
    
    try:
        if not file_path.exists():
            return ToolResult(status="error", message=f"Path '{file_path}' does not exist")
        
        if file_path.is_dir():
            if not recursive:
                return ToolResult(status="error", message=f"'{file_path}' is a directory. Use recursive=true to delete it")
            shutil.rmtree(file_path)
            return ToolResult(status="success", message=f"Deleted directory '{file_path}'")
        else:
            file_path.unlink()
            return ToolResult(status="success", message=f"Deleted file '{file_path}'")
        
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied deleting '{file_path}'")
    except Exception as e:
        return ToolResult(status="error", message=f"Error deleting '{file_path}': {e}")


tool_spec = ToolSpec(
    name="delete.file",
    description="Delete files and directories.",
    handler=_delete_file,
    usage="/tool run delete.file <path> [recursive]",
    package="builtin",
    function={
        "name": "delete_file",
        "description": "Delete a file or directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path to delete."},
                "recursive": {"type": "boolean", "description": "Delete directories recursively (default: false)."}
            },
            "required": ["path"],
        },
    },
)
