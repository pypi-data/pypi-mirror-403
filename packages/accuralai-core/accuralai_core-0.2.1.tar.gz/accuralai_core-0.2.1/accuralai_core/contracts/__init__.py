"""Shared models, protocols, and errors."""

from .models import GenerateRequest, GenerateResponse, Usage
from .protocols import (
    Backend,
    Cache,
    Canonicalizer,
    EventPublisher,
    Instrumentation,
    PostProcessor,
    Router,
    Validator,
)
from .errors import (
    CacheError,
    AccuralAIError,
    ConfigurationError,
    PipelineError,
    BackendError,
    ValidationError,
    StageContext,
    raise_with_context,
)

__all__ = [
    "GenerateRequest",
    "GenerateResponse",
    "Usage",
    "Backend",
    "Cache",
    "Canonicalizer",
    "EventPublisher",
    "Instrumentation",
    "PostProcessor",
    "Router",
    "Validator",
    "CacheError",
    "AccuralAIError",
    "ConfigurationError",
    "PipelineError",
    "BackendError",
    "ValidationError",
    "StageContext",
    "raise_with_context",
]
