"""Entry-point discovery helpers."""

from __future__ import annotations

from importlib import metadata
from typing import List

from .specs import PluginSpec


def discover_entry_points(group: str) -> List[PluginSpec]:
    """Discover plugin specs registered under the given entry-point group."""
    try:
        entries = metadata.entry_points(group=group)
    except TypeError:  # pragma: no cover - Python <3.10 compatibility path
        entries = metadata.entry_points().select(group=group)
    specs: List[PluginSpec] = []
    for entry in entries:
        specs.append(PluginSpec(name=entry.name, group=group, entry_point=entry))
    return specs
