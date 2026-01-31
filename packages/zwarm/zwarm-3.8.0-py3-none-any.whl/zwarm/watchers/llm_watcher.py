"""
LLM-based watcher for nuanced trajectory analysis.

Unlike rule-based watchers, this watcher uses a language model to assess
the orchestrator's trajectory and provide context-aware guidance.

The watcher compresses the full message history into a compact trajectory
representation (similar to what Codex shows in its UI) to minimize token
usage while preserving the "shape" of the agent's behavior.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from zwarm.watchers.base import Watcher, WatcherContext, WatcherResult
from zwarm.watchers.registry import register_watcher

logger = logging.getLogger(__name__)


def _get_field(item: Any, name: str, default: Any = None) -> Any:
    """Get field from dict or object."""
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _extract_tool_call_summary(tc: Any) -> str:
    """Extract a compact summary of a tool call."""
    if isinstance(tc, dict):
        func = tc.get("function", tc)
        name = func.get("name", tc.get("name", "?"))
        args = func.get("arguments", tc.get("arguments", ""))
    else:
        name = getattr(tc, "name", "?")
        args = getattr(tc, "arguments", "")

    # Parse args if JSON string
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except (json.JSONDecodeError, TypeError):
            pass

    # Create compact arg summary
    if isinstance(args, dict):
        # Show key args based on tool type
        if name == "delegate":
            task = args.get("task", "")[:50]
            mode = args.get("mode", "sync")
            return f"delegate({mode}): {task}..."
        elif name == "converse":
            msg = args.get("message", "")[:40]
            return f"converse: {msg}..."
        elif name == "bash":
            cmd = args.get("command", "")[:60]
            return f"$ {cmd}"
        elif name in ("check_session", "peek_session", "end_session"):
            sid = args.get("session_id", "")[:8]
            return f"{name}({sid})"
        elif name == "list_sessions":
            return "list_sessions()"
        else:
            # Generic: show first arg
            first_val = next(iter(args.values()), "") if args else ""
            if isinstance(first_val, str) and len(first_val) > 30:
                first_val = first_val[:30] + "..."
            return f"{name}({first_val})"
    else:
        return f"{name}({str(args)[:30]})"


def compress_trajectory(messages: list[dict[str, Any]], max_steps: int = 50) -> str:
    """
    Compress full message history into a compact trajectory representation.

    Output format (similar to Codex UI):
    ```
    [1] thinking: "preparing to inspect the codebase"
        → delegate(sync): Add authentication to...
    [2] thinking: "checking session status"
        → check_session(abc123)
    [3] thinking: "session completed, verifying"
        → $ pytest tests/
    ```

    Args:
        messages: Full message history from orchestrator
        max_steps: Maximum steps to include (most recent)

    Returns:
        Compact trajectory string
    """
    steps = []
    step_num = 0

    for msg in messages:
        role = _get_field(msg, "role", "")

        if role == "system":
            continue  # Skip system messages

        if role == "assistant":
            step_num += 1
            content = _get_field(msg, "content", "")
            tool_calls = _get_field(msg, "tool_calls", [])

            # Extract thinking/reasoning summary
            thinking = ""
            if content:
                # Take first line or first 80 chars as "thinking"
                first_line = content.split("\n")[0].strip()
                if len(first_line) > 80:
                    thinking = first_line[:80] + "..."
                else:
                    thinking = first_line

            # Extract tool calls
            actions = []
            if tool_calls:
                for tc in tool_calls[:3]:  # Max 3 tool calls per step
                    actions.append(_extract_tool_call_summary(tc))
                if len(tool_calls) > 3:
                    actions.append(f"... +{len(tool_calls) - 3} more")

            # Format step
            step_lines = [f"[{step_num}]"]
            if thinking:
                step_lines[0] += f' thinking: "{thinking}"'
            for action in actions:
                step_lines.append(f"    → {action}")

            steps.append("\n".join(step_lines))

        elif role == "tool":
            # Tool results - just note if error
            content = str(_get_field(msg, "content", ""))
            if "error" in content.lower() or "failed" in content.lower():
                steps.append(f"    ⚠ tool returned error")

        elif role == "user" and step_num > 0:
            # User message mid-conversation (watcher nudge, etc.)
            content = _get_field(msg, "content", "")
            if content and "[WATCHER" in content:
                steps.append(f"    📍 watcher nudge")
            elif content:
                preview = content[:50].replace("\n", " ")
                steps.append(f"    💬 user: {preview}...")

    # Take most recent steps
    if len(steps) > max_steps:
        steps = ["... (earlier steps omitted)"] + steps[-max_steps:]

    return "\n".join(steps)


def _build_watcher_prompt(
    trajectory: str,
    task: str,
    step: int,
    max_steps: int,
    session_summary: str,
) -> str:
    """Build the prompt for the LLM watcher."""
    return f"""You are a trajectory watcher observing an orchestrator agent. Your job is to assess whether the agent is on track and provide guidance if needed.

## Original Task
{task}

## Progress
Step {step}/{max_steps}

## Active Sessions
{session_summary}

## Trajectory (recent steps)
{trajectory}

---

Analyze this trajectory and respond with a JSON object:
{{
  "status": "ok" | "concern" | "problem",
  "assessment": "Brief 1-2 sentence assessment of trajectory health",
  "guidance": "If status is concern/problem, specific actionable guidance. Otherwise null."
}}

Things to watch for:
- Is the agent making progress toward the task?
- Is it spinning or repeating actions?
- Is it going off on tangents unrelated to the task?
- Is it delegating appropriately or trying to do everything directly?
- Are sessions being completed or just started and abandoned?

Be concise. Only flag real issues, not minor inefficiencies."""


@register_watcher("llm")
class LLMWatcher(Watcher):
    """
    LLM-based watcher for nuanced trajectory analysis.

    Uses a language model to assess the orchestrator's trajectory
    and provide context-aware guidance that rule-based watchers can't.

    Config options:
        model: Model to use (default: gpt-4o-mini)
        threshold: How often to run (every N steps, default: 5)
        temperature: LLM temperature (default: 0.3)
    """

    name = "llm"
    description = "LLM-based trajectory analysis for nuanced guidance"

    async def observe(self, ctx: WatcherContext) -> WatcherResult:
        config = self.config
        threshold = config.get("threshold", 5)
        model = config.get("model", "gpt-4o-mini")
        temperature = config.get("temperature", 0.3)

        # Only run every N steps to save costs
        if ctx.step % threshold != 0 or ctx.step == 0:
            return WatcherResult.ok()

        try:
            # Compress trajectory
            trajectory = compress_trajectory(ctx.messages)

            # Build session summary
            active = [s for s in ctx.sessions if s.get("status") == "running"]
            completed = [s for s in ctx.sessions if s.get("status") == "completed"]
            failed = [s for s in ctx.sessions if s.get("status") == "failed"]
            session_summary = f"{len(active)} running, {len(completed)} completed, {len(failed)} failed"

            # Build prompt
            prompt = _build_watcher_prompt(
                trajectory=trajectory,
                task=ctx.task,
                step=ctx.step,
                max_steps=ctx.max_steps,
                session_summary=session_summary,
            )

            # Call LLM
            response = await self._call_llm(prompt, model, temperature)

            # Parse response
            result = self._parse_response(response)

            if result["status"] == "ok":
                return WatcherResult.ok()
            elif result["status"] == "concern":
                return WatcherResult.nudge(
                    guidance=result.get("guidance", result["assessment"]),
                    reason=f"LLM assessment: {result['assessment']}",
                    metadata={"llm_response": result},
                )
            else:  # problem
                return WatcherResult.nudge(
                    guidance=result.get("guidance", result["assessment"]),
                    reason=f"LLM detected problem: {result['assessment']}",
                    priority=10,  # Higher priority for problems
                    metadata={"llm_response": result},
                )

        except Exception as e:
            logger.warning(f"LLM watcher failed: {e}")
            return WatcherResult.ok()  # Don't block on watcher failure

    async def _call_llm(self, prompt: str, model: str, temperature: float) -> str:
        """Call the LLM using OpenAI Responses API."""
        import openai

        client = openai.AsyncOpenAI()

        # Use Responses API (consistent with wbal)
        response = await client.responses.create(
            model=model,
            input=[{"role": "user", "content": prompt}],
            temperature=temperature,
            text={"format": {"type": "json_object"}},
        )

        # Extract text from response
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        # Fallback: look through output items
        for item in getattr(response, "output", []):
            if getattr(item, "type", None) == "message":
                for content in getattr(item, "content", []):
                    if getattr(content, "type", None) == "output_text":
                        return getattr(content, "text", "{}")
            # Also check for direct text attribute
            text = getattr(item, "text", None)
            if text:
                return text

        return "{}"

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response JSON."""
        try:
            result = json.loads(response)
            # Validate required fields
            if "status" not in result:
                result["status"] = "ok"
            if "assessment" not in result:
                result["assessment"] = "No assessment provided"
            return result
        except json.JSONDecodeError:
            return {
                "status": "ok",
                "assessment": "Failed to parse LLM response",
            }
