"""Tool that prints current session state."""

from __future__ import annotations

import json
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _session_info(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    data = state.to_serializable()
    message = json.dumps(data, indent=2)
    return ToolResult(status="success", message=message, data=data)


tool_spec = ToolSpec(
    name="session.info",
    description="Show current session configuration (backend, model, metadata, tags).",
    handler=_session_info,
    usage="/tool run session.info",
    package="builtin",
    function={
        "name": "session_info",
        "description": "Return the current AccuralAI session configuration.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
)
