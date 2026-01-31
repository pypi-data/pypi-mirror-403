"""Tests for HarmonyAdapter."""

import pytest
from ibm_watsonx_ai_120b.adapters.harmony_adapter import HarmonyAdapter
from ibm_watsonx_ai_120b.utils.tokens import strip_harmony_tokens


class TestHarmonyAdapter:
    """Tests for HarmonyAdapter."""

    def test_strip_harmony_tokens_basic(self):
        """Test stripping basic harmony tokens."""
        text = "Hello <|start|> world <|end|>"
        result = strip_harmony_tokens(text)
        assert "<|start|>" not in result
        assert "<|end|>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_strip_harmony_tokens_channel(self):
        """Test stripping channel markers."""
        text = "assistant<|channel|>analysis This is the response"
        result = strip_harmony_tokens(text)
        assert "<|channel|>" not in result
        assert "assistant" not in result.lower() or "This is the response" in result

    def test_strip_harmony_tokens_preserves_content(self):
        """Test that actual content is preserved."""
        text = "The weather is sunny and 75°F"
        result = strip_harmony_tokens(text)
        assert result == text

    def test_strip_harmony_tokens_empty_input(self):
        """Test handling empty input."""
        assert strip_harmony_tokens("") == ""
        assert strip_harmony_tokens(None) is None

    def test_clean_response_cleans_content(self):
        """Test that clean_response cleans message content."""
        response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello <|channel|> world",
                }
            }]
        }

        result = HarmonyAdapter.clean_response(response)

        assert "<|channel|>" not in result["choices"][0]["message"]["content"]

    def test_clean_response_cleans_reasoning_content(self):
        """Test that clean_response cleans reasoning_content."""
        response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Answer",
                    "reasoning_content": "Thinking <|start|> process",
                }
            }]
        }

        result = HarmonyAdapter.clean_response(response)

        assert "<|start|>" not in result["choices"][0]["message"]["reasoning_content"]

    def test_clean_response_cleans_tool_calls(self):
        """Test that clean_response cleans tool call names."""
        response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather<|channel|>analysis",
                            "arguments": "{}",
                        }
                    }]
                }
            }]
        }

        result = HarmonyAdapter.clean_response(response)

        func_name = result["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
        assert "<|channel|>" not in func_name

    def test_clean_response_preserves_structure(self):
        """Test that clean_response preserves response structure."""
        response = {
            "id": "test123",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello",
                },
                "finish_reason": "stop",
            }]
        }

        result = HarmonyAdapter.clean_response(response)

        assert result["id"] == "test123"
        assert result["choices"][0]["finish_reason"] == "stop"

    def test_clean_text_static_method(self):
        """Test the clean_text static method."""
        text = "<|start|>Hello<|end|>"
        result = HarmonyAdapter.clean_text(text)
        assert result == "Hello"
