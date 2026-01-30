"""Tool registry for interactive CLI."""

from __future__ import annotations

import importlib
import pkgutil
from importlib.metadata import entry_points
from typing import Dict, Iterable

from .models import ToolSpec


class ToolRegistry:
    """Registry that discovers CLI tools from entry points."""

    ENTRY_GROUP = "accuralai_cli.tools"

    def __init__(self) -> None:
        self._specs: Dict[str, ToolSpec] = {}
        self._discovered = False

    def load(self) -> None:
        if self._discovered:
            return

        self._specs.clear()

        # Discover built-in tools bundled with CLI.
        from . import builtin as builtin_tools

        for finder, name, _ in pkgutil.iter_modules(builtin_tools.__path__, f"{builtin_tools.__name__}."):
            module = importlib.import_module(name)
            if hasattr(module, "tool_spec"):
                spec: ToolSpec = module.tool_spec
                self._specs[spec.name] = spec

        # Discover via entry points.
        try:
            eps = entry_points(group=self.ENTRY_GROUP)
        except TypeError:  # pragma: no cover - Python <3.10
            eps = entry_points().get(self.ENTRY_GROUP, [])

        for ep in eps:
            spec: ToolSpec = ep.load()
            spec.package = ep.module
            self._specs[spec.name] = spec

        self._discovered = True

    def reload(self) -> None:
        self._discovered = False
        self.load()

    def list_tools(self) -> Iterable[ToolSpec]:
        self.load()
        return sorted(self._specs.values(), key=lambda spec: spec.name)

    def get(self, name: str) -> ToolSpec | None:
        self.load()
        return self._specs.get(name)

    def get_by_function(self, function_name: str) -> ToolSpec | None:
        self.load()
        for spec in self._specs.values():
            if spec.function and spec.function.get("name") == function_name:
                return spec
        return None
