"""Protocol definitions for pipeline stage abstractions."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Mapping, Protocol, TypeVar, runtime_checkable

from .models import GenerateRequest, GenerateResponse


T_contra = TypeVar("T_contra", contravariant=True)
T_cov = TypeVar("T_cov", covariant=True)
PluginFactory = Callable[..., Awaitable[Any]]
"""Generic signature for async plugin factories discovered via entry points."""


@runtime_checkable
class Canonicalizer(Protocol):
    """Normalizes a request prior to caching and routing."""

    async def canonicalize(self, request: GenerateRequest) -> GenerateRequest:
        ...


@runtime_checkable
class Cache(Protocol):
    """Caches responses keyed by request-specific identifiers."""

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        ...

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        ...

    async def invalidate(self, key: str) -> None:
        ...


@runtime_checkable
class Router(Protocol):
    """Selects a backend identifier for the incoming request."""

    async def route(self, request: GenerateRequest) -> str:
        ...


@runtime_checkable
class Backend(Protocol):
    """Calls an LLM backend using a routed request."""

    async def generate(self, request: GenerateRequest, *, routed_to: str) -> GenerateResponse:
        ...


@runtime_checkable
class Validator(Protocol):
    """Validates or transforms a backend response."""

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        ...


@runtime_checkable
class PostProcessor(Protocol):
    """Enriches or reformats a response after validation."""

    async def process(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        ...


@runtime_checkable
class EventPublisher(Protocol):
    """Publishes structured pipeline events for observability."""

    async def publish(self, event_name: str, payload: Mapping[str, Any]) -> None:
        ...


@runtime_checkable
class Instrumentation(Protocol):
    """Observability hooks invoked around each pipeline stage."""

    async def on_stage_start(self, stage: str, *, context: Dict[str, Any]) -> None:
        ...

    async def on_stage_end(self, stage: str, *, context: Dict[str, Any]) -> None:
        ...

    async def on_error(self, stage: str, *, error: Exception, context: Dict[str, Any]) -> None:
        ...
