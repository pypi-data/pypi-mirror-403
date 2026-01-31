"""
Base watcher interface and types.

Watchers observe agent trajectories and can intervene to correct course.
They're designed to be:
- Composable: Layer multiple watchers for different concerns
- Non-blocking: Check asynchronously, don't slow down the agent
- Actionable: Return clear guidance when correction is needed
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WatcherAction(str, Enum):
    """What action to take based on watcher observation."""

    CONTINUE = "continue"  # Keep going, trajectory looks good
    NUDGE = "nudge"  # Insert guidance into next prompt
    PAUSE = "pause"  # Pause for human review
    ABORT = "abort"  # Stop execution immediately


@dataclass
class WatcherContext:
    """
    Context provided to watchers for observation.

    Contains everything a watcher might need to evaluate trajectory.
    """

    # Current orchestrator state
    task: str  # Original task
    step: int  # Current step number
    max_steps: int  # Maximum steps allowed
    messages: list[dict[str, Any]]  # Conversation history

    # Session activity
    sessions: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    # Working directory context
    working_dir: str | None = None
    files_changed: list[str] = field(default_factory=list)

    # Custom metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WatcherResult:
    """
    Result from a watcher observation.

    Contains the recommended action and any guidance to inject.
    """

    action: WatcherAction = WatcherAction.CONTINUE
    reason: str = ""  # Why this action was recommended
    guidance: str = ""  # Message to inject if action is NUDGE
    priority: int = 0  # Higher priority watchers take precedence
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def ok() -> "WatcherResult":
        """Trajectory looks good, continue."""
        return WatcherResult(action=WatcherAction.CONTINUE)

    @staticmethod
    def nudge(guidance: str, reason: str = "", priority: int = 0) -> "WatcherResult":
        """Insert guidance to correct trajectory."""
        return WatcherResult(
            action=WatcherAction.NUDGE,
            guidance=guidance,
            reason=reason,
            priority=priority,
        )

    @staticmethod
    def pause(reason: str, priority: int = 0) -> "WatcherResult":
        """Pause for human review."""
        return WatcherResult(
            action=WatcherAction.PAUSE,
            reason=reason,
            priority=priority,
        )

    @staticmethod
    def abort(reason: str, priority: int = 100) -> "WatcherResult":
        """Stop execution immediately."""
        return WatcherResult(
            action=WatcherAction.ABORT,
            reason=reason,
            priority=priority,
        )


class Watcher(ABC):
    """
    Base class for watchers.

    Watchers observe agent trajectories and provide guidance when needed.
    They're designed to be stateless - all context comes from WatcherContext.
    """

    name: str = "base"
    description: str = ""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize watcher with optional config."""
        self.config = config or {}

    @abstractmethod
    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        """
        Observe the current trajectory and decide action.

        Args:
            ctx: Current context with all trajectory info

        Returns:
            WatcherResult with recommended action
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"
