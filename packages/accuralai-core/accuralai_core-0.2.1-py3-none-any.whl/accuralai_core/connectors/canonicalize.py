"""Canonicalizer connector utilities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..config.schema import PluginSettings
from ..contracts.errors import ConfigurationError
from ..contracts.models import GenerateRequest
from ..contracts.protocols import Canonicalizer
from ..plugins.registry import PluginRegistry

CANONICALIZER_GROUP = "accuralai_core.canonicalizers"
LOGGER = logging.getLogger("accuralai.core")


@dataclass(slots=True)
class CanonicalizerBinding:
    """Resolved canonicalizer implementation and metadata."""

    canonicalizer: Canonicalizer
    plugin_id: Optional[str]


class IdentityCanonicalizer(Canonicalizer):
    """Fallback canonicalizer that normalizes minimal metadata."""

    async def canonicalize(self, request: GenerateRequest) -> GenerateRequest:
        normalized_tags = sorted(set(tag.lower() for tag in request.tags))
        return request.model_copy(update={"tags": normalized_tags})


async def build_identity_canonicalizer(**_: object) -> Canonicalizer:
    """Built-in fallback canonicalizer."""
    return IdentityCanonicalizer()


def ensure_builtin_canonicalizer(registry: PluginRegistry) -> None:
    """Ensure identity canonicalizer is registered for local development."""
    if not registry.has_plugin(CANONICALIZER_GROUP, "identity"):
        registry.register_builtin(CANONICALIZER_GROUP, "identity", build_identity_canonicalizer)


async def load_canonicalizer(
    settings: PluginSettings,
    registry: PluginRegistry,
) -> CanonicalizerBinding:
    """Load canonicalizer implementation using registry."""
    ensure_builtin_canonicalizer(registry)

    candidates = []
    if settings.plugin:
        candidates.append(settings.plugin)
    candidates.append("identity")

    last_error: Exception | None = None
    for plugin_id in candidates:
        try:
            canonicalizer = await registry.build(
                CANONICALIZER_GROUP,
                plugin_id,
                config=settings,
            )
            if plugin_id != (settings.plugin or "identity"):
                LOGGER.warning(
                    "Falling back to canonicalizer '%s' (requested '%s' unavailable).",
                    plugin_id,
                    settings.plugin,
                )
            return CanonicalizerBinding(canonicalizer=canonicalizer, plugin_id=plugin_id)
        except KeyError as error:
            last_error = error
            continue
    raise ConfigurationError(
        f"Canonicalizer plugin '{settings.plugin}' is not available.",
        cause=last_error,
    )
