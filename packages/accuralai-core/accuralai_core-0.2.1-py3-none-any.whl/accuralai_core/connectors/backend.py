"""Backend connector and registry helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from uuid import uuid4

from ..config.schema import BackendSettings
from ..contracts.errors import BackendError, ConfigurationError
from ..contracts.models import GenerateRequest, GenerateResponse, Usage
from ..contracts.protocols import Backend
from ..core.pipeline import BackendRunner
from ..plugins.registry import PluginRegistry

BACKEND_GROUP = "accuralai_core.backends"


@dataclass(slots=True)
class BackendBinding:
    """Backend runner and metadata for the pipeline."""

    runner: BackendRunner
    plugin_ids: Dict[str, str]


class MockBackend(Backend):
    """Simple backend used during development and testing."""

    async def generate(self, request: GenerateRequest, *, routed_to: str) -> GenerateResponse:
        usage = Usage(
            prompt_tokens=len(request.prompt),
            completion_tokens=len(request.prompt),
            extra={"backend": "mock"},
        )
        return GenerateResponse(
            id=uuid4(),
            request_id=request.id,
            output_text=f"[mock:{routed_to}] {request.prompt}",
            finish_reason="stop",
            usage=usage,
            latency_ms=0,
        )


async def build_mock_backend(**_: object) -> Backend:
    """Built-in mock backend factory."""
    return MockBackend()


def ensure_builtin_backend(registry: PluginRegistry) -> None:
    """Register built-in mock backend for source checkouts."""
    if not registry.has_plugin(BACKEND_GROUP, "mock"):
        registry.register_builtin(BACKEND_GROUP, "mock", build_mock_backend)


async def load_backends(
    backend_settings: Dict[str, BackendSettings],
    registry: PluginRegistry,
) -> BackendBinding:
    """Instantiate backends from settings and register them in a runner."""
    ensure_builtin_backend(registry)

    instances: Dict[str, Backend] = {}
    plugin_ids: Dict[str, str] = {}

    if not backend_settings:
        backend_settings = {"mock": BackendSettings(plugin="mock")}

    for backend_id, settings in backend_settings.items():
        if not settings.enabled:
            continue
        plugin_id = settings.plugin
        if not plugin_id:
            msg = f"Backend '{backend_id}' missing plugin identifier"
            raise ConfigurationError(msg)
        try:
            backend = await registry.build(BACKEND_GROUP, plugin_id, config=settings, backend_id=backend_id)
        except KeyError as error:
            msg = f"Backend plugin '{plugin_id}' not available"
            raise ConfigurationError(msg, cause=error) from error
        except Exception as error:  # pragma: no cover - plugin-defined failure
            raise BackendError(str(error), cause=error) from error

        instances[backend_id] = backend
        plugin_ids[backend_id] = plugin_id

    if not instances:
        msg = "No enabled backends configured"
        raise ConfigurationError(msg)

    return BackendBinding(runner=BackendRunner(backends=instances), plugin_ids=plugin_ids)
