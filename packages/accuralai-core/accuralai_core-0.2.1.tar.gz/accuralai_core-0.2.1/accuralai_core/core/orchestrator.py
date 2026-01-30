"""High-level orchestration API."""

from __future__ import annotations

import asyncio
from typing import Iterable, Optional

from ..config.defaults import get_default_settings
from ..config.loader import load_settings
from ..config.schema import CoreSettings
from ..contracts.models import GenerateRequest, GenerateResponse
from ..contracts.protocols import EventPublisher, Instrumentation
from ..core.instrumentation import build_default_instrumentation
from ..plugins.registry import PluginRegistry
from ..connectors.backend import load_backends
from ..connectors.cache import CacheBinding, load_cache
from ..connectors.canonicalize import CanonicalizerBinding, load_canonicalizer
from ..connectors.post_process import PostProcessorBinding, load_post_processors
from ..connectors.router import RouterBinding, load_router
from ..connectors.validator import ValidatorBinding, load_validators
from ..core.context import ExecutionContext
from ..core.pipeline import Pipeline

PLUGIN_GROUPS = (
    "accuralai_core.canonicalizers",
    "accuralai_core.caches",
    "accuralai_core.routers",
    "accuralai_core.backends",
    "accuralai_core.validators",
    "accuralai_core.post_processors",
)


class CoreOrchestrator:
    """Main entry point for executing the AccuralAI pipeline."""

    def __init__(
        self,
        *,
        config: CoreSettings | None = None,
        registry: PluginRegistry | None = None,
        instrumentation: Instrumentation | None = None,
        event_publisher: EventPublisher | None = None,
        config_overrides: dict | None = None,
        config_paths: Iterable[str] | None = None,
    ) -> None:
        self._config = config or self._load_config(config_overrides=config_overrides, config_paths=config_paths)
        self._registry = registry or PluginRegistry.from_discovery(PLUGIN_GROUPS)
        self._instrumentation = instrumentation or build_default_instrumentation(
            self._config.instrumentation.model_dump(),
        )
        self._event_publisher = event_publisher
        self._pipeline: Pipeline | None = None
        self._pipeline_lock = asyncio.Lock()

    async def __aenter__(self) -> "CoreOrchestrator":
        await self._ensure_pipeline()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        await self.aclose()

    async def aclose(self) -> None:
        """Placeholder for future cleanup hooks."""
        # Backends may expose close hooks through lifecycle module in the future.
        self._pipeline = None

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Run the compound pipeline with the supplied request."""
        pipeline = await self._ensure_pipeline()
        ctx = ExecutionContext(
            request=request,
            config=self._config,
            instrumentation=self._instrumentation,
            event_publisher=self._event_publisher,
        )
        return await pipeline.run(ctx)

    async def _ensure_pipeline(self) -> Pipeline:
        if self._pipeline is not None:
            return self._pipeline

        async with self._pipeline_lock:
            if self._pipeline is None:
                bindings = await self._build_bindings()
                stage_plugins = self._build_stage_plugin_mapping(bindings)
                self._pipeline = Pipeline(
                    canonicalizer=bindings["canonicalizer"].canonicalizer,
                    cache=bindings["cache"].cache,
                    router=bindings["router"].router,
                    backend_runner=bindings["backend"].runner,
                    validator=bindings["validator"].validator,
                    post_processors=bindings["post_processors"].processors,
                    instrumentation=self._instrumentation,
                    cache_strategy=bindings["cache"].strategy,
                    stage_plugins=stage_plugins,
                )
        return self._pipeline  # type: ignore[return-value]

    async def _build_bindings(self) -> dict[str, object]:
        canonicalizer_binding = await load_canonicalizer(self._config.canonicalizer, self._registry)
        cache_binding = await load_cache(self._config.cache, self._registry)
        router_binding = await load_router(self._config.router, self._registry)
        backend_binding = await load_backends(self._config.backends, self._registry)
        validator_binding = await load_validators(self._config.validators, self._registry)
        post_binding = await load_post_processors(self._config.post_processors, self._registry)

        return {
            "canonicalizer": canonicalizer_binding,
            "cache": cache_binding,
            "router": router_binding,
            "backend": backend_binding,
            "validator": validator_binding,
            "post_processors": post_binding,
        }

    def _build_stage_plugin_mapping(self, bindings: dict[str, object]) -> dict[str, Optional[str]]:
        cache_binding: CacheBinding = bindings["cache"]  # type: ignore[assignment]
        canonicalizer_binding: CanonicalizerBinding = bindings["canonicalizer"]  # type: ignore[assignment]
        router_binding: RouterBinding = bindings["router"]  # type: ignore[assignment]
        validator_binding: ValidatorBinding = bindings["validator"]  # type: ignore[assignment]
        post_binding: PostProcessorBinding = bindings["post_processors"]  # type: ignore[assignment]

        stage_plugins: dict[str, Optional[str]] = {
            "canonicalize": canonicalizer_binding.plugin_id,
            "router": router_binding.plugin_id,
            "validator": "validator-chain" if len(validator_binding.plugin_ids) > 1 else (validator_binding.plugin_ids[0] if validator_binding.plugin_ids else None),
        }
        if cache_binding.plugin_id:
            stage_plugins["cache.get"] = cache_binding.plugin_id
            stage_plugins["cache.set"] = cache_binding.plugin_id

        for index, plugin_id in enumerate(post_binding.plugin_ids):
            stage_plugins[f"post_process[{index}]"] = plugin_id

        return stage_plugins

    def _load_config(
        self,
        *,
        config_overrides: dict | None,
        config_paths: Iterable[str] | None,
    ) -> CoreSettings:
        if config_overrides or config_paths:
            return load_settings(overrides=config_overrides, config_paths=config_paths)
        return get_default_settings()
