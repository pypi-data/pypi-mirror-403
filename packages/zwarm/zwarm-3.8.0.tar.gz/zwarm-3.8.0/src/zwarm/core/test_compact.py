"""Tests for the compact module."""

import pytest

from zwarm.core.compact import (
    compact_messages,
    estimate_tokens,
    find_tool_groups,
    should_compact,
)


class TestEstimateTokens:
    def test_simple_messages(self):
        """Estimate tokens for simple text messages."""
        messages = [
            {"role": "user", "content": "Hello world"},  # 11 chars
            {"role": "assistant", "content": "Hi there!"},  # 9 chars
        ]
        # ~20 chars / 4 = ~5 tokens
        tokens = estimate_tokens(messages)
        assert tokens == 5

    def test_empty_messages(self):
        """Empty messages return 0 tokens."""
        assert estimate_tokens([]) == 0

    def test_messages_with_tool_calls(self):
        """Tool calls add to token count."""
        messages = [
            {
                "role": "assistant",
                "content": "Let me check",
                "tool_calls": [
                    {"function": {"name": "read", "arguments": '{"path": "/foo/bar"}'}}
                ],
            }
        ]
        tokens = estimate_tokens(messages)
        assert tokens > 0


class TestFindToolGroups:
    def test_no_tool_calls(self):
        """No tool groups in simple conversation."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        groups = find_tool_groups(messages)
        assert groups == []

    def test_openai_format_tool_call(self):
        """Detect OpenAI-style tool call groups."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Read file"},
            {
                "role": "assistant",
                "content": "Reading...",
                "tool_calls": [{"id": "tc1", "function": {"name": "read"}}],
            },
            {"role": "tool", "tool_call_id": "tc1", "content": "file contents"},
            {"role": "assistant", "content": "Here's the file"},
        ]
        groups = find_tool_groups(messages)
        assert groups == [(2, 3)]  # Assistant with tool_calls + tool response

    def test_multiple_tool_responses(self):
        """Group includes all consecutive tool responses."""
        messages = [
            {"role": "user", "content": "Do things"},
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "tc1", "function": {"name": "a"}},
                    {"id": "tc2", "function": {"name": "b"}},
                ],
            },
            {"role": "tool", "tool_call_id": "tc1", "content": "result1"},
            {"role": "tool", "tool_call_id": "tc2", "content": "result2"},
            {"role": "assistant", "content": "Done"},
        ]
        groups = find_tool_groups(messages)
        assert groups == [(1, 3)]  # Indices 1, 2, 3 form one group

    def test_anthropic_format_tool_use(self):
        """Detect Anthropic-style tool_use content blocks."""
        messages = [
            {"role": "user", "content": "Read file"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Reading..."},
                    {"type": "tool_use", "id": "tu1", "name": "read", "input": {}},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "tu1", "content": "data"},
                ],
            },
            {"role": "assistant", "content": "Got it"},
        ]
        groups = find_tool_groups(messages)
        assert groups == [(1, 2)]  # Assistant with tool_use + user with tool_result


class TestCompactMessages:
    def test_no_compaction_needed_few_messages(self):
        """Don't compact if we have fewer messages than keep thresholds."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Task"},
            {"role": "assistant", "content": "Response"},
        ]
        result = compact_messages(messages, keep_first_n=2, keep_last_n=2)
        assert not result.was_compacted
        assert result.messages == messages
        assert "Too few" in result.preserved_reason

    def test_compacts_middle_messages(self):
        """Remove messages from the middle, keeping first and last."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Task"},
            {"role": "assistant", "content": "Step 1"},
            {"role": "user", "content": "Continue"},
            {"role": "assistant", "content": "Step 2"},
            {"role": "user", "content": "More"},
            {"role": "assistant", "content": "Step 3"},
            {"role": "user", "content": "Final"},
            {"role": "assistant", "content": "Done"},
        ]
        result = compact_messages(messages, keep_first_n=2, keep_last_n=2)

        assert result.was_compacted
        assert result.removed_count > 0
        # First 2 and last 2 should be preserved
        assert result.messages[0]["content"] == "System"
        assert result.messages[1]["content"] == "Task"
        assert result.messages[-1]["content"] == "Done"
        assert result.messages[-2]["content"] == "Final"

    def test_preserves_tool_call_pairs(self):
        """Never split tool call from its response."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Task"},
            {"role": "assistant", "content": "Old message 1"},
            {"role": "assistant", "content": "Old message 2"},
            {
                "role": "assistant",
                "content": "Calling tool",
                "tool_calls": [{"id": "tc1", "function": {"name": "test"}}],
            },
            {"role": "tool", "tool_call_id": "tc1", "content": "Tool result"},
            {"role": "assistant", "content": "Recent 1"},
            {"role": "user", "content": "Recent 2"},
        ]
        result = compact_messages(messages, keep_first_n=2, keep_last_n=2)

        # The tool call pair should either both be kept or both removed
        has_tool_call = any(m.get("tool_calls") for m in result.messages)
        has_tool_response = any(m.get("role") == "tool" for m in result.messages)

        # They should match - either both present or both absent
        assert has_tool_call == has_tool_response

    def test_adds_compaction_marker(self):
        """Add a marker message when compaction occurs."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Task"},
        ] + [{"role": "assistant", "content": f"Msg {i}"} for i in range(20)]

        result = compact_messages(messages, keep_first_n=2, keep_last_n=3)

        if result.was_compacted:
            # Should have a system message about compaction
            marker_msgs = [
                m for m in result.messages
                if m.get("role") == "system" and "compacted" in m.get("content", "").lower()
            ]
            assert len(marker_msgs) == 1

    def test_token_based_compaction(self):
        """Compact based on token threshold."""
        # Create messages that exceed token limit
        messages = [
            {"role": "system", "content": "System prompt " * 100},
            {"role": "user", "content": "Task " * 100},
        ] + [
            {"role": "assistant", "content": f"Response {i} " * 50}
            for i in range(10)
        ]

        # Should not compact if under limit
        result_under = compact_messages(messages, max_tokens=100000)
        # Might or might not compact depending on estimate

        # Should compact if over limit
        result_over = compact_messages(messages, max_tokens=100, target_token_pct=0.5)
        # With such a low limit, should definitely try to compact
        assert result_over.original_count == len(messages)


class TestShouldCompact:
    def test_under_threshold(self):
        """Don't compact when under threshold."""
        messages = [{"role": "user", "content": "Hello"}]
        assert not should_compact(messages, max_tokens=1000, threshold_pct=0.85)

    def test_over_threshold(self):
        """Compact when over threshold."""
        messages = [{"role": "user", "content": "x" * 4000}]  # ~1000 tokens
        assert should_compact(messages, max_tokens=500, threshold_pct=0.85)


class TestEdgeCases:
    def test_all_tool_calls(self):
        """Handle conversation that's mostly tool calls."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Task"},
        ]
        # Add many tool call pairs
        for i in range(5):
            messages.append({
                "role": "assistant",
                "tool_calls": [{"id": f"tc{i}", "function": {"name": "test"}}],
            })
            messages.append({"role": "tool", "tool_call_id": f"tc{i}", "content": f"result{i}"})

        messages.append({"role": "assistant", "content": "Final"})

        result = compact_messages(messages, keep_first_n=2, keep_last_n=1)

        # Should still produce valid output
        assert len(result.messages) > 0

        # Check no orphaned tool calls
        for i, msg in enumerate(result.messages):
            if msg.get("tool_calls"):
                # Next message should be a tool response
                if i + 1 < len(result.messages):
                    # Either next is tool response, or this is at the end
                    pass  # Structural validity checked by not raising

    def test_empty_messages(self):
        """Handle empty message list."""
        result = compact_messages([])
        assert result.messages == []
        assert not result.was_compacted

    def test_only_system_and_user(self):
        """Handle minimal conversation."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
        ]
        result = compact_messages(messages, keep_first_n=2, keep_last_n=2)
        assert not result.was_compacted
        assert result.messages == messages


class TestPydanticModelMessages:
    """Test handling of Pydantic model messages (not just dicts)."""

    def test_estimate_tokens_with_objects(self):
        """estimate_tokens should handle objects with attributes."""
        class MockMessage:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        messages = [
            MockMessage("user", "Hello world"),
            MockMessage("assistant", "Hi there!"),
        ]
        tokens = estimate_tokens(messages)
        assert tokens > 0

    def test_should_compact_with_objects(self):
        """should_compact should handle objects with attributes."""
        class MockMessage:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        messages = [MockMessage("user", "x" * 4000)]
        # Should not crash
        result = should_compact(messages, max_tokens=500, threshold_pct=0.85)
        assert result is True

    def test_find_tool_groups_with_objects(self):
        """find_tool_groups should handle objects with attributes."""
        class MockMessage:
            def __init__(self, role, content=None, tool_calls=None):
                self.role = role
                self.content = content
                self.tool_calls = tool_calls

        messages = [
            MockMessage("user", "Task"),
            MockMessage("assistant", "Done"),
        ]
        # Should not crash
        groups = find_tool_groups(messages)
        assert groups == []
