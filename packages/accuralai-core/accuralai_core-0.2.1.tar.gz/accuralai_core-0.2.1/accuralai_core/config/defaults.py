"""Default configuration presets."""

from __future__ import annotations

from typing import Any, Dict

from .schema import BackendSettings, CacheSettings, CoreSettings, RouterSettings, ToolSettings


def get_default_settings() -> CoreSettings:
    """Return baseline settings that rely on built-in mock components."""
    defaults: Dict[str, Any] = {
        "canonicalizer": {
            "plugin": "advanced",
            "options": {
                "enable_whitespace_compression": False,  # Disabled - preserving whitespace improves response quality
                "normalize_tags": True,
                "default_tags": [],
                "metadata_defaults": {},
                "auto_cache_key": True,
                "cache_key_metadata_fields": [],
            },
        },
        "cache": CacheSettings(
            plugin="layered",
            ttl_s=300,
            options={
                "stats_enabled": True,
                "promote_on_hit": True,
                "memory": {"max_entries": 512, "copy_on_get": True, "stats_enabled": True},
                "disk": {
                    "path": ".cache/accuralai-core/cache.sqlite",
                    "size_limit_mb": 256,
                    "ensure_directory": True,
                },
            },
        ).model_dump(),
        "router": RouterSettings(default_backend="mock").model_dump(),
        "backends": {"mock": BackendSettings(plugin="mock").model_dump()},
        "validators": [
            {
                "plugin": "tool",
                "options": {
                    "available_tools": [
                        "read.file",
                        "write.file", 
                        "list.directory",
                        "search.files",
                        "grep.text",
                        "file.info",
                        "get.working_directory",
                        "path.exists",
                        "run.command",
                        "delete.file",
                        "copy.file",
                        "move.file",
                        "create.directory",
                        "change.working_directory",
                        "get.environment_variables"
                    ],
                    "provide_feedback": True,
                    "feedback_message": "I attempted to use a tool that is not available. I am a general purpose AI assistant and can help with a wide variety of topics and tasks. Please provide the answer directly without using tools, or use one of the available tools."
                }
            }
        ],
        "post_processors": [],
        "tools": ToolSettings(
            enabled_by_default=[
                "read.file",
                "write.file", 
                "list.directory",
                "search.files",
                "grep.text",
                "file.info",
                "get.working_directory",
                "path.exists"
            ],
            disabled_by_default=[
                "run.command",
                "delete.file",
                "copy.file",
                "move.file",
                "create.directory",
                "change.working_directory",
                "get.environment_variables"
            ],
            auto_enable=False
        ).model_dump(),
    }
    return CoreSettings.model_validate(defaults)


def get_dev_settings() -> CoreSettings:
    """Return developer-friendly settings (identical to defaults for now)."""
    return get_default_settings()
