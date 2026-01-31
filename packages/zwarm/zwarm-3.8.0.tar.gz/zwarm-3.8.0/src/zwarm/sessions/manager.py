"""
Codex Session Manager - Background process management for Codex agents.

This module implements the CodexSessionManager, which handles:
- Spawning `codex exec --json` subprocesses
- Parsing Codex's JSONL output format
- Loading config from .zwarm/codex.toml

Inherits shared functionality from BaseSessionManager.
"""

from __future__ import annotations

import json
import subprocess
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .base import (
    BaseSessionManager,
    Session,
    SessionMessage,
    SessionStatus,
)

# Re-export for backwards compatibility
CodexSession = Session


class CodexSessionManager(BaseSessionManager):
    """
    Manages background Codex sessions.

    Sessions are stored in:
    .zwarm/sessions/<session_id>/
        meta.json      - Session metadata
        turns/
            turn_1.jsonl
            turn_2.jsonl
            ...
    """

    adapter_name = "codex"
    default_model = "gpt-5.1-codex-mini"

    # =========================================================================
    # Codex-specific config handling
    # =========================================================================

    def _load_codex_config(self) -> dict[str, Any]:
        """
        Load codex.toml from state_dir.

        Returns parsed TOML as dict, or empty dict if not found.
        """
        codex_toml = self.state_dir / "codex.toml"
        if not codex_toml.exists():
            return {}
        try:
            with open(codex_toml, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    def _build_codex_overrides(self, config: dict[str, Any]) -> list[str]:
        """
        Convert codex.toml config to -c override flags.

        Handles nested sections like [features] and [sandbox_workspace_write].

        Returns list of ["-c", "key=value", "-c", "key2=value2", ...]
        """
        overrides = []

        def add_override(key: str, value: Any):
            """Add a -c override for a key=value pair."""
            if isinstance(value, bool):
                value = "true" if value else "false"
            overrides.extend(["-c", f"{key}={value}"])

        for key, value in config.items():
            if isinstance(value, dict):
                # Nested section like [features] or [sandbox_workspace_write]
                for subkey, subvalue in value.items():
                    add_override(f"{key}.{subkey}", subvalue)
            else:
                # Top-level key
                add_override(key, value)

        return overrides

    # =========================================================================
    # Session lifecycle (Codex-specific implementation)
    # =========================================================================

    def start_session(
        self,
        task: str,
        working_dir: Path | None = None,
        model: str | None = None,
        sandbox: str = "workspace-write",
        source: str = "user",
    ) -> Session:
        """
        Start a new Codex session in the background.

        Args:
            task: The task description
            working_dir: Working directory for codex (default: cwd)
            model: Model override (default: from codex.toml or gpt-5.1-codex-mini)
            sandbox: Sandbox mode (ignored if full_danger=true in codex.toml)
            source: Who spawned this session ("user" or "orchestrator:<id>")

        Returns:
            The created session

        Note:
            Settings are read from .zwarm/codex.toml and passed via -c overrides.
            Run `zwarm init` to set up the config.
        """
        session_id = str(uuid4())
        working_dir = working_dir or Path.cwd()
        now = datetime.now().isoformat()

        # Load codex config from .zwarm/codex.toml
        codex_config = self._load_codex_config()

        # Get model from config or use default
        effective_model = model or codex_config.get("model", self.default_model)

        # Check if full_danger mode is enabled
        full_danger = codex_config.get("full_danger", False)

        session = Session(
            id=session_id,
            task=task,
            status=SessionStatus.PENDING,
            working_dir=working_dir,
            created_at=now,
            updated_at=now,
            model=effective_model,
            turn=1,
            messages=[SessionMessage(role="user", content=task, timestamp=now)],
            source=source,
            adapter=self.adapter_name,
        )

        # Create session directory
        session_dir = self._session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Build command with -c overrides from codex.toml
        cmd = ["codex"]

        # Add -c overrides from codex.toml (excluding special keys we handle separately)
        config_for_overrides = {k: v for k, v in codex_config.items() if k not in ("model", "full_danger")}
        cmd.extend(self._build_codex_overrides(config_for_overrides))

        # Add exec command and flags
        cmd.extend([
            "exec",
            "--json",
            "--skip-git-repo-check",
            "--model",
            effective_model,
            "-C",
            str(working_dir.absolute()),
        ])

        # Full danger mode bypasses all safety controls
        if full_danger:
            cmd.append("--dangerously-bypass-approvals-and-sandbox")

        cmd.extend(["--", task])

        # Start process with output redirected to file
        output_path = self._output_path(session_id, 1)
        output_file = open(output_path, "w")

        proc = subprocess.Popen(
            cmd,
            cwd=working_dir,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # Detach from parent process group
        )

        session.pid = proc.pid
        session.status = SessionStatus.RUNNING
        self._save_session(session)

        return session

    def inject_message(
        self,
        session_id: str,
        message: str,
    ) -> Session | None:
        """
        Inject a follow-up message into a completed session.

        This starts a new turn with the conversation context.

        Args:
            session_id: Session to continue
            message: The follow-up message

        Returns:
            Updated session or None if not found/not ready
        """
        session = self.get_session(session_id)
        if not session:
            return None

        if session.status == SessionStatus.RUNNING:
            return None

        # Build context from previous messages
        context_parts = []
        for msg in session.messages:
            if msg.role == "user":
                context_parts.append(f"USER: {msg.content}")
            elif msg.role == "assistant":
                context_parts.append(f"ASSISTANT: {msg.content}")

        # Create augmented prompt with context
        augmented_task = f"""Continue the following conversation:

{chr(10).join(context_parts)}

USER: {message}

Continue from where you left off, addressing the user's new message."""

        # Start new turn
        session.turn += 1
        now = datetime.now().isoformat()
        session.messages.append(
            SessionMessage(role="user", content=message, timestamp=now)
        )

        # Build command with -c overrides from codex.toml
        codex_config = self._load_codex_config()
        full_danger = codex_config.get("full_danger", False)

        cmd = ["codex"]

        # Add -c overrides from codex.toml (excluding special keys)
        config_for_overrides = {k: v for k, v in codex_config.items() if k not in ("model", "full_danger")}
        cmd.extend(self._build_codex_overrides(config_for_overrides))

        cmd.extend([
            "exec",
            "--json",
            "--skip-git-repo-check",
            "--model",
            session.model,
            "-C",
            str(session.working_dir.absolute()),
        ])

        # Full danger mode bypasses all safety controls
        if full_danger:
            cmd.append("--dangerously-bypass-approvals-and-sandbox")

        cmd.extend(["--", augmented_task])

        # Start process
        output_path = self._output_path(session.id, session.turn)
        output_file = open(output_path, "w")

        proc = subprocess.Popen(
            cmd,
            cwd=session.working_dir,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        session.pid = proc.pid
        session.status = SessionStatus.RUNNING
        self._save_session(session)

        return session

    # =========================================================================
    # Output parsing (Codex-specific JSONL format)
    # =========================================================================

    def _is_output_complete(self, session_id: str, turn: int) -> bool:
        """
        Check if output file indicates the task completed.

        Looks for completion markers like 'turn.completed' or 'task.completed'
        in the JSONL output. This is more reliable than PID checking.
        """
        output_path = self._output_path(session_id, turn)
        if not output_path.exists():
            return False

        try:
            content = output_path.read_text()
            for line in content.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    event_type = event.get("type", "")
                    # Check for any completion marker
                    if event_type in (
                        "turn.completed",
                        "task.completed",
                        "completed",
                        "done",
                    ):
                        return True
                    # Also check for error as a form of completion
                    if event_type == "error":
                        return True
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

        return False

    def _parse_output(
        self, output_path: Path
    ) -> tuple[list[SessionMessage], dict[str, int], str | None]:
        """
        Parse JSONL output from codex exec.

        Returns:
            (messages, token_usage, error)
        """
        messages: list[SessionMessage] = []
        usage: dict[str, int] = {}
        error: str | None = None

        if not output_path.exists():
            return messages, usage, "Output file not found"

        content = output_path.read_text()

        for line in content.strip().split("\n"):
            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type", "")

            if event_type == "item.completed":
                item = event.get("item", {})
                item_type = item.get("type", "")

                if item_type == "agent_message":
                    text = item.get("text", "")
                    if text:
                        messages.append(
                            SessionMessage(
                                role="assistant",
                                content=text,
                                timestamp=datetime.now().isoformat(),
                            )
                        )

                elif item_type == "reasoning":
                    # Could optionally capture reasoning
                    pass

                elif item_type == "function_call":
                    # Track tool calls
                    func_name = item.get("name", "unknown")
                    messages.append(
                        SessionMessage(
                            role="tool",
                            content=f"[Calling: {func_name}]",
                            metadata={"function": func_name},
                        )
                    )

                elif item_type == "function_call_output":
                    output = item.get("output", "")
                    if output and len(output) < 500:
                        messages.append(
                            SessionMessage(
                                role="tool",
                                content=f"[Output]: {output[:500]}",
                            )
                        )

            elif event_type == "turn.completed":
                turn_usage = event.get("usage", {})
                for key, value in turn_usage.items():
                    usage[key] = usage.get(key, 0) + value
                # Compute total_tokens if not present
                if "total_tokens" not in usage:
                    usage["total_tokens"] = usage.get("input_tokens", 0) + usage.get(
                        "output_tokens", 0
                    )

            elif event_type == "error":
                error = event.get("message", str(event))

        return messages, usage, error

    def get_trajectory(
        self, session_id: str, full: bool = False, max_output_len: int = 200
    ) -> list[dict]:
        """
        Get the full trajectory of a session - all steps in order.

        Args:
            session_id: Session to get trajectory for
            full: If True, include full untruncated content
            max_output_len: Max length for outputs when full=False

        Returns a list of step dicts with type, summary, and details.
        This shows the "broad strokes" of what the agent did.
        """
        if full:
            max_output_len = 999999  # Effectively unlimited
        session = self.get_session(session_id)
        if not session:
            return []

        trajectory = []

        for turn in range(1, session.turn + 1):
            output_path = self._output_path(session.id, turn)
            if not output_path.exists():
                continue

            content = output_path.read_text()
            step_num = 0

            for line in content.strip().split("\n"):
                if not line.strip():
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type", "")

                if event_type == "item.completed":
                    item = event.get("item", {})
                    item_type = item.get("type", "")
                    step_num += 1

                    if item_type == "reasoning":
                        text = item.get("text", "")
                        summary_len = max_output_len if full else 100
                        trajectory.append(
                            {
                                "turn": turn,
                                "step": step_num,
                                "type": "reasoning",
                                "summary": text[:summary_len]
                                + ("..." if len(text) > summary_len else ""),
                                "full_text": text if full else None,
                            }
                        )

                    elif item_type == "command_execution":
                        cmd = item.get("command", "")
                        output = item.get("aggregated_output", "")
                        exit_code = item.get("exit_code")
                        # Truncate output
                        output_preview = output[:max_output_len]
                        if len(output) > max_output_len:
                            output_preview += "..."
                        trajectory.append(
                            {
                                "turn": turn,
                                "step": step_num,
                                "type": "command",
                                "command": cmd,
                                "output": output_preview.strip(),
                                "exit_code": exit_code,
                            }
                        )

                    elif item_type == "function_call":
                        func_name = item.get("name", "unknown")
                        args = item.get("arguments", {})
                        args_str = str(args)
                        args_len = max_output_len if full else 100
                        trajectory.append(
                            {
                                "turn": turn,
                                "step": step_num,
                                "type": "tool_call",
                                "tool": func_name,
                                "args_preview": args_str[:args_len]
                                + ("..." if len(args_str) > args_len else ""),
                                "full_args": args if full else None,
                            }
                        )

                    elif item_type == "function_call_output":
                        output = item.get("output", "")
                        output_preview = output[:max_output_len]
                        if len(output) > max_output_len:
                            output_preview += "..."
                        trajectory.append(
                            {
                                "turn": turn,
                                "step": step_num,
                                "type": "tool_output",
                                "output": output_preview,
                            }
                        )

                    elif item_type == "agent_message":
                        text = item.get("text", "")
                        summary_len = max_output_len if full else 200
                        trajectory.append(
                            {
                                "turn": turn,
                                "step": step_num,
                                "type": "message",
                                "summary": text[:summary_len]
                                + ("..." if len(text) > summary_len else ""),
                                "full_text": text if full else None,
                                "full_length": len(text),
                            }
                        )

        return trajectory
