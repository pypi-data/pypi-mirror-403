"""Runtime registry for pipeline plugins."""

from __future__ import annotations

import inspect
from collections import defaultdict
from typing import Any, Dict, Iterable, List, MutableMapping

from .discovery import discover_entry_points
from .specs import PluginSpec

PluginMap = MutableMapping[str, PluginSpec]


class PluginRegistry:
    """Holds plugin specs discovered via entry points or manual registration."""

    def __init__(self) -> None:
        self._specs: Dict[str, PluginMap] = defaultdict(dict)
        self._instances: Dict[str, Dict[str, Any]] = defaultdict(dict)

    @classmethod
    def from_discovery(cls, groups: Iterable[str]) -> "PluginRegistry":
        """Create a registry pre-populated with entry-point results."""
        registry = cls()
        for group in groups:
            for spec in discover_entry_points(group):
                registry.register(spec)
        return registry

    def register(self, spec: PluginSpec) -> None:
        """Register a plugin spec."""
        self._specs[spec.group][spec.name] = spec

    def register_builtin(self, group: str, name: str, factory: Any) -> None:
        """Register a built-in plugin factory without requiring entry points."""
        self.register(PluginSpec(group=group, name=name, factory=factory))

    def get_spec(self, group: str, name: str) -> PluginSpec:
        """Return the spec registered for the given plugin."""
        spec = self._specs.get(group, {}).get(name)
        if spec is None:
            available = ", ".join(sorted(self._specs.get(group, {}).keys()))
            msg = f"Plugin '{group}:{name}' not found. Available: {available or 'none'}"
            raise KeyError(msg)
        return spec

    async def build(self, group: str, name: str, **kwargs: Any) -> Any:
        """Instantiate a plugin, caching the instance per registry."""
        cache = self._instances[group]
        if name in cache:
            return cache[name]

        spec = self.get_spec(group, name)
        factory = spec.load()
        instance = factory(**kwargs)
        if inspect.isawaitable(instance):
            instance = await instance
        cache[name] = instance
        return instance

    def list_plugins(self, group: str) -> List[str]:
        """List available plugin names for a group."""
        return sorted(self._specs.get(group, {}).keys())

    def has_plugin(self, group: str, name: str) -> bool:
        """Return True if the plugin exists."""
        return name in self._specs.get(group, {})
