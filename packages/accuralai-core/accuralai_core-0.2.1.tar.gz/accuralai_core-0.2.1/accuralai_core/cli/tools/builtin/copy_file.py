"""Tool that copies files and directories."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _copy_file(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    source = None
    destination = None
    recursive = False
    
    if call_args and isinstance(call_args, dict):
        source = call_args.get("source")
        destination = call_args.get("destination")
        recursive = call_args.get("recursive", False)
    
    if args:
        source = source or args[0]
        if len(args) > 1:
            destination = args[1]
        if len(args) > 2:
            recursive = args[2].lower() in ("true", "yes", "1", "recursive")
    
    if not source or not destination:
        return ToolResult(status="error", message="Usage: /tool run copy.file <source> <destination> [recursive]")
    
    source_path = Path(str(source)).expanduser().resolve()
    dest_path = Path(str(destination)).expanduser().resolve()
    
    try:
        if not source_path.exists():
            return ToolResult(status="error", message=f"Source path '{source_path}' does not exist")
        
        if source_path.is_dir():
            if not recursive:
                return ToolResult(status="error", message=f"'{source_path}' is a directory. Use recursive=true to copy it")
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            return ToolResult(status="success", message=f"Copied directory '{source_path}' to '{dest_path}'")
        else:
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            return ToolResult(status="success", message=f"Copied file '{source_path}' to '{dest_path}'")
        
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied copying '{source_path}'")
    except Exception as e:
        return ToolResult(status="error", message=f"Error copying '{source_path}': {e}")


tool_spec = ToolSpec(
    name="copy.file",
    description="Copy files and directories.",
    handler=_copy_file,
    usage="/tool run copy.file <source> <destination> [recursive]",
    package="builtin",
    function={
        "name": "copy_file",
        "description": "Copy a file or directory to a new location.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file or directory path."},
                "destination": {"type": "string", "description": "Destination file or directory path."},
                "recursive": {"type": "boolean", "description": "Copy directories recursively (default: false)."}
            },
            "required": ["source", "destination"],
        },
    },
)
