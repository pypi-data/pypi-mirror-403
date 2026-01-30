"""Pipeline orchestration logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Sequence

from ..contracts.errors import raise_with_context
from ..contracts.models import GenerateRequest, GenerateResponse
from ..contracts.protocols import (
    Backend,
    Cache,
    Canonicalizer,
    Instrumentation,
    PostProcessor,
    Router,
    Validator,
)
from ..utils.timing import measure_latency
from ..utils.tokenizer import DEFAULT_TOKENIZER, Tokenizer
from .context import ExecutionContext
from .events import (
    BACKEND_CALLED,
    CACHE_HIT,
    CACHE_MISS,
    CACHE_STORE,
    ROUTE_SELECTED,
    VALIDATION_COMPLETE,
)
from .instrumentation import instrument_stage

LOGGER = logging.getLogger("accuralai.core")


CacheStrategy = Callable[[GenerateRequest], Optional[str]]


@dataclass(slots=True)
class BackendRunner:
    """Thin wrapper around backend implementations."""

    backends: Mapping[str, Backend]

    async def generate(self, backend_id: str, request: GenerateRequest) -> GenerateResponse:
        backend = self.backends.get(backend_id)
        if backend is None:
            msg = f"Backend '{backend_id}' is not registered"
            raise KeyError(msg)
        LOGGER.debug(f"Invoking backend '{backend_id}' with {len(request.tools) if request.tools else 0} tools")
        return await backend.generate(request, routed_to=backend_id)


class Pipeline:
    """Executes the configured generation pipeline."""

    def __init__(
        self,
        *,
        canonicalizer: Canonicalizer,
        cache: Cache | None,
        router: Router,
        backend_runner: BackendRunner,
        validator: Validator,
        post_processors: Sequence[PostProcessor] | None,
        instrumentation: Instrumentation,
        cache_strategy: CacheStrategy,
        stage_plugins: Mapping[str, Optional[str]],
        tokenizer: Tokenizer | None = None,
    ) -> None:
        self._canonicalizer = canonicalizer
        self._cache = cache
        self._router = router
        self._backend_runner = backend_runner
        self._validator = validator
        self._post_processors = list(post_processors or [])
        self._instrumentation = instrumentation
        self._cache_strategy = cache_strategy
        self._stage_plugins = stage_plugins
        self._tokenizer = tokenizer or DEFAULT_TOKENIZER

    async def run(self, ctx: ExecutionContext) -> GenerateResponse:
        """Execute the pipeline for a single request."""
        canonical = await self._run_stage(
            "canonicalize",
            ctx,
            self._canonicalizer.canonicalize,
            ctx.request,
        )

        if canonical.id != ctx.request.id:
            canonical = canonical.model_copy(update={"id": ctx.request.id})

        ctx.canonical_request = canonical
        
        # Collect canonicalization metrics
        canonicalize_metrics = {}
        if hasattr(self._canonicalizer, 'metrics'):
            metrics = self._canonicalizer.metrics
            canonicalize_metrics = {
                "original_token_count": metrics.original_token_count,
                "optimized_token_count": metrics.optimized_token_count,
                "tokens_saved": metrics.tokens_saved,
                "compression_ratio": metrics.compression_ratio,
                "deduplication_applied": metrics.deduplication_applied,
                "whitespace_compression_applied": metrics.whitespace_compression_applied,
                "structure_optimization_applied": metrics.structure_optimization_applied,
            }

        cache_key = self._cache_strategy(canonical)
        cached_response: Optional[GenerateResponse] = None
        cache_latency_ms: Optional[int] = None
        
        # Collect initial cache stats
        cache_stats = {}
        if self._cache and hasattr(self._cache, 'stats'):
            cache_stats = self._cache.stats.copy()
            
        if cache_key and self._cache:
            async def measured_cache_get(key: str, *, request: GenerateRequest) -> GenerateResponse | None:
                nonlocal cache_latency_ms
                async with measure_latency() as tracker:
                    result = await self._cache.get(key, request=request)
                cache_latency_ms = tracker.elapsed_ms
                return result

            cached_response = await self._run_stage(
                "cache.get",
                ctx,
                measured_cache_get,
                cache_key,
                request=canonical,
            )
            if cached_response:
                latency_ms = cache_latency_ms or 0
                if cached_response.latency_ms != latency_ms:
                    cached_response = cached_response.model_copy(update={"latency_ms": latency_ms})
                await ctx.record_event(
                    CACHE_HIT,
                    {"cache_key": cache_key, "backend": "cache", "latency_ms": latency_ms},
                )
        if not cached_response and cache_key and self._cache:
            await ctx.record_event(
                CACHE_MISS,
                {"cache_key": cache_key, "latency_ms": cache_latency_ms or 0},
            )

        response_source = "cache" if cached_response else "backend"

        if cached_response:
            response = self._ensure_usage_tokens(cached_response, canonical)
        else:
            backend_id = await self._run_stage(
                "router",
                ctx,
                self._router.route,
                canonical,
            )
            LOGGER.debug(f"Router selected backend: '{backend_id}'")
            await ctx.record_event(ROUTE_SELECTED, {"backend_id": backend_id})
            response = await self._invoke_backend(ctx, backend_id, canonical)
            response = self._ensure_usage_tokens(response, canonical)
            if cache_key and self._cache:
                await self._run_stage(
                    "cache.set",
                    ctx,
                    self._cache.set,
                    cache_key,
                    response,
                    ttl_s=None,
                )
                await ctx.record_event(CACHE_STORE, {"cache_key": cache_key})

        validated = await self._run_stage(
            "validator",
            ctx,
            self._validator.validate,
            response,
            request=canonical,
        )
        await ctx.record_event(
            VALIDATION_COMPLETE,
            {"source": response_source, "finish_reason": validated.finish_reason},
        )

        final_response = await self._run_post_processors(ctx, validated, canonical)
        if final_response.request_id != ctx.request.id:
            final_response = final_response.model_copy(update={"request_id": ctx.request.id})

        # Add cache status to response metadata
        cache_status = "hit" if cached_response else "miss" if cache_key and self._cache else "disabled"
        final_response.metadata["cache_status"] = cache_status
        final_response.metadata["response_source"] = response_source
        if cache_key:
            final_response.metadata["cache_key"] = cache_key
            
        # Add canonicalization metrics to response metadata
        if canonicalize_metrics:
            final_response.metadata["canonicalize_metrics"] = canonicalize_metrics
            
        # Add cache metrics to response metadata
        if cache_stats:
            final_response.metadata["cache_stats"] = cache_stats

        ctx.response = final_response
        return final_response

    async def _invoke_backend(
        self,
        ctx: ExecutionContext,
        backend_id: str,
        request: GenerateRequest,
    ) -> GenerateResponse:
        async def call_backend(target_backend: str, canonical_request: GenerateRequest) -> GenerateResponse:
            async with measure_latency() as tracker:
                backend_response = await self._backend_runner.generate(target_backend, canonical_request)
            latency = tracker.elapsed_ms
            if backend_response.latency_ms == 0:
                backend_response = backend_response.model_copy(update={"latency_ms": latency})
            await ctx.record_event(
                BACKEND_CALLED,
                {"backend_id": target_backend, "latency_ms": latency},
            )
            return backend_response

        return await self._run_stage(
            "backend.generate",
            ctx,
            call_backend,
            backend_id,
            request,
            plugin_id=backend_id,
        )

    async def _run_post_processors(
        self,
        ctx: ExecutionContext,
        response: GenerateResponse,
        request: GenerateRequest,
    ) -> GenerateResponse:
        current = response
        for index, processor in enumerate(self._post_processors):
            stage_name = f"post_process[{index}]"
            current = await self._run_stage(
                stage_name,
                ctx,
                processor.process,
                current,
                request=request,
            )
        return current

    async def _run_stage(
        self,
        stage: str,
        ctx: ExecutionContext,
        func: Callable,
        *args,
        plugin_id: Optional[str] = None,
        **kwargs,
    ):
        ctx.ensure_not_cancelled()
        ctx.mark_stage_start(stage)
        resolved_plugin = plugin_id if plugin_id is not None else self._stage_plugins.get(stage)
        stage_context = {
            "trace_id": ctx.trace_id,
            "stage": stage,
            "plugin_id": resolved_plugin,
        }
        async with instrument_stage(
            self._instrumentation,
            stage=stage,
            context=stage_context,
        ):
            try:
                result = await func(*args, **kwargs)
            except Exception as error:  # pragma: no cover - delegated to helper
                raise_with_context(
                    error,
                    stage=stage,
                    plugin_id=resolved_plugin,
                    request_id=str(ctx.request.id),
                )
        ctx.mark_stage_end(stage)
        return result

    def _ensure_usage_tokens(self, response: GenerateResponse, request: GenerateRequest) -> GenerateResponse:
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        updated: Dict[str, int] = {}

        if prompt_tokens == 0:
            prompt_tokens = self._tokenizer.count_request_tokens(request)
            updated["prompt_tokens"] = prompt_tokens

        if completion_tokens == 0:
            completion_tokens = self._tokenizer.count_response_tokens(response)
            updated["completion_tokens"] = completion_tokens

        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
            updated["total_tokens"] = total_tokens

        if not updated:
            return response

        new_usage = usage.model_copy(update=updated)
        return response.model_copy(update={"usage": new_usage})
