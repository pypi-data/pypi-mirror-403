"""Plugin metadata representations."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import EntryPoint
from typing import Any, Callable, Mapping, Optional


@dataclass(slots=True)
class PluginSpec:
    """Metadata describing a plugin implementation."""

    name: str
    group: str
    entry_point: Optional[EntryPoint] = None
    factory: Optional[Callable[..., Any]] = None
    meta: Mapping[str, Any] = field(default_factory=dict)

    def load(self) -> Callable[..., Any]:
        """Return the callable factory for this plugin."""
        if self.factory is not None:
            return self.factory
        if self.entry_point is not None:
            return self.entry_point.load()
        msg = f"Plugin '{self.group}:{self.name}' does not define a factory"
        raise RuntimeError(msg)
