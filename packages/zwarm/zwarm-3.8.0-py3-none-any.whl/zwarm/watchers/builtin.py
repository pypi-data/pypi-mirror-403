"""
Built-in watchers for common trajectory alignment needs.
"""

from __future__ import annotations

import re
from typing import Any

from wbal.helper import TOOL_CALL_TYPE, TOOL_RESULT_TYPE
from zwarm.watchers.base import Watcher, WatcherContext, WatcherResult, WatcherAction
from zwarm.watchers.registry import register_watcher


def _get_field(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            text = _content_to_text(part)
            if text:
                parts.append(text)
        return "\n".join(parts)
    if isinstance(content, dict):
        text = content.get("text") or content.get("content") or content.get("refusal")
        return str(text) if text is not None else ""
    text = getattr(content, "text", None)
    if text is None:
        text = getattr(content, "refusal", None)
    return str(text) if text is not None else ""


def _normalize_tool_call(tool_call: Any) -> dict[str, Any]:
    if isinstance(tool_call, dict):
        if isinstance(tool_call.get("function"), dict):
            return tool_call
        name = tool_call.get("name", "")
        arguments = tool_call.get("arguments", "")
        call_id = tool_call.get("call_id")
    else:
        name = getattr(tool_call, "name", "")
        arguments = getattr(tool_call, "arguments", "")
        call_id = getattr(tool_call, "call_id", None)

    normalized = {
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }
    if call_id:
        normalized["call_id"] = call_id
    return normalized


def _normalize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in messages:
        item_type = _get_field(item, "type")
        role = _get_field(item, "role")
        content = ""
        tool_calls: list[dict[str, Any]] = []

        if item_type in (TOOL_CALL_TYPE, "function_call"):
            tool_calls = [_normalize_tool_call(item)]
            role = role or "assistant"
        else:
            raw_tool_calls = _get_field(item, "tool_calls") or []
            if raw_tool_calls and not isinstance(raw_tool_calls, list):
                raw_tool_calls = [raw_tool_calls]
            if raw_tool_calls:
                tool_calls = [
                    _normalize_tool_call(tc) for tc in raw_tool_calls
                ]

            if role or item_type == "message" or item_type is None:
                content = _content_to_text(_get_field(item, "content"))

            if item_type == TOOL_RESULT_TYPE and not content:
                content = _content_to_text(_get_field(item, "output"))
                role = role or "tool"

        if not role and not content and not tool_calls:
            continue

        normalized.append(
            {
                "role": role,
                "content": content or "",
                "tool_calls": tool_calls,
            }
        )
    return normalized


@register_watcher("progress")
class ProgressWatcher(Watcher):
    """
    Watches for lack of progress.

    Detects when the agent appears stuck:
    - Repeating same tool calls
    - Not making session progress
    - Spinning without completing tasks
    """

    name = "progress"
    description = "Detects when agent is stuck or spinning"

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        messages = _normalize_messages(ctx.messages)
        config = self.config
        max_same_calls = config.get("max_same_calls", 3)
        min_progress_steps = config.get("min_progress_steps", 5)

        # Check for repeated tool calls
        if len(messages) >= max_same_calls * 2:
            recent_assistant = [
                m for m in messages[-max_same_calls * 2 :]
                if m.get("role") == "assistant"
            ]
            if len(recent_assistant) >= max_same_calls:
                # Check if tool calls are repeating
                tool_calls = []
                for msg in recent_assistant:
                    if "tool_calls" in msg:
                        for tc in msg["tool_calls"]:
                            tool_calls.append(
                                f"{tc.get('function', {}).get('name', '')}:{tc.get('function', {}).get('arguments', '')}"
                            )

                if len(tool_calls) >= max_same_calls:
                    # Check for repetition
                    if len(set(tool_calls[-max_same_calls:])) == 1:
                        return WatcherResult.nudge(
                            guidance=(
                                "You appear to be repeating the same action. "
                                "Consider a different approach or ask for clarification."
                            ),
                            reason=f"Repeated tool call: {tool_calls[-1][:100]}",
                        )

        # Check for no session completions in a while
        if ctx.step >= min_progress_steps:
            completed = [
                e for e in ctx.events
                if e.get("kind") == "session_completed"
            ]
            started = [
                e for e in ctx.events
                if e.get("kind") == "session_started"
            ]
            if len(started) > 0 and len(completed) == 0:
                return WatcherResult.nudge(
                    guidance=(
                        "Several sessions have been started but none completed. "
                        "Focus on completing current sessions before starting new ones."
                    ),
                    reason="No session completions",
                )

        return WatcherResult.ok()


@register_watcher("budget")
class BudgetWatcher(Watcher):
    """
    Watches resource budget (steps, sessions).

    Warns when approaching limits.
    """

    name = "budget"
    description = "Monitors resource usage against limits"

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        config = self.config
        warn_at_percent = config.get("warn_at_percent", 80)
        max_sessions = config.get("max_sessions", 10)

        # Check step budget
        if ctx.max_steps > 0:
            percent_used = (ctx.step / ctx.max_steps) * 100
            if percent_used >= warn_at_percent:
                remaining = ctx.max_steps - ctx.step
                return WatcherResult.nudge(
                    guidance=(
                        f"You have {remaining} steps remaining out of {ctx.max_steps}. "
                        "Prioritize completing the most important parts of the task."
                    ),
                    reason=f"Step budget {percent_used:.0f}% used",
                )

        # Check session count (only count active sessions, not completed/failed)
        active_sessions = [
            s for s in ctx.sessions
            if s.get("status") == "active"
        ]
        if len(active_sessions) >= max_sessions:
            return WatcherResult.nudge(
                guidance=(
                    f"You have {len(active_sessions)} active sessions. "
                    "Consider completing or closing existing sessions before starting new ones."
                ),
                reason=f"Active session limit reached ({len(active_sessions)}/{max_sessions})",
            )

        return WatcherResult.ok()


@register_watcher("scope")
class ScopeWatcher(Watcher):
    """
    Watches for scope creep.

    Ensures the agent stays focused on the original task.
    """

    name = "scope"
    description = "Detects scope creep and keeps agent on task"

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        config = self.config
        focus_keywords = config.get("focus_keywords", [])
        avoid_keywords = config.get("avoid_keywords", [])
        max_tangent_steps = config.get("max_tangent_steps", 3)

        # Check last few messages for avoid keywords
        if avoid_keywords:
            messages = _normalize_messages(ctx.messages)
            recent_content = " ".join(
                m.get("content", "") or ""
                for m in messages[-max_tangent_steps * 2:]
            ).lower()

            for keyword in avoid_keywords:
                if keyword.lower() in recent_content:
                    return WatcherResult.nudge(
                        guidance=(
                            f"The task involves '{keyword}' which may be out of scope. "
                            f"Remember the original task: {ctx.task[:200]}"
                        ),
                        reason=f"Detected avoid keyword: {keyword}",
                    )

        return WatcherResult.ok()


@register_watcher("pattern")
class PatternWatcher(Watcher):
    """
    Watches for specific patterns in output.

    Configurable regex patterns that trigger nudges/alerts.
    """

    name = "pattern"
    description = "Watches for configurable patterns in output"

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        messages = _normalize_messages(ctx.messages)
        config = self.config
        patterns = config.get("patterns", [])

        # Each pattern is: {"regex": "...", "action": "nudge|pause|abort", "message": "..."}
        for pattern_config in patterns:
            regex = pattern_config.get("regex")
            if not regex:
                continue

            try:
                compiled = re.compile(regex, re.IGNORECASE)
            except re.error:
                continue

            # Check recent messages
            for msg in messages[-10:]:
                content = msg.get("content", "") or ""
                if compiled.search(content):
                    action = pattern_config.get("action", "nudge")
                    message = pattern_config.get("message", f"Pattern matched: {regex}")

                    if action == "abort":
                        return WatcherResult.abort(message)
                    elif action == "pause":
                        return WatcherResult.pause(message)
                    else:
                        return WatcherResult.nudge(guidance=message, reason=f"Pattern: {regex}")

        return WatcherResult.ok()


@register_watcher("delegation")
class DelegationWatcher(Watcher):
    """
    Watches for the orchestrator trying to write code directly.

    The orchestrator should DELEGATE coding tasks to executors (Codex, Claude Code),
    not write code itself via bash heredocs, cat, echo, etc.

    Detects patterns like:
    - cat >> file << 'EOF' (heredocs)
    - echo "code" >> file
    - printf "..." > file.py
    - tee file.py << EOF
    """

    name = "delegation"
    description = "Ensures orchestrator delegates coding instead of writing directly"

    # Patterns that indicate direct code writing
    DIRECT_WRITE_PATTERNS = [
        # Heredocs
        r"cat\s+>+\s*\S+.*<<",
        r"tee\s+\S+.*<<",
        # Echo/printf to code files
        r"echo\s+['\"].*['\"]\s*>+\s*\S+\.(py|js|ts|go|rs|java|cpp|c|rb|sh)",
        r"printf\s+['\"].*['\"]\s*>+\s*\S+\.(py|js|ts|go|rs|java|cpp|c|rb|sh)",
        # Sed/awk inline editing (complex patterns suggest code modification)
        r"sed\s+-i.*['\"].*def\s+|class\s+|function\s+|import\s+",
    ]

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        messages = _normalize_messages(ctx.messages)
        config = self.config
        strict = config.get("strict", True)  # If True, nudge. If False, just warn.

        # Check recent messages for bash tool calls
        for msg in messages[-10:]:
            if msg.get("role") != "assistant":
                continue

            # Check tool calls
            tool_calls = msg.get("tool_calls", [])
            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")
                args = func.get("arguments", "")

                # Only check bash calls
                if name != "bash":
                    continue

                # Parse arguments (could be JSON string)
                if isinstance(args, str):
                    try:
                        import json
                        args_dict = json.loads(args)
                        command = args_dict.get("command", "")
                    except (json.JSONDecodeError, AttributeError):
                        command = args
                else:
                    command = args.get("command", "") if isinstance(args, dict) else ""

                # Check for direct write patterns
                for pattern in self.DIRECT_WRITE_PATTERNS:
                    if re.search(pattern, command, re.IGNORECASE):
                        guidance = (
                            "You are trying to write code directly via bash. "
                            "As the orchestrator, you should DELEGATE coding tasks to executors "
                            "using delegate(). Use bash only for verification commands "
                            "(git status, running tests, etc.), not for writing code."
                        )
                        if strict:
                            return WatcherResult.nudge(
                                guidance=guidance,
                                reason=f"Direct code write detected: {command[:100]}...",
                            )
                        else:
                            # Just log, don't nudge
                            return WatcherResult.ok()

        return WatcherResult.ok()


@register_watcher("quality")
class QualityWatcher(Watcher):
    """
    Watches for quality issues.

    Detects:
    - Missing tests when code is written
    - Large file changes
    - Missing error handling
    """

    name = "quality"
    description = "Watches for quality issues in code changes"

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        config = self.config
        require_tests = config.get("require_tests", True)
        max_files_changed = config.get("max_files_changed", 10)

        # Check for large changes
        if len(ctx.files_changed) > max_files_changed:
            return WatcherResult.nudge(
                guidance=(
                    f"You've modified {len(ctx.files_changed)} files. "
                    "Consider breaking this into smaller, focused changes."
                ),
                reason=f"Large change: {len(ctx.files_changed)} files",
            )

        # Check for tests if code files are changed
        if require_tests and ctx.files_changed:
            code_files = [
                f for f in ctx.files_changed
                if f.endswith((".py", ".js", ".ts", ".go", ".rs"))
                and not f.startswith("test_")
                and not f.endswith("_test.py")
                and "/test" not in f
            ]
            test_files = [
                f for f in ctx.files_changed
                if "test" in f.lower()
            ]

            if code_files and not test_files:
                return WatcherResult.nudge(
                    guidance=(
                        "Code files were modified but no test files were added or updated. "
                        "Consider adding tests for the changes."
                    ),
                    reason="Code without tests",
                )

        return WatcherResult.ok()


@register_watcher("delegation_reminder")
class DelegationReminderWatcher(Watcher):
    """
    Reminds the orchestrator to delegate work instead of doing it directly.

    Counts consecutive non-delegation tool calls (bash commands that aren't
    delegation-related). When the count exceeds a threshold, nudges the
    orchestrator to consider delegating to executors instead.

    This is a softer reminder than the DelegationWatcher - it doesn't detect
    specific code-writing patterns, just notices when the orchestrator seems
    to be doing a lot of direct work that could potentially be delegated.
    """

    name = "delegation_reminder"
    description = "Reminds orchestrator to delegate after many direct tool calls"

    # Tools that count as delegation-related (don't count against threshold)
    DELEGATION_TOOLS = {
        "delegate",
        "converse",
        "check_session",
        "end_session",
        "list_sessions",
        "chat",  # Talking to user is not direct work
    }

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        messages = _normalize_messages(ctx.messages)
        config = self.config
        threshold = config.get("threshold", 10)  # Max consecutive non-delegation calls
        lookback = config.get("lookback", 30)  # How many messages to check

        # Count consecutive non-delegation tool calls from the end
        consecutive_non_delegation = 0

        # Look through recent messages in reverse order
        for msg in reversed(messages[-lookback:]):
            if msg.get("role") != "assistant":
                continue

            tool_calls = msg.get("tool_calls", [])
            if not tool_calls:
                # Text-only response doesn't reset counter, but doesn't add to it
                continue

            # Check each tool call in this message
            has_delegation = False
            has_non_delegation = False

            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")

                if name in self.DELEGATION_TOOLS:
                    has_delegation = True
                elif name:  # Any other tool call
                    has_non_delegation = True

            if has_delegation:
                # Found a delegation tool - stop counting
                break
            elif has_non_delegation:
                # Add to consecutive count (one per message, not per tool call)
                consecutive_non_delegation += 1

        # Check if threshold exceeded
        if consecutive_non_delegation >= threshold:
            return WatcherResult.nudge(
                guidance=(
                    f"You've made {consecutive_non_delegation} consecutive direct tool calls "
                    "without delegating to an executor. Remember: as the orchestrator, your role "
                    "is to delegate coding work to executors, not do it yourself via bash. "
                    "Consider whether the work you're doing could be delegated to an executor "
                    "using delegate(). Executors can write code, run tests, and handle complex "
                    "file operations more effectively than direct bash commands."
                ),
                reason=f"Consecutive non-delegation calls: {consecutive_non_delegation}",
            )

        return WatcherResult.ok()
