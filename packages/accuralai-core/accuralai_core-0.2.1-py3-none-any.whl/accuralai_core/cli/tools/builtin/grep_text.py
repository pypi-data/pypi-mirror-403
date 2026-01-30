"""Tool that searches for text patterns in files."""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _grep_text(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    pattern = None
    directory = "."
    file_pattern = "*"
    case_sensitive = False
    recursive = True
    
    if call_args and isinstance(call_args, dict):
        pattern = call_args.get("pattern")
        directory = call_args.get("directory", ".")
        file_pattern = call_args.get("file_pattern", "*")
        case_sensitive = call_args.get("case_sensitive", False)
        recursive = call_args.get("recursive", True)
    
    if args:
        pattern = pattern or args[0]
        if len(args) > 1:
            directory = args[1]
        if len(args) > 2:
            file_pattern = args[2]
        if len(args) > 3:
            case_sensitive = args[3].lower() in ("true", "yes", "1", "case")
        if len(args) > 4:
            recursive = args[4].lower() in ("true", "yes", "1", "recursive")
    
    if not pattern:
        return ToolResult(status="error", message="Usage: /tool run grep.text <pattern> [directory] [file_pattern] [case_sensitive] [recursive]")
    
    search_path = Path(str(directory)).expanduser().resolve()
    if not search_path.is_dir():
        return ToolResult(status="error", message=f"Directory '{search_path}' not found.")
    
    try:
        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        matches = []
        
        if recursive:
            for root, dirs, files in os.walk(search_path):
                root_path = Path(root)
                for file in files:
                    if fnmatch.fnmatch(file, file_pattern):
                        file_path = root_path / file
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if regex.search(line):
                                        matches.append({
                                            "file": str(file_path),
                                            "line": line_num,
                                            "content": line.rstrip()
                                        })
                        except (PermissionError, UnicodeDecodeError):
                            continue
        else:
            for file in os.listdir(search_path):
                if fnmatch.fnmatch(file, file_pattern):
                    file_path = search_path / file
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if regex.search(line):
                                        matches.append({
                                            "file": str(file_path),
                                            "line": line_num,
                                            "content": line.rstrip()
                                        })
                        except (PermissionError, UnicodeDecodeError):
                            continue
        
        if matches:
            # Group matches by file for better display
            file_matches = {}
            for match in matches:
                file_path = match["file"]
                if file_path not in file_matches:
                    file_matches[file_path] = []
                file_matches[file_path].append(f"  {match['line']}: {match['content']}")
            
            message_parts = [f"Found {len(matches)} matches for '{pattern}':"]
            for file_path, lines in file_matches.items():
                message_parts.append(f"\n{file_path}:")
                message_parts.extend(lines)
            
            message = "\n".join(message_parts)
        else:
            message = f"No matches found for '{pattern}' in {search_path}"
        
        return ToolResult(
            status="success",
            message=message,
            data={"pattern": pattern, "directory": str(search_path), "matches": matches, "count": len(matches)}
        )
        
    except re.error as e:
        return ToolResult(status="error", message=f"Invalid regex pattern: {e}")
    except PermissionError:
        return ToolResult(status="error", message=f"Permission denied accessing '{search_path}'")


tool_spec = ToolSpec(
    name="grep.text",
    description="Search for text patterns in files.",
    handler=_grep_text,
    usage="/tool run grep.text 'import' [directory] [file_pattern] [case_sensitive] [recursive]",
    package="builtin",
    function={
        "name": "grep_text",
        "description": "Search for text patterns in files using regex.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for."},
                "directory": {"type": "string", "description": "Directory to search in (default: current directory)."},
                "file_pattern": {"type": "string", "description": "File pattern to search in (default: '*')."},
                "case_sensitive": {"type": "boolean", "description": "Whether search is case sensitive (default: false)."},
                "recursive": {"type": "boolean", "description": "Whether to search recursively (default: true)."}
            },
            "required": ["pattern"],
        },
    },
)
