"""Configuration schema for accuralai-core."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings


class PluginSettings(BaseModel):
    """Generic plugin reference with configuration options."""

    plugin: Optional[str] = None
    enabled: bool = True
    options: Dict[str, Any] = Field(default_factory=dict)


class CacheSettings(PluginSettings):
    """Cache-specific configuration."""

    ttl_s: Optional[int] = Field(default=None, ge=0)


class RouterSettings(PluginSettings):
    """Router-specific configuration."""

    default_backend: Optional[str] = None


class BackendSettings(PluginSettings):
    """Backend configuration."""

    concurrency_limit: Optional[int] = Field(default=None, ge=1)


class ValidatorSettings(PluginSettings):
    """Validator configuration with optional identifier."""

    id: Optional[str] = None
    stop_on_failure: bool = False


class PostProcessorSettings(PluginSettings):
    """Post-processor configuration."""

    id: Optional[str] = None


class ToolSettings(BaseModel):
    """Tool configuration settings."""

    enabled_by_default: List[str] = Field(default_factory=list)
    disabled_by_default: List[str] = Field(default_factory=list)
    auto_enable: bool = Field(default=False)


class InstrumentationSettings(BaseModel):
    """Settings controlling instrumentation behaviour."""

    logging: Dict[str, Any] = Field(default_factory=lambda: {"enabled": True})


class CoreSettings(BaseSettings):
    """Top-level settings for the orchestrator."""

    canonicalizer: PluginSettings = Field(default_factory=PluginSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    router: RouterSettings = Field(default_factory=RouterSettings)
    backends: Dict[str, BackendSettings] = Field(default_factory=dict)
    validators: List[ValidatorSettings] = Field(default_factory=list)
    post_processors: List[PostProcessorSettings] = Field(default_factory=list)
    tools: ToolSettings = Field(default_factory=ToolSettings)
    instrumentation: InstrumentationSettings = Field(default_factory=InstrumentationSettings)

    model_config = {"env_prefix": "COMPOUNDAI_CORE__"}

    @model_validator(mode="after")
    def _ensure_backend_plugins(cls, settings: "CoreSettings") -> "CoreSettings":
        """Validate that backend definitions have plugin identifiers."""
        for backend_id, backend_cfg in settings.backends.items():
            if backend_cfg.plugin is None:
                msg = f"Backend '{backend_id}' requires a plugin identifier"
                raise ValueError(msg)
        return settings
