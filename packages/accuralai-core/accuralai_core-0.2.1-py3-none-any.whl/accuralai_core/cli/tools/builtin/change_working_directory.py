"""Tool that changes the current working directory."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _change_working_directory(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    path = None
    
    if call_args and isinstance(call_args, dict):
        path = call_args.get("path")
    
    if args:
        path = path or args[0]
    
    if not path:
        return ToolResult(status="error", message="Usage: /tool run change.working_directory <path>")
    
    try:
        new_path = Path(str(path)).expanduser().resolve()
        
        if not new_path.exists():
            return ToolResult(status="error", message=f"Directory '{new_path}' does not exist")
        
        if not new_path.is_dir():
            return ToolResult(status="error", message=f"'{new_path}' is not a directory")
        
        old_cwd = Path.cwd().resolve()
        os.chdir(new_path)
        new_cwd = Path.cwd().resolve()
        
        return ToolResult(
            status="success",
            message=f"Changed directory from '{old_cwd}' to '{new_cwd}'",
            data={"old_directory": str(old_cwd), "new_directory": str(new_cwd)}
        )
        
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied accessing '{path}'")
    except Exception as e:
        return ToolResult(status="error", message=f"Error changing directory: {e}")


tool_spec = ToolSpec(
    name="change.working_directory",
    description="Change the current working directory.",
    handler=_change_working_directory,
    usage="/tool run change.working_directory <path>",
    package="builtin",
    function={
        "name": "change_working_directory",
        "description": "Change the current working directory to the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to change to."}
            },
            "required": ["path"],
        },
    },
)
