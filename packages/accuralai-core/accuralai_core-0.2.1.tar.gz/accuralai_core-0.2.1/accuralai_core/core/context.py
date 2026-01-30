"""Execution context shared across pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..contracts.models import GenerateRequest, GenerateResponse
from ..contracts.protocols import EventPublisher, Instrumentation
from ..utils.ids import generate_trace_id
from ..utils.timing import monotonic_ms


@dataclass(slots=True)
class ExecutionContext:
    """Holds request-scoped state for pipeline execution."""

    request: GenerateRequest
    config: Any
    instrumentation: Instrumentation
    event_publisher: Optional[EventPublisher] = None
    trace_id: str = field(default_factory=generate_trace_id)
    start_ms: int = field(default_factory=monotonic_ms)
    canonical_request: Optional[GenerateRequest] = None
    response: Optional[GenerateResponse] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False

    def mark_stage_start(self, stage: str) -> None:
        """Record that a stage is starting."""
        self.metadata["current_stage"] = stage
        self.metadata.setdefault("stage_history", []).append({"stage": stage, "event": "start"})

    def mark_stage_end(self, stage: str) -> None:
        """Record that a stage has completed."""
        self.metadata.setdefault("stage_history", []).append({"stage": stage, "event": "end"})
        self.metadata.pop("current_stage", None)

    async def record_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Publish an event when an event publisher is configured."""
        if not self.event_publisher:
            return
        enriched = {"trace_id": self.trace_id, **payload}
        await self.event_publisher.publish(event_name, enriched)

    def elapsed_ms(self) -> int:
        """Return milliseconds elapsed since context creation."""
        return monotonic_ms() - self.start_ms

    def cancel(self) -> None:
        """Mark the context as cancelled."""
        self.cancelled = True

    def ensure_not_cancelled(self) -> None:
        """Raise if pipeline execution has been cancelled."""
        if self.cancelled:
            raise RuntimeError("Pipeline execution cancelled")
