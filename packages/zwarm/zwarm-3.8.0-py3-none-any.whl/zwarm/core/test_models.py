"""Tests for core models and state management."""

import tempfile
from pathlib import Path

import pytest

from zwarm.core.models import (
    ConversationSession,
    Event,
    Message,
    SessionMode,
    SessionStatus,
    Task,
    TaskStatus,
    event_session_completed,
    event_session_started,
    event_task_created,
)
from zwarm.core.state import StateManager


class TestMessage:
    def test_create_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_message_serialization(self):
        msg = Message(role="assistant", content="Hi there")
        data = msg.to_dict()
        restored = Message.from_dict(data)
        assert restored.role == msg.role
        assert restored.content == msg.content


class TestConversationSession:
    def test_create_session(self):
        session = ConversationSession(
            adapter="codex_mcp",
            mode=SessionMode.SYNC,
            task_description="Test task",
        )
        assert session.id is not None
        assert session.adapter == "codex_mcp"
        assert session.mode == SessionMode.SYNC
        assert session.status == SessionStatus.ACTIVE

    def test_add_message(self):
        session = ConversationSession()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there")
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_complete_session(self):
        session = ConversationSession()
        session.complete("Done!")
        assert session.status == SessionStatus.COMPLETED
        assert session.completed_at is not None
        assert session.exit_message == "Done!"

    def test_fail_session(self):
        session = ConversationSession()
        session.fail("Error occurred")
        assert session.status == SessionStatus.FAILED
        assert session.exit_message == "Error occurred"

    def test_session_serialization(self):
        session = ConversationSession(
            adapter="claude_code",
            mode=SessionMode.ASYNC,
            task_description="Build feature",
            model="claude-sonnet",
        )
        session.add_message("user", "Start")
        session.conversation_id = "conv-123"

        data = session.to_dict()
        restored = ConversationSession.from_dict(data)

        assert restored.id == session.id
        assert restored.adapter == "claude_code"
        assert restored.mode == SessionMode.ASYNC
        assert restored.conversation_id == "conv-123"
        assert len(restored.messages) == 1


class TestTask:
    def test_create_task(self):
        task = Task(description="Fix the bug")
        assert task.id is not None
        assert task.status == TaskStatus.PENDING

    def test_task_lifecycle(self):
        task = Task(description="Implement feature")

        # Start
        task.start("session-123")
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.session_id == "session-123"

        # Complete
        task.complete("Feature implemented")
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Feature implemented"

    def test_task_serialization(self):
        task = Task(description="Test task", parent_task_id="parent-123")
        task.start("session-456")

        data = task.to_dict()
        restored = Task.from_dict(data)

        assert restored.id == task.id
        assert restored.description == "Test task"
        assert restored.parent_task_id == "parent-123"
        assert restored.session_id == "session-456"


class TestEvent:
    def test_create_event(self):
        event = Event(
            kind="test_event",
            session_id="session-123",
            payload={"key": "value"},
        )
        assert event.id is not None
        assert event.kind == "test_event"

    def test_event_factories(self):
        session = ConversationSession(task_description="Test")
        event = event_session_started(session)
        assert event.kind == "session_started"
        assert event.session_id == session.id

        task = Task(description="Do something")
        event = event_task_created(task)
        assert event.kind == "task_created"
        assert event.task_id == task.id


class TestStateManager:
    def test_init_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / ".zwarm"
            manager = StateManager(state_dir)
            manager.init()

            assert state_dir.exists()
            assert (state_dir / "sessions").exists()
            assert (state_dir / "orchestrator").exists()
            assert (state_dir / "events.jsonl").exists()

    def test_session_crud(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(Path(tmpdir) / ".zwarm")
            manager.init()

            # Add
            session = ConversationSession(task_description="Test")
            manager.add_session(session)

            # Get
            retrieved = manager.get_session(session.id)
            assert retrieved is not None
            assert retrieved.task_description == "Test"

            # Update
            session.add_message("user", "Hello")
            manager.update_session(session)

            # List
            sessions = manager.list_sessions()
            assert len(sessions) == 1

            # Filter by status
            active = manager.list_sessions(status="active")
            assert len(active) == 1

    def test_task_crud(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(Path(tmpdir) / ".zwarm")
            manager.init()

            # Add
            task = Task(description="Build feature")
            manager.add_task(task)

            # Get
            retrieved = manager.get_task(task.id)
            assert retrieved is not None

            # Update
            task.start("session-123")
            manager.update_task(task)

            # List
            tasks = manager.list_tasks(status="in_progress")
            assert len(tasks) == 1

    def test_event_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(Path(tmpdir) / ".zwarm")
            manager.init()

            # Log events
            session = ConversationSession()
            manager.log_event(event_session_started(session))
            manager.log_event(event_session_completed(session))

            # Read events
            events = manager.get_events()
            assert len(events) == 2
            assert events[0].kind == "session_completed"  # Most recent first

            # Filter by session
            events = manager.get_events(session_id=session.id)
            assert len(events) == 2

            # Filter by kind
            events = manager.get_events(kind="session_started")
            assert len(events) == 1

    def test_orchestrator_messages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(Path(tmpdir) / ".zwarm")
            manager.init()

            messages = [
                {"role": "system", "content": "You are an orchestrator"},
                {"role": "user", "content": "Build a feature"},
            ]
            manager.save_orchestrator_messages(messages)

            loaded = manager.load_orchestrator_messages()
            assert len(loaded) == 2
            assert loaded[0]["role"] == "system"

    def test_state_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / ".zwarm"

            # Create and save state
            manager1 = StateManager(state_dir)
            manager1.init()

            session = ConversationSession(task_description="Persistent session")
            manager1.add_session(session)

            task = Task(description="Persistent task")
            manager1.add_task(task)

            # Load in new manager
            manager2 = StateManager(state_dir)
            manager2.load()

            assert manager2.get_session(session.id) is not None
            assert manager2.get_task(task.id) is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
