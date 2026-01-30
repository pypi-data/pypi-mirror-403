"""Lifecycle hook management for the orchestrator."""

from __future__ import annotations

from typing import Awaitable, Callable, List, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .orchestrator import CoreOrchestrator

LifecycleHook = Callable[["CoreOrchestrator"], Awaitable[None]]

_startup_hooks: List[LifecycleHook] = []
_shutdown_hooks: List[LifecycleHook] = []


def register_startup_hook(hook: LifecycleHook) -> None:
    """Register a coroutine executed during orchestrator startup."""
    _startup_hooks.append(hook)


def register_shutdown_hook(hook: LifecycleHook) -> None:
    """Register a coroutine executed during orchestrator shutdown."""
    _shutdown_hooks.append(hook)


async def startup(orchestrator: "CoreOrchestrator") -> None:
    """Invoke registered startup hooks."""
    for hook in _startup_hooks:
        await hook(orchestrator)


async def shutdown(orchestrator: "CoreOrchestrator") -> None:
    """Invoke registered shutdown hooks."""
    for hook in reversed(_shutdown_hooks):
        await hook(orchestrator)
