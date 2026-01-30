"""Shared error hierarchy for accuralai-core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class StageContext:
    """Metadata describing where an error originated."""

    stage: Optional[str] = None
    plugin_id: Optional[str] = None
    request_id: Optional[str] = None


class AccuralAIError(Exception):
    """Base exception for all accuralai-core failures."""

    def __init__(
        self,
        message: str,
        *,
        stage_context: Optional[StageContext] = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.stage_context = stage_context
        self.__cause__ = cause

    def with_stage_context(self, stage_context: StageContext) -> "AccuralAIError":
        """Attach stage context to an existing error."""
        if self.stage_context is None:
            self.stage_context = stage_context
        return self


class ConfigurationError(AccuralAIError):
    """Raised when configuration loading or validation fails."""


class PipelineError(AccuralAIError):
    """Raised when a pipeline stage encounters an unrecoverable error."""


class BackendError(PipelineError):
    """Raised by backend adapters when a generation call fails."""

    def __init__(
        self,
        message: str,
        *,
        stage_context: Optional[StageContext] = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, stage_context=stage_context, cause=cause)


class ValidationError(PipelineError):
    """Raised when validator modules fail or reject a response."""


class CacheError(PipelineError):
    """Raised when cache modules fail to read/write."""


def raise_with_context(
    error: Exception,
    *,
    stage: Optional[str] = None,
    plugin_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """Raise the provided error ensuring stage context is attached."""
    context = StageContext(stage=stage, plugin_id=plugin_id, request_id=request_id)
    if isinstance(error, AccuralAIError):
        raise error.with_stage_context(context)

    raise PipelineError(str(error), stage_context=context, cause=error) from error
