"""
Flat-file state management for zwarm.

State structure (with instance isolation):
.zwarm/
├── instances.json              # Registry of all instances
└── instances/
    └── <instance-id>/
        ├── state.json          # Current state (sessions, tasks)
        ├── events.jsonl        # Append-only event log
        ├── sessions/
        │   └── <session-id>/
        │       ├── messages.json
        │       └── output.log
        └── orchestrator/
            └── messages.json   # Orchestrator's message history (for resume)

Legacy structure (single instance, for backwards compat):
.zwarm/
├── state.json
├── events.jsonl
└── ...
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import ConversationSession, Event, Task


# --- Instance Registry ---

def get_instances_registry_path(base_dir: Path | str = ".zwarm") -> Path:
    """Get path to the instances registry file."""
    return Path(base_dir) / "instances.json"


def list_instances(base_dir: Path | str = ".zwarm") -> list[dict[str, Any]]:
    """List all registered instances."""
    registry_path = get_instances_registry_path(base_dir)
    if not registry_path.exists():
        return []
    try:
        return json.loads(registry_path.read_text()).get("instances", [])
    except (json.JSONDecodeError, KeyError):
        return []


def register_instance(
    instance_id: str,
    name: str | None = None,
    task: str | None = None,
    base_dir: Path | str = ".zwarm",
) -> None:
    """Register an instance in the global registry."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)

    registry_path = get_instances_registry_path(base_dir)

    # Load existing registry
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text())
        except json.JSONDecodeError:
            registry = {"instances": []}
    else:
        registry = {"instances": []}

    # Check if instance already registered
    existing_ids = {inst["id"] for inst in registry["instances"]}
    if instance_id in existing_ids:
        # Update existing entry
        for inst in registry["instances"]:
            if inst["id"] == instance_id:
                inst["updated_at"] = datetime.now().isoformat()
                inst["status"] = "active"
                if name:
                    inst["name"] = name
                if task:
                    inst["task"] = task[:100]  # Truncate
                break
    else:
        # Add new entry
        registry["instances"].append({
            "id": instance_id,
            "name": name or instance_id[:8],
            "task": (task[:100] if task else None),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
        })

    registry_path.write_text(json.dumps(registry, indent=2))


def update_instance_status(
    instance_id: str,
    status: str,
    base_dir: Path | str = ".zwarm",
) -> None:
    """Update an instance's status in the registry."""
    registry_path = get_instances_registry_path(base_dir)
    if not registry_path.exists():
        return

    try:
        registry = json.loads(registry_path.read_text())
    except json.JSONDecodeError:
        return

    for inst in registry.get("instances", []):
        if inst["id"] == instance_id:
            inst["status"] = status
            inst["updated_at"] = datetime.now().isoformat()
            break

    registry_path.write_text(json.dumps(registry, indent=2))


def get_instance_state_dir(
    instance_id: str | None = None,
    base_dir: Path | str = ".zwarm",
) -> Path:
    """
    Get the state directory for an instance.

    If instance_id is None, returns the legacy path for backwards compat.
    """
    base = Path(base_dir)
    if instance_id is None:
        return base  # Legacy: .zwarm/
    return base / "instances" / instance_id


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for non-standard types."""
    # Handle pydantic models
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # Handle objects with __dict__
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    # Handle datetime
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    # Fallback to string representation
    return str(obj)


class StateManager:
    """
    Manages flat-file state for zwarm.

    All state is stored as JSON files in a directory.
    With instance isolation: .zwarm/instances/<instance-id>/
    Legacy (no instance): .zwarm/

    This enables:
    - Git-backed history
    - Easy debugging (just read the files)
    - Resume from previous state
    - Multiple concurrent orchestrators (with instance isolation)
    """

    def __init__(
        self,
        state_dir: Path | str = ".zwarm",
        instance_id: str | None = None,
    ):
        self.base_dir = Path(state_dir)
        self.instance_id = instance_id

        # Resolve actual state directory
        if instance_id:
            self.state_dir = get_instance_state_dir(instance_id, self.base_dir)
        else:
            self.state_dir = self.base_dir

        self._sessions: dict[str, ConversationSession] = {}
        self._tasks: dict[str, Task] = {}
        self._orchestrator_messages: list[dict[str, Any]] = []

    def init(self) -> None:
        """Initialize state directory structure."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "sessions").mkdir(exist_ok=True)
        (self.state_dir / "orchestrator").mkdir(exist_ok=True)

        # Touch events.jsonl
        events_file = self.state_dir / "events.jsonl"
        if not events_file.exists():
            events_file.touch()

    # --- Sessions ---

    def add_session(self, session: ConversationSession) -> None:
        """Add a session and persist it."""
        self._sessions[session.id] = session
        self._save_session(session)
        self._save_state()

    def get_session(self, session_id: str) -> ConversationSession | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def update_session(self, session: ConversationSession) -> None:
        """Update a session and persist it."""
        self._sessions[session.id] = session
        self._save_session(session)
        self._save_state()

    def list_sessions(self, status: str | None = None) -> list[ConversationSession]:
        """List sessions, optionally filtered by status."""
        sessions = list(self._sessions.values())
        if status:
            sessions = [s for s in sessions if s.status.value == status]
        return sessions

    def _save_session(self, session: ConversationSession) -> None:
        """Save session to its own directory."""
        session_dir = self.state_dir / "sessions" / session.id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save messages
        messages_file = session_dir / "messages.json"
        messages_file.write_text(json.dumps([m.to_dict() for m in session.messages], indent=2))

    # --- Tasks ---

    def add_task(self, task: Task) -> None:
        """Add a task and persist it."""
        self._tasks[task.id] = task
        self._save_state()

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def update_task(self, task: Task) -> None:
        """Update a task and persist it."""
        self._tasks[task.id] = task
        self._save_state()

    def list_tasks(self, status: str | None = None) -> list[Task]:
        """List tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status.value == status]
        return tasks

    # --- Events ---

    def log_event(self, event: Event) -> None:
        """Append an event to the log."""
        events_file = self.state_dir / "events.jsonl"
        with open(events_file, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def get_events(
        self,
        session_id: str | None = None,
        task_id: str | None = None,
        kind: str | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        """Read events from the log, optionally filtered."""
        events_file = self.state_dir / "events.jsonl"
        if not events_file.exists():
            return []

        events = []
        with open(events_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = Event.from_dict(json.loads(line))
                if session_id and event.session_id != session_id:
                    continue
                if task_id and event.task_id != task_id:
                    continue
                if kind and event.kind != kind:
                    continue
                events.append(event)

        # Most recent first
        events.reverse()
        if limit:
            events = events[:limit]
        return events

    # --- Orchestrator State ---

    def save_orchestrator_messages(self, messages: list[dict[str, Any]]) -> None:
        """Save orchestrator's message history for resume."""
        self._orchestrator_messages = messages
        messages_file = self.state_dir / "orchestrator" / "messages.json"
        # Use custom encoder to handle non-serializable types
        messages_file.write_text(json.dumps(messages, indent=2, default=_json_serializer))

    def load_orchestrator_messages(self) -> list[dict[str, Any]]:
        """Load orchestrator's message history for resume."""
        messages_file = self.state_dir / "orchestrator" / "messages.json"
        if not messages_file.exists():
            return []
        return json.loads(messages_file.read_text())

    # --- State Persistence ---

    def _save_state(self) -> None:
        """Save current state to state.json."""
        state = {
            "updated_at": datetime.now().isoformat(),
            "sessions": {sid: s.to_dict() for sid, s in self._sessions.items()},
            "tasks": {tid: t.to_dict() for tid, t in self._tasks.items()},
        }
        state_file = self.state_dir / "state.json"
        state_file.write_text(json.dumps(state, indent=2))

    def load(self) -> None:
        """Load state from state.json."""
        state_file = self.state_dir / "state.json"
        if not state_file.exists():
            return

        state = json.loads(state_file.read_text())

        # Load sessions
        for sid, sdata in state.get("sessions", {}).items():
            self._sessions[sid] = ConversationSession.from_dict(sdata)

        # Load tasks
        for tid, tdata in state.get("tasks", {}).items():
            self._tasks[tid] = Task.from_dict(tdata)

    def clear(self) -> None:
        """Clear all state (for testing)."""
        self._sessions.clear()
        self._tasks.clear()
        self._orchestrator_messages.clear()

        # Clear files
        state_file = self.state_dir / "state.json"
        if state_file.exists():
            state_file.unlink()

        events_file = self.state_dir / "events.jsonl"
        if events_file.exists():
            events_file.write_text("")
