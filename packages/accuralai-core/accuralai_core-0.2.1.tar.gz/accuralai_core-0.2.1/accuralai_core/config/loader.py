"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping

from ..contracts.errors import ConfigurationError
from .schema import CoreSettings


def load_settings(
    *,
    overrides: Mapping[str, Any] | None = None,
    config_paths: Iterable[str | Path] | None = None,
) -> CoreSettings:
    """Load settings from optional file paths, environment, and overrides."""
    merged: Dict[str, Any] = {}
    if config_paths:
        for path in config_paths:
            file_data = load_from_file(path)
            merged = merge_dicts(merged, file_data)

    if overrides:
        merged = merge_dicts(merged, dict(overrides))

    return CoreSettings(**merged)


def load_from_file(path: str | Path) -> Dict[str, Any]:
    """Load a configuration mapping from a TOML file."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        msg = f"Configuration file '{file_path}' does not exist"
        raise ConfigurationError(msg)

    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - Python <3.11 w/out tomli
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError as fallback_error:
            msg = (
                "Reading configuration files requires the 'tomli' package on "
                "Python < 3.11. Install accuralai-core with the 'toml' extra or "
                "add tomli to your environment."
            )
            raise ConfigurationError(msg, cause=fallback_error) from fallback_error

    try:
        data = tomllib.loads(file_path.read_text())
    except tomllib.TOMLDecodeError as error:  # pragma: no cover - tomllib handles decode errors
        msg = f"Invalid TOML configuration in '{file_path}': {error}"
        raise ConfigurationError(msg, cause=error) from error

    return data if isinstance(data, dict) else {}


def merge_dicts(base: MutableMapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    """Deep-merge override into base and return a new mapping."""
    result: Dict[str, Any] = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], MutableMapping)
            and isinstance(value, Mapping)
        ):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
