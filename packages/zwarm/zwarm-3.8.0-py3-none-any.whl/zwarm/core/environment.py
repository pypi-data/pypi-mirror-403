"""
OrchestratorEnv: A lean environment for the zwarm orchestrator.

Unlike ChatEnv, this environment:
- Has no notes/observations (we use StateManager instead)
- Has no chat() tool (orchestrator communicates via output_handler)
- Shows active sessions, step progress, and budget in observe()
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from pydantic import PrivateAttr
from wbal.environment import Environment

if TYPE_CHECKING:
    from zwarm.core.models import ConversationSession
    from zwarm.sessions import CodexSessionManager


class OrchestratorEnv(Environment):
    """
    Lean environment for the orchestrator agent.

    Provides:
    - Task context
    - Working directory info
    - Active session visibility
    - Step progress tracking
    - Budget/resource monitoring
    - Output handler for messages
    """

    task: str = ""
    working_dir: Path = Path(".")
    output_handler: Callable[[str], None] = lambda x: print(x)

    # Session manager (set by orchestrator) - pulls live data each observe()
    _session_manager: "CodexSessionManager | None" = PrivateAttr(default=None)

    # Legacy: old sessions dict (deprecated, for backwards compat)
    _sessions: dict[str, "ConversationSession"] | None = PrivateAttr(default=None)

    # Progress tracking (updated by orchestrator each step)
    _step_count: int = PrivateAttr(default=0)
    _max_steps: int = PrivateAttr(default=50)
    _total_tokens: int = PrivateAttr(default=0)
    _executor_tokens: int = PrivateAttr(default=0)  # Executor token usage

    # Budget config (set from config)
    _budget_max_sessions: int | None = PrivateAttr(default=None)

    # Pilot mode: simpler observation since human is in control
    _pilot_mode: bool = PrivateAttr(default=False)

    def set_session_manager(self, manager: "CodexSessionManager") -> None:
        """Set the session manager for live session visibility in observe()."""
        self._session_manager = manager

    def set_sessions(self, sessions: dict[str, "ConversationSession"]) -> None:
        """Legacy: Set the sessions dict for observe() visibility."""
        self._sessions = sessions

    def update_progress(
        self,
        step_count: int,
        max_steps: int,
        total_tokens: int = 0,
        executor_tokens: int = 0,
    ) -> None:
        """Update progress tracking (called by orchestrator each step)."""
        self._step_count = step_count
        self._max_steps = max_steps
        self._total_tokens = total_tokens
        self._executor_tokens = executor_tokens

    def set_budget(self, max_sessions: int | None = None) -> None:
        """Set budget limits from config."""
        self._budget_max_sessions = max_sessions

    def set_pilot_mode(self, enabled: bool = True) -> None:
        """
        Enable pilot mode for simpler env observation.

        In pilot mode, the human is in control and can use :status/:sessions
        commands to see detailed progress. The LLM only needs a brief context.
        """
        self._pilot_mode = enabled

    def observe(self) -> str:
        """
        Return observable state for the orchestrator.

        In full mode (autonomous orchestrator):
        - Progress (steps, tokens)
        - Session summary (pulled LIVE from CodexSessionManager)
        - Active sessions with their status
        - Working directory

        In pilot mode (human in control):
        - Brief session status (just what's active)
        - Working directory

        Note: Task is NOT included here as it's already in the user message.
        """
        if self._pilot_mode:
            return self._observe_pilot()
        return self._observe_full()

    def _observe_pilot(self) -> str:
        """Lean observation for pilot mode (human is in control)."""
        parts = []

        # Brief session status - just enough for context
        if self._session_manager is not None:
            sessions = self._session_manager.list_sessions()

            running = [s for s in sessions if s.status.value == "running"]
            if running:
                session_lines = []
                for s in running:
                    task_preview = s.task[:40] + "..." if len(s.task) > 40 else s.task
                    session_lines.append(f"  • {s.short_id}: {task_preview}")
                parts.append("## Active Sessions\n" + "\n".join(session_lines))

            # Just show counts for completed/failed
            completed = sum(1 for s in sessions if s.status.value == "completed")
            failed = sum(1 for s in sessions if s.status.value == "failed")
            if completed or failed:
                status = []
                if completed:
                    status.append(f"{completed} completed")
                if failed:
                    status.append(f"{failed} failed")
                parts.append(f"Previous: {', '.join(status)}")

        # Working directory
        parts.append(f"Working dir: {self.working_dir.absolute()}")

        return "\n\n".join(parts) if parts else ""

    def _observe_full(self) -> str:
        """Full observation for autonomous orchestrator runs."""
        parts = []

        # Progress bar and stats
        progress_pct = (
            (self._step_count / self._max_steps * 100) if self._max_steps > 0 else 0
        )
        bar_len = 20
        filled = (
            int(bar_len * self._step_count / self._max_steps)
            if self._max_steps > 0
            else 0
        )
        bar = "█" * filled + "░" * (bar_len - filled)

        progress_lines = [
            f"Steps: [{bar}] {self._step_count}/{self._max_steps} ({progress_pct:.0f}%)",
        ]
        if self._total_tokens > 0 or self._executor_tokens > 0:
            token_parts = []
            if self._total_tokens > 0:
                token_parts.append(f"orchestrator: ~{self._total_tokens:,}")
            if self._executor_tokens > 0:
                token_parts.append(f"executors: ~{self._executor_tokens:,}")
            progress_lines.append(f"Tokens: {', '.join(token_parts)}")

        parts.append("## Progress\n" + "\n".join(progress_lines))

        # Session summary - pull LIVE from CodexSessionManager
        if self._session_manager is not None:
            sessions = self._session_manager.list_sessions()

            running = sum(1 for s in sessions if s.status.value == "running")
            completed = sum(1 for s in sessions if s.status.value == "completed")
            failed = sum(1 for s in sessions if s.status.value == "failed")
            total = len(sessions)

            summary = f"Sessions: {running} running, {completed} done, {failed} failed ({total} total)"
            if self._budget_max_sessions:
                summary += f" [limit: {self._budget_max_sessions}]"

            parts.append(f"## Resources\n{summary}")

            # Running sessions detail
            running_sessions = [s for s in sessions if s.status.value == "running"]
            if running_sessions:
                session_lines = []
                for session in running_sessions:
                    task_preview = (
                        session.task[:50] + "..."
                        if len(session.task) > 50
                        else session.task
                    )
                    tokens = session.token_usage.get("total_tokens", 0)
                    token_info = f", {tokens:,} tok" if tokens else ""
                    session_lines.append(
                        f"  • {session.short_id} (turn {session.turn}{token_info}): {task_preview}"
                    )
                parts.append("## Running Sessions\n" + "\n".join(session_lines))

            # Recently completed (for visibility)
            recent_completed = [
                s for s in sessions
                if s.status.value == "completed"
            ][:3]  # Last 3 completed
            if recent_completed:
                session_lines = []
                for session in recent_completed:
                    task_preview = (
                        session.task[:40] + "..."
                        if len(session.task) > 40
                        else session.task
                    )
                    tokens = session.token_usage.get("total_tokens", 0)
                    session_lines.append(
                        f"  • {session.short_id} ✓ ({tokens:,} tok): {task_preview}"
                    )
                parts.append("## Recently Completed\n" + "\n".join(session_lines))

        # Working directory (less prominent)
        parts.append(f"## Context\nWorking dir: {self.working_dir.absolute()}")

        return "\n\n".join(parts)
