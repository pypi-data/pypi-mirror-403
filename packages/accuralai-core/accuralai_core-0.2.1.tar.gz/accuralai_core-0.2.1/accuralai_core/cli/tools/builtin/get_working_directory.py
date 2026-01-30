"""Tool that gets the current working directory."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _get_working_directory(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    try:
        cwd = Path.cwd().resolve()
        return ToolResult(
            status="success",
            message=str(cwd),
            data={"working_directory": str(cwd)}
        )
    except Exception as e:
        return ToolResult(status="error", message=f"Error getting working directory: {e}")


tool_spec = ToolSpec(
    name="get.working_directory",
    description="Get the current working directory.",
    handler=_get_working_directory,
    usage="/tool run get.working_directory",
    package="builtin",
    function={
        "name": "get_working_directory",
        "description": "Get the current working directory path.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
)
