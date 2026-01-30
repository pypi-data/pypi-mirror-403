"""Tool that creates directories."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _create_directory(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    path = None
    parents = True
    
    if call_args and isinstance(call_args, dict):
        path = call_args.get("path")
        parents = call_args.get("parents", True)
    
    if args:
        path = path or args[0]
        if len(args) > 1:
            parents = args[1].lower() in ("true", "yes", "1", "parents")
    
    if not path:
        return ToolResult(status="error", message="Usage: /tool run create.directory <path> [parents]")
    
    dir_path = Path(str(path)).expanduser().resolve()
    
    try:
        if dir_path.exists():
            if dir_path.is_dir():
                return ToolResult(status="success", message=f"Directory '{dir_path}' already exists")
            else:
                return ToolResult(status="error", message=f"Path '{dir_path}' exists but is not a directory")
        
        dir_path.mkdir(parents=parents, exist_ok=False)
        return ToolResult(status="success", message=f"Created directory '{dir_path}'")
        
    except FileExistsError:
        return ToolResult(status="error", message=f"Directory '{dir_path}' already exists")
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied creating '{dir_path}'")
    except Exception as e:
        return ToolResult(status="error", message=f"Error creating directory: {e}")


tool_spec = ToolSpec(
    name="create.directory",
    description="Create directories.",
    handler=_create_directory,
    usage="/tool run create.directory <path> [parents]",
    package="builtin",
    function={
        "name": "create_directory",
        "description": "Create a directory at the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to create."},
                "parents": {"type": "boolean", "description": "Create parent directories if they don't exist (default: true)."}
            },
            "required": ["path"],
        },
    },
)
