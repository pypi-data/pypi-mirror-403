"""
System prompts for zwarm agents.
"""

from zwarm.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT, get_orchestrator_prompt
from zwarm.prompts.pilot import PILOT_SYSTEM_PROMPT, get_pilot_prompt

__all__ = [
    "ORCHESTRATOR_SYSTEM_PROMPT",
    "get_orchestrator_prompt",
    "PILOT_SYSTEM_PROMPT",
    "get_pilot_prompt",
]
