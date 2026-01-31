"""
Delegation tools for the orchestrator.

These are the core tools that orchestrators use to delegate work to executors.
They use the same session managers that `zwarm interactive` uses - no special
MCP integration, no separate code path.

The orchestrator LLM has access to the exact same tools a human would use.

Supports multiple adapters:
- codex: OpenAI's Codex CLI (default)
- claude: Anthropic's Claude Code CLI

Tools:
- delegate: Start a new session (with adapter selection)
- converse: Continue a conversation (inject follow-up message)
- check_session: Check status of a session
- end_session: End/kill a session
- list_sessions: List all sessions
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wbal.helper import weaveTool

if TYPE_CHECKING:
    from zwarm.orchestrator import Orchestrator

# Available adapters
ADAPTERS = ["codex", "claude"]


def _get_session_manager(orchestrator: "Orchestrator"):
    """
    Get the default session manager for list/get operations.

    Uses CodexSessionManager as the default since all adapters share
    the same .zwarm/sessions/ directory structure.
    """
    if not hasattr(orchestrator, "_session_manager") or orchestrator._session_manager is None:
        from zwarm.sessions import CodexSessionManager
        orchestrator._session_manager = CodexSessionManager(orchestrator.working_dir / ".zwarm")
    return orchestrator._session_manager


def _get_adapter_manager(orchestrator: "Orchestrator", adapter: str):
    """
    Get the session manager for a specific adapter.

    Each adapter has its own manager for start_session/inject_message,
    but they all share the same .zwarm/sessions/ directory.

    Args:
        orchestrator: The orchestrator instance
        adapter: Adapter name ("codex" or "claude")

    Returns:
        Session manager for the specified adapter
    """
    # Initialize adapter managers dict if needed
    if not hasattr(orchestrator, "_adapter_managers"):
        orchestrator._adapter_managers = {}

    # Return cached manager if exists
    if adapter in orchestrator._adapter_managers:
        return orchestrator._adapter_managers[adapter]

    # Create new manager for this adapter
    from zwarm.sessions import get_session_manager
    manager = get_session_manager(adapter, str(orchestrator.working_dir / ".zwarm"))
    orchestrator._adapter_managers[adapter] = manager

    return manager


def _truncate(text: str, max_len: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def _format_session_header(session) -> str:
    """Format a nice session header."""
    adapter = getattr(session, "adapter", "codex")
    return f"[{session.short_id}] {adapter} ({session.status.value})"


def _get_total_tokens(session) -> int:
    """Get total tokens, computing from input+output if not present."""
    usage = session.token_usage
    if "total_tokens" in usage:
        return usage["total_tokens"]
    return usage.get("input_tokens", 0) + usage.get("output_tokens", 0)


def _validate_working_dir(
    requested_dir: Path | str | None,
    default_dir: Path,
    allowed_dirs: list[str] | None,
) -> tuple[Path, str | None]:
    """
    Validate requested working directory against allowed_dirs config.

    Args:
        requested_dir: Directory requested by the agent (or None for default)
        default_dir: The orchestrator's working directory
        allowed_dirs: Config setting - None means only default allowed,
                     ["*"] means any, or list of allowed paths

    Returns:
        (validated_path, error_message) - error is None if valid
    """
    if requested_dir is None:
        return default_dir, None

    requested = Path(requested_dir).resolve()

    # Check if directory exists
    if not requested.exists():
        return default_dir, f"Directory does not exist: {requested}"

    if not requested.is_dir():
        return default_dir, f"Not a directory: {requested}"

    # If allowed_dirs is None, only default is allowed
    if allowed_dirs is None:
        if requested == default_dir.resolve():
            return requested, None
        return default_dir, (
            f"Directory not allowed: {requested}. "
            f"Agent can only delegate to working directory ({default_dir}). "
            "Set orchestrator.allowed_dirs in config to allow other directories."
        )

    # If ["*"], any directory is allowed
    if allowed_dirs == ["*"]:
        return requested, None

    # Check against allowed list
    for allowed in allowed_dirs:
        allowed_path = Path(allowed).resolve()
        # Allow if requested is the allowed path or a subdirectory of it
        try:
            requested.relative_to(allowed_path)
            return requested, None
        except ValueError:
            continue

    return default_dir, (
        f"Directory not allowed: {requested}. "
        f"Allowed directories: {allowed_dirs}"
    )


@weaveTool
def delegate(
    self: "Orchestrator",
    task: str,
    model: str | None = None,
    working_dir: str | None = None,
    adapter: str = "codex",
) -> dict[str, Any]:
    """
    Delegate work to an executor agent. Returns immediately - sessions run async.

    Supports multiple adapters:
    - codex: OpenAI's Codex CLI (default, fast, good for code tasks)
    - claude: Claude Code CLI (powerful, good for complex reasoning)

    WORKFLOW:
        1. delegate(task="...") -> session_id
        2. sleep(30)
        3. peek_session(session_id) -> {is_running: true/false}
        4. If is_running, goto 2
        5. check_session(session_id) -> FULL response

    Args:
        task: Clear description of what to do. Be specific about requirements.
        model: Model override (codex: gpt-5.1-codex-mini, claude: sonnet).
        working_dir: Directory for executor to work in (default: orchestrator's dir).
        adapter: Which executor to use - "codex" (default) or "claude".

    Returns:
        {session_id, status: "running", adapter}

    Example:
        delegate(task="Add a logout button to the navbar")
        delegate(task="Refactor auth to OAuth2", adapter="claude")
    """
    # Validate adapter
    if adapter not in ADAPTERS:
        return {
            "success": False,
            "error": f"Unknown adapter: {adapter}. Available: {ADAPTERS}",
            "hint": f"Use one of: {ADAPTERS}",
        }

    # Validate working directory
    effective_dir, dir_error = _validate_working_dir(
        working_dir,
        self.working_dir,
        self.config.orchestrator.allowed_dirs,
    )

    if dir_error:
        return {
            "success": False,
            "error": dir_error,
            "hint": "Use the default working directory or ask user to update allowed_dirs config",
        }

    # Get the session manager for this adapter
    manager = _get_adapter_manager(self, adapter)

    # Determine model (defaults vary by adapter)
    if model:
        effective_model = model
    elif self.config.executor.model:
        effective_model = self.config.executor.model
    else:
        # Use adapter-specific defaults
        effective_model = manager.default_model

    # Determine sandbox mode
    sandbox = self.config.executor.sandbox or "workspace-write"

    # Start the session
    session = manager.start_session(
        task=task,
        working_dir=effective_dir,
        model=effective_model,
        sandbox=sandbox,
        source=f"orchestrator:{self.instance_id or 'default'}",
    )

    # Return immediately - session runs in background
    return {
        "success": True,
        "session": _format_session_header(session),
        "session_id": session.id,
        "status": "running",
        "task": _truncate(task, 100),
        "adapter": adapter,
        "model": effective_model,
        "hint": "Use sleep() then check_session(session_id) to monitor progress",
    }


@weaveTool
def converse(
    self: "Orchestrator",
    session_id: str,
    message: str,
) -> dict[str, Any]:
    """
    Continue a conversation with a session.

    This injects a follow-up message into the session, providing the
    conversation history as context. Like chatting with a developer.
    Returns immediately - use sleep() + check_session() to poll for the response.

    Works with any adapter (codex or claude) - automatically uses the
    correct adapter based on the session's original adapter.

    Args:
        session_id: The session to continue (from delegate() result).
        message: Your next message.

    Returns:
        {session_id, turn, status: "running"}

    Example:
        converse(session_id="abc123", message="Add tests")
        sleep(30)
        check_session(session_id)  # Get response
    """
    # First get session to determine adapter
    default_manager = _get_session_manager(self)
    session = default_manager.get_session(session_id)

    if not session:
        return {
            "success": False,
            "error": f"Unknown session: {session_id}",
            "hint": "Use list_sessions() to see available sessions",
        }

    # Check if session is in a conversable state
    from zwarm.sessions import SessionStatus
    if session.status == SessionStatus.RUNNING:
        return {
            "success": False,
            "error": "Session is still running",
            "hint": "Wait for the current task to complete, or use check_session() to monitor",
        }

    if session.status == SessionStatus.KILLED:
        return {
            "success": False,
            "error": "Session was killed",
            "hint": "Start a new session with delegate()",
        }

    # Get the correct adapter manager for this session
    adapter = getattr(session, "adapter", "codex")
    manager = _get_adapter_manager(self, adapter)

    # Inject the follow-up message
    # This uses the adapter's inject_message() which:
    # 1. Builds context from previous messages
    # 2. Starts a new turn with the context + new message (background process)
    updated_session = manager.inject_message(session_id, message)

    if not updated_session:
        return {
            "success": False,
            "error": "Failed to inject message",
            "session_id": session_id,
        }

    # Return immediately - session runs in background
    return {
        "success": True,
        "session": _format_session_header(updated_session),
        "session_id": session_id,
        "turn": updated_session.turn,
        "status": "running",
        "adapter": adapter,
        "you_said": _truncate(message, 100),
        "hint": "Use sleep() then check_session(session_id) to see the response",
    }


@weaveTool
def check_session(
    self: "Orchestrator",
    session_id: str,
) -> dict[str, Any]:
    """
    Check the status of a session and get the FULL response.

    This is your primary tool for seeing what an executor accomplished.
    Returns the complete, untruncated response from the agent.

    Use this after peek_session() shows the session is done, or when
    you need to see the full details of what was accomplished.

    Args:
        session_id: The session to check.

    Returns:
        {session_id, status, response (FULL), tokens, runtime}
    """
    manager = _get_session_manager(self)

    session = manager.get_session(session_id)
    if not session:
        return {
            "success": False,
            "error": f"Unknown session: {session_id}",
            "hint": "Use list_sessions() to see available sessions",
        }

    # Get latest response - FULL, not truncated
    response_text = ""
    messages = manager.get_messages(session_id)
    for msg in reversed(messages):
        if msg.role == "assistant":
            response_text = msg.content  # Full content, no truncation
            break

    # Build log path
    log_path = str(manager._output_path(session.id, session.turn))

    result = {
        "success": True,
        "session": _format_session_header(session),
        "session_id": session_id,
        "status": session.status.value,
        "is_running": session.is_running,
        "turn": session.turn,
        "message_count": len(messages),
        "task": _truncate(session.task, 80),  # Task can stay truncated
        "response": response_text if response_text else "(no response yet)",  # FULL response
        "tokens": _get_total_tokens(session),
        "runtime": session.runtime,
        "log_file": log_path,
    }

    # Add error info if failed
    from zwarm.sessions import SessionStatus
    if session.status == SessionStatus.FAILED:
        result["success"] = False
        result["error"] = session.error or "Unknown error"

    return result


@weaveTool
def peek_session(
    self: "Orchestrator",
    session_id: str,
) -> dict[str, Any]:
    """
    Quick peek at a session - minimal info for FAST POLLING.

    Use this in your polling loop to check if a session is done:
        1. delegate() -> start work
        2. sleep(30)
        3. peek_session() -> is_running? If yes, goto 2
        4. check_session() -> get FULL response

    Returns truncated preview only. Once done, use check_session() for full response.

    Args:
        session_id: The session to peek at.

    Returns:
        {session_id, status, is_running, latest_message (truncated preview)}
    """
    manager = _get_session_manager(self)

    session = manager.get_session(session_id)
    if not session:
        return {"success": False, "error": f"Unknown session: {session_id}"}

    # Get latest assistant message only
    latest = ""
    messages = manager.get_messages(session_id)
    for msg in reversed(messages):
        if msg.role == "assistant":
            latest = msg.content.replace("\n", " ")
            break

    return {
        "success": True,
        "session_id": session.short_id,
        "status": session.status.value,
        "is_running": session.status.value == "running",
        "latest_message": _truncate(latest, 150) if latest else None,
    }


@weaveTool
def get_trajectory(
    self: "Orchestrator",
    session_id: str,
    full: bool = False,
) -> dict[str, Any]:
    """
    Get the step-by-step trajectory of what the agent did.

    Shows reasoning, commands, tool calls, and responses in execution order.
    Use this to understand HOW the agent approached a task, debug failures,
    or verify the agent took the right steps.

    Args:
        session_id: The session to get trajectory for.
        full: If True, include FULL untruncated content for all steps.
              If False (default), returns concise summaries.

    Returns:
        {steps: ["[thinking] ...", "[command] $ ...", "[response] ..."], step_count}

    When to use:
    - check_session() -> what did the agent conclude? (FULL response)
    - get_trajectory() -> what steps did the agent take? (step-by-step)
    """
    manager = _get_session_manager(self)

    session = manager.get_session(session_id)
    if not session:
        return {"success": False, "error": f"Unknown session: {session_id}"}

    trajectory = manager.get_trajectory(session_id, full=full)

    # Format steps for easy reading
    formatted_steps = []
    for step in trajectory:
        step_type = step.get("type", "unknown")

        if step_type == "reasoning":
            text = step.get("full_text") if full else step.get("summary", "")
            formatted_steps.append(f"[thinking] {text}")
        elif step_type == "command":
            cmd = step.get("command", "")
            output = step.get("output", "")
            exit_code = step.get("exit_code")
            step_str = f"[command] $ {cmd}"
            if output:
                if full:
                    step_str += f"\n  → {output}"
                else:
                    step_str += f"\n  → {output[:100]}{'...' if len(output) > 100 else ''}"
            if exit_code and exit_code != 0:
                step_str += f" (exit: {exit_code})"
            formatted_steps.append(step_str)
        elif step_type == "tool_call":
            if full and step.get("full_args"):
                import json
                args_str = json.dumps(step["full_args"], indent=2)
                formatted_steps.append(f"[tool] {step.get('tool', 'unknown')}\n  {args_str}")
            else:
                formatted_steps.append(f"[tool] {step.get('tool', 'unknown')}({step.get('args_preview', '')})")
        elif step_type == "tool_output":
            output = step.get("output", "")
            if not full:
                output = output[:100]
            formatted_steps.append(f"[result] {output}")
        elif step_type == "message":
            text = step.get("full_text") if full else step.get("summary", "")
            formatted_steps.append(f"[response] {text}")

    return {
        "success": True,
        "session_id": session.short_id,
        "task": _truncate(session.task, 80),
        "step_count": len(trajectory),
        "steps": formatted_steps,
        "mode": "full" if full else "summary",
    }


@weaveTool
def end_session(
    self: "Orchestrator",
    session_id: str,
    reason: str | None = None,
    delete: bool = False,
) -> dict[str, Any]:
    """
    End/kill a session.

    Call this when:
    - You want to stop a running session
    - Clean up a completed session
    - Cancel a task

    Args:
        session_id: The session to end.
        reason: Optional reason for ending.
        delete: If True, delete session entirely (removes from list_sessions).

    Returns:
        {session_id, status}
    """
    manager = _get_session_manager(self)

    session = manager.get_session(session_id)
    if not session:
        return {
            "success": False,
            "error": f"Unknown session: {session_id}",
        }

    # If delete requested, remove entirely
    if delete:
        deleted = manager.delete_session(session_id)
        return {
            "success": deleted,
            "session_id": session_id,
            "status": "deleted",
            "reason": reason or "deleted by orchestrator",
        }

    # Kill if still running
    if session.is_running:
        killed = manager.kill_session(session_id)
        if not killed:
            return {
                "success": False,
                "error": "Failed to kill session",
                "session_id": session_id,
            }

        # Refresh
        session = manager.get_session(session_id)

    return {
        "success": True,
        "session": _format_session_header(session),
        "session_id": session_id,
        "status": session.status.value,
        "reason": reason or "ended by orchestrator",
        "turn": session.turn,
        "tokens": _get_total_tokens(session),
    }


@weaveTool
def list_sessions(
    self: "Orchestrator",
    status: str | None = None,
) -> dict[str, Any]:
    """
    List all sessions, optionally filtered by status.

    Returns rich information about each session including:
    - Status (running/completed/failed)
    - Last update time (for detecting changes)
    - Last message preview (quick peek at response)
    - Whether it's recently updated (needs_attention flag)

    Use this to monitor multiple parallel sessions and see which
    ones have new responses.

    Args:
        status: Filter by status ("running", "completed", "failed", "killed").

    Returns:
        {sessions: [...], count, running, completed, needs_attention}
    """
    from datetime import datetime

    manager = _get_session_manager(self)

    # Map string status to enum
    from zwarm.sessions import SessionStatus
    status_filter = None
    if status:
        status_map = {
            "running": SessionStatus.RUNNING,
            "completed": SessionStatus.COMPLETED,
            "failed": SessionStatus.FAILED,
            "killed": SessionStatus.KILLED,
            "pending": SessionStatus.PENDING,
        }
        status_filter = status_map.get(status.lower())

    sessions = manager.list_sessions(status=status_filter)

    def time_ago(iso_str: str) -> tuple[str, float]:
        """Convert ISO timestamp to ('Xm ago', seconds)."""
        try:
            dt = datetime.fromisoformat(iso_str)
            delta = datetime.now() - dt
            secs = delta.total_seconds()
            if secs < 60:
                return f"{int(secs)}s ago", secs
            elif secs < 3600:
                return f"{int(secs/60)}m ago", secs
            elif secs < 86400:
                return f"{secs/3600:.1f}h ago", secs
            else:
                return f"{secs/86400:.1f}d ago", secs
        except:
            return "?", 999999

    session_list = []
    needs_attention_count = 0

    for s in sessions:
        status_icon = {
            "running": "●",
            "completed": "✓",
            "failed": "✗",
            "killed": "○",
            "pending": "◌",
        }.get(s.status.value, "?")

        updated_str, updated_secs = time_ago(s.updated_at)

        # Get last assistant message
        messages = manager.get_messages(s.id)
        last_message = ""
        for msg in reversed(messages):
            if msg.role == "assistant":
                last_message = msg.content.replace("\n", " ")
                break

        # Flag sessions that need attention:
        # - Recently completed (< 60s)
        # - Failed
        is_recent = updated_secs < 60
        needs_attention = (
            (s.status == SessionStatus.COMPLETED and is_recent) or
            s.status == SessionStatus.FAILED
        )
        if needs_attention:
            needs_attention_count += 1

        session_list.append({
            "id": s.short_id,
            "full_id": s.id,
            "status": f"{status_icon} {s.status.value}",
            "is_running": s.status == SessionStatus.RUNNING,
            "task": _truncate(s.task, 50),
            "turn": s.turn,
            "updated": updated_str,
            "updated_secs": int(updated_secs),
            "last_message": _truncate(last_message, 100) if last_message else "(no response yet)",
            "needs_attention": needs_attention,
            "tokens": _get_total_tokens(s),
        })

    # Summary counts
    running_count = sum(1 for s in sessions if s.status == SessionStatus.RUNNING)
    completed_count = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)

    return {
        "success": True,
        "sessions": session_list,
        "count": len(sessions),
        "running": running_count,
        "completed": completed_count,
        "needs_attention": needs_attention_count,
        "filter": status or "all",
        "hint": "Sessions with needs_attention=True have new responses to review" if needs_attention_count else None,
    }


@weaveTool
def sleep(self, seconds: float) -> dict[str, Any]:
    """
    Sleep for a specified number of seconds.

    Use this when you've started async sessions (wait=False) and want to
    give them time to complete before checking their status. This lets you
    manage your own polling loop:

    1. delegate(task, wait=False) -> start background work
    2. sleep(10) -> wait a bit
    3. peek_session(id) -> check if done
    4. Repeat 2-3 if still running

    Args:
        seconds: Number of seconds to sleep (max 300 = 5 minutes)

    Returns:
        Dict with success status and actual sleep duration
    """
    # Cap at 5 minutes to prevent accidental long hangs
    max_sleep = 300.0
    actual_seconds = min(float(seconds), max_sleep)

    if actual_seconds <= 0:
        return {
            "success": False,
            "error": "Sleep duration must be positive",
            "requested": seconds,
        }

    time.sleep(actual_seconds)

    return {
        "success": True,
        "slept_seconds": actual_seconds,
        "capped": actual_seconds < seconds,
        "max_allowed": max_sleep if actual_seconds < seconds else None,
    }
