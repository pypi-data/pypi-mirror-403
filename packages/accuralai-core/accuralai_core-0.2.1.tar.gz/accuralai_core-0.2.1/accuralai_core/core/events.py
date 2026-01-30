"""Event definitions emitted during pipeline execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

PIPELINE_START = "pipeline.start"
PIPELINE_END = "pipeline.end"
STAGE_START = "stage.start"
STAGE_END = "stage.end"
PIPELINE_ERROR = "pipeline.error"
CACHE_HIT = "cache.hit"
CACHE_MISS = "cache.miss"
CACHE_STORE = "cache.store"
ROUTE_SELECTED = "router.selected"
BACKEND_CALLED = "backend.called"
VALIDATION_COMPLETE = "validator.complete"


def event_payload(event: str, **payload: Any) -> Dict[str, Any]:
    """Construct a standard event payload."""
    data = {"event": event}
    data.update(payload)
    return data


@dataclass(slots=True)
class PipelineEvent:
    """Runtime representation of an event to be published."""

    name: str
    payload: Dict[str, Any]
