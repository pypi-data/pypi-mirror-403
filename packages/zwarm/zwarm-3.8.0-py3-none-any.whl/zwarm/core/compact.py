"""
Message compaction for context window management.

Safely prunes old messages while preserving:
- System prompt and initial user task
- Tool call/response pairs (never orphaned)
- Recent conversation context
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object (handles both Pydantic models and dicts)."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


@dataclass
class CompactionResult:
    """Result of a compaction operation."""

    messages: list[dict[str, Any]]
    removed_count: int
    original_count: int
    preserved_reason: str | None = None

    @property
    def was_compacted(self) -> bool:
        return self.removed_count > 0


def estimate_tokens(messages: list[Any]) -> int:
    """
    Rough token estimate for messages.

    Uses ~4 chars per token as a simple heuristic.
    This is intentionally conservative.
    Handles both dict messages and Pydantic model messages.
    """
    total_chars = 0
    for msg in messages:
        content = _get_attr(msg, "content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            # Anthropic-style content blocks
            for block in content:
                if isinstance(block, dict):
                    total_chars += len(str(block.get("text", "")))
                    total_chars += len(str(block.get("input", "")))
                elif isinstance(block, str):
                    total_chars += len(block)
                else:
                    # Pydantic model block
                    total_chars += len(str(_get_attr(block, "text", "")))
                    total_chars += len(str(_get_attr(block, "input", "")))

        # Tool calls add tokens too
        tool_calls = _get_attr(msg, "tool_calls", []) or []
        for tc in tool_calls:
            func = _get_attr(tc, "function", {}) or {}
            args = _get_attr(func, "arguments", "") if isinstance(func, dict) else getattr(func, "arguments", "")
            total_chars += len(str(args))

    return total_chars // 4


def find_tool_groups(messages: list[Any]) -> list[tuple[int, int]]:
    """
    Find message index ranges that form tool call groups.

    A tool call group is:
    - An assistant message with tool_calls
    - All following tool/user response messages until the next assistant message

    This handles both OpenAI format (role="tool") and Anthropic format
    (role="user" with tool_result content).
    Also handles Pydantic model messages.

    Returns list of (start_idx, end_idx) tuples (inclusive).
    """
    groups = []
    i = 0

    while i < len(messages):
        msg = messages[i]

        # Check for tool calls in assistant message
        has_tool_calls = False

        # OpenAI format: tool_calls field
        if _get_attr(msg, "role") == "assistant" and _get_attr(msg, "tool_calls"):
            has_tool_calls = True

        # Anthropic format: content blocks with type="tool_use"
        if _get_attr(msg, "role") == "assistant":
            content = _get_attr(msg, "content", [])
            if isinstance(content, list):
                for block in content:
                    block_type = _get_attr(block, "type", None)
                    if block_type == "tool_use":
                        has_tool_calls = True
                        break

        if has_tool_calls:
            start = i
            j = i + 1

            # Find all following tool responses
            while j < len(messages):
                next_msg = messages[j]
                role = _get_attr(next_msg, "role", "")

                # OpenAI format: tool role
                if role == "tool":
                    j += 1
                    continue

                # Anthropic format: user message with tool_result
                if role == "user":
                    content = _get_attr(next_msg, "content", [])
                    if isinstance(content, list):
                        has_tool_result = any(
                            _get_attr(b, "type", None) == "tool_result"
                            for b in content
                        )
                        if has_tool_result:
                            j += 1
                            continue

                # Not a tool response, stop here
                break

            groups.append((start, j - 1))
            i = j
        else:
            i += 1

    return groups


def compact_messages(
    messages: list[Any],
    keep_first_n: int = 2,
    keep_last_n: int = 10,
    max_tokens: int | None = None,
    target_token_pct: float = 0.7,
) -> CompactionResult:
    """
    Compact message history by removing old messages (LRU-style).

    Preserves:
    - First N messages (system prompt, user task)
    - Last N messages (recent context)
    - Tool call/response pairs are NEVER split

    Args:
        messages: The message list to compact
        keep_first_n: Number of messages to always keep at the start
        keep_last_n: Number of messages to always keep at the end
        max_tokens: If set, compact when estimated tokens exceed this
        target_token_pct: Target percentage of max_tokens after compaction

    Returns:
        CompactionResult with the compacted messages and stats
    """
    original_count = len(messages)

    # Nothing to compact if we have few messages
    if len(messages) <= keep_first_n + keep_last_n:
        return CompactionResult(
            messages=messages,
            removed_count=0,
            original_count=original_count,
            preserved_reason="Too few messages to compact",
        )

    # Check if compaction is needed based on tokens
    if max_tokens:
        current_tokens = estimate_tokens(messages)
        if current_tokens < max_tokens:
            return CompactionResult(
                messages=messages,
                removed_count=0,
                original_count=original_count,
                preserved_reason=f"Under token limit ({current_tokens}/{max_tokens})",
            )

    # Find tool call groups (these must stay together)
    tool_groups = find_tool_groups(messages)

    # Build a set of "protected" indices (in tool groups)
    protected_indices: set[int] = set()
    for start, end in tool_groups:
        for idx in range(start, end + 1):
            protected_indices.add(idx)

    # Determine which messages are in the "middle" (candidates for removal)
    # Middle = not in first N, not in last N
    middle_start = keep_first_n
    middle_end = len(messages) - keep_last_n

    if middle_start >= middle_end:
        return CompactionResult(
            messages=messages,
            removed_count=0,
            original_count=original_count,
            preserved_reason="No middle messages to remove",
        )

    # Find removable message ranges in the middle
    # We remove from the oldest (lowest index) first
    removable_ranges: list[tuple[int, int]] = []
    i = middle_start

    while i < middle_end:
        # Check if this index is in a tool group
        in_group = False
        for start, end in tool_groups:
            if start <= i <= end:
                # This message is part of a tool group
                # Check if the ENTIRE group is in the middle
                if start >= middle_start and end < middle_end:
                    # Entire group is removable as a unit
                    removable_ranges.append((start, end))
                    i = end + 1
                    in_group = True
                    break
                else:
                    # Group spans protected region, skip it entirely
                    i = end + 1
                    in_group = True
                    break

        if not in_group:
            # Single message, can be removed individually
            removable_ranges.append((i, i))
            i += 1

    # Deduplicate and sort ranges
    removable_ranges = sorted(set(removable_ranges), key=lambda x: x[0])

    if not removable_ranges:
        return CompactionResult(
            messages=messages,
            removed_count=0,
            original_count=original_count,
            preserved_reason="All middle messages are in protected tool groups",
        )

    # Determine how many to remove
    # Start by removing the oldest half of removable ranges
    if max_tokens:
        # Token-based: remove until under target
        target_tokens = int(max_tokens * target_token_pct)
        indices_to_remove: set[int] = set()

        for start, end in removable_ranges:
            for idx in range(start, end + 1):
                indices_to_remove.add(idx)

            # Check if we've removed enough
            remaining = [m for i, m in enumerate(messages) if i not in indices_to_remove]
            if estimate_tokens(remaining) <= target_tokens:
                break
    else:
        # Count-based: remove oldest half of middle
        total_removable = sum(end - start + 1 for start, end in removable_ranges)
        target_remove = total_removable // 2

        indices_to_remove = set()
        removed = 0

        for start, end in removable_ranges:
            if removed >= target_remove:
                break
            for idx in range(start, end + 1):
                indices_to_remove.add(idx)
                removed += 1

    # Build new message list
    new_messages = [m for i, m in enumerate(messages) if i not in indices_to_remove]

    # Add a compaction marker so the model knows history was truncated
    if indices_to_remove and len(new_messages) > keep_first_n:
        # Insert marker after the preserved first messages
        marker = {
            "role": "system",
            "content": (
                f"[Context compacted: {len(indices_to_remove)} older messages removed "
                f"to manage context window. Conversation continues below.]"
            ),
        }
        new_messages.insert(keep_first_n, marker)

    logger.info(
        f"Compacted messages: {original_count} -> {len(new_messages)} "
        f"(removed {len(indices_to_remove)})"
    )

    return CompactionResult(
        messages=new_messages,
        removed_count=len(indices_to_remove),
        original_count=original_count,
    )


def should_compact(
    messages: list[Any],
    max_tokens: int,
    threshold_pct: float = 0.85,
) -> bool:
    """
    Check if messages should be compacted.

    Returns True if estimated tokens exceed threshold percentage of max.
    Handles both dict messages and Pydantic model messages.
    """
    current = estimate_tokens(messages)
    threshold = int(max_tokens * threshold_pct)
    return current >= threshold
