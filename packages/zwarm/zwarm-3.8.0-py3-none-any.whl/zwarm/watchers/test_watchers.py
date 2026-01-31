"""Tests for the watcher system."""

import pytest

from zwarm.watchers import (
    Watcher,
    WatcherContext,
    WatcherResult,
    WatcherAction,
    WatcherManager,
    WatcherConfig,
    get_watcher,
    list_watchers,
)


class TestWatcherRegistry:
    def test_list_watchers(self):
        """Built-in watchers should be registered."""
        watchers = list_watchers()
        assert "progress" in watchers
        assert "budget" in watchers
        assert "scope" in watchers
        assert "pattern" in watchers
        assert "quality" in watchers

    def test_get_watcher(self):
        """Can get watcher by name."""
        watcher = get_watcher("progress")
        assert watcher.name == "progress"

    def test_get_unknown_watcher(self):
        """Unknown watcher raises error."""
        with pytest.raises(ValueError, match="Unknown watcher"):
            get_watcher("nonexistent")


class TestProgressWatcher:
    @pytest.mark.asyncio
    async def test_continues_on_normal_progress(self):
        """Normal progress should continue."""
        watcher = get_watcher("progress")
        ctx = WatcherContext(
            task="Test task",
            step=2,
            max_steps=10,
            messages=[
                {"role": "user", "content": "Start"},
                {"role": "assistant", "content": "Working on it"},
            ],
        )
        result = await watcher.observe(ctx)
        assert result.action == WatcherAction.CONTINUE


class TestBudgetWatcher:
    @pytest.mark.asyncio
    async def test_warns_at_budget_threshold(self):
        """Should warn when approaching step limit."""
        watcher = get_watcher("budget", {"warn_at_percent": 80})
        ctx = WatcherContext(
            task="Test task",
            step=9,  # 90% of max
            max_steps=10,
            messages=[],
        )
        result = await watcher.observe(ctx)
        assert result.action == WatcherAction.NUDGE
        assert "remaining" in result.guidance.lower()

    @pytest.mark.asyncio
    async def test_continues_when_under_budget(self):
        """Should continue when well under budget."""
        watcher = get_watcher("budget")
        ctx = WatcherContext(
            task="Test task",
            step=2,
            max_steps=10,
            messages=[],
        )
        result = await watcher.observe(ctx)
        assert result.action == WatcherAction.CONTINUE

    @pytest.mark.asyncio
    async def test_only_counts_active_sessions(self):
        """Should only count active sessions, not completed/failed ones."""
        watcher = get_watcher("budget", {"max_sessions": 2})
        # Create 5 sessions: 1 active, 2 completed, 2 failed
        ctx = WatcherContext(
            task="Test task",
            step=2,
            max_steps=10,
            messages=[],
            sessions=[
                {"id": "s1", "status": "active"},
                {"id": "s2", "status": "completed"},
                {"id": "s3", "status": "completed"},
                {"id": "s4", "status": "failed"},
                {"id": "s5", "status": "failed"},
            ],
        )
        # Should continue because only 1 active session (limit is 2)
        result = await watcher.observe(ctx)
        assert result.action == WatcherAction.CONTINUE

    @pytest.mark.asyncio
    async def test_warns_when_active_sessions_at_limit(self):
        """Should warn when active sessions reach the limit."""
        watcher = get_watcher("budget", {"max_sessions": 2})
        ctx = WatcherContext(
            task="Test task",
            step=2,
            max_steps=10,
            messages=[],
            sessions=[
                {"id": "s1", "status": "active"},
                {"id": "s2", "status": "active"},
                {"id": "s3", "status": "completed"},
            ],
        )
        # Should nudge because 2 active sessions (at limit)
        result = await watcher.observe(ctx)
        assert result.action == WatcherAction.NUDGE
        assert "2 active sessions" in result.guidance


class TestPatternWatcher:
    @pytest.mark.asyncio
    async def test_detects_pattern(self):
        """Should detect configured patterns."""
        watcher = get_watcher("pattern", {
            "patterns": [
                {"regex": r"ERROR", "action": "nudge", "message": "Error detected!"}
            ]
        })
        ctx = WatcherContext(
            task="Test task",
            step=1,
            max_steps=10,
            messages=[
                {"role": "assistant", "content": "Got ERROR in the build"}
            ],
        )
        result = await watcher.observe(ctx)
        assert result.action == WatcherAction.NUDGE
        assert "Error detected" in result.guidance

    @pytest.mark.asyncio
    async def test_abort_pattern(self):
        """Should abort on critical patterns."""
        watcher = get_watcher("pattern", {
            "patterns": [
                {"regex": r"rm -rf /", "action": "abort", "message": "Dangerous command!"}
            ]
        })
        ctx = WatcherContext(
            task="Test task",
            step=1,
            max_steps=10,
            messages=[
                {"role": "assistant", "content": "Running rm -rf /"}
            ],
        )
        result = await watcher.observe(ctx)
        assert result.action == WatcherAction.ABORT


class TestWatcherManager:
    @pytest.mark.asyncio
    async def test_runs_multiple_watchers(self):
        """Manager runs all watchers."""
        manager = WatcherManager([
            WatcherConfig(name="progress"),
            WatcherConfig(name="budget"),
        ])
        ctx = WatcherContext(
            task="Test task",
            step=2,
            max_steps=10,
            messages=[],
        )
        result = await manager.observe(ctx)
        assert isinstance(result, WatcherResult)

    @pytest.mark.asyncio
    async def test_highest_priority_wins(self):
        """Most severe action should win."""
        manager = WatcherManager([
            WatcherConfig(name="budget", config={"warn_at_percent": 50}),  # Will nudge
            WatcherConfig(name="pattern", config={
                "patterns": [{"regex": "ABORT", "action": "abort", "message": "Abort!"}]
            }),
        ])
        ctx = WatcherContext(
            task="Test task",
            step=6,  # 60% - triggers budget nudge
            max_steps=10,
            messages=[
                {"role": "assistant", "content": "Must ABORT now"}
            ],
        )
        result = await manager.observe(ctx)
        # Abort should take precedence over nudge
        assert result.action == WatcherAction.ABORT

    @pytest.mark.asyncio
    async def test_empty_manager_continues(self):
        """Manager with no watchers should continue."""
        manager = WatcherManager([])
        ctx = WatcherContext(
            task="Test task",
            step=1,
            max_steps=10,
            messages=[],
        )
        result = await manager.observe(ctx)
        assert result.action == WatcherAction.CONTINUE

    @pytest.mark.asyncio
    async def test_disabled_watcher_skipped(self):
        """Disabled watchers should be skipped."""
        manager = WatcherManager([
            WatcherConfig(name="pattern", enabled=False, config={
                "patterns": [{"regex": ".*", "action": "abort", "message": "Always abort"}]
            }),
        ])
        ctx = WatcherContext(
            task="Test task",
            step=1,
            max_steps=10,
            messages=[
                {"role": "assistant", "content": "This would normally trigger abort"}
            ],
        )
        result = await manager.observe(ctx)
        # Since the pattern watcher is disabled, should continue
        assert result.action == WatcherAction.CONTINUE
