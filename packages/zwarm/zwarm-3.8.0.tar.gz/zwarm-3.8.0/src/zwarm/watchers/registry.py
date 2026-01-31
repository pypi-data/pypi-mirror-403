"""
Watcher registry for discovering and instantiating watchers.
"""

from __future__ import annotations

from typing import Any, Type

from zwarm.watchers.base import Watcher


# Global watcher registry
_WATCHERS: dict[str, Type[Watcher]] = {}


def register_watcher(name: str):
    """
    Decorator to register a watcher class.

    Example:
        @register_watcher("progress")
        class ProgressWatcher(Watcher):
            ...
    """

    def decorator(cls: Type[Watcher]) -> Type[Watcher]:
        cls.name = name
        _WATCHERS[name] = cls
        return cls

    return decorator


def get_watcher(name: str, config: dict[str, Any] | None = None) -> Watcher:
    """
    Get a watcher instance by name.

    Args:
        name: Registered watcher name
        config: Optional config to pass to watcher

    Returns:
        Instantiated watcher

    Raises:
        ValueError: If watcher not found
    """
    if name not in _WATCHERS:
        raise ValueError(
            f"Unknown watcher: {name}. Available: {list(_WATCHERS.keys())}"
        )
    return _WATCHERS[name](config)


def list_watchers() -> list[str]:
    """List all registered watcher names."""
    return list(_WATCHERS.keys())
