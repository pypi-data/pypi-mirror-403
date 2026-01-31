"""
Orchestrator: The agent that coordinates multiple executor agents.

The orchestrator:
- Plans and breaks down complex tasks
- Delegates work to executor agents (codex, claude-code, etc.)
- Supervises progress and provides clarification
- Verifies work before marking complete

It does NOT write code directly - that's the executor's job.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import weave
from pydantic import Field, PrivateAttr
from wbal.agents.yaml_agent import YamlAgent
from wbal.helper import TOOL_CALL_TYPE, format_openai_tool_response
from wbal.lm import LM as wbalLMGeneric
from wbal.lm import GPT5LargeVerbose

from zwarm.core.compact import compact_messages, should_compact
from zwarm.core.config import ZwarmConfig, load_config
from zwarm.core.environment import OrchestratorEnv
from zwarm.core.models import ConversationSession
from zwarm.core.state import StateManager
from zwarm.prompts import get_orchestrator_prompt
from zwarm.watchers import (
    WatcherAction,
    WatcherContext,
    WatcherManager,
    build_watcher_manager,
)


class Orchestrator(YamlAgent):
    """
    Multi-agent orchestrator built on WBAL's YamlAgent.

    Extends YamlAgent with:
    - Delegation tools (delegate, converse, check_session, end_session)
    - Session tracking
    - State persistence
    - Watcher integration
    - Weave integration
    """

    # LM definition override:
    lm: wbalLMGeneric = Field(default_factory=GPT5LargeVerbose)

    # Configuration
    config: ZwarmConfig = Field(default_factory=ZwarmConfig)
    working_dir: Path = Field(default_factory=Path.cwd)

    # Instance identification (for multi-orchestrator isolation)
    instance_id: str | None = Field(default=None)
    instance_name: str | None = Field(default=None)

    # Load tools from modules (delegation + bash for verification)
    agent_tool_modules: list[str] = Field(
        default=[
            "zwarm.tools.delegation",
            "wbal.tools.bash",
        ]
    )

    # State management
    _state: StateManager = PrivateAttr()
    _sessions: dict[str, ConversationSession] = PrivateAttr(default_factory=dict)
    _watcher_manager: WatcherManager | None = PrivateAttr(default=None)
    _resumed: bool = PrivateAttr(default=False)
    _total_tokens: int = PrivateAttr(default=0)  # Cumulative orchestrator tokens
    _executor_usage: dict[str, int] = PrivateAttr(
        default_factory=lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
    )
    # Callback for step progress (used by CLI to print tool calls)
    _step_callback: Callable[[int, list[tuple[dict[str, Any], Any]]], None] | None = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        """Initialize state after model creation."""
        super().model_post_init(__context)

        # Initialize state manager with instance isolation
        base_state_dir = self.working_dir / self.config.state_dir
        self._state = StateManager(
            state_dir=base_state_dir,
            instance_id=self.instance_id,
        )
        self._state.init()
        self._state.load()

        # Register instance if using instance isolation
        if self.instance_id:
            from zwarm.core.state import register_instance

            register_instance(
                instance_id=self.instance_id,
                name=self.instance_name,
                task=None,  # Will be updated when task is set
                base_dir=base_state_dir,
            )

        # Load existing sessions
        for session in self._state.list_sessions():
            self._sessions[session.id] = session

        # Initialize Weave if configured
        if self.config.weave.enabled and self.config.weave.project:
            weave.init(self.config.weave.project)

        # Initialize watchers if configured
        if self.config.watchers.enabled:
            self._watcher_manager = build_watcher_manager(
                {
                    "watchers": [
                        {"name": w.name, "enabled": w.enabled, "config": w.config}
                        for w in self.config.watchers.watchers
                    ]
                }
            )

        # Initialize CodexSessionManager and link to environment
        # This is the SAME manager used by delegation tools
        from zwarm.sessions import CodexSessionManager
        self._session_manager = CodexSessionManager(self.working_dir / ".zwarm")

        # Link session manager to environment for live session visibility in observe()
        if hasattr(self.env, "set_session_manager"):
            self.env.set_session_manager(self._session_manager)

        # Set budget limits in environment
        if hasattr(self.env, "set_budget"):
            # Extract budget from watcher config if available
            max_sessions = None
            for w in self.config.watchers.watchers:
                if w.name == "budget" and w.config:
                    max_sessions = w.config.get("max_sessions")
                    break
            self.env.set_budget(max_sessions=max_sessions)

    @property
    def state(self) -> StateManager:
        """Access state manager."""
        return self._state

    def get_executor_usage(self) -> dict[str, int]:
        """Get aggregated token usage from executor sessions."""
        return self._executor_usage

    def save_state(self) -> None:
        """Save orchestrator state for resume."""
        self._state.save_orchestrator_messages(self.messages)

    def load_state(self) -> None:
        """Load orchestrator state for resume.

        Only marks as resumed if we actually loaded non-empty messages.
        This prevents the resume message from being injected before the
        system prompt when there's no saved state to resume from.
        """
        loaded_messages = self._state.load_orchestrator_messages()
        if loaded_messages:
            self.messages = self._sanitize_messages_for_resume(loaded_messages)
            self._resumed = True
        # If no messages were saved, don't set _resumed - start fresh

    def _sanitize_messages_for_resume(self, messages: list[dict]) -> list[dict]:
        """
        Sanitize messages loaded from disk for sending back to the API.

        OpenAI's reasoning models include response-only fields (status, encrypted_content)
        in reasoning blocks that can't be sent back as input. We keep the reasoning
        items but strip the response-only fields.

        Response-only fields that must be removed:
        - status: reasoning item status (null, "in_progress", "completed")
        - encrypted_content: encrypted reasoning content
        """
        # Fields that are response-only and must be stripped for input
        RESPONSE_ONLY_FIELDS = {
            "status",
            "encrypted_content",
        }

        def clean_item(item: Any) -> Any:
            """Recursively clean an item, removing response-only fields."""
            if isinstance(item, dict):
                return {
                    k: clean_item(v)
                    for k, v in item.items()
                    if k not in RESPONSE_ONLY_FIELDS
                }
            elif isinstance(item, list):
                return [clean_item(x) for x in item]
            else:
                return item

        return [clean_item(msg) for msg in messages]

    def _maybe_compact(self) -> bool:
        """
        Check if compaction is needed and compact if so.

        Returns True if compaction was performed.
        """
        compact_config = self.config.orchestrator.compaction
        if not compact_config.enabled:
            return False

        # Check if we should compact
        if not should_compact(
            self.messages,
            max_tokens=compact_config.max_tokens,
            threshold_pct=compact_config.threshold_pct,
        ):
            return False

        # Perform compaction
        result = compact_messages(
            self.messages,
            keep_first_n=compact_config.keep_first_n,
            keep_last_n=compact_config.keep_last_n,
            max_tokens=compact_config.max_tokens,
            target_token_pct=compact_config.target_pct,
        )

        if result.was_compacted:
            self.messages = result.messages

            # Log compaction event
            from zwarm.core.models import Event

            self._state.log_event(
                Event(
                    kind="context_compacted",
                    payload={
                        "step": self._step_count,
                        "original_count": result.original_count,
                        "new_count": len(result.messages),
                        "removed_count": result.removed_count,
                    },
                )
            )

            return True

        return False

    def _inject_resume_message(self) -> None:
        """Inject a system message about resumed state."""
        if not self._resumed:
            return

        # Build list of old sessions and INVALIDATE their conversation IDs
        # The MCP server was restarted, so all conversation IDs are now stale
        old_sessions = []
        invalidated_count = 0
        for sid, session in self._sessions.items():
            old_sessions.append(
                f"  - {sid[:8]}... ({session.adapter}, {session.status.value})"
            )
            # Clear stale conversation_id to prevent converse() from trying to use it
            if session.conversation_id:
                session.conversation_id = None
                invalidated_count += 1

        session_info = "\n".join(old_sessions) if old_sessions else "  (none)"

        resume_msg = {
            "role": "user",
            "content": f"""[SYSTEM NOTICE] You have been resumed from a previous session.

CRITICAL: Your previous executor sessions are NO LONGER USABLE. The MCP server was restarted, so all conversation state was lost. {invalidated_count} conversation ID(s) have been invalidated.

Previous sessions (conversation IDs cleared):
{session_info}

You MUST start NEW sessions with delegate() to continue any work. The converse() tool will fail on these old sessions because they have no active conversation.

Review what was accomplished in the previous session and delegate new tasks as needed.""",
        }

        self.messages.append(resume_msg)
        self._resumed = False  # Only inject once

    def perceive(self) -> None:
        """
        Override perceive to properly inject system prompt and environment observation.

        Fixes over base YamlAgent:
        1. Always injects system prompt on step 0, even if messages isn't empty
           (pilot mode adds user messages before perceive runs)
        2. Only adds "Task: " message if there's actually a task (skips for pilot mode)
        3. Refreshes environment observation each step

        Note: self.messages can contain both dict messages AND OpenAI response objects
        (ResponseReasoningItem, ResponseMessageItem, etc.), so we must check isinstance().
        """
        from datetime import datetime

        def _is_dict_msg(msg, role: str | None = None, content_check: str | None = None) -> bool:
            """Check if msg is a dict with optional role/content matching."""
            if not isinstance(msg, dict):
                return False
            if role and msg.get("role") != role:
                return False
            if content_check and content_check not in msg.get("content", ""):
                return False
            return True

        # On step 0, ensure system prompt is present
        if self._step_count == 0:
            # Check if system prompt already exists (avoid duplicates on resume)
            has_system_prompt = False
            if self.system_prompt:
                prompt_snippet = self.system_prompt[:100]
                has_system_prompt = any(
                    _is_dict_msg(msg, role="system", content_check=prompt_snippet)
                    for msg in self.messages
                )

            if not has_system_prompt and self.system_prompt:
                today = datetime.now().strftime("%Y-%m-%d")
                # Insert at beginning to ensure it's first
                self.messages.insert(0, {
                    "role": "system",
                    "content": f"{self.system_prompt}\n\nToday's date: {today}",
                })

            # Add task message ONLY if we have a task (skip for pilot mode where task is empty)
            task = getattr(self.env, "task", "")
            if task:
                # Check if Task message already exists (avoid duplicates)
                has_task_msg = any(
                    isinstance(msg, dict)
                    and msg.get("role") == "user"
                    and msg.get("content", "").startswith("Task: ")
                    for msg in self.messages
                )
                if not has_task_msg:
                    self.messages.append({"role": "user", "content": f"Task: {task}"})

        # Update environment observation
        env_obs = (self.env.observe() or "").strip()
        if not env_obs:
            return

        # Find and update existing env observation, or append new one
        # Look for a system message containing our markers
        # Note: pilot mode uses "## Active Sessions", full mode uses "## Progress"
        env_markers = ["## Progress", "## Active Sessions", "Working dir:"]

        for i, msg in enumerate(self.messages):
            if not isinstance(msg, dict):
                continue
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if any(marker in content for marker in env_markers):
                    # Update in place
                    self.messages[i]["content"] = env_obs
                    return

        # Not found - append as new system message
        self.messages.append({"role": "system", "content": env_obs})

    @weave.op()
    def _run_watchers(self) -> WatcherAction:
        """Run watchers and return the action to take."""
        if not self._watcher_manager:
            return WatcherAction.CONTINUE

        # Build watcher context
        task = getattr(self.env, "task", "") if self.env else ""
        events = [e.to_dict() for e in self.state.get_events(limit=200)]
        ctx = WatcherContext(
            task=task,
            step=self._step_count,
            max_steps=self.maxSteps,
            messages=self.messages,
            sessions=[s.to_dict() for s in self._sessions.values()],
            events=events,
            working_dir=str(self.working_dir.absolute()) if self.working_dir else None,
            metadata={
                "config": self.config.to_dict()
                if hasattr(self.config, "to_dict")
                else {},
            },
        )

        # Run watchers synchronously (they're async internally)
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're in an async context, create a task
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run, self._watcher_manager.observe(ctx)
                ).result()
        else:
            result = asyncio.run(self._watcher_manager.observe(ctx))

        # Log watcher execution to events
        from zwarm.core.models import Event

        watcher_names = [w.name for w in self.config.watchers.watchers if w.enabled]
        self.state.log_event(
            Event(
                kind="watchers_run",
                payload={
                    "step": self._step_count,
                    "watchers": watcher_names,
                    "action": result.action.value,
                    "triggered_by": result.metadata.get("triggered_by"),
                    "reason": result.metadata.get("reason"),
                },
            )
        )

        # Handle watcher result
        if result.action == WatcherAction.NUDGE and result.guidance:
            # Inject guidance as a message with configurable role
            message_role = self.config.watchers.message_role
            # Validate role (default to user if invalid)
            if message_role not in ("user", "assistant", "system"):
                message_role = "user"

            self.messages.append(
                {
                    "role": message_role,
                    "content": f"[WATCHER: {result.metadata.get('triggered_by', 'unknown')}] {result.guidance}",
                }
            )

        return result.action

    def do(self) -> list[tuple[dict[str, Any], Any]]:
        """
        Execute tool calls from the LLM response.

        Overrides base do() to capture and return tool calls with results
        for Weave tracing visibility.

        Returns:
            List of (tool_call_info, result) tuples
        """
        if self._last_response is None:
            return []

        output = getattr(self._last_response, "output", None)
        if output is None:
            return []

        # Extract tool calls
        tool_calls = [
            item for item in output if getattr(item, "type", None) == TOOL_CALL_TYPE
        ]

        # If no tool calls, handle text output
        if not tool_calls:
            output_text = getattr(self._last_response, "output_text", "")
            if output_text and hasattr(self.env, "output_handler"):
                self.env.output_handler(output_text)
            return []

        # Execute each tool call and collect results
        tool_results: list[tuple[dict[str, Any], Any]] = []

        for tc in tool_calls:
            tc_name = getattr(tc, "name", "")
            tc_args_raw = getattr(tc, "arguments", "{}")
            tc_id = getattr(tc, "call_id", "")

            # Parse arguments
            if isinstance(tc_args_raw, str):
                try:
                    tc_args = json.loads(tc_args_raw)
                except json.JSONDecodeError:
                    tc_args = {}
            else:
                tc_args = tc_args_raw or {}

            # Execute tool
            if tc_name in self._tool_callables:
                try:
                    tc_output = self._tool_callables[tc_name](**tc_args)
                except Exception as e:
                    tc_output = f"Error executing {tc_name}: {e}"
            else:
                tc_output = f"Unknown tool: {tc_name}"

            # Collect tool call info and result
            tool_call_info = {
                "name": tc_name,
                "args": tc_args,
                "call_id": tc_id,
            }
            tool_results.append((tool_call_info, tc_output))

            # Format and append result to messages
            result = format_openai_tool_response(tc_output, tc_id)
            self.messages.append(result)

        return tool_results

    @weave.op()
    def step(self) -> list[tuple[dict[str, Any], Any]]:
        """
        Execute one perceive-invoke-do cycle.

        Overrides base step() to return tool calls with results
        for Weave tracing visibility.

        Returns:
            List of (tool_call_info, result) tuples from this step.
            Each tuple contains:
            - tool_call_info: {"name": str, "args": dict, "call_id": str}
            - result: The tool output (any type)
        """
        # Check for context compaction before perceive
        # This prevents context overflow on long-running tasks
        self._maybe_compact()

        # Update environment with current progress before perceive
        if hasattr(self.env, "update_progress"):
            executor_usage = self.get_executor_usage()
            self.env.update_progress(
                step_count=self._step_count,
                max_steps=self.maxSteps,
                total_tokens=self._total_tokens,
                executor_tokens=executor_usage.get("total_tokens", 0),
            )

        self.perceive()
        self.invoke()

        # Track cumulative token usage from the API response
        if self._last_response and hasattr(self._last_response, "usage"):
            usage = self._last_response.usage
            if usage:
                self._total_tokens += getattr(usage, "total_tokens", 0)

        tool_results = self.do()
        self._step_count += 1
        return tool_results

    @weave.op()
    def run(
        self, task: str | None = None, max_steps: int | None = None
    ) -> dict[str, Any]:
        """
        Run the orchestrator until stop condition is met.

        Overrides base run() to integrate watchers.

        Args:
            task: The task string. If not provided, uses env.task
            max_steps: Override maxSteps for this run.

        Returns:
            Dict with run results
        """
        # Set task from argument or environment
        if task is not None:
            self.env.task = task

        # Override max_steps if provided
        if max_steps is not None:
            self.maxSteps = max_steps

        # Reset counters
        self._step_count = 0
        self._total_tokens = 0

        # Inject resume message if we were resumed
        self._inject_resume_message()

        for _ in range(self.maxSteps):
            # Run watchers before each step
            watcher_action = self._run_watchers()

            if watcher_action == WatcherAction.ABORT:
                return {
                    "steps": self._step_count,
                    "task": self.env.task,
                    "stopped_by": "watcher_abort",
                }
            elif watcher_action == WatcherAction.PAUSE:
                # For now, treat pause as stop (could add human-in-loop later)
                return {
                    "steps": self._step_count,
                    "task": self.env.task,
                    "stopped_by": "watcher_pause",
                }
            # NUDGE and CONTINUE just continue

            tool_results = self.step()

            # Call step callback if registered (for CLI progress display)
            if self._step_callback:
                self._step_callback(self._step_count, tool_results)

            if self.stopCondition:
                break

        return {
            "steps": self._step_count,
            "task": self.env.task,
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass  # Session cleanup handled by CodexSessionManager


def build_orchestrator(
    config_path: Path | None = None,
    task: str | None = None,
    working_dir: Path | None = None,
    overrides: list[str] | None = None,
    resume: bool = False,
    output_handler: Callable[[str], None] | None = None,
    instance_id: str | None = None,
    instance_name: str | None = None,
) -> Orchestrator:
    """
    Build an orchestrator from configuration.

    Args:
        config_path: Path to YAML config file
        task: The task to accomplish
        working_dir: Working directory (default: cwd)
        overrides: CLI overrides (--set key=value)
        resume: Whether to resume from previous state
        output_handler: Function to handle orchestrator output
        instance_id: Unique ID for this instance (enables multi-orchestrator isolation)
        instance_name: Human-readable name for this instance

    Returns:
        Configured Orchestrator instance
    """
    from uuid import uuid4

    # Resolve working directory first (needed for config loading)
    working_dir = working_dir or Path.cwd()

    # Load configuration from working_dir (not cwd!)
    # This ensures config.toml and .env are loaded from the project being worked on
    config = load_config(
        config_path=config_path,
        overrides=overrides,
        working_dir=working_dir,
    )

    # Generate instance ID if not provided (enables isolation by default for new runs)
    # For resume, instance_id should be provided explicitly
    if instance_id is None and not resume:
        instance_id = str(uuid4())

    # Build system prompt
    system_prompt = _build_system_prompt(config, working_dir)

    # Create lean orchestrator environment
    env = OrchestratorEnv(
        task=task or "",
        working_dir=working_dir,
    )

    # Set up output handler
    if output_handler:
        env.output_handler = output_handler

    # Create orchestrator
    orchestrator = Orchestrator(
        config=config,
        working_dir=working_dir,
        system_prompt=system_prompt,
        maxSteps=config.orchestrator.max_steps,
        env=env,
        instance_id=instance_id,
        instance_name=instance_name,
    )

    # Resume if requested
    if resume:
        orchestrator.load_state()

    return orchestrator


def _build_system_prompt(config: ZwarmConfig, working_dir: Path | None = None) -> str:
    """Build the orchestrator system prompt."""
    return get_orchestrator_prompt(
        working_dir=str(working_dir) if working_dir else None
    )
