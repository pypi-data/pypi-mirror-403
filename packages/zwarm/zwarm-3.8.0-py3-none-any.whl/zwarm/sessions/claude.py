"""
Claude Session Manager - Background process management for Claude Code agents.

This module implements the ClaudeSessionManager, which handles:
- Spawning `claude -p --output-format stream-json` subprocesses
- Parsing Claude Code's stream-json output format
- Loading config from .zwarm/claude.toml

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


class ClaudeSessionManager(BaseSessionManager):
    """
    Manages background Claude Code sessions.

    Sessions are stored in:
    .zwarm/sessions/<session_id>/
        meta.json      - Session metadata
        turns/
            turn_1.jsonl
            turn_2.jsonl
            ...

    Uses claude -p --output-format stream-json --verbose for JSON output.
    """

    adapter_name = "claude"
    default_model = "sonnet"  # Claude uses aliases like sonnet, opus, haiku

    # =========================================================================
    # Claude-specific config handling
    # =========================================================================

    def _load_claude_config(self) -> dict[str, Any]:
        """
        Load claude.toml from state_dir.

        Returns parsed TOML as dict, or empty dict if not found.
        """
        claude_toml = self.state_dir / "claude.toml"
        if not claude_toml.exists():
            return {}
        try:
            with open(claude_toml, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    # =========================================================================
    # Session lifecycle (Claude-specific implementation)
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
        Start a new Claude Code session in the background.

        Args:
            task: The task description
            working_dir: Working directory for claude (default: cwd)
            model: Model override (default: from claude.toml or sonnet)
            sandbox: Sandbox mode - maps to permission modes
            source: Who spawned this session ("user" or "orchestrator:<id>")

        Returns:
            The created session

        Note:
            Settings are read from .zwarm/claude.toml.
            Run `zwarm init` to set up the config.
        """
        session_id = str(uuid4())
        working_dir = working_dir or Path.cwd()
        now = datetime.now().isoformat()

        # Load claude config from .zwarm/claude.toml
        claude_config = self._load_claude_config()

        # Get model from config or use default
        effective_model = model or claude_config.get("model", self.default_model)

        # Check if full_danger mode is enabled
        full_danger = claude_config.get("full_danger", False)

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

        # Build command
        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive)
            "--output-format", "stream-json",
            "--verbose",  # Required for stream-json
            "--model", effective_model,
        ]

        # Add working directory access
        if working_dir != Path.cwd():
            cmd.extend(["--add-dir", str(working_dir.absolute())])

        # Full danger mode bypasses all permission checks
        if full_danger:
            cmd.append("--dangerously-skip-permissions")

        # Add the task as the prompt
        cmd.append(task)

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

        Claude Code supports --continue to continue a session, but for
        simplicity we use the same context-injection pattern as Codex.

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

        # Build command
        claude_config = self._load_claude_config()
        full_danger = claude_config.get("full_danger", False)

        cmd = [
            "claude",
            "-p",
            "--output-format", "stream-json",
            "--verbose",
            "--model", session.model,
        ]

        if session.working_dir != Path.cwd():
            cmd.extend(["--add-dir", str(session.working_dir.absolute())])

        if full_danger:
            cmd.append("--dangerously-skip-permissions")

        cmd.append(augmented_task)

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
    # Output parsing (Claude-specific stream-json format)
    # =========================================================================

    def _is_output_complete(self, session_id: str, turn: int) -> bool:
        """
        Check if output file indicates the task completed.

        Looks for {"type":"result",...} in the stream-json output.
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
                    # Claude uses "result" for completion
                    if event_type == "result":
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
        Parse stream-json output from claude -p.

        Claude's stream-json format:
        - {"type":"system","subtype":"init",...}
        - {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
        - {"type":"user","message":{"content":[{"type":"tool_result",...}]}}
        - {"type":"result","usage":{...},...}

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

            if event_type == "assistant":
                # Assistant message with content array
                msg = event.get("message", {})
                content_blocks = msg.get("content", [])

                for block in content_blocks:
                    block_type = block.get("type", "")

                    if block_type == "text":
                        text = block.get("text", "")
                        if text:
                            messages.append(
                                SessionMessage(
                                    role="assistant",
                                    content=text,
                                    timestamp=datetime.now().isoformat(),
                                )
                            )

                    elif block_type == "tool_use":
                        # Track tool calls
                        tool_name = block.get("name", "unknown")
                        messages.append(
                            SessionMessage(
                                role="tool",
                                content=f"[Calling: {tool_name}]",
                                metadata={"function": tool_name, "tool_use_id": block.get("id")},
                            )
                        )

            elif event_type == "user":
                # Tool results
                msg = event.get("message", {})
                content_blocks = msg.get("content", [])

                for block in content_blocks:
                    if block.get("type") == "tool_result":
                        tool_content = block.get("content", "")
                        is_error = block.get("is_error", False)
                        if tool_content and len(str(tool_content)) < 500:
                            prefix = "[Error]" if is_error else "[Output]"
                            messages.append(
                                SessionMessage(
                                    role="tool",
                                    content=f"{prefix}: {str(tool_content)[:500]}",
                                )
                            )

            elif event_type == "result":
                # Final result with usage info
                result_usage = event.get("usage", {})

                # Map Claude's usage fields to our standard format
                usage["input_tokens"] = result_usage.get("input_tokens", 0)
                usage["output_tokens"] = result_usage.get("output_tokens", 0)
                usage["cache_read_input_tokens"] = result_usage.get("cache_read_input_tokens", 0)
                usage["cache_creation_input_tokens"] = result_usage.get("cache_creation_input_tokens", 0)
                usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]

                # Check for errors
                if event.get("is_error"):
                    error = event.get("result", "Unknown error")
                elif event.get("subtype") == "error":
                    error = event.get("result", "Unknown error")

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
        """
        if full:
            max_output_len = 999999

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

                if event_type == "assistant":
                    msg = event.get("message", {})
                    content_blocks = msg.get("content", [])

                    for block in content_blocks:
                        block_type = block.get("type", "")
                        step_num += 1

                        if block_type == "text":
                            text = block.get("text", "")
                            summary_len = max_output_len if full else 200
                            trajectory.append({
                                "turn": turn,
                                "step": step_num,
                                "type": "message",
                                "summary": text[:summary_len] + ("..." if len(text) > summary_len else ""),
                                "full_text": text if full else None,
                                "full_length": len(text),
                            })

                        elif block_type == "tool_use":
                            tool_name = block.get("name", "unknown")
                            args = block.get("input", {})
                            args_str = str(args)
                            args_len = max_output_len if full else 100
                            trajectory.append({
                                "turn": turn,
                                "step": step_num,
                                "type": "tool_call",
                                "tool": tool_name,
                                "args_preview": args_str[:args_len] + ("..." if len(args_str) > args_len else ""),
                                "full_args": args if full else None,
                            })

                elif event_type == "user":
                    # Tool results
                    msg = event.get("message", {})
                    content_blocks = msg.get("content", [])

                    for block in content_blocks:
                        if block.get("type") == "tool_result":
                            step_num += 1
                            output = str(block.get("content", ""))
                            output_preview = output[:max_output_len]
                            if len(output) > max_output_len:
                                output_preview += "..."
                            trajectory.append({
                                "turn": turn,
                                "step": step_num,
                                "type": "tool_output",
                                "output": output_preview,
                                "is_error": block.get("is_error", False),
                            })

        return trajectory
