"""Data structures describing interactive CLI tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Literal, Optional

from ..state import SessionState


ToolStatus = Literal["success", "error"]


@dataclass(slots=True)
class ToolResult:
    """Outcome returned by a tool invocation."""

    status: ToolStatus
    message: str
    data: Any | None = None
    suggest_prompt: Optional[str] = None


ToolHandler = Callable[[SessionState, list[str], Optional[Dict[str, Any]]], Awaitable[ToolResult]]


@dataclass(slots=True)
class ToolSpec:
    """Metadata describing a CLI tool."""

    name: str
    description: str
    handler: ToolHandler
    usage: Optional[str] = None
    package: Optional[str] = None
    function: Optional[Dict[str, Any]] = None
