"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_watsonx_response():
    """Create a mock WatsonX API response."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "openai/gpt-oss-120b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?",
                "refusal": None,
            },
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18,
        },
    }


@pytest.fixture
def mock_thinking_only_response():
    """Create a mock response with only reasoning_content."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "openai/gpt-oss-120b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "",
                "reasoning_content": "Let me think about this...",
                "refusal": None,
            },
            "finish_reason": "stop",
        }],
    }


@pytest.fixture
def mock_tool_call_response():
    """Create a mock response with tool calls in content."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "openai/gpt-oss-120b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": '{"tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "get_weather", "arguments": {"location": "Tokyo"}}}]}',
                "refusal": None,
            },
            "finish_reason": "stop",
        }],
    }


@pytest.fixture
def sample_tools():
    """Sample tool definitions."""
    return [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name",
                    }
                },
                "required": ["location"],
            },
        },
    }]


@pytest.fixture
def sample_schema():
    """Sample JSON schema."""
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "active": {"type": "boolean"},
        },
        "required": ["name", "age"],
    }


@pytest.fixture
def mock_model_inference():
    """Create a mock ModelInference for testing."""
    with patch("ibm_watsonx_ai.foundation_models.ModelInference") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance
