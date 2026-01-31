"""
Interactive REPL for zwarm session management.

A clean, autocomplete-enabled interface for managing codex sessions.
This is the user's direct REPL over the session primitives.

Topology: interactive → CodexSessionManager (substrate)
"""

from __future__ import annotations

import shlex
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table

console = Console()


# =============================================================================
# Session ID Completer
# =============================================================================


class SessionCompleter(Completer):
    """
    Autocomplete for session IDs.

    Provides completions for commands that take session IDs.
    """

    def __init__(self, get_sessions_fn):
        """
        Args:
            get_sessions_fn: Callable that returns list of sessions
        """
        self.get_sessions_fn = get_sessions_fn

        # Commands that take session ID as first argument
        self.session_commands = {
            "?", "peek", "show", "traj", "trajectory", "watch",
            "c", "continue",
        }
        # Commands that take session ID OR "all"
        self.session_or_all_commands = {"kill", "rm", "delete"}

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()

        # If we're completing the first word, suggest commands
        if len(words) == 0 or (len(words) == 1 and not text.endswith(" ")):
            word = words[0] if words else ""
            commands = [
                "spawn", "ls", "peek", "show", "traj", "watch",
                "c", "kill", "rm", "help", "quit",
            ]
            for cmd in commands:
                if cmd.startswith(word.lower()):
                    yield Completion(cmd, start_position=-len(word))
            return

        # If we have a command and need session ID
        cmd = words[0].lower()
        needs_session = cmd in self.session_commands or cmd in self.session_or_all_commands

        if needs_session:
            # Get sessions
            try:
                sessions = self.get_sessions_fn()
            except Exception:
                return

            # What has user typed for session ID?
            if len(words) == 1 and text.endswith(" "):
                # Just typed command + space, show all IDs
                partial = ""
            elif len(words) == 2 and not text.endswith(" "):
                # Typing session ID
                partial = words[1]
            else:
                return

            # For kill/rm, also offer "all" as option
            if cmd in self.session_or_all_commands:
                if "all".startswith(partial.lower()):
                    yield Completion(
                        "all",
                        start_position=-len(partial),
                        display="all",
                        display_meta="all sessions",
                    )

            # Yield matching session IDs
            for s in sessions:
                short_id = s.short_id
                if short_id.lower().startswith(partial.lower()):
                    # Show task as meta info
                    task_preview = s.task[:30] + "..." if len(s.task) > 30 else s.task
                    yield Completion(
                        short_id,
                        start_position=-len(partial),
                        display=short_id,
                        display_meta=f"{s.status.value}: {task_preview}",
                    )


# =============================================================================
# Display Helpers
# =============================================================================


def time_ago(iso_str: str) -> str:
    """Convert ISO timestamp to human-readable 'Xs/Xm/Xh ago' format."""
    try:
        dt = datetime.fromisoformat(iso_str)
        delta = datetime.now() - dt
        secs = delta.total_seconds()
        if secs < 60:
            return f"{int(secs)}s"
        elif secs < 3600:
            return f"{int(secs/60)}m"
        elif secs < 86400:
            return f"{secs/3600:.1f}h"
        else:
            return f"{secs/86400:.1f}d"
    except Exception:
        return "?"


STATUS_ICONS = {
    "running": "[yellow]●[/]",
    "completed": "[green]✓[/]",
    "failed": "[red]✗[/]",
    "killed": "[dim]○[/]",
    "pending": "[dim]◌[/]",
}


# =============================================================================
# Commands
# =============================================================================


def cmd_help():
    """Show help."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Command", style="cyan", width=35)
    table.add_column("Description")

    table.add_row("[bold]Session Lifecycle[/]", "")
    table.add_row('spawn "task" [--model M] [--adapter A]', "Start new session")
    table.add_row('c ID "message"', "Continue conversation")
    table.add_row("kill ID | all", "Stop session(s)")
    table.add_row("rm ID | all", "Delete session(s)")
    table.add_row("", "")
    table.add_row("[bold]Viewing[/]", "")
    table.add_row("ls", "Dashboard of all sessions")
    table.add_row("? ID  /  peek ID", "Quick peek (status + latest preview)")
    table.add_row("show ID [-v]", "Full response from agent (-v: verbose)")
    table.add_row("traj ID [--full]", "Trajectory (--full: all data)")
    table.add_row("watch ID", "Live follow session output")
    table.add_row("", "")
    table.add_row("[bold]Configuration[/]", "")
    table.add_row("models", "List available models and adapters")
    table.add_row("", "")
    table.add_row("[bold]Shell[/]", "")
    table.add_row("!<command>", "Run shell command (e.g., !ls, !git status)")
    table.add_row("", "")
    table.add_row("[bold]Meta[/]", "")
    table.add_row("help", "Show this help")
    table.add_row("quit", "Exit")

    console.print(table)


def cmd_models():
    """Show available models."""
    from zwarm.core.registry import list_models, list_adapters

    table = Table(title="Available Models", box=None)
    table.add_column("Adapter", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Aliases", style="dim")
    table.add_column("Price ($/1M)", justify="right")
    table.add_column("Description")

    for adapter in list_adapters():
        first = True
        for model in list_models(adapter):
            default_mark = " *" if model.is_default else ""
            price = f"{model.input_per_million:.2f}/{model.output_per_million:.2f}"
            aliases = ", ".join(model.aliases)
            table.add_row(
                adapter if first else "",
                f"{model.canonical}{default_mark}",
                aliases,
                price,
                model.description,
            )
            first = False

    console.print(table)
    console.print("\n[dim]* = default for adapter. Price = input/output per 1M tokens.[/]")
    console.print("[dim]Use --model <name> or --adapter <adapter> with spawn.[/]")


def cmd_ls(manager):
    """List all sessions."""
    from zwarm.sessions import SessionStatus
    from zwarm.core.costs import estimate_session_cost, format_cost

    sessions = manager.list_sessions()

    if not sessions:
        console.print("  [dim]No sessions. Use 'spawn \"task\"' to start one.[/]")
        return

    # Summary counts
    running = sum(1 for s in sessions if s.status == SessionStatus.RUNNING)
    completed = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
    failed = sum(1 for s in sessions if s.status == SessionStatus.FAILED)
    killed = sum(1 for s in sessions if s.status == SessionStatus.KILLED)

    # Total cost and tokens
    total_cost = 0.0
    total_tokens = 0
    for s in sessions:
        cost_info = estimate_session_cost(s.model, s.token_usage)
        if cost_info["cost"] is not None:
            total_cost += cost_info["cost"]
        total_tokens += s.token_usage.get("total_tokens", 0)

    parts = []
    if running:
        parts.append(f"[yellow]{running} running[/]")
    if completed:
        parts.append(f"[green]{completed} done[/]")
    if failed:
        parts.append(f"[red]{failed} failed[/]")
    if killed:
        parts.append(f"[dim]{killed} killed[/]")
    parts.append(f"[cyan]{total_tokens:,} tokens[/]")
    parts.append(f"[green]{format_cost(total_cost)}[/]")
    if parts:
        console.print(" | ".join(parts))
        console.print()

    # Table
    table = Table(box=None, show_header=True, header_style="bold dim")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("", width=2)
    table.add_column("Model", width=12)
    table.add_column("T", width=2)
    table.add_column("Task", max_width=26)
    table.add_column("Updated", justify="right", width=8)
    table.add_column("Last Message", max_width=36)

    for s in sessions:
        icon = STATUS_ICONS.get(s.status.value, "?")
        task_preview = s.task[:23] + "..." if len(s.task) > 26 else s.task
        updated = time_ago(s.updated_at)

        # Short model name (e.g., "gpt-5.1-codex-mini" -> "codex-mini")
        model_short = s.model or "?"
        if "codex" in model_short.lower():
            # Extract codex variant: gpt-5.1-codex-mini -> codex-mini
            parts = model_short.split("-")
            codex_idx = next((i for i, p in enumerate(parts) if "codex" in p.lower()), -1)
            if codex_idx >= 0:
                model_short = "-".join(parts[codex_idx:])
        elif len(model_short) > 12:
            model_short = model_short[:10] + ".."

        # Get last assistant message
        messages = manager.get_messages(s.id)
        last_msg = ""
        for msg in reversed(messages):
            if msg.role == "assistant":
                last_msg = msg.content.replace("\n", " ")[:33]
                if len(msg.content) > 33:
                    last_msg += "..."
                break

        # Style based on status
        if s.status == SessionStatus.RUNNING:
            last_msg_styled = f"[yellow]{last_msg or '(working...)'}[/]"
            updated_styled = f"[yellow]{updated}[/]"
        elif s.status == SessionStatus.COMPLETED:
            try:
                dt = datetime.fromisoformat(s.updated_at)
                is_recent = (datetime.now() - dt).total_seconds() < 60
            except Exception:
                is_recent = False
            if is_recent:
                last_msg_styled = f"[green bold]{last_msg or '(done)'}[/]"
                updated_styled = f"[green bold]{updated} ★[/]"
            else:
                last_msg_styled = f"[green]{last_msg or '(done)'}[/]"
                updated_styled = f"[dim]{updated}[/]"
        elif s.status == SessionStatus.FAILED:
            err = s.error[:33] if s.error else "(failed)"
            last_msg_styled = f"[red]{err}...[/]"
            updated_styled = f"[red]{updated}[/]"
        else:
            last_msg_styled = f"[dim]{last_msg or '-'}[/]"
            updated_styled = f"[dim]{updated}[/]"

        table.add_row(s.short_id, icon, f"[dim]{model_short}[/]", str(s.turn), task_preview, updated_styled, last_msg_styled)

    console.print(table)


def cmd_ls_multi(sessions: list, managers: dict | None = None):
    """
    List sessions from multiple managers.

    Args:
        sessions: List of Session objects
        managers: Optional dict of adapter -> manager for getting messages
    """
    from zwarm.sessions import SessionStatus
    from zwarm.core.costs import estimate_session_cost, format_cost

    if not sessions:
        console.print("  [dim]No sessions. Use 'spawn \"task\"' to start one.[/]")
        return

    # Summary counts
    running = sum(1 for s in sessions if s.status == SessionStatus.RUNNING)
    completed = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
    failed = sum(1 for s in sessions if s.status == SessionStatus.FAILED)
    killed = sum(1 for s in sessions if s.status == SessionStatus.KILLED)

    # Total cost and tokens
    total_cost = 0.0
    total_tokens = 0
    for s in sessions:
        cost_info = estimate_session_cost(s.model, s.token_usage)
        if cost_info["cost"] is not None:
            total_cost += cost_info["cost"]
        total_tokens += s.token_usage.get("total_tokens", 0)

    parts = []
    if running:
        parts.append(f"[yellow]{running} running[/]")
    if completed:
        parts.append(f"[green]{completed} done[/]")
    if failed:
        parts.append(f"[red]{failed} failed[/]")
    if killed:
        parts.append(f"[dim]{killed} killed[/]")
    parts.append(f"[cyan]{total_tokens:,} tokens[/]")
    parts.append(f"[green]{format_cost(total_cost)}[/]")
    if parts:
        console.print(" | ".join(parts))
        console.print()

    # Table
    table = Table(box=None, show_header=True, header_style="bold dim")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("", width=2)
    table.add_column("Adapter", width=7)
    table.add_column("Model", width=12)
    table.add_column("T", width=2)
    table.add_column("Task", max_width=24)
    table.add_column("Updated", justify="right", width=8)

    for s in sessions:
        icon = STATUS_ICONS.get(s.status.value, "?")
        task_preview = s.task[:21] + "..." if len(s.task) > 24 else s.task
        updated = time_ago(s.updated_at)

        # Short model name
        model_short = s.model or "?"
        if "codex" in model_short.lower():
            parts = model_short.split("-")
            codex_idx = next((i for i, p in enumerate(parts) if "codex" in p.lower()), -1)
            if codex_idx >= 0:
                model_short = "-".join(parts[codex_idx:])
        elif len(model_short) > 12:
            model_short = model_short[:10] + ".."

        # Adapter short name
        adapter_short = getattr(s, "adapter", "?")[:7]

        # Style based on status
        if s.status == SessionStatus.RUNNING:
            updated_styled = f"[yellow]{updated}[/]"
        elif s.status == SessionStatus.COMPLETED:
            try:
                dt = datetime.fromisoformat(s.updated_at)
                is_recent = (datetime.now() - dt).total_seconds() < 60
            except Exception:
                is_recent = False
            if is_recent:
                updated_styled = f"[green bold]{updated} ★[/]"
            else:
                updated_styled = f"[dim]{updated}[/]"
        elif s.status == SessionStatus.FAILED:
            updated_styled = f"[red]{updated}[/]"
        else:
            updated_styled = f"[dim]{updated}[/]"

        table.add_row(s.short_id, icon, f"[dim]{adapter_short}[/]", f"[dim]{model_short}[/]", str(s.turn), task_preview, updated_styled)

    console.print(table)


def cmd_peek(manager, session_id: str):
    """Quick peek at session status."""
    session = manager.get_session(session_id)
    if not session:
        console.print(f"  [red]Session not found:[/] {session_id}")
        return

    icon = STATUS_ICONS.get(session.status.value, "?")
    console.print(f"\n{icon} [cyan]{session.short_id}[/] ({session.status.value})")
    console.print(f"  [dim]Task:[/] {session.task[:60]}...")
    console.print(f"  [dim]Model:[/] {session.model} | [dim]Turn:[/] {session.turn} | [dim]Updated:[/] {time_ago(session.updated_at)}")

    # Latest message
    messages = manager.get_messages(session.id)
    for msg in reversed(messages):
        if msg.role == "assistant":
            preview = msg.content.replace("\n", " ")[:100]
            if len(msg.content) > 100:
                preview += "..."
            console.print(f"\n  [bold]Latest:[/] {preview}")
            break
    console.print()


def cmd_show(manager, session_id: str, verbose: bool = False):
    """
    Full session details with messages.

    Args:
        manager: Session manager
        session_id: Session to show
        verbose: If True, show everything including full system messages
    """
    from zwarm.core.costs import estimate_session_cost

    session = manager.get_session(session_id)
    if not session:
        console.print(f"  [red]Session not found:[/] {session_id}")
        return

    # Header
    icon = STATUS_ICONS.get(session.status.value, "?")
    console.print(f"\n{icon} [bold cyan]{session.short_id}[/] - {session.status.value}")
    console.print(f"  [dim]Task:[/] {session.task[:100]}..." if len(session.task) > 100 else f"  [dim]Task:[/] {session.task}")
    console.print(f"  [dim]Model:[/] {session.model} | [dim]Turn:[/] {session.turn} | [dim]Runtime:[/] {session.runtime}")

    # Token usage with cost estimate
    usage = session.token_usage
    input_tok = usage.get("input_tokens", 0)
    output_tok = usage.get("output_tokens", 0)
    total_tok = usage.get("total_tokens", input_tok + output_tok)

    cost_info = estimate_session_cost(session.model, usage)
    cost_str = f"[green]{cost_info['cost_formatted']}[/]" if cost_info["pricing_known"] else "[dim]?[/]"

    console.print(f"  [dim]Tokens:[/] {total_tok:,} ({input_tok:,} in / {output_tok:,} out) | [dim]Cost:[/] {cost_str}")

    if session.error:
        console.print(f"  [red]Error:[/] {session.error}")

    # Messages - show FULL assistant response (that's the point of show)
    messages = manager.get_messages(session.id)
    if messages:
        console.print(f"\n[bold]Messages ({len(messages)}):[/]")
        for msg in messages:
            role = msg.role
            content = msg.content

            if role == "user":
                # User messages (task) can be truncated unless verbose
                if not verbose and len(content) > 200:
                    content = content[:200] + "..."
                console.print(f"  [blue]USER:[/] {content}")
            elif role == "assistant":
                # FULL assistant response - this is what users need to see
                console.print(f"  [green]ASSISTANT:[/] {content}")
            else:
                # System/other messages truncated unless verbose
                if not verbose and len(content) > 100:
                    content = content[:100] + "..."
                console.print(f"  [dim]{role.upper()}:[/] {content}")

    console.print()


def cmd_traj(manager, session_id: str, full: bool = False):
    """
    Show session trajectory.

    Args:
        manager: Session manager
        session_id: Session to show trajectory for
        full: If True, show full untruncated content for all steps
    """
    session = manager.get_session(session_id)
    if not session:
        console.print(f"  [red]Session not found:[/] {session_id}")
        return

    trajectory = manager.get_trajectory(session_id, full=full)

    mode_str = "[bold green](FULL)[/]" if full else "[dim](summary - use --full for complete)[/]"
    console.print(f"\n[bold]Trajectory for {session.short_id}[/] ({len(trajectory)} steps) {mode_str}")
    console.print(f"  [dim]Task:[/] {session.task[:60]}...")
    console.print()

    for i, step in enumerate(trajectory):
        step_type = step.get("type", "unknown")

        if step_type == "reasoning":
            text = step.get("full_text") if full else step.get("summary", "")
            console.print(f"  [dim]{i+1}.[/] [magenta]💭 thinking[/]")
            if text:
                if full:
                    # Full mode: show everything, handle multiline
                    for line in text.split("\n"):
                        console.print(f"     {line}")
                else:
                    console.print(f"     {text[:150]}{'...' if len(text) > 150 else ''}")

        elif step_type == "command":
            cmd = step.get("command", "")
            output = step.get("output", "")
            exit_code = step.get("exit_code", 0)
            console.print(f"  [dim]{i+1}.[/] [yellow]$ {cmd}[/]")
            if output:
                if full:
                    # Full mode: show complete output
                    for line in output.split("\n")[:50]:  # Cap at 50 lines for sanity
                        console.print(f"     {line}")
                    if output.count("\n") > 50:
                        console.print(f"     [dim]... ({output.count(chr(10)) - 50} more lines)[/]")
                else:
                    console.print(f"     {output[:100]}{'...' if len(output) > 100 else ''}")
            if exit_code and exit_code != 0:
                console.print(f"     [red](exit: {exit_code})[/]")

        elif step_type == "tool_call":
            tool = step.get("tool", "unknown")
            if full and step.get("full_args"):
                import json
                args_str = json.dumps(step["full_args"], indent=2)
                console.print(f"  [dim]{i+1}.[/] [cyan]🔧 {tool}[/]")
                for line in args_str.split("\n"):
                    console.print(f"     {line}")
            else:
                args_preview = step.get("args_preview", "")
                console.print(f"  [dim]{i+1}.[/] [cyan]🔧 {tool}[/]({args_preview})")

        elif step_type == "tool_output":
            output = step.get("output", "")
            if full:
                # Full mode: show complete output
                for line in output.split("\n")[:30]:
                    console.print(f"     [dim]→ {line}[/]")
                if output.count("\n") > 30:
                    console.print(f"     [dim]... ({output.count(chr(10)) - 30} more lines)[/]")
            else:
                console.print(f"     [dim]→ {output[:100]}{'...' if len(output) > 100 else ''}[/]")

        elif step_type == "message":
            text = step.get("full_text") if full else step.get("summary", "")
            console.print(f"  [dim]{i+1}.[/] [green]💬 response[/]")
            if text:
                if full:
                    # Full mode: show everything
                    for line in text.split("\n"):
                        console.print(f"     {line}")
                else:
                    console.print(f"     {text[:150]}{'...' if len(text) > 150 else ''}")

    console.print()


def cmd_watch(manager, session_id: str):
    """
    Watch session output live.

    Polls trajectory and displays new steps as they appear.
    """
    from zwarm.sessions import SessionStatus

    session = manager.get_session(session_id)
    if not session:
        console.print(f"  [red]Session not found:[/] {session_id}")
        return

    console.print(f"\n[bold]Watching {session.short_id}[/]...")
    console.print(f"  [dim]Task:[/] {session.task[:60]}...")
    console.print(f"  [dim]Model:[/] {session.model}")
    console.print(f"  [dim]Press Ctrl+C to stop watching[/]\n")

    seen_steps = 0
    last_status = None

    try:
        while True:
            # Refresh session
            session = manager.get_session(session_id)
            if not session:
                console.print("[red]Session disappeared![/]")
                break

            # Status change
            if session.status.value != last_status:
                icon = STATUS_ICONS.get(session.status.value, "?")
                console.print(f"\n{icon} Status: [bold]{session.status.value}[/]")
                last_status = session.status.value

            # Get trajectory
            trajectory = manager.get_trajectory(session_id, full=False)

            # Show new steps
            for i, step in enumerate(trajectory[seen_steps:], start=seen_steps + 1):
                step_type = step.get("type", "unknown")

                if step_type == "reasoning":
                    text = step.get("summary", "")[:80]
                    console.print(f"  [magenta]💭[/] {text}...")

                elif step_type == "command":
                    cmd = step.get("command", "")
                    console.print(f"  [yellow]$[/] {cmd}")

                elif step_type == "tool_call":
                    tool = step.get("tool", "unknown")
                    console.print(f"  [cyan]🔧[/] {tool}(...)")

                elif step_type == "message":
                    text = step.get("summary", "")[:80]
                    console.print(f"  [green]💬[/] {text}...")

            seen_steps = len(trajectory)

            # Check if done
            if session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.KILLED):
                console.print(f"\n[dim]Session {session.status.value}. Final message:[/]")
                messages = manager.get_messages(session.id)
                for msg in reversed(messages):
                    if msg.role == "assistant":
                        console.print(f"  {msg.content[:200]}...")
                        break
                break

            time.sleep(1.0)

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/]")

    console.print()


def cmd_spawn(managers: dict, task: str, working_dir: Path, model: str, adapter: str | None = None):
    """
    Spawn a new session.

    Args:
        managers: Dict of adapter name -> session manager
        task: Task description
        working_dir: Working directory
        model: Model name or alias
        adapter: Adapter override (auto-detected from model if None)
    """
    from zwarm.core.registry import get_adapter_for_model, get_default_model, resolve_model

    # Auto-detect adapter from model if not specified
    if adapter is None:
        detected = get_adapter_for_model(model)
        if detected:
            adapter = detected
        else:
            # Default to codex if model not recognized
            adapter = "codex"

    # Resolve model alias to canonical name if needed
    model_info = resolve_model(model)
    effective_model = model_info.canonical if model_info else model

    # Get the right manager
    if adapter not in managers:
        console.print(f"  [red]Unknown adapter:[/] {adapter}")
        console.print(f"  [dim]Available: {', '.join(managers.keys())}[/]")
        return

    manager = managers[adapter]

    console.print(f"\n[dim]Spawning session...[/]")
    console.print(f"  [dim]Adapter:[/] {adapter}")
    console.print(f"  [dim]Model:[/] {effective_model}")
    console.print(f"  [dim]Dir:[/] {working_dir}")

    try:
        session = manager.start_session(
            task=task,
            working_dir=working_dir,
            model=effective_model,
            sandbox="workspace-write",
            source="user",
        )

        console.print(f"\n[green]✓[/] Session: [cyan]{session.short_id}[/]")
        console.print(f"  [dim]Use 'watch {session.short_id}' to follow progress[/]")
        console.print(f"  [dim]Use 'show {session.short_id}' when complete[/]")

    except Exception as e:
        console.print(f"  [red]Error:[/] {e}")


def cmd_continue(manager, session_id: str, message: str):
    """Continue a conversation."""
    from zwarm.sessions import SessionStatus

    session = manager.get_session(session_id)
    if not session:
        console.print(f"  [red]Session not found:[/] {session_id}")
        return

    if session.status == SessionStatus.RUNNING:
        console.print(f"  [yellow]Session still running - wait for it to complete[/]")
        return

    if session.status == SessionStatus.KILLED:
        console.print(f"  [red]Session was killed - start a new one[/]")
        return

    console.print(f"\n[dim]Injecting message into {session.short_id}...[/]")

    updated = manager.inject_message(session_id, message)
    if updated:
        console.print(f"[green]✓[/] Message sent (turn {updated.turn})")
        console.print(f"  [dim]Use 'watch {session.short_id}' to follow response[/]")
    else:
        console.print(f"  [red]Failed to inject message[/]")


def cmd_kill(manager, target: str):
    """
    Kill session(s).

    Args:
        target: Session ID or "all" to kill all running
    """
    from zwarm.sessions import SessionStatus

    if target.lower() == "all":
        # Kill all running
        sessions = manager.list_sessions(status=SessionStatus.RUNNING)
        if not sessions:
            console.print("  [dim]No running sessions[/]")
            return

        killed = 0
        for s in sessions:
            if manager.kill_session(s.id):
                killed += 1
                console.print(f"  [green]✓[/] Killed {s.short_id}")

        console.print(f"\n[green]Killed {killed} session(s)[/]")
    else:
        # Kill single session
        session = manager.get_session(target)
        if not session:
            console.print(f"  [red]Session not found:[/] {target}")
            return

        if manager.kill_session(session.id):
            console.print(f"[green]✓[/] Killed {session.short_id}")
        else:
            console.print(f"  [yellow]Session not running or already stopped[/]")


def cmd_rm(manager, target: str):
    """
    Delete session(s).

    Args:
        target: Session ID or "all" to delete all non-running
    """
    from zwarm.sessions import SessionStatus

    if target.lower() == "all":
        # Delete all non-running (completed, failed, killed)
        sessions = manager.list_sessions()
        to_delete = [s for s in sessions if s.status != SessionStatus.RUNNING]

        if not to_delete:
            console.print("  [dim]Nothing to delete[/]")
            return

        deleted = 0
        for s in to_delete:
            if manager.delete_session(s.id):
                deleted += 1

        console.print(f"[green]✓[/] Deleted {deleted} session(s)")
    else:
        # Delete single session
        session = manager.get_session(target)
        if not session:
            console.print(f"  [red]Session not found:[/] {target}")
            return

        if manager.delete_session(session.id):
            console.print(f"[green]✓[/] Deleted {session.short_id}")
        else:
            console.print(f"  [red]Failed to delete[/]")




# =============================================================================
# Main REPL
# =============================================================================


def run_interactive(
    working_dir: Path,
    model: str = "gpt-5.1-codex-mini",
):
    """
    Run the interactive REPL.

    Args:
        working_dir: Default working directory for sessions
        model: Default model for sessions
    """
    from zwarm.sessions import get_session_manager
    from zwarm.core.registry import get_adapter_for_model, list_adapters

    # Initialize managers for all adapters
    state_dir = working_dir / ".zwarm"
    managers = {}
    for adapter in list_adapters():
        try:
            managers[adapter] = get_session_manager(adapter, str(state_dir))
        except Exception:
            pass  # Adapter not available

    if not managers:
        console.print("[red]No adapters available. Run 'zwarm init' first.[/]")
        return

    # Primary manager for listing (aggregates across all adapters)
    primary_adapter = get_adapter_for_model(model) or "codex"
    if primary_adapter not in managers:
        primary_adapter = list(managers.keys())[0]

    # Setup prompt with autocomplete
    def get_sessions():
        # Aggregate sessions from all managers
        all_sessions = []
        for mgr in managers.values():
            all_sessions.extend(mgr.list_sessions())
        return all_sessions

    completer = SessionCompleter(get_sessions)
    style = Style.from_dict({
        "prompt": "cyan bold",
    })

    session = PromptSession(
        completer=completer,
        history=InMemoryHistory(),
        style=style,
        complete_while_typing=True,
    )

    # Welcome
    console.print("\n[bold cyan]zwarm interactive[/] - Session Manager\n")
    console.print(f"  [dim]Dir:[/] {working_dir.absolute()}")
    console.print(f"  [dim]Model:[/] {model}")
    console.print(f"  [dim]Adapters:[/] {', '.join(managers.keys())}")
    console.print(f"\n  Type [cyan]help[/] for commands, [cyan]models[/] to see available models.")
    console.print(f"  [dim]Tab to autocomplete session IDs[/]\n")

    # REPL
    while True:
        try:
            raw = session.prompt("> ").strip()
            if not raw:
                continue

            # Bang command: !cmd runs shell command
            if raw.startswith("!"):
                import subprocess
                shell_cmd = raw[1:].strip()
                if shell_cmd:
                    try:
                        result = subprocess.run(
                            shell_cmd,
                            shell=True,
                            cwd=working_dir,
                            capture_output=True,
                            text=True,
                        )
                        if result.stdout:
                            console.print(result.stdout.rstrip())
                        if result.stderr:
                            console.print(f"[red]{result.stderr.rstrip()}[/]")
                        if result.returncode != 0:
                            console.print(f"[dim](exit code: {result.returncode})[/]")
                    except Exception as e:
                        console.print(f"[red]Error:[/] {e}")
                continue

            try:
                parts = shlex.split(raw)
            except ValueError:
                parts = raw.split()

            cmd = parts[0].lower()
            args = parts[1:]

            # Helper to find session and return the correct manager for its adapter
            def find_session(sid: str):
                # First, find the session (any manager can load it)
                session = None
                for mgr in managers.values():
                    session = mgr.get_session(sid)
                    if session:
                        break

                if not session:
                    return None, None

                # Return the manager that matches the session's adapter
                adapter = getattr(session, "adapter", "codex")
                if adapter in managers:
                    return managers[adapter], session
                else:
                    # Fallback to whichever manager found it
                    return mgr, session

            # Dispatch
            if cmd in ("q", "quit", "exit"):
                console.print("\n[dim]Goodbye![/]\n")
                break

            elif cmd in ("h", "help"):
                cmd_help()

            elif cmd == "models":
                cmd_models()

            elif cmd in ("ls", "list"):
                # Aggregate sessions from all managers
                from zwarm.sessions import SessionStatus
                from zwarm.core.costs import estimate_session_cost, format_cost

                all_sessions = []
                for mgr in managers.values():
                    all_sessions.extend(mgr.list_sessions())

                if not all_sessions:
                    console.print("  [dim]No sessions. Use 'spawn \"task\"' to start one.[/]")
                else:
                    # Use first manager's cmd_ls logic but with aggregated sessions
                    cmd_ls_multi(all_sessions, managers)

            elif cmd in ("?", "peek"):
                if not args:
                    console.print("  [red]Usage:[/] peek ID")
                else:
                    mgr, _ = find_session(args[0])
                    if mgr:
                        cmd_peek(mgr, args[0])
                    else:
                        console.print(f"  [red]Session not found:[/] {args[0]}")

            elif cmd == "show":
                if not args:
                    console.print("  [red]Usage:[/] show ID [-v]")
                else:
                    verbose = "-v" in args or "--verbose" in args
                    sid = [a for a in args if not a.startswith("-")][0]
                    mgr, _ = find_session(sid)
                    if mgr:
                        cmd_show(mgr, sid, verbose=verbose)
                    else:
                        console.print(f"  [red]Session not found:[/] {sid}")

            elif cmd in ("traj", "trajectory"):
                if not args:
                    console.print("  [red]Usage:[/] traj ID [--full]")
                else:
                    full = "--full" in args
                    sid = [a for a in args if not a.startswith("-")][0]
                    mgr, _ = find_session(sid)
                    if mgr:
                        cmd_traj(mgr, sid, full=full)
                    else:
                        console.print(f"  [red]Session not found:[/] {sid}")

            elif cmd == "watch":
                if not args:
                    console.print("  [red]Usage:[/] watch ID")
                else:
                    mgr, _ = find_session(args[0])
                    if mgr:
                        cmd_watch(mgr, args[0])
                    else:
                        console.print(f"  [red]Session not found:[/] {args[0]}")

            elif cmd == "spawn":
                if not args:
                    console.print("  [red]Usage:[/] spawn \"task\" [--model M] [--adapter A]")
                else:
                    # Parse spawn args
                    task_parts = []
                    spawn_dir = working_dir
                    spawn_model = model
                    spawn_adapter = None
                    i = 0
                    while i < len(args):
                        if args[i] in ("--dir", "-d") and i + 1 < len(args):
                            spawn_dir = Path(args[i + 1])
                            i += 2
                        elif args[i] in ("--model", "-m") and i + 1 < len(args):
                            spawn_model = args[i + 1]
                            i += 2
                        elif args[i] in ("--adapter", "-a") and i + 1 < len(args):
                            spawn_adapter = args[i + 1]
                            i += 2
                        else:
                            task_parts.append(args[i])
                            i += 1

                    task = " ".join(task_parts)
                    if task:
                        cmd_spawn(managers, task, spawn_dir, spawn_model, spawn_adapter)
                    else:
                        console.print("  [red]Task required[/]")

            elif cmd in ("c", "continue"):
                if len(args) < 2:
                    console.print("  [red]Usage:[/] c ID \"message\"")
                else:
                    mgr, _ = find_session(args[0])
                    if mgr:
                        cmd_continue(mgr, args[0], " ".join(args[1:]))
                    else:
                        console.print(f"  [red]Session not found:[/] {args[0]}")

            elif cmd == "kill":
                if not args:
                    console.print("  [red]Usage:[/] kill ID | all")
                elif args[0].lower() == "all":
                    # Kill all running across all managers
                    killed = 0
                    for mgr in managers.values():
                        from zwarm.sessions import SessionStatus
                        for s in mgr.list_sessions(status=SessionStatus.RUNNING):
                            if mgr.kill_session(s.id):
                                killed += 1
                                console.print(f"  [green]✓[/] Killed {s.short_id}")
                    if killed:
                        console.print(f"\n[green]Killed {killed} session(s)[/]")
                    else:
                        console.print("  [dim]No running sessions[/]")
                else:
                    mgr, _ = find_session(args[0])
                    if mgr:
                        cmd_kill(mgr, args[0])
                    else:
                        console.print(f"  [red]Session not found:[/] {args[0]}")

            elif cmd in ("rm", "delete"):
                if not args:
                    console.print("  [red]Usage:[/] rm ID | all")
                elif args[0].lower() == "all":
                    # Delete all non-running across all managers
                    deleted = 0
                    for mgr in managers.values():
                        from zwarm.sessions import SessionStatus
                        for s in mgr.list_sessions():
                            if s.status != SessionStatus.RUNNING:
                                if mgr.delete_session(s.id):
                                    deleted += 1
                    if deleted:
                        console.print(f"[green]✓[/] Deleted {deleted} session(s)")
                    else:
                        console.print("  [dim]Nothing to delete[/]")
                else:
                    mgr, _ = find_session(args[0])
                    if mgr:
                        cmd_rm(mgr, args[0])
                    else:
                        console.print(f"  [red]Session not found:[/] {args[0]}")

            else:
                console.print(f"  [yellow]Unknown command:[/] {cmd}")
                console.print("  [dim]Type 'help' for commands[/]")

        except KeyboardInterrupt:
            console.print("\n[dim](Ctrl+C again or 'quit' to exit)[/]")
        except EOFError:
            console.print("\n[dim]Goodbye![/]\n")
            break
        except Exception as e:
            console.print(f"  [red]Error:[/] {e}")
