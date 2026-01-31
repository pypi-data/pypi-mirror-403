"""
zwarm: Multi-Agent CLI Orchestration Research Platform

A framework for orchestrating multiple CLI coding agents (codex, claude-code, gemini)
with support for sync (conversational) and async (fire-and-forget) delegation.
"""

from zwarm.core.config import ZwarmConfig, load_config
from zwarm.core.models import (
    ConversationSession,
    Event,
    Message,
    SessionMode,
    SessionStatus,
    Task,
    TaskStatus,
)
from zwarm.core.state import StateManager
from zwarm.orchestrator import Orchestrator, build_orchestrator

__all__ = [
    # Config
    "ZwarmConfig",
    "load_config",
    # Models
    "ConversationSession",
    "Event",
    "Message",
    "SessionMode",
    "SessionStatus",
    "Task",
    "TaskStatus",
    # State
    "StateManager",
    # Orchestrator
    "Orchestrator",
    "build_orchestrator",
]
