"""Tool that gets file and directory information."""

from __future__ import annotations

import stat
from datetime import datetime
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _file_info(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    path = None
    
    if call_args and isinstance(call_args, dict):
        path = call_args.get("path")
    
    if args:
        path = path or args[0]
    
    if not path:
        return ToolResult(status="error", message="Usage: /tool run file.info <path>")
    
    file_path = Path(str(path)).expanduser().resolve()
    
    try:
        if not file_path.exists():
            return ToolResult(status="error", message=f"Path '{file_path}' does not exist")
        
        stat_info = file_path.stat()
        
        # Format file size
        size = stat_info.st_size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
        
        # Format permissions
        permissions = stat.filemode(stat_info.st_mode)
        
        # Format timestamps
        created = datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        accessed = datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")
        
        file_type = "Directory" if file_path.is_dir() else "File"
        
        info_lines = [
            f"Path: {file_path}",
            f"Type: {file_type}",
            f"Size: {size_str}",
            f"Permissions: {permissions}",
            f"Created: {created}",
            f"Modified: {modified}",
            f"Accessed: {accessed}",
        ]
        
        # Add additional info for directories
        if file_path.is_dir():
            try:
                contents = list(file_path.iterdir())
                info_lines.append(f"Contents: {len(contents)} items")
            except PermissionError:
                info_lines.append("Contents: Permission denied")
        
        message = "\n".join(info_lines)
        
        return ToolResult(
            status="success",
            message=message,
            data={
                "path": str(file_path),
                "type": file_type.lower(),
                "size": size,
                "size_formatted": size_str,
                "permissions": permissions,
                "created": created,
                "modified": modified,
                "accessed": accessed,
            }
        )
        
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied accessing '{file_path}'")
    except Exception as e:
        return ToolResult(status="error", message=f"Error getting file info: {e}")


tool_spec = ToolSpec(
    name="file.info",
    description="Get file and directory information.",
    handler=_file_info,
    usage="/tool run file.info <path>",
    package="builtin",
    function={
        "name": "file_info",
        "description": "Get detailed information about a file or directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path to get info for."}
            },
            "required": ["path"],
        },
    },
)
