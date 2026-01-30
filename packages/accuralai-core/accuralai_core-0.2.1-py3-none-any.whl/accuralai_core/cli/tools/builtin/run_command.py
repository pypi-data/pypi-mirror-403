"""Tool that runs shell commands."""

from __future__ import annotations

import asyncio
import shlex
from typing import List

from ...state import SessionState
from ..models import ToolResult, ToolSpec


async def _run_command(state: SessionState, args: List[str], call_args=None) -> ToolResult:
    command = None
    working_dir = "."
    timeout = 30
    
    if call_args and isinstance(call_args, dict):
        command = call_args.get("command")
        working_dir = call_args.get("working_dir", ".")
        timeout = call_args.get("timeout", 30)
    
    if args:
        command = command or " ".join(args)
    
    if not command:
        return ToolResult(status="error", message="Usage: /tool run run.command <command> [working_dir] [timeout]")
    
    try:
        # Parse command into list for subprocess
        cmd_parts = shlex.split(command)
        
        # Run the command
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return ToolResult(
                status="error", 
                message=f"Command timed out after {timeout} seconds"
            )
        
        # Decode output
        stdout_text = stdout.decode('utf-8', errors='replace')
        stderr_text = stderr.decode('utf-8', errors='replace')
        
        # Prepare result message
        result_parts = []
        if stdout_text:
            result_parts.append(f"STDOUT:\n{stdout_text}")
        if stderr_text:
            result_parts.append(f"STDERR:\n{stderr_text}")
        
        if not result_parts:
            result_parts.append("Command completed with no output")
        
        message = "\n".join(result_parts)
        
        # Determine status based on return code
        status = "success" if process.returncode == 0 else "error"
        
        return ToolResult(
            status=status,
            message=message,
            data={
                "command": command,
                "working_dir": working_dir,
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text
            }
        )
        
    except FileNotFoundError:
        return ToolResult(status="error", message=f"Command not found: {command}")
    except Exception as e:
        return ToolResult(status="error", message=f"Error running command: {e}")


tool_spec = ToolSpec(
    name="run.command",
    description="Execute shell commands.",
    handler=_run_command,
    usage="/tool run run.command 'ls -la' [working_dir] [timeout]",
    package="builtin",
    function={
        "name": "run_command",
        "description": "Execute a shell command and return the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute."},
                "working_dir": {"type": "string", "description": "Working directory for the command (default: current directory)."},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)."}
            },
            "required": ["command"],
        },
    },
)
