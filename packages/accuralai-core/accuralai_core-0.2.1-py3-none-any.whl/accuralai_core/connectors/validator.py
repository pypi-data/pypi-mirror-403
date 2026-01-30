"""Validator connector utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from ..config.schema import ValidatorSettings
from ..contracts.errors import ValidationError, raise_with_context
from ..contracts.models import GenerateRequest, GenerateResponse
from ..contracts.protocols import Validator
from ..plugins.registry import PluginRegistry

VALIDATOR_GROUP = "accuralai_core.validators"


@dataclass(slots=True)
class ValidatorBinding:
    """Validator chain and metadata."""

    validator: Validator
    plugin_ids: Sequence[str]


class NoOpValidator(Validator):
    """Pass-through validator."""

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        return response


async def build_noop_validator(**_: object) -> Validator:
    """Built-in validator factory."""
    return NoOpValidator()


def ensure_builtin_validator(registry: PluginRegistry) -> None:
    """Register fallback validator implementation."""
    if not registry.has_plugin(VALIDATOR_GROUP, "noop"):
        registry.register_builtin(VALIDATOR_GROUP, "noop", build_noop_validator)


class ValidatorChain(Validator):
    """Sequentially executes validators."""

    def __init__(self, entries: Sequence[Tuple[str, ValidatorSettings, Validator]]) -> None:
        self._entries = list(entries)

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        current = response
        for plugin_id, settings, validator in self._entries:
            if not settings.enabled:
                continue
            try:
                current = await validator.validate(current, request=request)
            except Exception as error:  # pragma: no cover - delegated to helper
                raise_with_context(
                    ValidationError(str(error), cause=error),
                    stage="validator",
                    plugin_id=plugin_id,
                    request_id=str(request.id),
                )
            if settings.stop_on_failure and current.finish_reason == "content_filter":
                break
        return current


async def load_validators(
    validator_settings: Sequence[ValidatorSettings],
    registry: PluginRegistry,
) -> ValidatorBinding:
    """Construct validator chain from configuration."""
    ensure_builtin_validator(registry)

    if not validator_settings:
        validator = await registry.build(VALIDATOR_GROUP, "noop")
        return ValidatorBinding(validator=validator, plugin_ids=["noop"])

    entries: List[Tuple[str, ValidatorSettings, Validator]] = []
    plugin_ids: List[str] = []
    for settings in validator_settings:
        plugin_id = settings.plugin or "noop"
        validator = await registry.build(VALIDATOR_GROUP, plugin_id, config=settings)
        entries.append((plugin_id, settings, validator))
        plugin_ids.append(plugin_id)

    return ValidatorBinding(validator=ValidatorChain(entries), plugin_ids=plugin_ids)
