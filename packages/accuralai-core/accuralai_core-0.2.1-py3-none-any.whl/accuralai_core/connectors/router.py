"""Router connector utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config.schema import RouterSettings
from ..contracts.models import GenerateRequest
from ..contracts.protocols import Router
from ..plugins.registry import PluginRegistry

ROUTER_GROUP = "accuralai_core.routers"


@dataclass(slots=True)
class RouterBinding:
    """Resolved router implementation and metadata."""

    router: Router
    plugin_id: Optional[str]


class DefaultRouter(Router):
    """Fallback router that uses route hints or configuration defaults."""

    def __init__(self, default_backend: Optional[str]) -> None:
        self._default_backend = default_backend or "mock"

    async def route(self, request: GenerateRequest) -> str:
        if request.route_hint:
            return request.route_hint
        return self._default_backend


async def build_default_router(**kwargs: object) -> Router:
    """Built-in router factory."""
    default_backend = None
    if isinstance(kwargs.get("config"), RouterSettings):
        default_backend = kwargs["config"].default_backend
    return DefaultRouter(default_backend)


def ensure_builtin_router(registry: PluginRegistry) -> None:
    """Ensure default router is available during development."""
    if not registry.has_plugin(ROUTER_GROUP, "default"):
        registry.register_builtin(ROUTER_GROUP, "default", build_default_router)


async def load_router(
    settings: RouterSettings,
    registry: PluginRegistry,
) -> RouterBinding:
    """Load router implementation."""
    ensure_builtin_router(registry)

    plugin_id = settings.plugin or "default"
    router = await registry.build(ROUTER_GROUP, plugin_id, config=settings)
    return RouterBinding(router=router, plugin_id=plugin_id)
