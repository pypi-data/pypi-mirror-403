"""Execution helpers for CLI tools."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from ..state import SessionState
from .models import ToolResult, ToolSpec


class ToolRunner:
    """Runs tools with timeout and error handling."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def run(
        self,
        spec: ToolSpec,
        state: SessionState,
        args: list[str],
        call_args: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        try:
            return await asyncio.wait_for(spec.handler(state, args, call_args), timeout=self.timeout)
        except asyncio.TimeoutError:
            return ToolResult(status="error", message="Tool timed out.")
        except Exception as error:  # pragma: no cover - defensive guard
            return ToolResult(status="error", message=str(error))
