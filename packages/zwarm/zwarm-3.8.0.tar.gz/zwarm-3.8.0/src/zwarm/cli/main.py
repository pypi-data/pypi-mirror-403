"""
CLI for zwarm orchestration.

Commands:
- zwarm orchestrate: Start an orchestrator session
- zwarm exec: Run a single executor directly (for testing)
- zwarm status: Show current state
- zwarm history: Show event history
- zwarm configs: Manage configurations
"""

from __future__ import annotations

import asyncio
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Create console for rich output
console = Console()


def _resolve_task(task: str | None, task_file: Path | None) -> str | None:
    """
    Resolve task from multiple sources (priority order):
    1. --task flag
    2. --task-file flag
    3. stdin (if not a tty)
    """
    # Direct task takes priority
    if task:
        return task

    # Then file
    if task_file:
        if not task_file.exists():
            console.print(f"[red]Error:[/] Task file not found: {task_file}")
            raise typer.Exit(1)
        return task_file.read_text().strip()

    # Finally stdin (only if piped, not interactive)
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        if stdin_content:
            return stdin_content

    return None

# Main app with rich help
app = typer.Typer(
    name="zwarm",
    help="""
[bold cyan]zwarm[/] - Multi-Agent CLI Orchestration Research Platform

[bold]DESCRIPTION[/]
    Orchestrate multiple CLI coding agents (Codex, Claude Code) with
    delegation, conversation, and trajectory alignment (watchers).

[bold]QUICK START[/]
    [dim]# Initialize zwarm in your project[/]
    $ zwarm init

    [dim]# Run the orchestrator[/]
    $ zwarm orchestrate --task "Build a hello world function"

    [dim]# Check state after running[/]
    $ zwarm status

[bold]COMMANDS[/]
    [cyan]init[/]         Initialize zwarm (creates .zwarm/ with config)
    [cyan]reset[/]        Reset state and optionally config files
    [cyan]orchestrate[/]  Start orchestrator to delegate tasks to executors
    [cyan]pilot[/]        Conversational orchestrator REPL (interactive)
    [cyan]exec[/]         Run a single executor directly (for testing)
    [cyan]status[/]       Show current state (sessions, tasks, events)
    [cyan]history[/]      Show event history log
    [cyan]configs[/]      Manage configuration files

[bold]CONFIGURATION[/]
    Config lives in [cyan].zwarm/config.toml[/] (created by init).
    Use [cyan]--config[/] flag for YAML files.
    See [cyan]zwarm configs list[/] for available configurations.

[bold]ADAPTERS[/]
    [cyan]codex_mcp[/]    Codex via MCP server (sync conversations)
    [cyan]claude_code[/]  Claude Code CLI

[bold]WATCHERS[/] (trajectory aligners)
    [cyan]progress[/]     Detects stuck/spinning agents
    [cyan]budget[/]       Monitors step/session limits
    [cyan]scope[/]        Detects scope creep
    [cyan]pattern[/]      Custom regex pattern matching
    [cyan]quality[/]      Code quality checks
    """,
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=False,
)

# Configs subcommand group
configs_app = typer.Typer(
    name="configs",
    help="""
Manage zwarm configurations.

[bold]SUBCOMMANDS[/]
    [cyan]list[/]   List available configuration files
    [cyan]show[/]   Display a configuration file's contents
    """,
    rich_markup_mode="rich",
    no_args_is_help=True,
)
app.add_typer(configs_app, name="configs")


@app.command()
def orchestrate(
    task: Annotated[Optional[str], typer.Option("--task", "-t", help="The task to accomplish")] = None,
    task_file: Annotated[Optional[Path], typer.Option("--task-file", "-f", help="Read task from file")] = None,
    config: Annotated[Optional[Path], typer.Option("--config", "-c", help="Path to config YAML")] = None,
    overrides: Annotated[Optional[list[str]], typer.Option("--set", help="Override config (key=value)")] = None,
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
    resume: Annotated[bool, typer.Option("--resume", help="Resume from previous state")] = False,
    max_steps: Annotated[Optional[int], typer.Option("--max-steps", help="Maximum orchestrator steps")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed output")] = False,
    instance: Annotated[Optional[str], typer.Option("--instance", "-i", help="Instance ID (for isolation/resume)")] = None,
    instance_name: Annotated[Optional[str], typer.Option("--name", "-n", help="Human-readable instance name")] = None,
):
    """
    Start an orchestrator session.

    The orchestrator breaks down tasks and delegates to executor agents
    (Codex, Claude Code). It can have sync conversations or fire-and-forget
    async delegations.

    Each run creates an isolated instance to prevent conflicts when running
    multiple orchestrators in the same directory.

    [bold]Examples:[/]
        [dim]# Simple task[/]
        $ zwarm orchestrate --task "Add a logout button to the navbar"

        [dim]# Task from file[/]
        $ zwarm orchestrate -f task.md

        [dim]# Task from stdin[/]
        $ cat task.md | zwarm orchestrate
        $ zwarm orchestrate < task.md

        [dim]# With config file[/]
        $ zwarm orchestrate -c configs/base.yaml --task "Refactor auth"

        [dim]# Override settings[/]
        $ zwarm orchestrate --task "Fix bug" --set executor.adapter=claude_code

        [dim]# Named instance (easier to track)[/]
        $ zwarm orchestrate --task "Add tests" --name test-work

        [dim]# Resume a specific instance[/]
        $ zwarm orchestrate --resume --instance abc123

        [dim]# List all instances[/]
        $ zwarm instances
    """
    from zwarm.orchestrator import build_orchestrator

    # Resolve task from: --task, --task-file, or stdin
    resolved_task = _resolve_task(task, task_file)
    if not resolved_task:
        console.print("[red]Error:[/] No task provided. Use --task, --task-file, or pipe from stdin.")
        raise typer.Exit(1)

    task = resolved_task

    # Build overrides list
    override_list = list(overrides or [])
    if max_steps:
        override_list.append(f"orchestrator.max_steps={max_steps}")

    console.print(f"[bold]Starting orchestrator...[/]")
    console.print(f"  Task: {task}")
    console.print(f"  Working dir: {working_dir.absolute()}")
    if instance:
        console.print(f"  Instance: {instance}" + (f" ({instance_name})" if instance_name else ""))
    console.print()

    # Output handler to show orchestrator messages
    def output_handler(msg: str) -> None:
        if msg.strip():
            console.print(f"[dim][orchestrator][/] {msg}")

    orchestrator = None
    try:
        orchestrator = build_orchestrator(
            config_path=config,
            task=task,
            working_dir=working_dir.absolute(),
            overrides=override_list,
            resume=resume,
            output_handler=output_handler,
            instance_id=instance,
            instance_name=instance_name,
        )

        if resume:
            console.print("  [dim]Resuming from previous state...[/]")

        # Show instance ID if auto-generated
        if orchestrator.instance_id and not instance:
            console.print(f"  [dim]Instance: {orchestrator.instance_id[:8]}[/]")

        # Set up step callback for live progress display
        def step_callback(step_num: int, tool_results: list) -> None:
            """Print tool calls and results as they happen."""
            if not tool_results:
                return
            for tool_info, result in tool_results:
                name = tool_info.get("name", "?")
                # Truncate args for display
                args_str = str(tool_info.get("args", {}))
                if len(args_str) > 80:
                    args_str = args_str[:77] + "..."
                # Truncate result for display
                result_str = str(result)
                if len(result_str) > 100:
                    result_str = result_str[:97] + "..."
                console.print(f"[dim]step {step_num}[/] → [cyan]{name}[/]({args_str})")
                console.print(f"         └ {result_str}")

        orchestrator._step_callback = step_callback

        # Run the orchestrator loop
        console.print("[bold]--- Orchestrator running ---[/]\n")
        result = orchestrator.run(task=task)

        console.print(f"\n[bold green]--- Orchestrator finished ---[/]")
        console.print(f"  Steps: {result.get('steps', 'unknown')}")

        # Show exit message if any
        exit_msg = getattr(orchestrator, "_exit_message", "")
        if exit_msg:
            console.print(f"  Exit: {exit_msg[:200]}")

        # Save state for potential resume
        orchestrator.save_state()

        # Update instance status
        if orchestrator.instance_id:
            from zwarm.core.state import update_instance_status
            update_instance_status(
                orchestrator.instance_id,
                "completed",
                working_dir / ".zwarm",
            )
            console.print(f"  [dim]Instance {orchestrator.instance_id[:8]} marked completed[/]")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted.[/]")
        if orchestrator:
            orchestrator.save_state()
            console.print("[dim]State saved. Use --resume to continue.[/]")
            # Keep instance as "active" so it can be resumed
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/] {e}")
        if verbose:
            console.print_exception()
        # Update instance status to failed
        if orchestrator and orchestrator.instance_id:
            from zwarm.core.state import update_instance_status
            update_instance_status(
                orchestrator.instance_id,
                "failed",
                working_dir / ".zwarm",
            )
        sys.exit(1)


class PilotLM(str, Enum):
    """LM options for pilot mode."""
    gpt5_mini = "gpt5-mini"      # GPT5MiniTester - fast, cheap, good for testing
    gpt5 = "gpt5"                # GPT5Large - standard
    gpt5_verbose = "gpt5-verbose"  # GPT5LargeVerbose - with extended thinking


@app.command()
def pilot(
    task: Annotated[Optional[str], typer.Option("--task", "-t", help="Initial task (optional)")] = None,
    task_file: Annotated[Optional[Path], typer.Option("--task-file", "-f", help="Read task from file")] = None,
    config: Annotated[Optional[Path], typer.Option("--config", "-c", help="Path to config YAML")] = None,
    overrides: Annotated[Optional[list[str]], typer.Option("--set", help="Override config (key=value)")] = None,
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
    resume: Annotated[bool, typer.Option("--resume", help="Resume from previous state")] = False,
    instance: Annotated[Optional[str], typer.Option("--instance", "-i", help="Instance ID (for isolation/resume)")] = None,
    instance_name: Annotated[Optional[str], typer.Option("--name", "-n", help="Human-readable instance name")] = None,
    model: Annotated[PilotLM, typer.Option("--model", "-m", help="LM to use")] = PilotLM.gpt5_verbose,
):
    """
    Interactive conversational orchestrator REPL.

    Like 'orchestrate' but conversational: give instructions, watch the
    orchestrator work, course-correct in real-time, time-travel to checkpoints.

    [bold]Features:[/]
        - Streaming display of orchestrator thinking and tool calls
        - Turn-by-turn execution with checkpoints
        - Time travel (:goto T1) to return to previous states
        - Session visibility (:sessions) and state inspection (:state)

    [bold]Commands:[/]
        :help              Show help
        :history [N|all]   Show turn checkpoints
        :goto <turn|root>  Time travel (e.g., :goto T1)
        :state             Show orchestrator state
        :sessions          Show active executor sessions
        :reasoning on|off  Toggle reasoning display
        :quit              Exit

    [bold]LM Options:[/]
        gpt5-mini     GPT5MiniTester - fast/cheap, good for testing
        gpt5          GPT5Large - standard model
        gpt5-verbose  GPT5LargeVerbose - with extended thinking (default)

    [bold]Examples:[/]
        [dim]# Start fresh, give instructions interactively[/]
        $ zwarm pilot

        [dim]# Start with an initial task[/]
        $ zwarm pilot --task "Build user authentication"

        [dim]# Use faster model for testing[/]
        $ zwarm pilot --model gpt5-mini

        [dim]# Named instance[/]
        $ zwarm pilot --name my-feature

        [dim]# Resume a previous session[/]
        $ zwarm pilot --resume --instance abc123
    """
    from zwarm.cli.pilot import run_pilot, build_pilot_orchestrator

    # Resolve task (optional for pilot)
    resolved_task = _resolve_task(task, task_file)

    # Validate resume requirements
    if resume and not instance:
        console.print("[red]Error:[/] --resume requires --instance to specify which session to resume")
        console.print("  [dim]Use 'zwarm instances' to list available instances[/]")
        raise typer.Exit(1)

    console.print(f"[bold]{'Resuming' if resume else 'Starting'} pilot session...[/]")
    console.print(f"  Working dir: {working_dir.absolute()}")
    console.print(f"  Model: {model.value}")
    if resolved_task:
        console.print(f"  Initial task: {resolved_task[:60]}...")
    if instance:
        console.print(f"  Instance: {instance}" + (f" ({instance_name})" if instance_name else ""))
    if resume:
        console.print(f"  [yellow]Resuming from saved state...[/]")
    console.print()

    orchestrator = None
    try:
        orchestrator = build_pilot_orchestrator(
            config_path=config,
            working_dir=working_dir.absolute(),
            overrides=list(overrides or []),
            instance_id=instance,
            instance_name=instance_name,
            lm_choice=model.value,
        )

        # Show instance ID if auto-generated
        if orchestrator.instance_id and not instance:
            console.print(f"  [dim]Instance: {orchestrator.instance_id[:8]}[/]")

        # Resume from saved state if requested
        if resume:
            orchestrator.load_state()
            msg_count = len(orchestrator.messages)
            console.print(f"  [green]✓[/] Resumed with {msg_count} messages")

        # Run the pilot REPL
        run_pilot(orchestrator, initial_task=resolved_task)

        # Save state on exit
        orchestrator.save_state()
        console.print("\n[dim]State saved.[/]")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted.[/]")
        if orchestrator:
            orchestrator.save_state()
            console.print("[dim]State saved.[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@app.command()
def exec(
    task: Annotated[str, typer.Option("--task", "-t", help="Task to execute")],
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
    model: Annotated[Optional[str], typer.Option("--model", help="Model override")] = None,
    wait: Annotated[bool, typer.Option("--wait", help="Wait for completion and show result")] = False,
):
    """
    Run a single Codex session directly (for testing).

    Spawns a session using CodexSessionManager - same as interactive/pilot.
    Web search is always enabled via .codex/config.toml (set up by `zwarm init`).

    [bold]Examples:[/]
        [dim]# Quick test[/]
        $ zwarm exec --task "What is 2+2?" --wait

        [dim]# Run in background[/]
        $ zwarm exec --task "Build feature"

        [dim]# Web search is always available[/]
        $ zwarm exec --task "Find latest FastAPI docs" --wait
    """
    import time
    from zwarm.sessions import CodexSessionManager, SessionStatus

    console.print(f"[bold]Running Codex session...[/]")
    console.print(f"  Task: {task[:60]}{'...' if len(task) > 60 else ''}")
    if model:
        console.print(f"  Model: {model}")

    manager = CodexSessionManager(working_dir / ".zwarm")
    effective_model = model or "gpt-5.1-codex-mini"

    session = manager.start_session(
        task=task,
        working_dir=working_dir.absolute(),
        model=effective_model,
    )

    console.print(f"\n[green]Session started:[/] {session.short_id}")

    if wait:
        console.print("[dim]Waiting for completion...[/]")
        while True:
            time.sleep(2)
            session = manager.get_session(session.id)
            if session.status != SessionStatus.RUNNING:
                break

        if session.status == SessionStatus.COMPLETED:
            console.print(f"\n[green]✓ Completed[/]")
            # Show last assistant message
            for msg in reversed(session.messages):
                if msg.role == "assistant":
                    console.print(f"\n[bold]Response:[/]\n{msg.content}")
                    break
        else:
            console.print(f"\n[red]Status:[/] {session.status.value}")
            if session.error:
                console.print(f"[red]Error:[/] {session.error}")
    else:
        console.print("[dim]Running in background. Check with:[/]")
        console.print(f"  zwarm sessions")
        console.print(f"  zwarm session show {session.short_id}")


@app.command()
def status(
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
):
    """
    Show current state (sessions, tasks, events).

    Displays active sessions, pending tasks, and recent events
    from the .zwarm state directory.

    [bold]Example:[/]
        $ zwarm status
    """
    from zwarm.core.state import StateManager

    state_dir = working_dir / ".zwarm"
    if not state_dir.exists():
        console.print("[yellow]No zwarm state found in this directory.[/]")
        console.print("[dim]Run 'zwarm orchestrate' to start.[/]")
        return

    state = StateManager(state_dir)
    state.load()

    # Sessions table
    sessions = state.list_sessions()
    console.print(f"\n[bold]Sessions[/] ({len(sessions)})")
    if sessions:
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="dim")
        table.add_column("Mode")
        table.add_column("Status")
        table.add_column("Task")

        for s in sessions:
            status_style = {"active": "green", "completed": "blue", "failed": "red"}.get(s.status.value, "white")
            table.add_row(
                s.id[:8],
                s.mode.value,
                f"[{status_style}]{s.status.value}[/]",
                s.task_description[:50] + "..." if len(s.task_description) > 50 else s.task_description,
            )
        console.print(table)
    else:
        console.print("  [dim](none)[/]")

    # Tasks table
    tasks = state.list_tasks()
    console.print(f"\n[bold]Tasks[/] ({len(tasks)})")
    if tasks:
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="dim")
        table.add_column("Status")
        table.add_column("Description")

        for t in tasks:
            status_style = {"pending": "yellow", "in_progress": "cyan", "completed": "green", "failed": "red"}.get(t.status.value, "white")
            table.add_row(
                t.id[:8],
                f"[{status_style}]{t.status.value}[/]",
                t.description[:50] + "..." if len(t.description) > 50 else t.description,
            )
        console.print(table)
    else:
        console.print("  [dim](none)[/]")

    # Recent events
    events = state.get_events(limit=5)
    console.print(f"\n[bold]Recent Events[/]")
    if events:
        for e in events:
            console.print(f"  [dim]{e.timestamp.strftime('%H:%M:%S')}[/] {e.kind}")
    else:
        console.print("  [dim](none)[/]")


@app.command()
def instances(
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
    all_instances: Annotated[bool, typer.Option("--all", "-a", help="Show all instances (including completed)")] = False,
):
    """
    List all orchestrator instances.

    Shows instances that have been run in this directory. Use --all to include
    completed instances.

    [bold]Examples:[/]
        [dim]# List active instances[/]
        $ zwarm instances

        [dim]# List all instances[/]
        $ zwarm instances --all
    """
    from zwarm.core.state import list_instances as get_instances

    state_dir = working_dir / ".zwarm"
    all_inst = get_instances(state_dir)

    if not all_inst:
        console.print("[dim]No instances found.[/]")
        console.print("[dim]Run 'zwarm orchestrate' to start a new instance.[/]")
        return

    # Filter if not showing all
    if not all_instances:
        all_inst = [i for i in all_inst if i.get("status") == "active"]

    if not all_inst:
        console.print("[dim]No active instances. Use --all to see completed ones.[/]")
        return

    console.print(f"[bold]Instances[/] ({len(all_inst)} total)\n")

    for inst in all_inst:
        status = inst.get("status", "unknown")
        status_icon = {"active": "[green]●[/]", "completed": "[dim]✓[/]", "failed": "[red]✗[/]"}.get(status, "[dim]?[/]")

        inst_id = inst.get("id", "unknown")[:8]
        name = inst.get("name", "")
        task = (inst.get("task") or "")[:60]
        updated = inst.get("updated_at", "")[:19] if inst.get("updated_at") else ""

        console.print(f"  {status_icon} [bold]{inst_id}[/]" + (f" ({name})" if name and name != inst_id else ""))
        if task:
            console.print(f"      [dim]{task}[/]")
        if updated:
            console.print(f"      [dim]Updated: {updated}[/]")
        console.print()

    console.print("[dim]Use --instance <id> with 'orchestrate --resume' to resume an instance.[/]")


@app.command()
def history(
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
    kind: Annotated[Optional[str], typer.Option("--kind", "-k", help="Filter by event kind")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Number of events")] = 20,
):
    """
    Show event history.

    Displays the append-only event log with timestamps and details.

    [bold]Examples:[/]
        [dim]# Show last 20 events[/]
        $ zwarm history

        [dim]# Show more events[/]
        $ zwarm history --limit 50

        [dim]# Filter by kind[/]
        $ zwarm history --kind session_started
    """
    from zwarm.core.state import StateManager

    state_dir = working_dir / ".zwarm"
    if not state_dir.exists():
        console.print("[yellow]No zwarm state found.[/]")
        return

    state = StateManager(state_dir)
    events = state.get_events(kind=kind, limit=limit)

    console.print(f"\n[bold]Event History[/] (last {limit})\n")

    if not events:
        console.print("[dim]No events found.[/]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Time", style="dim")
    table.add_column("Event")
    table.add_column("Session/Task")
    table.add_column("Details")

    for e in events:
        details = ""
        if e.payload:
            details = ", ".join(f"{k}={str(v)[:30]}" for k, v in list(e.payload.items())[:2])

        table.add_row(
            e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            e.kind,
            (e.session_id or e.task_id or "-")[:8],
            details[:60],
        )

    console.print(table)


@configs_app.command("list")
def configs_list(
    config_dir: Annotated[Optional[Path], typer.Option("--dir", "-d", help="Directory to search")] = None,
):
    """
    List available agent/experiment configuration files (YAML).

    Note: config.toml is for user environment settings and is loaded
    automatically - use YAML files for agent configurations.

    [bold]Example:[/]
        $ zwarm configs list
    """
    search_dirs = [
        config_dir or Path.cwd(),
        Path.cwd() / "configs",
        Path.cwd() / ".zwarm",
    ]

    console.print("\n[bold]Available Configurations[/]\n")
    found = False

    for d in search_dirs:
        if not d.exists():
            continue
        for pattern in ["*.yaml", "*.yml"]:
            for f in d.glob(pattern):
                found = True
                try:
                    rel = f.relative_to(Path.cwd())
                    console.print(f"  [cyan]{rel}[/]")
                except ValueError:
                    console.print(f"  [cyan]{f}[/]")

    if not found:
        console.print("  [dim]No configuration files found.[/]")
        console.print("\n  [dim]Create a YAML config in configs/ to get started.[/]")

    # Check for config.toml and mention it (check both locations)
    new_config = Path.cwd() / ".zwarm" / "config.toml"
    legacy_config = Path.cwd() / "config.toml"
    if new_config.exists():
        console.print(f"\n[dim]Environment: .zwarm/config.toml (loaded automatically)[/]")
    elif legacy_config.exists():
        console.print(f"\n[dim]Environment: config.toml (legacy location, loaded automatically)[/]")


@configs_app.command("show")
def configs_show(
    config_path: Annotated[Path, typer.Argument(help="Path to configuration file")],
):
    """
    Show a configuration file's contents.

    Loads and displays the resolved configuration including
    any inherited values from 'extends:' directives.

    [bold]Example:[/]
        $ zwarm configs show configs/base.yaml
    """
    from zwarm.core.config import load_config
    import json

    if not config_path.exists():
        console.print(f"[red]File not found:[/] {config_path}")
        raise typer.Exit(1)

    try:
        config = load_config(config_path=config_path)
        console.print(f"\n[bold]Configuration:[/] {config_path}\n")
        console.print_json(json.dumps(config.to_dict(), indent=2))
    except Exception as e:
        console.print(f"[red]Error loading config:[/] {e}")
        raise typer.Exit(1)


@app.command()
def init(
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
    non_interactive: Annotated[bool, typer.Option("--yes", "-y", help="Accept defaults, no prompts")] = False,
    with_project: Annotated[bool, typer.Option("--with-project", help="Create zwarm.yaml project config")] = False,
):
    """
    Initialize zwarm in the current directory.

    Creates configuration files and the .zwarm state directory.
    Run this once per project to set up zwarm.

    [bold]Creates:[/]
        [cyan].zwarm/[/]              State directory for sessions and events
        [cyan].zwarm/config.toml[/]   Runtime settings (weave, adapter, watchers)
        [cyan].zwarm/codex.toml[/]    Codex CLI settings (model, web search, etc.)
        [cyan]zwarm.yaml[/]           Project config (optional, with --with-project)

    [bold]Configuration relationship:[/]
        config.toml   → Controls zwarm itself (tracing, which watchers run)
        codex.toml    → Codex settings, parsed by zwarm and passed via -c overrides
        zwarm.yaml    → Project-specific context injected into orchestrator

    [bold]Examples:[/]
        [dim]# Interactive setup[/]
        $ zwarm init

        [dim]# Quick setup with defaults[/]
        $ zwarm init --yes

        [dim]# Full setup with project config[/]
        $ zwarm init --with-project
    """
    console.print("\n[bold cyan]zwarm init[/] - Initialize zwarm configuration\n")

    state_dir = working_dir / ".zwarm"
    config_toml_path = state_dir / "config.toml"
    zwarm_yaml_path = working_dir / "zwarm.yaml"

    # Check for existing config (also check old location for migration)
    old_config_path = working_dir / "config.toml"
    if old_config_path.exists() and not config_toml_path.exists():
        console.print(f"[yellow]Note:[/] Found config.toml in project root.")
        console.print(f"  Config now lives in .zwarm/config.toml")
        if not non_interactive:
            migrate = typer.confirm("  Move to new location?", default=True)
            if migrate:
                state_dir.mkdir(parents=True, exist_ok=True)
                old_config_path.rename(config_toml_path)
                console.print(f"  [green]✓[/] Moved config.toml to .zwarm/")

    # Check for existing files
    if config_toml_path.exists():
        console.print(f"[yellow]Warning:[/] .zwarm/config.toml already exists")
        if not non_interactive:
            overwrite = typer.confirm("Overwrite?", default=False)
            if not overwrite:
                console.print("[dim]Skipping config.toml[/]")
                config_toml_path = None
        else:
            config_toml_path = None

    # Gather settings
    weave_project = ""
    adapter = "codex_mcp"
    watchers_enabled = ["progress", "budget", "delegation", "delegation_reminder"]
    create_project_config = with_project
    project_description = ""
    project_context = ""
    # Codex settings
    codex_model = "gpt-5.1-codex-mini"
    codex_reasoning = "high"

    if not non_interactive:
        console.print("[bold]Configuration[/]\n")

        # Weave project
        weave_project = typer.prompt(
            "  Weave project (entity/project, blank to skip)",
            default="",
            show_default=False,
        )

        # Adapter
        adapter = typer.prompt(
            "  Default adapter",
            default="codex_mcp",
            type=str,
        )

        # Codex model settings
        console.print("\n  [bold]Codex Model Settings[/] (.zwarm/codex.toml)")
        console.print("  [dim]These control the underlying Codex CLI that runs executor sessions[/]\n")

        console.print("  Available models:")
        console.print("    [cyan]1[/] gpt-5.1-codex-mini  [dim]- Fast, cheap, good for most tasks (Recommended)[/]")
        console.print("    [cyan]2[/] gpt-5.1-codex       [dim]- Balanced speed and capability[/]")
        console.print("    [cyan]3[/] gpt-5.1-codex-max   [dim]- Most capable, 400k context, expensive[/]")

        model_choice = typer.prompt(
            "  Select model (1-3)",
            default="1",
            type=str,
        )
        model_map = {
            "1": "gpt-5.1-codex-mini",
            "2": "gpt-5.1-codex",
            "3": "gpt-5.1-codex-max",
        }
        codex_model = model_map.get(model_choice, model_choice)
        if model_choice not in model_map:
            console.print(f"    [dim]Using custom model: {codex_model}[/]")

        console.print("\n  Reasoning effort (how much the model \"thinks\" before responding):")
        console.print("    [cyan]1[/] low     [dim]- Minimal reasoning, fastest responses[/]")
        console.print("    [cyan]2[/] medium  [dim]- Balanced reasoning[/]")
        console.print("    [cyan]3[/] high    [dim]- Maximum reasoning, best for complex tasks (Recommended)[/]")

        reasoning_choice = typer.prompt(
            "  Select reasoning effort (1-3)",
            default="3",
            type=str,
        )
        reasoning_map = {"1": "low", "2": "medium", "3": "high"}
        codex_reasoning = reasoning_map.get(reasoning_choice, "high")

        # Watchers
        console.print("\n  [bold]Watchers[/] (trajectory aligners)")
        available_watchers = ["progress", "budget", "delegation", "delegation_reminder", "scope", "pattern", "quality"]
        watchers_enabled = []
        for w in available_watchers:
            default = w in ["progress", "budget", "delegation", "delegation_reminder"]
            if typer.confirm(f"    Enable {w}?", default=default):
                watchers_enabled.append(w)

        # Project config
        console.print()
        create_project_config = typer.confirm(
            "  Create zwarm.yaml project config?",
            default=with_project,
        )

        if create_project_config:
            project_description = typer.prompt(
                "    Project description",
                default="",
                show_default=False,
            )
            console.print("    [dim]Project context (optional, press Enter twice to finish):[/]")
            context_lines = []
            while True:
                line = typer.prompt("    ", default="", show_default=False)
                if not line:
                    break
                context_lines.append(line)
            project_context = "\n".join(context_lines)

    # Create .zwarm directory
    console.print("\n[bold]Creating files...[/]\n")

    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "sessions").mkdir(exist_ok=True)
    (state_dir / "orchestrator").mkdir(exist_ok=True)
    console.print(f"  [green]✓[/] Created .zwarm/")

    # Create config.toml inside .zwarm/
    if config_toml_path:
        toml_content = _generate_config_toml(
            weave_project=weave_project,
            adapter=adapter,
            watchers=watchers_enabled,
        )
        config_toml_path.write_text(toml_content)
        console.print(f"  [green]✓[/] Created .zwarm/config.toml")

    # Create codex.toml for isolated codex configuration
    codex_toml_path = state_dir / "codex.toml"
    write_codex_toml = True
    if codex_toml_path.exists():
        if not non_interactive:
            overwrite_codex = typer.confirm("  .zwarm/codex.toml exists. Overwrite?", default=False)
            if not overwrite_codex:
                write_codex_toml = False
                console.print("  [dim]Skipping codex.toml[/]")
        else:
            write_codex_toml = False  # Don't overwrite in non-interactive mode

    if write_codex_toml:
        codex_content = _generate_codex_toml(model=codex_model, reasoning_effort=codex_reasoning)
        codex_toml_path.write_text(codex_content)
        console.print(f"  [green]✓[/] Created .zwarm/codex.toml")

    # Create claude.toml for isolated Claude Code configuration
    claude_toml_path = state_dir / "claude.toml"
    write_claude_toml = True
    if claude_toml_path.exists():
        if not non_interactive:
            overwrite_claude = typer.confirm("  .zwarm/claude.toml exists. Overwrite?", default=False)
            if not overwrite_claude:
                write_claude_toml = False
                console.print("  [dim]Skipping claude.toml[/]")
        else:
            write_claude_toml = False  # Don't overwrite in non-interactive mode

    if write_claude_toml:
        claude_content = _generate_claude_toml(model="sonnet")
        claude_toml_path.write_text(claude_content)
        console.print(f"  [green]✓[/] Created .zwarm/claude.toml")

    # Create zwarm.yaml
    if create_project_config:
        if zwarm_yaml_path.exists() and not non_interactive:
            overwrite = typer.confirm("  zwarm.yaml exists. Overwrite?", default=False)
            if not overwrite:
                create_project_config = False

        if create_project_config:
            yaml_content = _generate_zwarm_yaml(
                description=project_description,
                context=project_context,
                watchers=watchers_enabled,
            )
            zwarm_yaml_path.write_text(yaml_content)
            console.print(f"  [green]✓[/] Created zwarm.yaml")

    # Summary
    console.print("\n[bold green]Done![/] zwarm is ready.\n")

    # Explain config files
    console.print("[bold]Configuration files:[/]")
    console.print("  [cyan].zwarm/config.toml[/]  - Runtime settings (Weave tracing, watchers)")
    console.print("  [cyan].zwarm/codex.toml[/]   - Codex CLI settings (model, web search, sandbox)")
    if create_project_config:
        console.print("  [cyan]zwarm.yaml[/]          - Project context and constraints")
    console.print()
    console.print("  [dim]Edit these files to customize behavior. Run 'zwarm init' again to reconfigure.[/]\n")

    console.print("[bold]Next steps:[/]")
    console.print("  [dim]# Run the orchestrator[/]")
    console.print("  $ zwarm orchestrate --task \"Your task here\"\n")
    console.print("  [dim]# Or test an executor directly[/]")
    console.print("  $ zwarm exec --task \"What is 2+2?\"\n")
    console.print("  [dim]# Interactive session management[/]")
    console.print("  $ zwarm interactive\n")


def _generate_config_toml(
    weave_project: str = "",
    adapter: str = "codex_mcp",
    watchers: list[str] | None = None,
) -> str:
    """Generate config.toml content with all options at their defaults."""
    watchers = watchers or []

    lines = [
        "# zwarm configuration",
        "# Generated by 'zwarm init'",
        "# All values shown are defaults - uncomment and modify as needed",
        "",
        "# ============================================================================",
        "# Weave Integration (optional tracing/observability)",
        "# ============================================================================",
        "[weave]",
    ]

    if weave_project:
        lines.append(f'project = "{weave_project}"')
    else:
        lines.append('# project = "your-entity/your-project"  # Uncomment to enable Weave tracing')

    lines.extend([
        "enabled = true",
        "",
        "# ============================================================================",
        "# Orchestrator Settings",
        "# ============================================================================",
        "[orchestrator]",
        '# lm = "gpt-5-mini"                    # LLM for orchestrator (gpt-5-mini, gpt-5, claude-sonnet-4)',
        "max_steps = 50                         # Max steps for orchestrate command",
        "max_steps_per_turn = 60                # Max steps per turn in pilot mode",
        "parallel_delegations = 4               # Max concurrent delegations",
        '# prompt = "path/to/prompt.yaml"       # Custom prompt file (optional)',
        '# allowed_dirs = ["*"]                 # Directories agent can delegate to (default: working_dir only)',
        "",
        "# Context window compaction (prevents overflow on long tasks)",
        "[orchestrator.compaction]",
        "enabled = true",
        "max_tokens = 100000                    # Trigger compaction above this",
        "threshold_pct = 0.85                   # Compact when at this % of max_tokens",
        "target_pct = 0.7                       # Target this % after compaction",
        "keep_first_n = 2                       # Always keep first N messages (system + task)",
        "keep_last_n = 10                       # Always keep last N messages (recent context)",
        "",
        "# ============================================================================",
        "# Executor Settings (codex agent configuration)",
        "# ============================================================================",
        "[executor]",
        f'adapter = "{adapter}"                  # codex_mcp | codex_exec | claude_code',
        '# model = "gpt-5.1-codex-mini"         # Model for delegated sessions (uses codex.toml default if not set)',
        'sandbox = "workspace-write"            # read-only | workspace-write | danger-full-access',
        "timeout = 3600                         # Session timeout in seconds",
        'reasoning_effort = "high"              # low | medium | high',
        "",
        "# ============================================================================",
        "# Watchers (automated monitoring and nudges)",
        "# ============================================================================",
        "[watchers]",
        f"enabled = {str(bool(watchers)).lower()}",
        'message_role = "user"                  # Role for nudge messages: user | assistant | system',
        "",
        "# Default watchers: progress, budget, delegation_reminder",
        "# Uncomment below to customize:",
        "",
        "# [[watchers.watchers]]",
        '# name = "progress"',
        "# enabled = true",
        "",
        "# [[watchers.watchers]]",
        '# name = "budget"',
        "# enabled = true",
        "# [watchers.watchers.config]",
        "# max_sessions = 10",
        "# warn_at_percent = 80",
        "",
        "# [[watchers.watchers]]",
        '# name = "delegation_reminder"',
        "# enabled = true",
        "",
        "# ============================================================================",
        "# State Directory",
        "# ============================================================================",
        '# state_dir = ".zwarm"                 # Where to store session data',
        "",
    ])

    return "\n".join(lines)


def _generate_codex_toml(
    model: str = "gpt-5.1-codex-mini",
    reasoning_effort: str = "high",
) -> str:
    """
    Generate codex.toml for isolated codex configuration.

    This file is parsed by zwarm and settings are passed to codex via -c overrides.
    Each .zwarm directory has its own codex config, independent of ~/.codex/config.toml.
    """
    lines = [
        "# Codex configuration for zwarm",
        "# zwarm parses this file and passes settings to codex via -c overrides",
        "# Each .zwarm dir has its own config, independent of ~/.codex/config.toml",
        "# Generated by 'zwarm init'",
        "",
        "# Model settings",
        f'model = "{model}"',
        f'model_reasoning_effort = "{reasoning_effort}"  # low | medium | high',
        "",
        "# DANGER MODE - bypasses all safety controls",
        "# Set to true to use --dangerously-bypass-approvals-and-sandbox",
        "full_danger = true",
        "",
        "# Web search - enables web_search tool for agents",
        "[features]",
        "web_search_request = true",
        "",
        "# Sandbox settings - network access required for web search",
        "[sandbox_workspace_write]",
        "network_access = true",
        "",
        "# Approval policy - 'never' means no human approval needed",
        "# approval_policy = \"never\"",
        "",
        "# You can add any codex config key here",
        "# See: https://github.com/openai/codex#configuration",
        "",
    ]
    return "\n".join(lines)


def _generate_claude_toml(
    model: str = "sonnet",
) -> str:
    """
    Generate claude.toml for isolated Claude Code configuration.

    This file is parsed by zwarm and settings are passed to claude via CLI flags.
    Each .zwarm directory has its own claude config.
    """
    lines = [
        "# Claude Code configuration for zwarm",
        "# zwarm parses this file and passes settings to claude via CLI flags",
        "# Each .zwarm dir has its own config",
        "# Generated by 'zwarm init'",
        "",
        "# Model settings",
        f'model = "{model}"  # sonnet | opus | haiku',
        "",
        "# DANGER MODE - bypasses all permission checks",
        "# Set to true to use --dangerously-skip-permissions",
        "full_danger = true",
        "",
        "# Note: Claude Code uses different CLI flags than Codex",
        "# Common options:",
        "#   --model <model>         Model to use (sonnet, opus, haiku)",
        "#   --add-dir <path>        Additional directories to allow",
        "#   --allowed-tools <tools> Restrict available tools",
        "",
    ]
    return "\n".join(lines)


def _generate_zwarm_yaml(
    description: str = "",
    context: str = "",
    watchers: list[str] | None = None,
) -> str:
    """Generate zwarm.yaml project config."""
    watchers = watchers or []

    lines = [
        "# zwarm project configuration",
        "# Customize the orchestrator for this specific project",
        "",
        f'description: "{description}"' if description else 'description: ""',
        "",
        "# Project-specific context injected into the orchestrator",
        "# This helps the orchestrator understand your codebase",
        "context: |",
    ]

    if context:
        for line in context.split("\n"):
            lines.append(f"  {line}")
    else:
        lines.extend([
            "  # Describe your project here. For example:",
            "  # - Tech stack (FastAPI, React, PostgreSQL)",
            "  # - Key directories (src/api/, src/components/)",
            "  # - Coding conventions to follow",
        ])

    lines.extend([
        "",
        "# Project-specific constraints",
        "# The orchestrator will be reminded to follow these",
        "constraints:",
        "  # - \"Never modify migration files directly\"",
        "  # - \"All new endpoints need tests\"",
        "  # - \"Use existing patterns from src/api/\"",
        "",
        "# Default watchers for this project",
        "watchers:",
    ])

    for w in watchers:
        lines.append(f"  - {w}")

    if not watchers:
        lines.append("  # - progress")
        lines.append("  # - budget")

    lines.append("")

    return "\n".join(lines)


@app.command()
def reset(
    working_dir: Annotated[Path, typer.Option("--working-dir", "-w", help="Working directory")] = Path("."),
    state: Annotated[bool, typer.Option("--state", "-s", help="Reset .zwarm/ state directory")] = True,
    config: Annotated[bool, typer.Option("--config", "-c", help="Also delete config.toml")] = False,
    project: Annotated[bool, typer.Option("--project", "-p", help="Also delete zwarm.yaml")] = False,
    all_files: Annotated[bool, typer.Option("--all", "-a", help="Delete everything (state + config + project)")] = False,
    force: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
):
    """
    Reset zwarm state and optionally configuration files.

    By default, only clears the .zwarm/ state directory (sessions, events, orchestrator history).
    Use flags to also remove configuration files.

    [bold]Examples:[/]
        [dim]# Reset state only (default)[/]
        $ zwarm reset

        [dim]# Reset everything, no confirmation[/]
        $ zwarm reset --all --yes

        [dim]# Reset state and config.toml[/]
        $ zwarm reset --config
    """
    import shutil

    console.print("\n[bold cyan]zwarm reset[/] - Reset zwarm state\n")

    state_dir = working_dir / ".zwarm"
    config_toml_path = state_dir / "config.toml"  # New location
    old_config_toml_path = working_dir / "config.toml"  # Legacy location
    zwarm_yaml_path = working_dir / "zwarm.yaml"

    # Expand --all flag
    if all_files:
        state = True
        config = True
        project = True

    # Collect what will be deleted
    to_delete = []
    if state and state_dir.exists():
        to_delete.append((".zwarm/", state_dir))
    # Config: check both new and legacy locations (but skip if state already deletes it)
    if config and not state:
        if config_toml_path.exists():
            to_delete.append((".zwarm/config.toml", config_toml_path))
        if old_config_toml_path.exists():
            to_delete.append(("config.toml (legacy)", old_config_toml_path))
    if project and zwarm_yaml_path.exists():
        to_delete.append(("zwarm.yaml", zwarm_yaml_path))

    if not to_delete:
        console.print("[yellow]Nothing to reset.[/] No matching files found.")
        raise typer.Exit(0)

    # Show what will be deleted
    console.print("[bold]Will delete:[/]")
    for name, path in to_delete:
        if path.is_dir():
            # Count contents
            files = list(path.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            console.print(f"  [red]✗[/] {name} ({file_count} files)")
        else:
            console.print(f"  [red]✗[/] {name}")

    # Confirm
    if not force:
        console.print()
        confirm = typer.confirm("Proceed with reset?", default=False)
        if not confirm:
            console.print("[dim]Aborted.[/]")
            raise typer.Exit(0)

    # Delete
    console.print("\n[bold]Deleting...[/]")
    for name, path in to_delete:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            console.print(f"  [green]✓[/] Deleted {name}")
        except Exception as e:
            console.print(f"  [red]✗[/] Failed to delete {name}: {e}")

    console.print("\n[bold green]Reset complete.[/]")
    console.print("\n[dim]Run 'zwarm init' to set up again.[/]\n")


@app.command()
def clean(
    force: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Show what would be killed without killing")] = False,
):
    """
    Clean up orphaned processes from zwarm sessions.

    Finds and kills:
    - Orphaned codex mcp-server processes
    - Orphaned codex exec processes
    - Orphaned claude CLI processes

    [bold]Examples:[/]
        [dim]# See what would be cleaned[/]
        $ zwarm clean --dry-run

        [dim]# Clean without confirmation[/]
        $ zwarm clean --yes
    """
    import subprocess
    import signal

    console.print("\n[bold cyan]zwarm clean[/] - Clean up orphaned processes\n")

    # Patterns to search for
    patterns = [
        ("codex mcp-server", "Codex MCP server"),
        ("codex exec", "Codex exec"),
        ("claude.*--permission-mode", "Claude CLI"),
    ]

    found_processes = []

    for pattern, description in patterns:
        try:
            # Use pgrep to find matching processes
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    pid = pid.strip()
                    if pid and pid.isdigit():
                        # Get process info
                        try:
                            ps_result = subprocess.run(
                                ["ps", "-p", pid, "-o", "pid,ppid,etime,command"],
                                capture_output=True,
                                text=True,
                            )
                            if ps_result.returncode == 0:
                                lines = ps_result.stdout.strip().split("\n")
                                if len(lines) > 1:
                                    # Skip header, get process line
                                    proc_info = lines[1].strip()
                                    found_processes.append((int(pid), description, proc_info))
                        except Exception:
                            found_processes.append((int(pid), description, "(unknown)"))
        except FileNotFoundError:
            # pgrep not available, try ps with grep
            try:
                result = subprocess.run(
                    f"ps aux | grep '{pattern}' | grep -v grep",
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            if pid.isdigit():
                                found_processes.append((int(pid), description, line[:80]))
            except Exception:
                pass
        except Exception as e:
            console.print(f"[yellow]Warning:[/] Error searching for {description}: {e}")

    if not found_processes:
        console.print("[green]No orphaned processes found.[/] Nothing to clean.\n")
        raise typer.Exit(0)

    # Show what was found
    console.print(f"[bold]Found {len(found_processes)} process(es):[/]\n")
    for pid, description, info in found_processes:
        console.print(f"  [yellow]PID {pid}[/] - {description}")
        console.print(f"    [dim]{info[:100]}{'...' if len(info) > 100 else ''}[/]")

    if dry_run:
        console.print("\n[dim]Dry run - no processes killed.[/]\n")
        raise typer.Exit(0)

    # Confirm
    if not force:
        console.print()
        confirm = typer.confirm(f"Kill {len(found_processes)} process(es)?", default=False)
        if not confirm:
            console.print("[dim]Aborted.[/]")
            raise typer.Exit(0)

    # Kill processes
    console.print("\n[bold]Cleaning up...[/]")
    killed = 0
    failed = 0

    for pid, description, _ in found_processes:
        try:
            # First try SIGTERM
            os.kill(pid, signal.SIGTERM)
            console.print(f"  [green]✓[/] Killed PID {pid} ({description})")
            killed += 1
        except ProcessLookupError:
            console.print(f"  [dim]○[/] PID {pid} already gone")
        except PermissionError:
            console.print(f"  [red]✗[/] PID {pid} - permission denied (try sudo)")
            failed += 1
        except Exception as e:
            console.print(f"  [red]✗[/] PID {pid} - {e}")
            failed += 1

    console.print(f"\n[bold green]Cleanup complete.[/] Killed {killed}, failed {failed}.\n")


@app.command()
def interactive(
    default_dir: Annotated[Path, typer.Option("--dir", "-d", help="Default working directory")] = Path("."),
    model: Annotated[Optional[str], typer.Option("--model", help="Default model override")] = None,
):
    """
    Interactive REPL for session management.

    A clean, autocomplete-enabled interface for managing codex sessions.
    Tab-complete session IDs, watch live output, and manage the session lifecycle.

    [bold]Commands:[/]
        [cyan]spawn[/] "task"       Start a new session
        [cyan]ls[/]                 Dashboard of all sessions
        [cyan]peek[/] ID / [cyan]?[/] ID    Quick status check
        [cyan]show[/] ID            Full session details
        [cyan]traj[/] ID            Show trajectory (steps taken)
        [cyan]watch[/] ID           Live follow session output
        [cyan]c[/] ID "msg"         Continue conversation
        [cyan]kill[/] ID | all      Stop session(s)
        [cyan]rm[/] ID | all        Delete session(s)

    [bold]Examples:[/]
        $ zwarm interactive
        > spawn "Build auth module"
        > watch abc123
        > c abc123 "Now add tests"
        > ls
    """
    from zwarm.cli.interactive import run_interactive

    default_model = model or "gpt-5.1-codex-mini"
    run_interactive(working_dir=default_dir.absolute(), model=default_model)


@app.command()
def sessions(
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
    clean: Annotated[bool, typer.Option("--clean", "-c", help="Delete all non-running sessions")] = False,
    kill_all: Annotated[bool, typer.Option("--kill-all", "-k", help="Kill all running sessions")] = False,
    rm: Annotated[Optional[str], typer.Option("--rm", help="Delete specific session ID")] = None,
    kill: Annotated[Optional[str], typer.Option("--kill", help="Kill specific session ID")] = None,
):
    """
    Quick session management.

    By default, lists all sessions. Use flags for quick actions:

    [bold]Examples:[/]
        [dim]# List all sessions[/]
        $ zwarm sessions

        [dim]# Delete all completed/failed sessions[/]
        $ zwarm sessions --clean
        $ zwarm sessions -c

        [dim]# Kill all running sessions[/]
        $ zwarm sessions --kill-all
        $ zwarm sessions -k

        [dim]# Delete a specific session[/]
        $ zwarm sessions --rm abc123

        [dim]# Kill a specific session[/]
        $ zwarm sessions --kill abc123
    """
    from zwarm.sessions import CodexSessionManager, SessionStatus
    from zwarm.core.costs import estimate_session_cost, format_cost

    manager = CodexSessionManager(working_dir / ".zwarm")

    # Handle --kill (specific session)
    if kill:
        session = manager.get_session(kill)
        if not session:
            console.print(f"[red]Session not found:[/] {kill}")
            raise typer.Exit(1)
        if manager.kill_session(session.id):
            console.print(f"[green]✓[/] Killed {session.short_id}")
        else:
            console.print(f"[yellow]Session not running or already stopped[/]")
        return

    # Handle --rm (specific session)
    if rm:
        session = manager.get_session(rm)
        if not session:
            console.print(f"[red]Session not found:[/] {rm}")
            raise typer.Exit(1)
        if manager.delete_session(session.id):
            console.print(f"[green]✓[/] Deleted {session.short_id}")
        else:
            console.print(f"[red]Failed to delete[/]")
        return

    # Handle --kill-all
    if kill_all:
        running = manager.list_sessions(status=SessionStatus.RUNNING)
        if not running:
            console.print("[dim]No running sessions[/]")
            return
        killed = 0
        for s in running:
            if manager.kill_session(s.id):
                console.print(f"  [green]✓[/] Killed {s.short_id}")
                killed += 1
        console.print(f"\n[green]Killed {killed} session(s)[/]")
        return

    # Handle --clean
    if clean:
        all_sessions = manager.list_sessions()
        to_delete = [s for s in all_sessions if s.status != SessionStatus.RUNNING]
        if not to_delete:
            console.print("[dim]Nothing to clean[/]")
            return
        deleted = 0
        for s in to_delete:
            if manager.delete_session(s.id):
                deleted += 1
        console.print(f"[green]✓[/] Deleted {deleted} session(s)")
        return

    # Default: list all sessions
    all_sessions = manager.list_sessions()

    if not all_sessions:
        console.print("[dim]No sessions found.[/]")
        console.print("[dim]Start one with:[/]  zwarm session start \"your task\"")
        return

    # Summary counts
    running = sum(1 for s in all_sessions if s.status == SessionStatus.RUNNING)
    completed = sum(1 for s in all_sessions if s.status == SessionStatus.COMPLETED)
    failed = sum(1 for s in all_sessions if s.status == SessionStatus.FAILED)
    killed_count = sum(1 for s in all_sessions if s.status == SessionStatus.KILLED)

    parts = []
    if running:
        parts.append(f"[yellow]⟳ {running} running[/]")
    if completed:
        parts.append(f"[green]✓ {completed} completed[/]")
    if failed:
        parts.append(f"[red]✗ {failed} failed[/]")
    if killed_count:
        parts.append(f"[dim]⊘ {killed_count} killed[/]")

    console.print(" │ ".join(parts))
    console.print()

    # Table
    table = Table(box=None, show_header=True, header_style="bold dim")
    table.add_column("ID", style="cyan")
    table.add_column("", width=2)
    table.add_column("Task", max_width=45)
    table.add_column("Tokens", justify="right", style="dim")
    table.add_column("Cost", justify="right", style="dim")

    status_icons = {
        SessionStatus.RUNNING: "[yellow]⟳[/]",
        SessionStatus.COMPLETED: "[green]✓[/]",
        SessionStatus.FAILED: "[red]✗[/]",
        SessionStatus.KILLED: "[dim]⊘[/]",
        SessionStatus.PENDING: "[dim]○[/]",
    }

    for session in all_sessions:
        icon = status_icons.get(session.status, "?")
        task = session.task[:42] + "..." if len(session.task) > 45 else session.task
        tokens = session.token_usage.get("total_tokens", 0)
        tokens_str = f"{tokens:,}" if tokens else "-"

        # Cost estimate
        cost_info = estimate_session_cost(session.model, session.token_usage)
        cost_str = format_cost(cost_info.get("cost"))

        table.add_row(session.short_id, icon, task, tokens_str, cost_str)

    console.print(table)
    console.print()
    console.print("[dim]Quick actions:  --clean (-c) delete old  │  --kill-all (-k) stop running[/]")


# =============================================================================
# Session Manager Commands (background Codex processes)
# =============================================================================

session_app = typer.Typer(
    name="session",
    help="""
[bold cyan]Codex Session Manager[/]

Manage background Codex sessions. Run multiple codex tasks in parallel,
monitor their progress, and inject follow-up messages.

[bold]COMMANDS[/]
    [cyan]start[/]    Start a new session in the background
    [cyan]ls[/]       List all sessions
    [cyan]show[/]     Show messages for a session
    [cyan]logs[/]     Show raw JSONL output
    [cyan]inject[/]   Inject a follow-up message
    [cyan]kill[/]     Kill a running session
    [cyan]clean[/]    Remove old completed sessions

[bold]EXAMPLES[/]
    [dim]# Start a background session[/]
    $ zwarm session start "Add tests for auth module"

    [dim]# List all sessions[/]
    $ zwarm session ls

    [dim]# View session messages[/]
    $ zwarm session show abc123

    [dim]# Continue a completed session[/]
    $ zwarm session inject abc123 "Also add edge case tests"
""",
)
app.add_typer(session_app, name="session")


@session_app.command("start")
def session_start(
    task: Annotated[str, typer.Argument(help="Task description")],
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
    model: Annotated[str, typer.Option("--model", "-m", help="Model to use")] = "gpt-5.1-codex-mini",
):
    """
    Start a new Codex session in the background.

    The session runs independently and you can check on it later.
    Web search is always enabled via .codex/config.toml (set up by `zwarm init`).

    [bold]Examples:[/]
        [dim]# Simple task[/]
        $ zwarm session start "Fix the bug in auth.py"

        [dim]# With specific model[/]
        $ zwarm session start "Refactor the API" --model gpt-5.1-codex-max

        [dim]# Web search is always available[/]
        $ zwarm session start "Research latest OAuth2 best practices"
    """
    from zwarm.sessions import CodexSessionManager

    manager = CodexSessionManager(working_dir / ".zwarm")
    session = manager.start_session(
        task=task,
        working_dir=working_dir,
        model=model,
    )

    console.print()
    console.print(f"[green]✓ Session started[/]  [bold cyan]{session.short_id}[/]")
    console.print()
    console.print(f"  [dim]Task:[/]  {task[:70]}{'...' if len(task) > 70 else ''}")
    console.print(f"  [dim]Model:[/] {model}")
    console.print(f"  [dim]PID:[/]   {session.pid}")
    console.print()
    console.print("[dim]Commands:[/]")
    console.print(f"  [cyan]zwarm session ls[/]           [dim]List all sessions[/]")
    console.print(f"  [cyan]zwarm session show {session.short_id}[/]  [dim]View messages[/]")
    console.print(f"  [cyan]zwarm session logs {session.short_id} -f[/]  [dim]Follow live output[/]")


@session_app.command("ls")
def session_list(
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
    all_sessions: Annotated[bool, typer.Option("--all", "-a", help="Show all sessions including completed")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all sessions.

    Shows running sessions by default. Use --all to include completed.

    [bold]Examples:[/]
        $ zwarm session ls
        $ zwarm session ls --all
    """
    from zwarm.sessions import CodexSessionManager, SessionStatus

    manager = CodexSessionManager(working_dir / ".zwarm")
    sessions = manager.list_sessions()

    if not all_sessions:
        sessions = [s for s in sessions if s.status == SessionStatus.RUNNING]

    if json_output:
        import json
        console.print(json.dumps([s.to_dict() for s in sessions], indent=2))
        return

    if not sessions:
        if all_sessions:
            console.print("[dim]No sessions found.[/]")
        else:
            console.print("[dim]No running sessions.[/]")
            console.print("[dim]Use --all to see completed sessions, or start one with:[/]")
            console.print("  zwarm session start \"your task here\"")
        return

    # Show status summary
    running_count = sum(1 for s in sessions if s.status == SessionStatus.RUNNING)
    completed_count = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
    failed_count = sum(1 for s in sessions if s.status == SessionStatus.FAILED)

    summary_parts = []
    if running_count:
        summary_parts.append(f"[yellow]⟳ {running_count} running[/]")
    if completed_count:
        summary_parts.append(f"[green]✓ {completed_count} completed[/]")
    if failed_count:
        summary_parts.append(f"[red]✗ {failed_count} failed[/]")

    if summary_parts:
        console.print(" │ ".join(summary_parts))
        console.print()

    # Build table
    table = Table(box=None, show_header=True, header_style="bold dim")
    table.add_column("ID", style="cyan")
    table.add_column("", width=2)  # Status icon
    table.add_column("Task", max_width=50)
    table.add_column("Runtime", justify="right", style="dim")
    table.add_column("Tokens", justify="right", style="dim")

    status_icons = {
        SessionStatus.RUNNING: "[yellow]⟳[/]",
        SessionStatus.COMPLETED: "[green]✓[/]",
        SessionStatus.FAILED: "[red]✗[/]",
        SessionStatus.KILLED: "[dim]⊘[/]",
        SessionStatus.PENDING: "[dim]○[/]",
    }

    for session in sessions:
        status_icon = status_icons.get(session.status, "?")
        task_preview = session.task[:47] + "..." if len(session.task) > 50 else session.task
        tokens = session.token_usage.get("total_tokens", 0)
        tokens_str = f"{tokens:,}" if tokens else "-"

        table.add_row(
            session.short_id,
            status_icon,
            task_preview,
            session.runtime,
            tokens_str,
        )

    console.print()
    console.print(table)
    console.print()


@session_app.command("show")
def session_show(
    session_id: Annotated[str, typer.Argument(help="Session ID (or prefix)")],
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
    raw: Annotated[bool, typer.Option("--raw", "-r", help="Show raw messages without formatting")] = False,
):
    """
    Show messages for a session.

    Displays the conversation history with nice formatting.

    [bold]Examples:[/]
        $ zwarm session show abc123
        $ zwarm session show abc123 --raw
    """
    from zwarm.sessions import CodexSessionManager

    manager = CodexSessionManager(working_dir / ".zwarm")
    session = manager.get_session(session_id)

    if not session:
        console.print(f"[red]Session not found:[/] {session_id}")
        raise typer.Exit(1)

    # Get messages
    messages = manager.get_messages(session.id)

    # Status styling
    status_display = {
        "running": "[yellow]⟳ running[/]",
        "completed": "[green]✓ completed[/]",
        "failed": "[red]✗ failed[/]",
        "killed": "[dim]⊘ killed[/]",
        "pending": "[dim]○ pending[/]",
    }.get(session.status.value, session.status.value)

    console.print()
    console.print(f"[bold cyan]Session {session.short_id}[/]  {status_display}")
    console.print(f"[dim]Task:[/] {session.task}")
    console.print(f"[dim]Model:[/] {session.model}  [dim]│[/]  [dim]Turn:[/] {session.turn}  [dim]│[/]  [dim]Runtime:[/] {session.runtime}")
    console.print()

    if not messages:
        if session.status.value == "running":
            console.print("[yellow]Session is still running...[/]")
            console.print("[dim]Check back later for output.[/]")
        else:
            console.print("[dim]No messages captured.[/]")
        return

    # Display messages
    for msg in messages:
        if msg.role == "user":
            if raw:
                console.print(f"[bold blue]USER:[/] {msg.content}")
            else:
                console.print(Panel(msg.content, title="[bold blue]User[/]", border_style="blue"))

        elif msg.role == "assistant":
            if raw:
                console.print(f"[bold green]ASSISTANT:[/] {msg.content}")
            else:
                # Truncate very long messages
                content = msg.content
                if len(content) > 2000:
                    content = content[:2000] + "\n\n[dim]... (truncated, use --raw for full output)[/]"
                console.print(Panel(content, title="[bold green]Assistant[/]", border_style="green"))

        elif msg.role == "tool":
            if raw:
                console.print(f"[dim]TOOL: {msg.content}[/]")
            else:
                # Extract function name if present
                content = msg.content
                if content.startswith("[Calling:"):
                    console.print(f"  [dim]⚙[/] {content}")
                elif content.startswith("[Output]"):
                    console.print(f"    [dim]└─ {content[9:]}[/]")  # Skip "[Output]:"
                else:
                    console.print(f"  [dim]{content}[/]")

    console.print()

    # Show token usage
    if session.token_usage:
        tokens = session.token_usage
        console.print(f"[dim]Tokens: {tokens.get('input_tokens', 0):,} in / {tokens.get('output_tokens', 0):,} out[/]")

    # Show error if any
    if session.error:
        console.print(f"[red]Error:[/] {session.error}")

    # Helpful tip
    console.print()
    if session.status.value == "running":
        console.print(f"[dim]Tip: Use 'zwarm session logs {session.short_id} --follow' to watch live output[/]")
    elif session.status.value == "completed":
        console.print(f"[dim]Tip: Use 'zwarm session inject {session.short_id} \"your message\"' to continue the conversation[/]")


@session_app.command("logs")
def session_logs(
    session_id: Annotated[str, typer.Argument(help="Session ID (or prefix)")],
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
    turn: Annotated[Optional[int], typer.Option("--turn", "-t", help="Specific turn number")] = None,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Follow output (like tail -f)")] = False,
):
    """
    Show raw JSONL logs for a session.

    [bold]Examples:[/]
        $ zwarm session logs abc123
        $ zwarm session logs abc123 --follow
    """
    from zwarm.sessions import CodexSessionManager

    manager = CodexSessionManager(working_dir / ".zwarm")
    session = manager.get_session(session_id)

    if not session:
        console.print(f"[red]Session not found:[/] {session_id}")
        raise typer.Exit(1)

    if follow and session.status.value == "running":
        # Follow mode - tail the file
        import time
        output_path = manager._output_path(session.id, turn or session.turn)

        console.print(f"[dim]Following {output_path}... (Ctrl+C to stop)[/]")
        console.print()

        try:
            with open(output_path, "r") as f:
                # Print existing content
                for line in f:
                    console.print(line.rstrip())

                # Follow new content
                while session.is_running:
                    line = f.readline()
                    if line:
                        console.print(line.rstrip())
                    else:
                        time.sleep(0.5)
                        # Refresh session status
                        session = manager.get_session(session_id)

        except KeyboardInterrupt:
            console.print("\n[dim]Stopped following.[/]")

    else:
        # Just print the output
        output = manager.get_output(session.id, turn)
        if output:
            console.print(output)
        else:
            console.print("[dim]No output yet.[/]")


@session_app.command("inject")
def session_inject(
    session_id: Annotated[str, typer.Argument(help="Session ID (or prefix)")],
    message: Annotated[str, typer.Argument(help="Follow-up message to inject")],
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
):
    """
    Inject a follow-up message into a completed session.

    This continues the conversation with context from the previous turn.
    Can only be used on completed (not running) sessions.

    [bold]Examples:[/]
        $ zwarm session inject abc123 "Also add edge case tests"
        $ zwarm session inject abc123 "Good, now refactor the code"
    """
    from zwarm.sessions import CodexSessionManager, SessionStatus

    manager = CodexSessionManager(working_dir / ".zwarm")
    session = manager.get_session(session_id)

    if not session:
        console.print(f"[red]Session not found:[/] {session_id}")
        raise typer.Exit(1)

    if session.status == SessionStatus.RUNNING:
        console.print("[yellow]Session is still running.[/]")
        console.print("[dim]Wait for it to complete, then inject a follow-up.[/]")
        raise typer.Exit(1)

    # Inject the message
    updated_session = manager.inject_message(session.id, message)

    if not updated_session:
        console.print("[red]Failed to inject message.[/]")
        raise typer.Exit(1)

    console.print()
    console.print(f"[green]✓ Message injected[/]  Turn {updated_session.turn} started")
    console.print()
    console.print(f"  [dim]Message:[/] {message[:70]}{'...' if len(message) > 70 else ''}")
    console.print(f"  [dim]PID:[/]     {updated_session.pid}")
    console.print()
    console.print("[dim]Commands:[/]")
    console.print(f"  [cyan]zwarm session show {session.short_id}[/]  [dim]View messages[/]")
    console.print(f"  [cyan]zwarm session logs {session.short_id} -f[/]  [dim]Follow live output[/]")


@session_app.command("kill")
def session_kill(
    session_id: Annotated[str, typer.Argument(help="Session ID (or prefix)")],
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
):
    """
    Kill a running session.

    [bold]Examples:[/]
        $ zwarm session kill abc123
    """
    from zwarm.sessions import CodexSessionManager

    manager = CodexSessionManager(working_dir / ".zwarm")
    session = manager.get_session(session_id)

    if not session:
        console.print(f"[red]Session not found:[/] {session_id}")
        raise typer.Exit(1)

    if not session.is_running:
        console.print(f"[yellow]Session {session.short_id} is not running.[/]")
        console.print(f"  [dim]Status:[/] {session.status.value}")
        return

    killed = manager.kill_session(session.id)

    if killed:
        console.print(f"[green]Killed session {session.short_id}[/]")
    else:
        console.print(f"[red]Failed to kill session {session.short_id}[/]")


@session_app.command("clean")
def session_clean(
    working_dir: Annotated[Path, typer.Option("--dir", "-d", help="Working directory")] = Path("."),
    keep_days: Annotated[int, typer.Option("--keep-days", "-k", help="Keep sessions newer than N days")] = 7,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
):
    """
    Remove old completed sessions.

    [bold]Examples:[/]
        $ zwarm session clean
        $ zwarm session clean --keep-days 1
    """
    from zwarm.sessions import CodexSessionManager, SessionStatus

    manager = CodexSessionManager(working_dir / ".zwarm")
    sessions = manager.list_sessions()

    # Count cleanable sessions
    cleanable = [s for s in sessions if s.status in (SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.KILLED)]

    if not cleanable:
        console.print("[dim]No sessions to clean.[/]")
        return

    console.print(f"Found {len(cleanable)} completed/failed sessions.")

    if not yes:
        confirm = typer.confirm(f"Remove sessions older than {keep_days} days?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            return

    cleaned = manager.cleanup_completed(keep_days)
    console.print(f"[green]Cleaned {cleaned} sessions.[/]")


# =============================================================================
# Main callback and entry point
# =============================================================================

def _get_version() -> str:
    """Get version from package metadata."""
    try:
        from importlib.metadata import version as get_pkg_version
        return get_pkg_version("zwarm")
    except Exception:
        return "0.0.0"


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version")] = False,
):
    """Main callback for version flag."""
    if version:
        console.print(f"[bold cyan]zwarm[/] version [green]{_get_version()}[/]")
        raise typer.Exit()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
