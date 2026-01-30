"""Plugin discovery and registry utilities."""

from .registry import PluginRegistry
from .discovery import discover_entry_points
from .specs import PluginSpec

__all__ = ["PluginRegistry", "discover_entry_points", "PluginSpec"]
