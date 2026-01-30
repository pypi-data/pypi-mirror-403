"""Tool that searches for files by name pattern."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _search_files(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    pattern = None
    directory = "."
    recursive = True
    
    if call_args and isinstance(call_args, dict):
        pattern = call_args.get("pattern")
        directory = call_args.get("directory", ".")
        recursive = call_args.get("recursive", True)
    
    if args:
        pattern = pattern or args[0]
        if len(args) > 1:
            directory = args[1]
        if len(args) > 2:
            recursive = args[2].lower() in ("true", "yes", "1", "recursive")
    
    if not pattern:
        return ToolResult(status="error", message="Usage: /tool run search.files <pattern> [directory] [recursive]")
    
    search_path = Path(str(directory)).expanduser().resolve()
    if not search_path.is_dir():
        return ToolResult(status="error", message=f"Directory '{search_path}' not found.")
    
    try:
        matches = []
        
        if recursive:
            for root, dirs, files in os.walk(search_path):
                root_path = Path(root)
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        matches.append(str(root_path / file))
        else:
            for file in os.listdir(search_path):
                if fnmatch.fnmatch(file, pattern):
                    matches.append(str(search_path / file))
        
        matches.sort()
        
        if matches:
            message = f"Found {len(matches)} files matching '{pattern}':\n" + "\n".join(matches)
        else:
            message = f"No files found matching '{pattern}' in {search_path}"
        
        return ToolResult(
            status="success",
            message=message,
            data={"pattern": pattern, "directory": str(search_path), "matches": matches, "count": len(matches)}
        )
        
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied accessing '{search_path}'")


tool_spec = ToolSpec(
    name="search.files",
    description="Search for files by name pattern.",
    handler=_search_files,
    usage="/tool run search.files '*.py' [directory] [recursive]",
    package="builtin",
    function={
        "name": "search_files",
        "description": "Search for files matching a pattern in a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "File pattern to search for (e.g., '*.py', 'test_*.txt')."},
                "directory": {"type": "string", "description": "Directory to search in (default: current directory)."},
                "recursive": {"type": "boolean", "description": "Whether to search recursively (default: true)."}
            },
            "required": ["pattern"],
        },
    },
)
