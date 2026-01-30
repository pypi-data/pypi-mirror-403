"""Cache connector utilities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from ..config.schema import CacheSettings
from ..contracts.errors import CacheError, ConfigurationError
from ..contracts.models import GenerateRequest, GenerateResponse
from ..contracts.protocols import Cache
from ..plugins.registry import PluginRegistry

CACHE_GROUP = "accuralai_core.caches"
CacheStrategy = Callable[[GenerateRequest], Optional[str]]
LOGGER = logging.getLogger("accuralai.core")


@dataclass(slots=True)
class CacheBinding:
    """Resolved cache implementation and associated metadata."""

    cache: Cache | None
    plugin_id: Optional[str]
    strategy: CacheStrategy


class InMemoryCache(Cache):
    """Development-only in-memory cache implementation."""

    def __init__(self) -> None:
        self._store: Dict[str, GenerateResponse] = {}

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        return self._store.get(key)

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        self._store[key] = value

    async def invalidate(self, key: str) -> None:
        self._store.pop(key, None)


async def build_inmemory_cache(**_: object) -> Cache:
    """Factory registered as built-in fallback."""
    return InMemoryCache()


def ensure_builtin_cache_plugins(registry: PluginRegistry) -> None:
    """Register built-in cache plugins when running from source checkout."""
    if not registry.has_plugin(CACHE_GROUP, "memory"):
        registry.register_builtin(CACHE_GROUP, "memory", build_inmemory_cache)


def default_cache_strategy(request: GenerateRequest) -> Optional[str]:
    """Derive cache key from request metadata."""
    return request.cache_key


async def load_cache(
    settings: CacheSettings,
    registry: PluginRegistry,
) -> CacheBinding:
    """Load cache implementation according to settings."""
    ensure_builtin_cache_plugins(registry)

    if not settings.enabled:
        return CacheBinding(cache=None, plugin_id=None, strategy=default_cache_strategy)

    candidates = []
    if settings.plugin:
        candidates.append(settings.plugin)
    candidates.append("memory")

    last_error: Exception | None = None
    for plugin_id in candidates:
        try:
            cache = await registry.build(CACHE_GROUP, plugin_id, config=settings)
            if plugin_id != (settings.plugin or "memory"):
                LOGGER.warning(
                    "Falling back to cache plugin '%s' (requested '%s' unavailable).",
                    plugin_id,
                    settings.plugin,
                )
            return CacheBinding(cache=cache, plugin_id=plugin_id, strategy=default_cache_strategy)
        except KeyError as error:
            last_error = error
            continue
        except Exception as error:  # pragma: no cover - plugin specific failure
            raise CacheError(str(error), cause=error) from error

    raise ConfigurationError(
        f"Cache plugin '{settings.plugin}' not available.",
        cause=last_error,
    )
