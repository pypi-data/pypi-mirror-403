"""
Pilot: Conversational REPL for the zwarm orchestrator.

A chatty interface where you guide the orchestrator turn-by-turn,
with time travel, checkpoints, and streaming event display.
"""

from __future__ import annotations

import copy
import json
import shlex
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from rich.console import Console

from zwarm.core.checkpoints import CheckpointManager
from zwarm.core.costs import estimate_session_cost, format_cost, get_pricing

console = Console()


class ChoogingSpinner:
    """
    A spinner that displays "Chooching" while waiting, adding an 'o' every second.

    Chooching → Choooching → Chooooching → ...
    """

    def __init__(self, base_word: str = "Chooching"):
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._base = base_word
        # Find where to insert extra 'o's (after "Ch" and before "ching")
        # "Chooching" -> insert after index 2
        self._prefix = "Ch"
        self._suffix = "ching"
        self._min_o = 2  # Start with "oo"

    def _spin(self):
        o_count = self._min_o
        while not self._stop_event.is_set():
            word = f"{self._prefix}{'o' * o_count}{self._suffix}"
            # Write with carriage return to overwrite, dim styling
            sys.stdout.write(f"\r\033[2m{word}\033[0m")
            sys.stdout.flush()
            o_count += 1
            # Wait 1 second, but check for stop every 100ms
            for _ in range(10):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)

    def start(self):
        """Start the spinner in a background thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the spinner and clear the line."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        # Clear the line
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


# Context window sizes for different models (in tokens)
# These are for the ORCHESTRATOR LLM, not the executors
MODEL_CONTEXT_WINDOWS = {
    # OpenAI models
    "gpt-5.1-codex": 200_000,
    "gpt-5.1-codex-mini": 200_000,
    "gpt-5.1-codex-max": 400_000,
    "gpt-5": 200_000,
    "gpt-5-mini": 200_000,
    "o3": 200_000,
    "o3-mini": 200_000,
    # Claude models (if used as orchestrator)
    "claude-sonnet": 200_000,
    "claude-opus": 200_000,
    "claude-haiku": 200_000,
    "sonnet": 200_000,
    "opus": 200_000,
    "haiku": 200_000,
    # Fallback
    "default": 128_000,
}


def get_context_window(model: str) -> int:
    """Get context window size for a model."""
    model_lower = model.lower()
    for prefix, size in MODEL_CONTEXT_WINDOWS.items():
        if model_lower.startswith(prefix):
            return size
    return MODEL_CONTEXT_WINDOWS["default"]


def render_context_bar(used: int, total: int, width: int = 30) -> str:
    """
    Render a visual context window usage bar.

    Args:
        used: Tokens used
        total: Total context window
        width: Bar width in characters

    Returns:
        Colored bar string like: [████████░░░░░░░░░░░░] 40%
    """
    if total <= 0:
        return "[dim]?[/]"

    pct = min(used / total, 1.0)
    filled = int(pct * width)
    empty = width - filled

    # Color based on usage
    if pct < 0.5:
        color = "green"
    elif pct < 0.75:
        color = "yellow"
    elif pct < 0.9:
        color = "red"
    else:
        color = "red bold"

    bar = f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"
    pct_str = f"{pct * 100:.0f}%"

    return f"{bar} {pct_str}"


# =============================================================================
# Build Pilot Orchestrator
# =============================================================================


def build_pilot_orchestrator(
    config_path: Path | None = None,
    working_dir: Path | None = None,
    overrides: list[str] | None = None,
    instance_id: str | None = None,
    instance_name: str | None = None,
    lm_choice: str = "gpt5-verbose",
) -> Any:
    """
    Build an orchestrator configured for pilot mode.

    Pilot mode differences from regular orchestrator:
    - Uses pilot system prompt (conversational, not autonomous)
    - Only delegation tools (no bash, exit, list_agents, run_agent)
    - LM selection based on user choice

    Args:
        config_path: Path to YAML config file
        working_dir: Working directory (default: cwd)
        overrides: CLI overrides (--set key=value)
        instance_id: Unique ID for this instance
        instance_name: Human-readable name for this instance
        lm_choice: LM to use (gpt5-mini, gpt5, gpt5-verbose)

    Returns:
        Configured Orchestrator instance for pilot mode
    """
    from wbal.lm import GPT5Large, GPT5LargeVerbose, GPT5MiniTester

    from zwarm.core.config import load_config
    from zwarm.core.environment import OrchestratorEnv
    from zwarm.orchestrator import Orchestrator
    from zwarm.prompts import get_pilot_prompt

    # Select LM based on choice
    lm_map = {
        "gpt5-mini": GPT5MiniTester,
        "gpt5": GPT5Large,
        "gpt5-verbose": GPT5LargeVerbose,
    }
    lm_class = lm_map.get(lm_choice, GPT5LargeVerbose)
    lm = lm_class()

    # Load configuration from working_dir (not cwd!)
    # This ensures config.toml and .env are loaded from the project being worked on
    config = load_config(
        config_path=config_path,
        overrides=overrides,
        working_dir=working_dir,
    )

    # Resolve working directory
    working_dir = working_dir or Path.cwd()

    # Generate instance ID if not provided
    if instance_id is None:
        instance_id = str(uuid4())

    # Build pilot system prompt
    system_prompt = get_pilot_prompt(working_dir=str(working_dir))

    # Create lean orchestrator environment (pilot mode = simpler observation)
    env = OrchestratorEnv(
        task="",  # No task - pilot is conversational
        working_dir=working_dir,
    )
    env.set_pilot_mode(True)  # Human is in control, use lean observation

    # Create orchestrator with ONLY delegation tools (no bash)
    orchestrator = Orchestrator(
        config=config,
        working_dir=working_dir,
        system_prompt=system_prompt,
        maxSteps=config.orchestrator.max_steps,
        env=env,
        instance_id=instance_id,
        instance_name=instance_name,
        lm=lm,
        # Only delegation tools - no bash
        agent_tool_modules=["zwarm.tools.delegation"],
    )

    # Remove unwanted tools that come from YamlAgent/OpenAIWBAgent
    # These are: exit, list_agents, run_agent
    _remove_unwanted_tools(orchestrator)

    return orchestrator


def _remove_unwanted_tools(orchestrator: Any) -> None:
    """
    Remove tools that aren't appropriate for pilot mode.

    Removes:
    - exit: Pilot doesn't auto-exit, user controls the session
    - list_agents: No delegate subagents in pilot mode
    - run_agent: No delegate subagents in pilot mode

    This works by wrapping getToolDefinitions to filter out unwanted tools.
    We use object.__setattr__ to bypass Pydantic's attribute checks.
    """
    import types

    unwanted = {"exit", "list_agents", "run_agent"}

    # Store original method
    original_get_tools = orchestrator.getToolDefinitions

    def filtered_get_tools(self):
        """Wrapped getToolDefinitions that filters out unwanted tools."""
        definitions, callables = original_get_tools()

        # Filter definitions - handle both OpenAI formats
        filtered_defs = []
        for td in definitions:
            # Check both possible name locations
            name = td.get("name") or td.get("function", {}).get("name")
            if name not in unwanted:
                filtered_defs.append(td)

        # Filter callables
        filtered_callables = {
            k: v for k, v in callables.items()
            if k not in unwanted
        }

        return filtered_defs, filtered_callables

    # Bind the new method to the instance, bypassing Pydantic
    bound_method = types.MethodType(filtered_get_tools, orchestrator)
    object.__setattr__(orchestrator, "getToolDefinitions", bound_method)


# =============================================================================
# Event Renderer (inspired by improver's run_agent.py)
# =============================================================================


class EventRenderer:
    """
    Streaming renderer for orchestrator events.

    Handles different event types with nice formatting:
    - Thinking/reasoning
    - Tool calls (delegate, converse, check_session, etc.)
    - Tool results
    - Assistant messages
    - Status messages
    """

    def __init__(self, *, show_reasoning: bool = True) -> None:
        self._assistant_open = False
        self._assistant_prefix = "  "
        self._thinking_open = False
        self._had_output = False
        self._show_reasoning = show_reasoning

        # ANSI codes
        self._dim = "\x1b[2m"
        self._italic = "\x1b[3m"
        self._green = "\x1b[32m"
        self._yellow = "\x1b[33m"
        self._cyan = "\x1b[36m"
        self._reset = "\x1b[0m"
        self._bold = "\x1b[1m"

        # Tool call tracking
        self._tool_names: Dict[str, str] = {}
        self._tool_args: Dict[str, str] = {}

    def _write(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def _write_err(self, text: str) -> None:
        sys.stderr.write(text)
        sys.stderr.flush()

    def _ensure_newline(self) -> None:
        if self._assistant_open:
            self._write("\n")
            self._assistant_open = False

    def _finish_thinking(self) -> None:
        if self._thinking_open:
            self._write("\n")
            self._thinking_open = False

    def _line(self, text: str) -> None:
        self._ensure_newline()
        self._write(f"{text}\n")

    def _style(self, text: str, *, dim: bool = False, italic: bool = False,
               green: bool = False, yellow: bool = False, cyan: bool = False,
               bold: bool = False) -> str:
        if not text:
            return text
        parts = []
        if dim:
            parts.append(self._dim)
        if italic:
            parts.append(self._italic)
        if green:
            parts.append(self._green)
        if yellow:
            parts.append(self._yellow)
        if cyan:
            parts.append(self._cyan)
        if bold:
            parts.append(self._bold)
        parts.append(text)
        parts.append(self._reset)
        return "".join(parts)

    def _truncate(self, text: str, max_len: int = 120) -> str:
        trimmed = " ".join(text.split())
        if len(trimmed) <= max_len:
            return trimmed
        return trimmed[: max_len - 3].rstrip() + "..."

    # -------------------------------------------------------------------------
    # Event handlers
    # -------------------------------------------------------------------------

    def status(self, message: str) -> None:
        """Display a status message."""
        self._finish_thinking()
        self._line(message)

    def thinking(self, text: str) -> None:
        """Display thinking/reasoning (dim italic)."""
        if not self._show_reasoning:
            return
        if not self._thinking_open:
            self._ensure_newline()
            self._write(self._style("  ", dim=True, italic=True))
            self._thinking_open = True
        formatted = text.replace("\n", f"\n  ")
        self._write(self._style(formatted, dim=True, italic=True))
        self._had_output = True

    def thinking_done(self) -> None:
        """Finish thinking block."""
        self._finish_thinking()

    def assistant(self, text: str) -> None:
        """Display assistant message."""
        self._finish_thinking()
        if not self._assistant_open:
            self._ensure_newline()
            self._write(self._style("• ", bold=True))
            self._assistant_open = True
        formatted = text.replace("\n", f"\n{self._assistant_prefix}")
        self._write(formatted)
        self._had_output = True

    def assistant_done(self) -> None:
        """Finish assistant block."""
        self._ensure_newline()

    def tool_call(self, name: str, args: Any, call_id: str = "") -> None:
        """Display a tool call."""
        self._finish_thinking()

        # Track for result matching
        if call_id:
            self._tool_names[call_id] = name
            self._tool_args[call_id] = str(args)

        # Format args based on tool type
        args_str = self._format_tool_args(name, args)

        prefix = self._style("→ ", green=True)
        tool_name = self._style(name, green=True, bold=True)

        if args_str:
            self._line(f"{prefix}{tool_name} {self._style(args_str, dim=True)}")
        else:
            self._line(f"{prefix}{tool_name}")

        self._had_output = True

    def tool_result(self, name: str, result: Any, call_id: str = "") -> None:
        """Display a tool result (compact)."""
        if result is None:
            return

        result_str = str(result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "..."

        # Show first few lines
        lines = result_str.split("\n")
        if len(lines) > 3:
            lines = lines[:3] + ["..."]

        for i, line in enumerate(lines):
            prefix = "  └ " if i == 0 else "    "
            self._line(f"{prefix}{self._style(line, dim=True)}")

    def error(self, message: str) -> None:
        """Display an error."""
        self._ensure_newline()
        self._write_err(f"{self._style('[error]', yellow=True, bold=True)} {message}\n")

    def _format_tool_args(self, name: str, args: Any) -> str:
        """Format tool arguments based on tool type."""
        if args is None:
            return ""

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, TypeError):
                return self._truncate(args)

        if not isinstance(args, dict):
            return self._truncate(str(args))

        # Tool-specific formatting
        if name == "delegate":
            task = args.get("task", "")[:60]
            mode = args.get("mode", "sync")
            return f"({mode}): {task}..."
        elif name == "converse":
            session_id = args.get("session_id", "")[:8]
            message = args.get("message", "")[:50]
            return f"[{session_id}]: {message}..."
        elif name == "check_session":
            session_id = args.get("session_id", "")[:8]
            return f"({session_id})"
        elif name == "end_session":
            session_id = args.get("session_id", "")[:8]
            return f"({session_id})"
        elif name == "list_sessions":
            return ""
        elif name == "bash":
            cmd = args.get("command", "")[:80]
            return f"$ {cmd}"
        else:
            # Generic: show first value
            first_val = next(iter(args.values()), "") if args else ""
            if isinstance(first_val, str) and len(first_val) > 40:
                first_val = first_val[:40] + "..."
            return str(first_val) if first_val else ""

    # -------------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------------

    def reset_turn(self) -> None:
        self._had_output = False

    def had_output(self) -> bool:
        return self._had_output

    def set_show_reasoning(self, value: bool) -> None:
        self._show_reasoning = value

    def show_reasoning(self) -> bool:
        return self._show_reasoning


# =============================================================================
# Command Parsing
# =============================================================================


def parse_command(text: str) -> Optional[List[str]]:
    """Parse a :command from user input. Returns None if not a command."""
    if not text.startswith(":"):
        return None
    cmdline = text[1:].strip()
    if not cmdline:
        return None
    try:
        return shlex.split(cmdline)
    except ValueError:
        return None


# =============================================================================
# Output Handler for Orchestrator Events
# =============================================================================


def make_event_handler(renderer: EventRenderer) -> Callable[[str], None]:
    """
    Create an output_handler that routes orchestrator output to the renderer.

    The orchestrator emits text through env.output_handler. We parse it
    to extract event types and route to appropriate renderer methods.
    """
    def handler(text: str) -> None:
        if not text:
            return

        # Check for reasoning prefix (from OpenAIWBAgent)
        if text.startswith("💭 "):
            renderer.thinking(text[2:])
            return

        # Default: treat as assistant message
        renderer.assistant(text)

    return handler


# =============================================================================
# Step Execution with Event Capture
# =============================================================================


def extract_events_from_response(response: Any) -> Dict[str, List[Any]]:
    """Extract structured events from an LLM response."""
    events = {
        "reasoning": [],
        "messages": [],
        "tool_calls": [],
    }

    output = getattr(response, "output", None)
    if not output:
        return events

    for item in output:
        item_type = getattr(item, "type", None)
        if item_type == "reasoning":
            events["reasoning"].append(item)
        elif item_type == "message":
            events["messages"].append(item)
        elif item_type == "function_call":
            events["tool_calls"].append(item)

    return events


def execute_step_with_events(
    orchestrator: Any,
    renderer: EventRenderer,
) -> tuple[List[tuple], bool]:
    """
    Execute one orchestrator step with event rendering.

    Returns:
        (tool_results, had_message) - tool call results and whether agent produced a message

    Note: Watchers are not run in pilot mode - the user is the watcher,
    actively guiding the orchestrator turn-by-turn.
    """
    had_message = False

    # Update environment with current progress before perceive
    # This ensures the observation has fresh step/token counts
    if hasattr(orchestrator, "env") and hasattr(orchestrator.env, "update_progress"):
        total_tokens = getattr(orchestrator, "_total_tokens", 0)
        executor_usage = orchestrator.get_executor_usage() if hasattr(orchestrator, "get_executor_usage") else {}
        orchestrator.env.update_progress(
            step_count=getattr(orchestrator, "_step_count", 0),
            max_steps=getattr(orchestrator, "maxSteps", 50),
            total_tokens=total_tokens,
            executor_tokens=executor_usage.get("total_tokens", 0),
        )

    # Execute perceive (updates environment observation)
    orchestrator.perceive()

    # Execute invoke (calls LLM)
    response = orchestrator.invoke()

    # Track cumulative token usage from the API response
    # (This mirrors what step() does in orchestrator.py)
    if hasattr(orchestrator, "_last_response") and orchestrator._last_response:
        last_response = orchestrator._last_response
        if hasattr(last_response, "usage") and last_response.usage:
            usage = last_response.usage
            tokens_this_call = getattr(usage, "total_tokens", 0)
            orchestrator._total_tokens = getattr(orchestrator, "_total_tokens", 0) + tokens_this_call

    # Extract and render events from response
    if response:
        events = extract_events_from_response(response)

        # Render reasoning
        for reasoning in events["reasoning"]:
            summary = getattr(reasoning, "summary", None)
            if summary:
                for item in summary:
                    text = getattr(item, "text", "")
                    if text:
                        renderer.thinking(text)
        renderer.thinking_done()

        # Render messages
        for msg in events["messages"]:
            content = getattr(msg, "content", [])
            for part in content:
                text = getattr(part, "text", "")
                if text:
                    renderer.assistant(text)
                    had_message = True
        renderer.assistant_done()

        # Render tool calls (before execution)
        for tc in events["tool_calls"]:
            name = getattr(tc, "name", "?")
            args = getattr(tc, "arguments", "")
            call_id = getattr(tc, "call_id", "")
            renderer.tool_call(name, args, call_id)

    # Execute do (runs tool calls)
    results = orchestrator.do()

    # Increment step count (normally done by step() but we call perceive/invoke/do separately)
    orchestrator._step_count += 1

    # Render tool results
    for tool_info, result in results:
        name = tool_info.get("name", "?")
        call_id = tool_info.get("call_id", "")
        renderer.tool_result(name, result, call_id)

    return results, had_message


def run_until_response(
    orchestrator: Any,
    renderer: EventRenderer,
    max_steps: int = 60,
) -> List[tuple]:
    """
    Run the orchestrator until it produces a message response.

    Keeps stepping while the agent only produces tool calls.
    Stops when:
    - Agent produces a text message (returns to user)
    - Max steps reached (configurable via orchestrator.max_steps_per_turn)
    - Stop condition triggered

    This is wrapped as a weave.op to group all child calls per turn.

    Args:
        orchestrator: The orchestrator instance
        renderer: Event renderer for output
        max_steps: Safety limit on steps per turn (default: 60)

    Returns:
        All tool results from the turn
    """
    import weave

    @weave.op(name="pilot_turn")
    def _run_turn():
        all_results = []
        spinner = ChoogingSpinner()

        for step in range(max_steps):
            # Show spinner only for the first step (initial LLM call after user message)
            # Subsequent steps have visible tool activity so no spinner needed
            if step == 0:
                spinner.start()

            try:
                results, had_message = execute_step_with_events(orchestrator, renderer)
            finally:
                if step == 0:
                    spinner.stop()

            all_results.extend(results)

            # Stop if agent produced a message
            if had_message:
                break

            # Stop if orchestrator signals completion
            if hasattr(orchestrator, "stopCondition") and orchestrator.stopCondition:
                break

            # Stop if no tool calls (agent is done but didn't message)
            if not results:
                break

        # Show session status at end of turn (if there are any sessions)
        render_session_status(orchestrator, renderer)

        return all_results

    return _run_turn()


# =============================================================================
# Main REPL
# =============================================================================


def print_help(renderer: EventRenderer) -> None:
    """Print help for pilot commands."""
    lines = [
        "",
        "Commands:",
        "  :help                Show this help",
        "  :status              Show pilot status (tokens, cost, context)",
        "  :history [N|all]     Show turn checkpoints",
        "  :goto <turn|root>    Jump to a prior turn (e.g., :goto T1)",
        "  :sessions            Show executor sessions",
        "  :reasoning [on|off]  Toggle reasoning display",
        "  :save                Save state (for later resume)",
        "  :quit / :exit        Exit the pilot (auto-saves)",
        "",
        "Resume:",
        "  State is auto-saved after each turn. To resume a session:",
        "  $ zwarm pilot --resume --instance <instance_id>",
        "",
        "Multiline input:",
        '  Start with """ and end with """ to enter multiple lines.',
        '  Example: """',
        "           paste your",
        "           content here",
        '           """',
        "",
    ]
    for line in lines:
        renderer.status(line)


def get_sessions_snapshot(orchestrator: Any) -> Dict[str, Any]:
    """Get a serializable snapshot of session state."""
    if hasattr(orchestrator, "_session_manager"):
        sessions = orchestrator._session_manager.list_sessions()
        return {
            "sessions": [
                {
                    "id": s.id,
                    "status": s.status.value,
                    "task": s.task[:100] if s.task else "",
                    "turns": s.turn,
                    "tokens": s.token_usage.get("total_tokens", 0),
                    "model": s.model,
                }
                for s in sessions
            ]
        }
    return {"sessions": []}


def render_session_status(orchestrator: Any, renderer: EventRenderer) -> None:
    """
    Render a compact session status line if there are active sessions.

    Shows: "Sessions: 2 running, 1 done, 0 failed"
    Only displays if there are any sessions.
    """
    if not hasattr(orchestrator, "_session_manager"):
        return

    sessions = orchestrator._session_manager.list_sessions()
    if not sessions:
        return

    running = sum(1 for s in sessions if s.status.value == "running")
    completed = sum(1 for s in sessions if s.status.value == "completed")
    failed = sum(1 for s in sessions if s.status.value == "failed")

    # Build status line with colors
    parts = []
    if running > 0:
        parts.append(f"[cyan]{running} running[/]")
    if completed > 0:
        parts.append(f"[green]{completed} done[/]")
    if failed > 0:
        parts.append(f"[red]{failed} failed[/]")

    if parts:
        status_line = ", ".join(parts)
        console.print(f"[dim]Sessions:[/] {status_line}")


def run_pilot(
    orchestrator: Any,
    *,
    initial_task: Optional[str] = None,
) -> None:
    """
    Run the pilot REPL.

    Args:
        orchestrator: A built orchestrator instance
        initial_task: Optional initial task to start with
    """
    import weave

    @weave.op(name="pilot_session")
    def _run_pilot_session():
        """Inner function wrapped with weave.op for clean logging."""
        _run_pilot_repl(orchestrator, initial_task)

    _run_pilot_session()


def _run_pilot_repl(
    orchestrator: Any,
    initial_task: Optional[str] = None,
) -> None:
    """
    The actual REPL implementation.
    """
    renderer = EventRenderer(show_reasoning=True)
    state = CheckpointManager()

    # Silence the default output_handler - we render events directly in execute_step_with_events
    # (Otherwise messages would be rendered twice)
    if hasattr(orchestrator, "env") and hasattr(orchestrator.env, "output_handler"):
        orchestrator.env.output_handler = lambda x: None

    # Welcome message
    renderer.status("")
    renderer.status("╭─────────────────────────────────────────╮")
    renderer.status("│          zwarm pilot                    │")
    renderer.status("│   Conversational orchestrator REPL      │")
    renderer.status("╰─────────────────────────────────────────╯")
    renderer.status("")
    renderer.status("Type :help for commands, :quit to exit.")
    renderer.status("")

    # Handle initial task if provided
    if initial_task:
        renderer.status(f"Initial task: {initial_task[:80]}...")
        orchestrator.messages.append({
            "role": "user",
            "content": initial_task,
        })

        renderer.reset_turn()
        max_steps = getattr(orchestrator.config.orchestrator, "max_steps_per_turn", 60)
        results = run_until_response(orchestrator, renderer, max_steps=max_steps)

        # Record checkpoint
        state.record(
            description=initial_task,
            state={
                "messages": orchestrator.messages,
                "sessions_snapshot": get_sessions_snapshot(orchestrator),
                "step_count": orchestrator._step_count,
            },
            metadata={
                "step_count": orchestrator._step_count,
                "message_count": len(orchestrator.messages),
            },
        )

        cp = state.current()
        if cp:
            renderer.status("")
            renderer.status(
                f"[{cp.label}] "
                f"step={cp.state['step_count']} "
                f"messages={len(cp.state['messages'])}"
            )
            renderer.status(f":goto {cp.label} to return here")

    # Main REPL loop
    while True:
        try:
            user_input = input("> ").strip()
        except EOFError:
            sys.stdout.write("\n")
            break
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            renderer.status("(Ctrl+C - type :quit to exit)")
            continue

        if not user_input:
            continue

        # Multiline input: if starts with """, collect until closing """
        if user_input.startswith('"""'):
            # Check if closing """ is on the same line (e.g., """hello""")
            rest = user_input[3:]
            if '"""' in rest:
                # Single line with both opening and closing
                user_input = rest[: rest.index('"""')]
            else:
                # Multiline mode - collect until we see """
                lines = [rest] if rest else []
                try:
                    while True:
                        line = input("... ")
                        if '"""' in line:
                            # Found closing quotes
                            idx = line.index('"""')
                            if idx > 0:
                                lines.append(line[:idx])
                            break
                        lines.append(line)
                except EOFError:
                    renderer.error("Multiline input interrupted (EOF)")
                    continue
                except KeyboardInterrupt:
                    sys.stdout.write("\n")
                    renderer.status("(Multiline cancelled)")
                    continue
                user_input = "\n".join(lines)

        if not user_input:
            continue

        # Parse command
        cmd_parts = parse_command(user_input)
        if cmd_parts:
            cmd = cmd_parts[0].lower()
            args = cmd_parts[1:]

            # :quit / :exit
            if cmd in ("quit", "exit", "q"):
                # Save state before exiting
                if hasattr(orchestrator, "save_state"):
                    orchestrator.save_state()
                    renderer.status("[dim]State saved.[/]")
                renderer.status("Goodbye!")
                break

            # :help
            if cmd == "help":
                print_help(renderer)
                continue

            # :history
            if cmd == "history":
                limit = None
                if args:
                    token = args[0].lower()
                    if token == "all":
                        limit = None  # Show all
                    elif token.isdigit():
                        limit = int(token)
                else:
                    limit = 10

                entries = state.history(limit=limit)
                if not entries:
                    renderer.status("No checkpoints yet.")
                else:
                    renderer.status("")
                    for entry in entries:
                        marker = "*" if entry["is_current"] else " "
                        desc = entry["description"]
                        desc_preview = desc[:60] + "..." if len(desc) > 60 else desc
                        renderer.status(
                            f"{marker}[{entry['label']}] "
                            f"step={entry['metadata'].get('step_count', '?')} "
                            f"msgs={entry['metadata'].get('message_count', '?')} "
                            f"| {desc_preview}"
                        )
                    renderer.status("")
                continue

            # :goto
            if cmd == "goto":
                if not args:
                    renderer.error("Usage: :goto <turn|root> (e.g., :goto T1)")
                    continue

                token = args[0]
                if token.lower() == "root":
                    # Go to root (before any turns)
                    state.goto(0)
                    # Reset orchestrator to initial state
                    if hasattr(orchestrator, "messages"):
                        # Keep only system messages
                        orchestrator.messages = [
                            m for m in orchestrator.messages
                            if m.get("role") == "system"
                        ][:1]
                    renderer.status("Switched to root (initial state).")
                    continue

                # Parse T1, T2, etc. or just numbers
                turn_id = None
                token_upper = token.upper()
                if token_upper.startswith("T") and token_upper[1:].isdigit():
                    turn_id = int(token_upper[1:])
                elif token.isdigit():
                    turn_id = int(token)

                if turn_id is None:
                    renderer.error(f"Invalid turn: {token}")
                    continue

                cp = state.goto(turn_id)
                if cp is None:
                    renderer.error(f"Turn T{turn_id} not found.")
                    continue

                # Restore orchestrator state
                orchestrator.messages = copy.deepcopy(cp.state["messages"])
                orchestrator._step_count = cp.state["step_count"]
                renderer.status(f"Switched to {cp.label}.")
                renderer.status(f"  instruction: {cp.description[:60]}...")
                renderer.status(f"  messages: {len(cp.state['messages'])}")
                continue

            # :state / :status
            if cmd in ("state", "status"):
                renderer.status("")
                renderer.status("[bold]Pilot Status[/]")
                renderer.status("")

                # Basic stats
                step_count = getattr(orchestrator, "_step_count", 0)
                msg_count = len(orchestrator.messages)
                total_tokens = getattr(orchestrator, "_total_tokens", 0)

                renderer.status(f"  Steps:    {step_count}")
                renderer.status(f"  Messages: {msg_count}")

                # Checkpoint
                cp = state.current()
                turn_label = cp.label if cp else "root"
                renderer.status(f"  Turn:     {turn_label}")

                # Token usage and context
                renderer.status("")
                renderer.status("[bold]Token Usage[/]")
                renderer.status("")

                # Get model from orchestrator if available
                model = "gpt-5.1-codex"  # Default
                if hasattr(orchestrator, "lm") and hasattr(orchestrator.lm, "model"):
                    model = orchestrator.lm.model
                elif hasattr(orchestrator, "config"):
                    model = getattr(orchestrator.config, "model", model)

                context_window = get_context_window(model)
                context_bar = render_context_bar(total_tokens, context_window)

                renderer.status(f"  Model:    {model}")
                renderer.status(f"  Tokens:   {total_tokens:,} / {context_window:,}")
                renderer.status(f"  Context:  {context_bar}")

                # Cost estimate for orchestrator
                pricing = get_pricing(model)
                if pricing and total_tokens > 0:
                    # Estimate assuming 30% input, 70% output (typical for agentic)
                    est_input = int(total_tokens * 0.3)
                    est_output = total_tokens - est_input
                    cost = pricing.estimate_cost(est_input, est_output)
                    renderer.status(f"  Est Cost: [green]{format_cost(cost)}[/] (pilot LLM)")

                # Executor sessions summary
                snapshot = get_sessions_snapshot(orchestrator)
                sessions = snapshot.get("sessions", [])
                if sessions:
                    renderer.status("")
                    renderer.status("[bold]Executor Sessions[/]")
                    renderer.status("")

                    exec_tokens = 0
                    exec_cost = 0.0
                    running = 0
                    completed = 0

                    for s in sessions:
                        exec_tokens += s.get("tokens", 0)
                        if s.get("status") == "running":
                            running += 1
                        elif s.get("status") == "completed":
                            completed += 1

                    renderer.status(f"  Sessions: {len(sessions)} ({running} running, {completed} done)")
                    renderer.status(f"  Tokens:   {exec_tokens:,}")

                renderer.status("")
                continue

            # :sessions
            if cmd == "sessions":
                snapshot = get_sessions_snapshot(orchestrator)
                sessions = snapshot.get("sessions", [])
                if not sessions:
                    renderer.status("No sessions.")
                else:
                    renderer.status("")
                    for s in sessions:
                        renderer.status(
                            f"  [{s['id'][:8]}] {s['status']} "
                            f"turns={s['turns']} | {s['task'][:50]}"
                        )
                    renderer.status("")
                continue

            # :reasoning
            if cmd == "reasoning":
                if not args:
                    current = "on" if renderer.show_reasoning() else "off"
                    renderer.status(f"Reasoning display: {current}")
                    continue

                value = args[0].lower()
                if value in ("on", "true", "yes", "1"):
                    renderer.set_show_reasoning(True)
                elif value in ("off", "false", "no", "0"):
                    renderer.set_show_reasoning(False)
                else:
                    renderer.error("Usage: :reasoning [on|off]")
                    continue

                current = "on" if renderer.show_reasoning() else "off"
                renderer.status(f"Reasoning display: {current}")
                continue

            # :save
            if cmd == "save":
                if hasattr(orchestrator, "save_state"):
                    orchestrator.save_state()
                    instance_id = getattr(orchestrator, "instance_id", None)
                    if instance_id:
                        renderer.status(f"[green]✓[/] State saved (instance: {instance_id[:8]})")
                        renderer.status(f"  [dim]Resume with: zwarm pilot --resume --instance {instance_id[:8]}[/]")
                    else:
                        renderer.status("[green]✓[/] State saved")
                else:
                    renderer.error("State saving not available")
                continue

            # Unknown command
            renderer.error(f"Unknown command: {cmd}")
            renderer.status("Type :help for available commands.")
            continue

        # Not a command - send to orchestrator as instruction
        renderer.status("")

        # Inject user message
        orchestrator.messages.append({
            "role": "user",
            "content": user_input,
        })

        # Execute steps until agent responds with a message
        renderer.reset_turn()
        max_steps = getattr(orchestrator.config.orchestrator, "max_steps_per_turn", 60)
        try:
            results = run_until_response(orchestrator, renderer, max_steps=max_steps)
        except Exception as e:
            renderer.error(f"Step failed: {e}")
            # Remove the user message on failure
            if orchestrator.messages and orchestrator.messages[-1].get("role") == "user":
                orchestrator.messages.pop()
            continue

        # Record checkpoint
        state.record(
            description=user_input,
            state={
                "messages": orchestrator.messages,
                "sessions_snapshot": get_sessions_snapshot(orchestrator),
                "step_count": orchestrator._step_count,
            },
            metadata={
                "step_count": orchestrator._step_count,
                "message_count": len(orchestrator.messages),
            },
        )

        # Save state for resume capability
        if hasattr(orchestrator, "save_state"):
            orchestrator.save_state()

        # Show turn info
        cp = state.current()
        if cp:
            renderer.status("")
            renderer.status(
                f"[{cp.label}] "
                f"step={cp.state['step_count']} "
                f"messages={len(cp.state['messages'])}"
            )
            renderer.status(f":goto {cp.label} to return here, :history for timeline")

        # Check stop condition
        if hasattr(orchestrator, "stopCondition") and orchestrator.stopCondition:
            renderer.status("")
            renderer.status("Orchestrator signaled completion.")
            if hasattr(orchestrator, "save_state"):
                orchestrator.save_state()
            break
