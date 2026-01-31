"""
Session Manager - Background process management for executor agents.

Supports multiple executor adapters:
- Codex (CodexSessionManager) - OpenAI's Codex CLI
- Claude (ClaudeSessionManager) - Anthropic's Claude Code CLI

Features:
- Start executor tasks in background processes
- Monitor status and view message history
- Inject follow-up messages (continue conversations)
- Kill running sessions
- Unified interface via BaseSessionManager
"""

from zwarm.sessions.base import (
    BaseSessionManager,
    CodexSession,  # Alias for Session (backwards compat)
    Session,
    SessionMessage,
    SessionStatus,
)
from zwarm.sessions.manager import CodexSessionManager

# Available adapters
AVAILABLE_ADAPTERS = ["codex", "claude"]

__all__ = [
    # Base classes
    "BaseSessionManager",
    "Session",
    "SessionMessage",
    "SessionStatus",
    # Backwards compatibility
    "CodexSession",
    # Adapters
    "CodexSessionManager",
    # Registry
    "AVAILABLE_ADAPTERS",
    # Factory
    "get_session_manager",
]


def get_session_manager(adapter: str, state_dir: str = ".zwarm") -> BaseSessionManager:
    """
    Factory function to get a session manager for the given adapter.

    Args:
        adapter: Adapter name ("codex" or "claude")
        state_dir: State directory path

    Returns:
        Session manager instance

    Raises:
        ValueError: If adapter is not recognized
    """
    if adapter == "codex":
        return CodexSessionManager(state_dir)
    elif adapter == "claude":
        from zwarm.sessions.claude import ClaudeSessionManager
        return ClaudeSessionManager(state_dir)
    else:
        raise ValueError(f"Unknown adapter: {adapter}. Available: {AVAILABLE_ADAPTERS}")
