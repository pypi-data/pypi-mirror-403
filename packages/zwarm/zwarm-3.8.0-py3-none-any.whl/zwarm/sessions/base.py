"""
Base Session Manager - Abstract interface for executor adapters.

This module defines the shared interface and data structures that all
session managers (Codex, Claude, etc.) must implement.

Architecture:
- Each session runs an executor CLI in a background subprocess
- Output is streamed to .zwarm/sessions/<session_id>/turns/turn_N.jsonl
- Session metadata stored in meta.json
- Adapters implement CLI-specific command building and output parsing
"""

from __future__ import annotations

import json
import os
import signal
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


class SessionStatus(str, Enum):
    """Status of a session."""

    PENDING = "pending"  # Created but not started
    RUNNING = "running"  # Process is running
    COMPLETED = "completed"  # Process exited successfully
    FAILED = "failed"  # Process exited with error
    KILLED = "killed"  # Manually killed


@dataclass
class SessionMessage:
    """A message in a session's history."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionMessage":
        return cls(
            role=data.get("role", "unknown"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Session:
    """A managed executor session."""

    id: str
    task: str
    status: SessionStatus
    working_dir: Path
    created_at: str
    updated_at: str
    pid: int | None = None
    exit_code: int | None = None
    model: str = ""
    turn: int = 1
    messages: list[SessionMessage] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None
    # Source tracking: "user" for direct spawns, "orchestrator:<instance_id>" for delegated
    source: str = "user"
    # Adapter used: "codex", "claude", etc.
    adapter: str = "codex"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "status": self.status.value,
            "working_dir": str(self.working_dir),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "model": self.model,
            "turn": self.turn,
            "messages": [m.to_dict() for m in self.messages],
            "token_usage": self.token_usage,
            "error": self.error,
            "source": self.source,
            "adapter": self.adapter,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            id=data["id"],
            task=data["task"],
            status=SessionStatus(data["status"]),
            working_dir=Path(data["working_dir"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            pid=data.get("pid"),
            exit_code=data.get("exit_code"),
            model=data.get("model", ""),
            turn=data.get("turn", 1),
            messages=[SessionMessage.from_dict(m) for m in data.get("messages", [])],
            token_usage=data.get("token_usage", {}),
            error=data.get("error"),
            source=data.get("source", "user"),
            adapter=data.get("adapter", "codex"),
        )

    @property
    def is_running(self) -> bool:
        """Check if the session process is still running."""
        if self.pid is None:
            return False
        try:
            os.kill(self.pid, 0)  # Signal 0 just checks if process exists
            return True
        except OSError:
            return False

    @property
    def short_id(self) -> str:
        """Get first 8 chars of ID for display."""
        return self.id[:8]

    @property
    def runtime(self) -> str:
        """Get human-readable runtime."""
        created = datetime.fromisoformat(self.created_at)
        now = datetime.now()
        delta = now - created

        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}s"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m"
        else:
            return f"{delta.total_seconds() / 3600:.1f}h"

    @property
    def source_display(self) -> str:
        """Get short display string for source."""
        if self.source == "user":
            return "you"
        elif self.source.startswith("orchestrator:"):
            instance_id = self.source.split(":", 1)[1]
            return f"orch:{instance_id[:4]}"
        else:
            return self.source[:8]


# Type alias for backwards compatibility
CodexSession = Session


class BaseSessionManager(ABC):
    """
    Abstract base class for session managers.

    Manages background executor sessions with:
    - Session lifecycle (start, inject, kill, delete)
    - State persistence (.zwarm/sessions/<id>/)
    - Output parsing (JSONL → messages, trajectory)

    Subclasses implement adapter-specific logic:
    - Command building (CLI flags, config handling)
    - Output parsing (different JSONL formats)
    """

    # Adapter identifier (override in subclasses)
    adapter_name: str = "base"

    # Default model (override in subclasses)
    default_model: str = ""

    def __init__(self, state_dir: Path | str = ".zwarm"):
        self.state_dir = Path(state_dir)
        self.sessions_dir = self.state_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Path helpers (shared)
    # =========================================================================

    def _session_dir(self, session_id: str) -> Path:
        """Get the directory for a session."""
        return self.sessions_dir / session_id

    def _meta_path(self, session_id: str) -> Path:
        """Get the metadata file path for a session."""
        return self._session_dir(session_id) / "meta.json"

    def _output_path(self, session_id: str, turn: int = 1) -> Path:
        """Get the output file path for a session turn."""
        session_dir = self._session_dir(session_id)
        turns_dir = session_dir / "turns"
        turns_dir.mkdir(parents=True, exist_ok=True)
        return turns_dir / f"turn_{turn}.jsonl"

    # =========================================================================
    # State persistence (shared)
    # =========================================================================

    def _save_session(self, session: Session) -> None:
        """Save session metadata."""
        session.updated_at = datetime.now().isoformat()
        meta_path = self._meta_path(session.id)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(json.dumps(session.to_dict(), indent=2))

    def _load_session(self, session_id: str) -> Session | None:
        """Load session from disk."""
        meta_path = self._meta_path(session_id)
        if not meta_path.exists():
            return None
        try:
            data = json.loads(meta_path.read_text())

            # Enforce adapter scoping so managers don't load each other's sessions.
            fallback_adapter = self.adapter_name if self.adapter_name == "codex" else "codex"
            adapter = data.get("adapter") or fallback_adapter
            if adapter != self.adapter_name:
                return None

            # Ensure adapter is recorded for older sessions that may be missing it.
            data["adapter"] = adapter

            return Session.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    # =========================================================================
    # Session retrieval (shared with adapter hooks)
    # =========================================================================

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID (supports partial ID matching)."""
        # Try exact match first
        session = self._load_session(session_id)
        if session:
            self._maybe_update_status(session)
            return session

        # Try partial match
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.name.startswith(session_id):
                session = self._load_session(session_dir.name)
                if session:
                    self._maybe_update_status(session)
                    return session

        return None

    def list_sessions(self, status: SessionStatus | None = None) -> list[Session]:
        """List all sessions, optionally filtered by status."""
        sessions = []
        if not self.sessions_dir.exists():
            return sessions

        for session_dir in self.sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
            session = self._load_session(session_dir.name)
            if session:
                self._maybe_update_status(session)
                if status is None or session.status == status:
                    sessions.append(session)

        # Sort by created_at descending (newest first)
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def _maybe_update_status(self, session: Session) -> None:
        """Update session status if process completed."""
        if session.status == SessionStatus.RUNNING:
            if self._is_output_complete(session.id, session.turn) or not session.is_running:
                self._update_session_status(session)

    def _update_session_status(self, session: Session) -> None:
        """Update session status after process completion."""
        output_path = self._output_path(session.id, session.turn)
        if output_path.exists():
            messages, usage, error = self._parse_output(output_path)
            session.messages = messages
            session.token_usage = usage

            has_response = any(m.role == "assistant" for m in messages)

            if error and not has_response:
                session.status = SessionStatus.FAILED
                session.error = error
            elif error and has_response:
                session.status = SessionStatus.COMPLETED
                session.error = f"Completed with error: {error}"
            else:
                session.status = SessionStatus.COMPLETED
        else:
            session.status = SessionStatus.FAILED
            session.error = "No output file found"

        self._save_session(session)

    # =========================================================================
    # Process management (shared)
    # =========================================================================

    def kill_session(self, session_id: str, delete: bool = False) -> bool:
        """Kill a running session."""
        session = self.get_session(session_id)
        if not session:
            return False

        if session.pid and session.is_running:
            try:
                os.killpg(os.getpgid(session.pid), signal.SIGTERM)
                time.sleep(0.5)
                if session.is_running:
                    os.killpg(os.getpgid(session.pid), signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass

        if delete:
            return self.delete_session(session.id)

        session.status = SessionStatus.KILLED
        session.error = "Manually killed"
        self._save_session(session)
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely (removes from disk)."""
        import shutil

        session = self.get_session(session_id)
        if not session:
            return False

        if session.pid and session.is_running:
            try:
                os.killpg(os.getpgid(session.pid), signal.SIGTERM)
                time.sleep(0.3)
                if session.is_running:
                    os.killpg(os.getpgid(session.pid), signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass

        session_dir = self._session_dir(session.id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
            return True

        return False

    def get_output(self, session_id: str, turn: int | None = None) -> str:
        """Get raw JSONL output for a session."""
        session = self.get_session(session_id)
        if not session:
            return ""

        if turn is None:
            turn = session.turn

        output_path = self._output_path(session.id, turn)
        if not output_path.exists():
            return ""

        return output_path.read_text()

    def get_messages(self, session_id: str) -> list[SessionMessage]:
        """Get parsed messages for a session across all turns."""
        session = self.get_session(session_id)
        if not session:
            return []

        all_messages = []
        for turn in range(1, session.turn + 1):
            output_path = self._output_path(session.id, turn)
            if output_path.exists():
                messages, _, _ = self._parse_output(output_path)
                all_messages.extend(messages)

        return all_messages

    def cleanup_completed(self, keep_days: int = 7) -> int:
        """Remove old completed/failed/killed sessions."""
        import shutil
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=keep_days)
        cleaned = 0

        for session in self.list_sessions():
            if session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.KILLED):
                created = datetime.fromisoformat(session.created_at)
                if created < cutoff:
                    session_dir = self._session_dir(session.id)
                    if session_dir.exists():
                        shutil.rmtree(session_dir)
                        cleaned += 1

        return cleaned

    # =========================================================================
    # Abstract methods (adapter-specific)
    # =========================================================================

    @abstractmethod
    def start_session(
        self,
        task: str,
        working_dir: Path | None = None,
        model: str | None = None,
        sandbox: str = "workspace-write",
        source: str = "user",
    ) -> Session:
        """
        Start a new session in the background.

        Args:
            task: The task description
            working_dir: Working directory for the executor
            model: Model override
            sandbox: Sandbox mode
            source: Who spawned this session

        Returns:
            The created session
        """
        pass

    @abstractmethod
    def inject_message(
        self,
        session_id: str,
        message: str,
    ) -> Session | None:
        """
        Inject a follow-up message into a completed session.

        Args:
            session_id: Session to continue
            message: The follow-up message

        Returns:
            Updated session or None if not found/not ready
        """
        pass

    @abstractmethod
    def _is_output_complete(self, session_id: str, turn: int) -> bool:
        """
        Check if output file indicates the task completed.

        Args:
            session_id: Session ID
            turn: Turn number

        Returns:
            True if output indicates completion
        """
        pass

    @abstractmethod
    def _parse_output(
        self, output_path: Path
    ) -> tuple[list[SessionMessage], dict[str, int], str | None]:
        """
        Parse JSONL output from the executor.

        Args:
            output_path: Path to the JSONL file

        Returns:
            (messages, token_usage, error)
        """
        pass

    @abstractmethod
    def get_trajectory(
        self, session_id: str, full: bool = False, max_output_len: int = 200
    ) -> list[dict]:
        """
        Get the full trajectory of a session.

        Args:
            session_id: Session to get trajectory for
            full: If True, include full untruncated content
            max_output_len: Max length for outputs when full=False

        Returns:
            List of step dicts with type, summary, and details
        """
        pass
