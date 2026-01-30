"""Session state utilities for the interactive CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Import version from package metadata
try:
    from importlib.metadata import version
    ACCURALAI_CORE_VERSION = version("accuralai-core")
except Exception:
    # Fallback if importlib.metadata is not available or package not installed
    ACCURALAI_CORE_VERSION = "Unknown"


@dataclass(slots=True)
class SessionState:
    """In-memory session configuration for the interactive shell."""

    system_prompt: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    route_hint: Optional[str] = None
    response_format: str = "text"
    stream: bool = False
    history_enabled: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)
    config_paths: List[str] = field(default_factory=list)
    config_overrides: Optional[Dict[str, Any]] = None
    debug: bool = False
    tools_version: int = 0
    tool_defs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tool_functions: Dict[str, str] = field(default_factory=dict)
    conversation: List[Dict[str, Any]] = field(default_factory=list)
    theme: str = "default"
    version: str = field(default_factory=lambda: ACCURALAI_CORE_VERSION)

    # MDAP settings
    mdap_enabled: bool = False
    mdap_preset: Optional[str] = None
    mdap_settings: Optional[Dict[str, Any]] = None

    def reset(self) -> None:
        """Reset non-configurable session preferences to defaults."""
        self.system_prompt = None
        self.tags.clear()
        self.metadata.clear()
        self.parameters.clear()
        self.route_hint = None
        self.response_format = "text"
        self.stream = False
        self.history_enabled = False
        self.history.clear()
        self.debug = False
        self.tools_version += 1
        self.tool_defs.clear()
        self.tool_functions.clear()
        self.conversation.clear()
        self.theme = "default"
        self.mdap_enabled = False
        self.mdap_preset = None
        self.mdap_settings = None

    def to_serializable(self) -> Dict[str, Any]:
        """Return JSON-serializable snapshot of the session."""
        return {
            "system_prompt": self.system_prompt,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "parameters": dict(self.parameters),
            "route_hint": self.route_hint,
            "response_format": self.response_format,
            "stream": self.stream,
            "history_enabled": self.history_enabled,
            "history": list(self.history),
            "config_paths": list(self.config_paths),
            "config_overrides": dict(self.config_overrides or {}),
            "debug": self.debug,
            "tools_version": self.tools_version,
            "tools": self.tool_defs,
            "tool_functions": dict(self.tool_functions),
            "conversation": list(self.conversation),
            "theme": self.theme,
            "version": self.version,
            "mdap_enabled": self.mdap_enabled,
            "mdap_preset": self.mdap_preset,
            "mdap_settings": self.mdap_settings,
        }


def create_default_state(
    *,
    config_paths: Optional[List[str]] = None,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> SessionState:
    """Build a session state populated with initial configuration paths."""
    state = SessionState()
    
    # Set a default system prompt that clarifies the AI is a general purpose LLM
    state.system_prompt = """You are a helpful, knowledgeable AI assistant with access to various tools for file manipulation, system operations, and information retrieval. You can discuss any topic, answer questions, provide explanations, and help with a wide range of tasks. The tools available to you are helpers that extend your capabilities - they do not restrict what topics you can discuss or what information you can provide. You should use tools when they would be helpful for the user's request, but you can also provide general knowledge, explanations, and assistance on any subject without needing to use tools."""
    
    if config_paths:
        state.config_paths.extend(config_paths)
    if config_overrides:
        state.config_overrides = dict(config_overrides)
    return state
