# zwarm

Multi-agent CLI for orchestrating coding agents. Spawn, manage, and converse with multiple coding agent sessions in parallel.

**Supports both [Codex CLI](https://github.com/openai/codex) and [Claude Code CLI](https://claude.com/claude-code).**

## Installation

```bash
# From PyPI
pip install zwarm

# Or with uv
uv pip install zwarm
```

**Requirements:**
- Python 3.13+
- At least one of:
  - `codex` CLI installed and authenticated (OpenAI)
  - `claude` CLI installed and authenticated (Anthropic)

**Environment:**
```bash
export OPENAI_API_KEY="sk-..."        # Required for Codex
export ANTHROPIC_API_KEY="sk-..."     # Required for Claude
export WEAVE_PROJECT="entity/zwarm"   # Optional: Weave tracing
```

## Three Interfaces

zwarm has three ways to work with coding agents:

| Interface | Who drives | Use case |
|-----------|------------|----------|
| `zwarm interactive` | **You** | Direct session control, experimentation |
| `zwarm pilot` | **You + LLM** | Conversational guidance with checkpoints |
| `zwarm orchestrate` | **LLM** | Fully autonomous task execution |

All three use the **same session manager** - they're different interfaces to the same underlying system.

```
                     .zwarm/sessions/ (GROUND TRUTH)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        Orchestrate        Pilot        Interactive
          (LLM)         (LLM+REPL)        (REPL)
```

---

## Quick Start

```bash
# Initialize zwarm in your project
zwarm init

# Start the pilot (recommended for most users)
zwarm pilot --task "Build a REST API with authentication"

# Or go fully autonomous
zwarm orchestrate --task "Build a REST API with authentication"

# Or manual control
zwarm interactive

Want a 3-minute walkthrough? See `docs/DEMO.md` for a pilot + interactive demo.
```

---

## Multi-Adapter Support

zwarm supports multiple executor backends:

| Adapter | CLI | Models | Config |
|---------|-----|--------|--------|
| **Codex** | `codex` | gpt-5.1-codex-mini, etc. | `.zwarm/codex.toml` |
| **Claude** | `claude` | sonnet, opus, haiku | `.zwarm/claude.toml` |

You can mix adapters in the same session - for example, use Claude Opus for complex reasoning tasks and Codex Mini for quick edits.

---

## Pilot Mode

**You chat with an LLM that delegates to coding agents.** Best of both worlds - LLM intelligence with human oversight.

```bash
zwarm pilot
zwarm pilot --task "Add user authentication"
zwarm pilot --resume  # Resume previous session
```

### Features

- **Conversational**: Chat naturally, the LLM handles delegation
- **Checkpoints**: Every turn is saved, time-travel with `:goto`
- **Resume**: Continue where you left off with `--resume`
- **Multiline input**: Use `"""` for pasting large prompts
- **Status bar**: See token usage, cost estimates, context window

### Commands

| Command | Description |
|---------|-------------|
| `:help` | Show all commands |
| `:status` | Token usage, cost, context window |
| `:history` | Show turn checkpoints |
| `:goto T3` | Jump back to turn 3 |
| `:sessions` | List executor sessions |
| `:save` | Save current state |
| `:quit` | Exit (auto-saves) |

### Example

```
$ zwarm pilot

> Add a login endpoint to the API

Chooooching...

I'll delegate this to a coding agent.

[delegate] task: "Add login endpoint with JWT..."
  → Session abc123 started

The agent is working on it. I'll check back shortly.

[sleep] 10s
[check_session] abc123
  → completed (45s, 12k tokens)

Done! The agent added a /login endpoint with JWT support...

> Now add rate limiting

I'll have the same agent continue with rate limiting.

[converse] abc123: "Add rate limiting to the login endpoint..."
```

### Multiline Input

Start with `"""` and end with `"""`:

```
> """
Here's a complex task:
1. Add authentication
2. Add rate limiting
3. Add tests
"""
```

---

## Interactive Mode

**You are the orchestrator.** Direct control over sessions with autocomplete.

```bash
zwarm interactive
```

### Commands

| Command | Description |
|---------|-------------|
| `spawn "task" [--search]` | Start a new session (--search enables web) |
| `ls` | Dashboard of all sessions (with costs, models) |
| `? ID` / `peek ID` | Quick status check |
| `show ID` | Full session details |
| `traj ID` | Show trajectory (steps taken) |
| `watch ID` | Live follow session output |
| `c ID "msg"` | Continue conversation |
| `kill ID \| all` | Stop session(s) |
| `rm ID \| all` | Delete session(s) |
| `!command` | Run shell command (e.g., `!git status`) |
| `help` | Show all commands |
| `quit` | Exit |

### Example

```
$ zwarm interactive

> spawn "Add tests for the auth module"
✓ Started abc123 (running)
  Use 'watch abc123' to follow

> spawn "Fix type errors in utils.py"
✓ Started def456 (running)

> ls
⟳ 2 running

ID       │    │ Task                          │ Model        │ Tokens  │ Cost
abc123   │ ⟳  │ Add tests for the auth...     │ codex-mini   │ 5,234   │ $0.052
def456   │ ⟳  │ Fix type errors in utils...   │ codex-mini   │ 2,100   │ $0.021

> watch abc123
Watching abc123... (Ctrl+C to stop)
  [step 3] shell: pytest tests/
  [step 4] write: tests/test_auth.py
  ...

> c abc123 "Also add edge case tests"
✓ Injected message, session running

> !git status
On branch main
Changes not staged for commit:
  ...

> kill all
  ✓ Killed abc123
  ✓ Killed def456
Killed 2 session(s)
```

---

## Orchestrate Mode

**An LLM runs autonomously.** Give it a task, it delegates to coding agents and manages them.

```bash
zwarm orchestrate --task "Build a REST API with authentication"
zwarm orchestrate --task-file task.md
echo "Fix the bug" | zwarm orchestrate
```

### How It Works

The orchestrator LLM has access to:

| Tool | Description |
|------|-------------|
| `delegate(task, adapter="codex")` | Start a new coding session |
| `converse(id, msg)` | Continue a session |
| `check_session(id)` | Get full session details |
| `peek_session(id)` | Quick status check |
| `list_sessions()` | List all sessions |
| `end_session(id)` | Kill/delete a session |
| `sleep(seconds)` | Wait before checking again |

**Async-first**: All sessions run in the background. The orchestrator uses `sleep()` to wait, then checks on progress.

**Multi-adapter**: Pass `adapter="claude"` or `adapter="codex"` to `delegate()` to choose the backend.

**Web Search**: Enable `web_search=True` in config for tasks needing current info (API docs, latest releases, etc.).

### Watchers

Watchers monitor the orchestrator and intervene when needed:

| Watcher | Purpose |
|---------|---------|
| `progress` | Detects stuck/spinning behavior |
| `budget` | Enforces step/session limits |
| `delegation` | Tracks delegation patterns |
| `delegation_reminder` | Nudges to delegate when doing too much directly |

---

## Session Management

### Quick Commands

```bash
# List all sessions with costs
zwarm sessions

# Clean up old sessions
zwarm sessions --clean
zwarm sessions -c

# Kill all running sessions
zwarm sessions --kill-all
zwarm sessions -k

# Target specific session
zwarm sessions --rm abc123
zwarm sessions --kill abc123
```

### Session Lifecycle

```
spawn → running → completed/failed/killed
                       ↓
               converse → running → completed
                               ↓
                         converse → ...
```

### Storage

```
.zwarm/sessions/<uuid>/
├── meta.json           # Status, task, model, adapter, tokens, cost
└── turns/
    ├── turn_1.jsonl    # Raw executor output for turn 1
    ├── turn_2.jsonl    # Output after continue
    └── ...
```

---

## Configuration

### Initialize

```bash
zwarm init
```

This creates:
- `.zwarm/config.toml` - Runtime settings (Weave, watchers)
- `.zwarm/codex.toml` - Codex CLI settings (model, reasoning)
- `.zwarm/claude.toml` - Claude CLI settings (model, permissions)
- `zwarm.yaml` - Project context (optional, with `--with-project`)

### Config Files

**`.zwarm/config.toml`** - Controls zwarm itself:
```toml
[weave]
project = "your-entity/zwarm"

[orchestrator]
max_steps = 50

[executor]
web_search = false  # Enable web search for all delegated sessions

[pilot]
max_steps_per_turn = 25

[watchers]
enabled = ["progress", "budget", "delegation", "delegation_reminder"]
```

**`.zwarm/codex.toml`** - Controls the Codex CLI:
```toml
model = "gpt-5.1-codex-mini"
model_reasoning_effort = "high"  # low | medium | high
full_auto = true
```

**`.zwarm/claude.toml`** - Controls the Claude Code CLI:
```toml
model = "sonnet"  # sonnet | opus | haiku
full_danger = true  # Skip permission prompts
```

**`zwarm.yaml`** - Project-specific context:
```yaml
description: "My awesome project"

context: |
  Tech stack: FastAPI, PostgreSQL, React
  Key directories: src/api/, src/components/

constraints:
  - "All new endpoints need tests"
  - "Use existing patterns from src/api/"
```

---

## CLI Reference

```bash
# Setup
zwarm init              # Initialize .zwarm/ with interactive prompts
zwarm init --yes        # Quick setup with defaults

# Interfaces
zwarm pilot             # Conversational LLM guidance (recommended)
zwarm pilot --resume    # Resume previous session
zwarm interactive       # Direct session control REPL
zwarm orchestrate       # Fully autonomous LLM

# Session management
zwarm sessions          # List all sessions
zwarm sessions -c       # Clean old sessions
zwarm sessions -k       # Kill all running

# Utilities
zwarm exec              # Run single executor (testing)
zwarm clean             # Kill orphaned processes
zwarm reset             # Reset .zwarm/ state
```

---

## Project Structure

```
zwarm/
├── src/zwarm/
│   ├── sessions/           # Session substrate
│   │   ├── base.py         # BaseSessionManager (ABC)
│   │   ├── manager.py      # CodexSessionManager
│   │   └── claude.py       # ClaudeSessionManager
│   ├── cli/
│   │   ├── main.py         # CLI commands
│   │   ├── pilot.py        # Pilot REPL
│   │   └── interactive.py  # Interactive REPL
│   ├── tools/
│   │   └── delegation.py   # Orchestrator tools (multi-adapter)
│   ├── core/
│   │   ├── config.py       # Configuration
│   │   ├── checkpoints.py  # Time-travel primitives
│   │   ├── costs.py        # Token cost estimation
│   │   └── state.py        # State persistence
│   ├── watchers/           # Trajectory alignment
│   ├── prompts/            # System prompts
│   └── orchestrator.py     # Orchestrator agent
└── docs/
    ├── CONCEPTS.md         # Architecture diagrams
    └── INTERNALS.md        # Developer documentation
```

---

## License

MIT
