"""Tool that checks if a path exists."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _path_exists(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    path = None
    
    if call_args and isinstance(call_args, dict):
        path = call_args.get("path")
    
    if args:
        path = path or args[0]
    
    if not path:
        return ToolResult(status="error", message="Usage: /tool run path.exists <path>")
    
    try:
        file_path = Path(str(path)).expanduser().resolve()
        exists = file_path.exists()
        
        if exists:
            if file_path.is_dir():
                file_type = "directory"
            elif file_path.is_file():
                file_type = "file"
            elif file_path.is_symlink():
                file_type = "symlink"
            else:
                file_type = "other"
            
            message = f"Path '{file_path}' exists ({file_type})"
        else:
            message = f"Path '{file_path}' does not exist"
        
        return ToolResult(
            status="success",
            message=message,
            data={
                "path": str(file_path),
                "exists": exists,
                "type": file_type if exists else None
            }
        )
        
    except Exception as e:
        return ToolResult(status="error", message=f"Error checking path: {e}")


tool_spec = ToolSpec(
    name="path.exists",
    description="Check if a path exists.",
    handler=_path_exists,
    usage="/tool run path.exists <path>",
    package="builtin",
    function={
        "name": "path_exists",
        "description": "Check if a file or directory path exists.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path to check."}
            },
            "required": ["path"],
        },
    },
)
