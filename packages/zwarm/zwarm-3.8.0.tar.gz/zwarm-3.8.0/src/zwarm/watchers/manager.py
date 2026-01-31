"""
Watcher manager for running multiple watchers.

Handles:
- Running watchers in parallel
- Combining results by priority
- Injecting guidance into orchestrator
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import weave

from zwarm.watchers.base import Watcher, WatcherContext, WatcherResult, WatcherAction
from zwarm.watchers.registry import get_watcher


@dataclass
class WatcherConfig:
    """Configuration for a watcher instance."""

    name: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


class WatcherManager:
    """
    Manages and runs multiple watchers.

    Watchers run in parallel and results are combined by priority.
    """

    def __init__(self, watcher_configs: list[WatcherConfig | dict] | None = None):
        """
        Initialize manager with watcher configurations.

        Args:
            watcher_configs: List of WatcherConfig or dicts with watcher configs
        """
        self._watchers: list[Watcher] = []
        self._results_history: list[tuple[str, WatcherResult]] = []

        # Load watchers from configs
        for cfg in watcher_configs or []:
            if isinstance(cfg, dict):
                cfg = WatcherConfig(**cfg)

            if cfg.enabled:
                try:
                    watcher = get_watcher(cfg.name, cfg.config)
                    self._watchers.append(watcher)
                except ValueError:
                    # Unknown watcher, skip
                    pass

    def add_watcher(self, watcher: Watcher) -> None:
        """Add a watcher instance."""
        self._watchers.append(watcher)

    @weave.op()
    async def _run_single_watcher(
        self,
        watcher_name: str,
        watcher: Watcher,
        ctx: WatcherContext,
    ) -> dict[str, Any]:
        """Run a single watcher - traced by Weave."""
        try:
            result = await watcher.observe(ctx)
            return {
                "watcher": watcher_name,
                "action": result.action.value,
                "priority": result.priority,
                "reason": result.reason,
                "guidance": result.guidance,
                "metadata": result.metadata,
                "success": True,
            }
        except Exception as e:
            return {
                "watcher": watcher_name,
                "success": False,
                "error": str(e),
            }

    @weave.op()
    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        """
        Run all watchers and return combined result.

        Results are combined by priority:
        - ABORT takes precedence over everything
        - PAUSE takes precedence over NUDGE
        - NUDGE takes precedence over CONTINUE
        - Within same action, higher priority wins

        Args:
            ctx: Context for watchers

        Returns:
            Combined WatcherResult
        """
        if not self._watchers:
            return WatcherResult.ok()

        # Run all watchers in parallel - each traced individually
        tasks = [
            self._run_single_watcher(watcher.name, watcher, ctx)
            for watcher in self._watchers
        ]
        watcher_outputs = await asyncio.gather(*tasks)

        # Collect valid results with their watcher names
        valid_results: list[tuple[str, WatcherResult]] = []
        for watcher, output in zip(self._watchers, watcher_outputs):
            if not output.get("success"):
                # Log and skip failed watchers
                continue
            result = WatcherResult(
                action=WatcherAction(output["action"]),
                priority=output["priority"],
                reason=output.get("reason"),
                guidance=output.get("guidance"),
                metadata=output.get("metadata", {}),
            )
            valid_results.append((watcher.name, result))
            self._results_history.append((watcher.name, result))

        if not valid_results:
            return WatcherResult.ok()

        # Sort by action severity (abort > pause > nudge > continue) then priority
        def sort_key(item: tuple[str, WatcherResult]) -> tuple[int, int]:
            _, result = item
            action_order = {
                WatcherAction.ABORT: 0,
                WatcherAction.PAUSE: 1,
                WatcherAction.NUDGE: 2,
                WatcherAction.CONTINUE: 3,
            }
            return (action_order[result.action], -result.priority)

        valid_results.sort(key=sort_key)

        # Return highest priority non-continue result
        for name, result in valid_results:
            if result.action != WatcherAction.CONTINUE:
                # Add which watcher triggered this
                result.metadata["triggered_by"] = name
                return result

        return WatcherResult.ok()

    def get_history(self) -> list[tuple[str, WatcherResult]]:
        """Get history of all watcher results."""
        return list(self._results_history)

    def clear_history(self) -> None:
        """Clear results history."""
        self._results_history.clear()


def build_watcher_manager(
    config: dict[str, Any] | None = None
) -> WatcherManager:
    """
    Build a WatcherManager from configuration.

    Args:
        config: Dict with "watchers" key containing list of watcher configs

    Returns:
        Configured WatcherManager
    """
    watcher_configs = (config or {}).get("watchers", [])
    return WatcherManager(watcher_configs)
