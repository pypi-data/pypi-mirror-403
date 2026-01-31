"""Tests for MessageAdapter."""

import pytest
from ibm_watsonx_ai_120b.adapters.message_adapter import MessageAdapter


class TestMessageAdapter:
    """Tests for MessageAdapter."""

    def test_adapt_messages_ensures_content_not_null(self):
        """Test that null content is converted to empty string."""
        messages = [
            {"role": "user", "content": None},
            {"role": "assistant", "content": None},
        ]

        result = MessageAdapter.adapt_messages(messages)

        assert result[0]["content"] == ""
        assert result[1]["content"] == ""

    def test_adapt_messages_converts_tool_role(self):
        """Test that tool role is converted to user role."""
        messages = [
            {"role": "tool", "content": '{"result": 42}', "tool_call_id": "call_123"},
        ]

        result = MessageAdapter.adapt_messages(messages)

        assert result[0]["role"] == "user"
        assert "Function result" in result[0]["content"]
        assert '{"result": 42}' in result[0]["content"]

    def test_adapt_messages_handles_assistant_with_tool_calls(self):
        """Test that assistant messages with tool_calls are converted."""
        messages = [{
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "Tokyo"}',
                }
            }],
        }]

        result = MessageAdapter.adapt_messages(messages)

        assert result[0]["role"] == "assistant"
        assert "get_weather" in result[0]["content"]
        assert "tool_calls" not in result[0]

    def test_adapt_messages_strips_tool_calls_from_regular_messages(self):
        """Test that tool_calls are stripped from regular messages."""
        messages = [{
            "role": "assistant",
            "content": "Hello",
            "tool_calls": [],
        }]

        result = MessageAdapter.adapt_messages(messages)

        assert "tool_calls" not in result[0]
        assert result[0]["content"] == "Hello"

    def test_format_for_api_minimal_format(self):
        """Test that format_for_api returns minimal format."""
        messages = [
            {"role": "system", "content": "You are helpful", "extra": "ignored"},
            {"role": "user", "content": "Hi", "name": "user1"},
        ]

        result = MessageAdapter.format_for_api(messages)

        assert result[0] == {"role": "system", "content": "You are helpful"}
        assert result[1] == {"role": "user", "content": "Hi"}

    def test_inject_system_message_replaces_existing(self):
        """Test that inject_system_message replaces existing by default."""
        messages = [
            {"role": "system", "content": "Old system message"},
            {"role": "user", "content": "Hi"},
        ]

        result = MessageAdapter.inject_system_message(messages, "New system message")

        assert result[0]["content"] == "New system message"
        assert len(result) == 2

    def test_inject_system_message_prepends_when_not_replacing(self):
        """Test that inject_system_message can prepend to existing."""
        messages = [
            {"role": "system", "content": "Original instructions"},
            {"role": "user", "content": "Hi"},
        ]

        result = MessageAdapter.inject_system_message(
            messages, "Additional instructions", replace=False
        )

        assert "Additional instructions" in result[0]["content"]
        assert "Original instructions" in result[0]["content"]

    def test_inject_system_message_adds_when_none_exists(self):
        """Test that inject_system_message adds when no system message exists."""
        messages = [
            {"role": "user", "content": "Hi"},
        ]

        result = MessageAdapter.inject_system_message(messages, "System message")

        assert result[0]["role"] == "system"
        assert result[0]["content"] == "System message"
        assert len(result) == 2

    def test_extract_last_assistant_content(self):
        """Test extracting content from last assistant message."""
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good!"},
        ]

        result = MessageAdapter.extract_last_assistant_content(messages)

        assert result == "I'm good!"

    def test_extract_last_assistant_content_returns_none_when_no_assistant(self):
        """Test that None is returned when no assistant message exists."""
        messages = [
            {"role": "user", "content": "Hi"},
        ]

        result = MessageAdapter.extract_last_assistant_content(messages)

        assert result is None
