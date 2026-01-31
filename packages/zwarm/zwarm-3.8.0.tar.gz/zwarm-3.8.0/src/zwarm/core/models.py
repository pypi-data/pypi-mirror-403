"""
Core models for zwarm.

These are the fundamental data structures:
- ConversationSession: A session with an executor agent (sync or async)
- Task: A unit of work that may be delegated
- Event: An append-only log entry for audit/debugging
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4


class SessionMode(str, Enum):
    """Execution mode for a session."""

    SYNC = "sync"
    ASYNC = "async"


class SessionStatus(str, Enum):
    """Status of a conversation session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Message:
    """A single message in a conversation."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )


@dataclass
class ConversationSession:
    """
    A conversational session with an executor agent.

    Supports both sync (iterative conversation) and async (fire-and-forget) modes.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    adapter: str = "codex_mcp"  # codex_mcp | codex_exec | claude_code
    mode: SessionMode = SessionMode.SYNC
    status: SessionStatus = SessionStatus.ACTIVE
    working_dir: Path = field(default_factory=Path.cwd)
    messages: list[Message] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    # Adapter-specific handles (not serialized)
    conversation_id: str | None = None  # MCP conversationId for codex
    process: subprocess.Popen | None = field(default=None, repr=False)

    # Metadata
    task_description: str = ""
    model: str | None = None
    exit_message: str | None = None

    # Token usage tracking for cost calculation
    token_usage: dict[str, int] = field(default_factory=lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    })

    def add_usage(self, usage: dict[str, int]) -> None:
        """Add token usage from an interaction."""
        if not usage:
            return
        for key in self.token_usage:
            self.token_usage[key] += usage.get(key, 0)

    def add_message(self, role: Literal["user", "assistant", "system"], content: str) -> Message:
        """Add a message to the conversation."""
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        return msg

    def complete(self, exit_message: str | None = None) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.exit_message = exit_message

    def fail(self, error: str | None = None) -> None:
        """Mark session as failed."""
        self.status = SessionStatus.FAILED
        self.completed_at = datetime.now()
        self.exit_message = error

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (for persistence)."""
        return {
            "id": self.id,
            "adapter": self.adapter,
            "mode": self.mode.value,
            "status": self.status.value,
            "working_dir": str(self.working_dir),
            "messages": [m.to_dict() for m in self.messages],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "conversation_id": self.conversation_id,
            "task_description": self.task_description,
            "model": self.model,
            "exit_message": self.exit_message,
            "token_usage": self.token_usage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversationSession:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            adapter=data.get("adapter", "codex_mcp"),
            mode=SessionMode(data["mode"]),
            status=SessionStatus(data["status"]),
            working_dir=Path(data["working_dir"]),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            conversation_id=data.get("conversation_id"),
            task_description=data.get("task_description", ""),
            model=data.get("model"),
            exit_message=data.get("exit_message"),
            token_usage=data.get("token_usage", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}),
        )


@dataclass
class Task:
    """
    A unit of work that may be delegated to an executor.

    Tasks track what needs to be done and link to the session doing the work.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    session_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    result: str | None = None
    parent_task_id: str | None = None  # For subtasks

    def start(self, session_id: str) -> None:
        """Mark task as started with a session."""
        self.status = TaskStatus.IN_PROGRESS
        self.session_id = session_id

    def complete(self, result: str | None = None) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error: str | None = None) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "parent_task_id": self.parent_task_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            id=data["id"],
            description=data["description"],
            status=TaskStatus(data["status"]),
            session_id=data.get("session_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result=data.get("result"),
            parent_task_id=data.get("parent_task_id"),
        )


@dataclass
class Event:
    """
    An append-only log entry for audit and debugging.

    Events capture everything that happens in the system.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    kind: str = ""  # session_started, message_sent, task_completed, etc.
    session_id: str | None = None
    task_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "kind": self.kind,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            kind=data["kind"],
            session_id=data.get("session_id"),
            task_id=data.get("task_id"),
            payload=data.get("payload", {}),
        )


# Event factory functions for common event types
def event_session_started(session: ConversationSession) -> Event:
    return Event(
        kind="session_started",
        session_id=session.id,
        payload={
            "adapter": session.adapter,
            "mode": session.mode.value,
            "task": session.task_description,
        },
    )


def event_message_sent(session: ConversationSession, message: Message) -> Event:
    return Event(
        kind="message_sent",
        session_id=session.id,
        payload={
            "role": message.role,
            "content": message.content[:500],  # Truncate for log
        },
    )


def event_session_completed(session: ConversationSession) -> Event:
    return Event(
        kind="session_completed",
        session_id=session.id,
        payload={
            "status": session.status.value,
            "exit_message": session.exit_message,
            "message_count": len(session.messages),
        },
    )


def event_task_created(task: Task) -> Event:
    return Event(
        kind="task_created",
        task_id=task.id,
        payload={"description": task.description},
    )


def event_task_completed(task: Task) -> Event:
    return Event(
        kind="task_completed",
        task_id=task.id,
        session_id=task.session_id,
        payload={
            "status": task.status.value,
            "result": task.result[:500] if task.result else None,
        },
    )
