"""Public API surface for accuralai-core."""

from __future__ import annotations

from importlib.metadata import version

from .contracts.models import GenerateRequest, GenerateResponse, Usage
from .core.orchestrator import CoreOrchestrator

__all__ = [
    "CoreOrchestrator",
    "GenerateRequest",
    "GenerateResponse",
    "Usage",
    "generate",
    "__version__",
]

try:  # pragma: no cover - metadata not present during local development
    __version__ = version("accuralai-core")
except Exception:  # pragma: no cover - fallback during editable installs
    __version__ = "0.0.0"


async def generate(request: GenerateRequest) -> GenerateResponse:
    """Convenience helper to run a request with default orchestrator settings."""
    orchestrator = CoreOrchestrator()
    try:
        return await orchestrator.generate(request)
    finally:
        await orchestrator.aclose()
