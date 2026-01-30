"""Post-processor connector utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from ..config.schema import PostProcessorSettings
from ..contracts.errors import PipelineError, raise_with_context
from ..contracts.models import GenerateRequest, GenerateResponse
from ..contracts.protocols import PostProcessor
from ..plugins.registry import PluginRegistry

POST_PROCESS_GROUP = "accuralai_core.post_processors"


@dataclass(slots=True)
class PostProcessorBinding:
    """Post-processor chain metadata."""

    processors: Sequence[PostProcessor]
    plugin_ids: Sequence[str]


class NoOpPostProcessor(PostProcessor):
    """Post-processor that leaves response unchanged."""

    async def process(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        return response


async def build_noop_post_processor(**_: object) -> PostProcessor:
    """Built-in noop processor factory."""
    return NoOpPostProcessor()


def ensure_builtin_post_processor(registry: PluginRegistry) -> None:
    """Register fallback post-processor."""
    if not registry.has_plugin(POST_PROCESS_GROUP, "noop"):
        registry.register_builtin(POST_PROCESS_GROUP, "noop", build_noop_post_processor)


async def load_post_processors(
    processor_settings: Sequence[PostProcessorSettings],
    registry: PluginRegistry,
) -> PostProcessorBinding:
    """Load post-processors from configuration."""
    ensure_builtin_post_processor(registry)

    if not processor_settings:
        return PostProcessorBinding(processors=[], plugin_ids=[])

    processors: List[PostProcessor] = []
    plugin_ids: List[str] = []
    for settings in processor_settings:
        plugin_id = settings.plugin or "noop"
        try:
            processor = await registry.build(POST_PROCESS_GROUP, plugin_id, config=settings)
        except Exception as error:  # pragma: no cover - plugin-defined failure
            raise_with_context(
                PipelineError(str(error), cause=error),
                stage="post_process",
                plugin_id=plugin_id,
                request_id=None,
            )
        processors.append(processor)
        plugin_ids.append(plugin_id)

    return PostProcessorBinding(processors=processors, plugin_ids=plugin_ids)
