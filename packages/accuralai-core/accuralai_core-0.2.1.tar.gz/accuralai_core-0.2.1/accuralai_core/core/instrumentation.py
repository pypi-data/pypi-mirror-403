"""Instrumentation helpers wrapping pipeline stages."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Sequence

from ..contracts.protocols import Instrumentation

LOGGER = logging.getLogger("accuralai.core")


class NullInstrumentation(Instrumentation):
    """No-op instrumentation used when none is configured."""

    async def on_stage_start(self, stage: str, *, context: Dict[str, Any]) -> None:  # noqa: D401
        return None

    async def on_stage_end(self, stage: str, *, context: Dict[str, Any]) -> None:  # noqa: D401
        return None

    async def on_error(self, stage: str, *, error: Exception, context: Dict[str, Any]) -> None:  # noqa: D401
        return None


class LoggingInstrumentation(Instrumentation):
    """Minimal instrumentation that logs pipeline events."""

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or LOGGER

    async def on_stage_start(self, stage: str, *, context: Dict[str, Any]) -> None:
        self._logger.debug(f"stage start: {stage}", extra={"stage": stage, "context": context})

    async def on_stage_end(self, stage: str, *, context: Dict[str, Any]) -> None:
        self._logger.debug(f"stage end: {stage}", extra={"stage": stage, "context": context})

    async def on_error(self, stage: str, *, error: Exception, context: Dict[str, Any]) -> None:
        self._logger.exception(
            "stage error",
            extra={"stage": stage, "context": context, "error": repr(error)},
        )


class CompositeInstrumentation(Instrumentation):
    """Fan-out instrumentation wrapper."""

    def __init__(self, instrumentations: Sequence[Instrumentation]) -> None:
        self._instrumentations = list(instrumentations)

    async def on_stage_start(self, stage: str, *, context: Dict[str, Any]) -> None:
        for instrumentation in self._instrumentations:
            await instrumentation.on_stage_start(stage, context=context)

    async def on_stage_end(self, stage: str, *, context: Dict[str, Any]) -> None:
        for instrumentation in self._instrumentations:
            await instrumentation.on_stage_end(stage, context=context)

    async def on_error(self, stage: str, *, error: Exception, context: Dict[str, Any]) -> None:
        for instrumentation in self._instrumentations:
            await instrumentation.on_error(stage, error=error, context=context)


def build_default_instrumentation(config: Dict[str, Any] | None = None) -> Instrumentation:
    """Return default instrumentation respecting config options."""
    if config and config.get("logging", {}).get("enabled", True) is False:
        return NullInstrumentation()
    return LoggingInstrumentation()


@asynccontextmanager
async def instrument_stage(
    instrumentation: Instrumentation,
    *,
    stage: str,
    context: Dict[str, Any],
):
    """Wrap a pipeline stage with instrumentation hooks."""
    await instrumentation.on_stage_start(stage, context=context)
    try:
        yield
    except Exception as exc:  # pragma: no cover - instrumentation shouldn't swallow errors
        await instrumentation.on_error(stage, error=exc, context=context)
        raise
    finally:
        await instrumentation.on_stage_end(stage, context=context)
