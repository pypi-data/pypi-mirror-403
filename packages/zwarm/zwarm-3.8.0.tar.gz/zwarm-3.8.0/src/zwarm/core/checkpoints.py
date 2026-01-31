"""
Checkpoint primitives for state management.

Provides time-travel capability by recording snapshots of state at key points.
Used by pilot for turn-by-turn checkpointing, and potentially by other
interfaces that need state restoration.

Topology reminder:
    orchestrator → pilot → interactive → CodexSessionManager

These primitives sit at the core layer, usable by any interface above.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Checkpoint:
    """
    A snapshot of state at a specific point in time.

    Attributes:
        checkpoint_id: Unique identifier (e.g., turn number)
        label: Human-readable label (e.g., "T1", "T2")
        description: What action led to this state
        state: The actual state snapshot (deep-copied)
        timestamp: When checkpoint was created
        metadata: Optional extra data
    """
    checkpoint_id: int
    label: str
    description: str
    state: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckpointManager:
    """
    Manages checkpoints and time travel.

    Maintains a list of checkpoints and a current position. Supports:
    - Recording new checkpoints
    - Jumping to any previous checkpoint
    - Branching (going back and continuing creates new timeline)
    - History inspection

    Usage:
        mgr = CheckpointManager()

        # Record state after each action
        mgr.record(description="Added auth", state={"messages": [...], ...})
        mgr.record(description="Fixed bug", state={"messages": [...], ...})

        # Jump back
        cp = mgr.goto(1)  # Go to first checkpoint
        restored_state = cp.state

        # Continue from there (branches off)
        mgr.record(description="Different path", state={...})
    """

    checkpoints: list[Checkpoint] = field(default_factory=list)
    current_index: int = -1  # -1 = root (before any checkpoints)
    next_id: int = 1
    label_prefix: str = "T"  # Labels will be T1, T2, etc.

    def record(
        self,
        description: str,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """
        Record a new checkpoint.

        If not at the end of history (i.e., we've gone back), this creates
        a branch - future checkpoints are discarded.

        Args:
            description: What action led to this state
            state: State to snapshot (will be deep-copied)
            metadata: Optional extra data

        Returns:
            The created checkpoint
        """
        checkpoint = Checkpoint(
            checkpoint_id=self.next_id,
            label=f"{self.label_prefix}{self.next_id}",
            description=description,
            state=copy.deepcopy(state),
            metadata=metadata or {},
        )

        # If we're not at the end, we're branching - truncate future
        if self.current_index < len(self.checkpoints) - 1:
            self.checkpoints = self.checkpoints[:self.current_index + 1]

        self.checkpoints.append(checkpoint)
        self.current_index = len(self.checkpoints) - 1
        self.next_id += 1

        return checkpoint

    def goto(self, checkpoint_id: int) -> Checkpoint | None:
        """
        Jump to a specific checkpoint.

        Args:
            checkpoint_id: The checkpoint ID to jump to (0 = root)

        Returns:
            The checkpoint, or None if not found (or root)
        """
        if checkpoint_id == 0:
            # Root state - before any checkpoints
            self.current_index = -1
            return None

        for i, cp in enumerate(self.checkpoints):
            if cp.checkpoint_id == checkpoint_id:
                self.current_index = i
                return cp

        return None  # Not found

    def goto_label(self, label: str) -> Checkpoint | None:
        """
        Jump to a checkpoint by label (e.g., "T1", "root").

        Args:
            label: The label to find

        Returns:
            The checkpoint, or None if not found
        """
        if label.lower() == "root":
            self.current_index = -1
            return None

        for i, cp in enumerate(self.checkpoints):
            if cp.label == label:
                self.current_index = i
                return cp

        return None

    def current(self) -> Checkpoint | None:
        """Get the current checkpoint, or None if at root."""
        if self.current_index < 0 or self.current_index >= len(self.checkpoints):
            return None
        return self.checkpoints[self.current_index]

    def current_state(self) -> dict[str, Any] | None:
        """Get the current state, or None if at root."""
        cp = self.current()
        return copy.deepcopy(cp.state) if cp else None

    def history(
        self,
        limit: int | None = None,
        include_state: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get history entries for display.

        Args:
            limit: Max entries to return (most recent)
            include_state: Whether to include full state in entries

        Returns:
            List of history entries with checkpoint info
        """
        entries = []
        for i, cp in enumerate(self.checkpoints):
            entry = {
                "checkpoint_id": cp.checkpoint_id,
                "label": cp.label,
                "description": cp.description,
                "timestamp": cp.timestamp,
                "is_current": i == self.current_index,
                "metadata": cp.metadata,
            }
            if include_state:
                entry["state"] = cp.state
            entries.append(entry)

        if limit:
            entries = entries[-limit:]

        return entries

    def label_for(self, checkpoint_id: int) -> str:
        """Get label for a checkpoint ID."""
        if checkpoint_id == 0:
            return "root"
        return f"{self.label_prefix}{checkpoint_id}"

    def __len__(self) -> int:
        """Number of checkpoints."""
        return len(self.checkpoints)

    def is_at_root(self) -> bool:
        """Whether we're at root (before any checkpoints)."""
        return self.current_index < 0

    def is_at_end(self) -> bool:
        """Whether we're at the most recent checkpoint."""
        return self.current_index == len(self.checkpoints) - 1
