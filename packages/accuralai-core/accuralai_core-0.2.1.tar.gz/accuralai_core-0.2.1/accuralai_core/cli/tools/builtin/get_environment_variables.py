"""Tool that gets environment variables."""

from __future__ import annotations

import os
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _get_environment_variables(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    variable = None
    
    if call_args and isinstance(call_args, dict):
        variable = call_args.get("variable")
    
    if args:
        variable = variable or args[0]
    
    try:
        if variable:
            # Get specific environment variable
            value = os.environ.get(variable)
            if value is None:
                return ToolResult(status="error", message=f"Environment variable '{variable}' not found")
            
            return ToolResult(
                status="success",
                message=f"{variable}={value}",
                data={"variable": variable, "value": value}
            )
        else:
            # Get all environment variables
            env_vars = dict(os.environ)
            sorted_vars = sorted(env_vars.items())
            
            message_lines = [f"Environment variables ({len(sorted_vars)} total):"]
            for key, value in sorted_vars:
                message_lines.append(f"{key}={value}")
            
            message = "\n".join(message_lines)
            
            return ToolResult(
                status="success",
                message=message,
                data={"environment_variables": env_vars, "count": len(sorted_vars)}
            )
        
    except Exception as e:
        return ToolResult(status="error", message=f"Error getting environment variables: {e}")


tool_spec = ToolSpec(
    name="get.environment_variables",
    description="Get environment variables.",
    handler=_get_environment_variables,
    usage="/tool run get.environment_variables [variable]",
    package="builtin",
    function={
        "name": "get_environment_variables",
        "description": "Get environment variables. If no variable specified, returns all environment variables.",
        "parameters": {
            "type": "object",
            "properties": {
                "variable": {"type": "string", "description": "Specific environment variable to get (optional)."}
            },
            "required": [],
        },
    },
)
