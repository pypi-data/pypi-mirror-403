"""Unit tests for WatsonX client and JSON handling."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestJSONSchemaAdapter:
    """Tests for JSONSchemaAdapter JSON extraction and validation."""

    @pytest.fixture
    def adapter(self):
        """Create a JSONSchemaAdapter instance."""
        from synx_developer.llm.watsonx_client.adapters.json_adapter import JSONSchemaAdapter
        return JSONSchemaAdapter(max_retries=3)

    def test_extract_json_pure_json(self, adapter):
        """Test extracting pure JSON."""
        text = '{"name": "test", "value": 42}'
        success, result, error = adapter.extract_json(text)
        assert success is True
        assert result == {"name": "test", "value": 42}
        assert error is None

    def test_extract_json_from_markdown(self, adapter):
        """Test extracting JSON from markdown code block."""
        text = '''Here is the response:
```json
{"name": "test", "value": 42}
```
'''
        success, result, error = adapter.extract_json(text)
        assert success is True
        assert result == {"name": "test", "value": 42}

    def test_extract_json_embedded_in_text(self, adapter):
        """Test extracting JSON embedded in explanatory text."""
        text = 'Based on the analysis, here is my response: {"status": "success", "count": 10} which satisfies the requirements.'
        success, result, error = adapter.extract_json(text)
        assert success is True
        assert result == {"status": "success", "count": 10}

    def test_extract_json_with_thinking_block(self, adapter):
        """Test extracting JSON after thinking block."""
        text = '''<think>Let me analyze this carefully...</think>
{"result": "found", "items": ["a", "b", "c"]}'''
        # First validate the response to strip thinking
        cleaned = adapter._validate_response(text)
        success, result, error = adapter.extract_json(cleaned)
        assert success is True
        assert result == {"result": "found", "items": ["a", "b", "c"]}

    def test_extract_json_empty_response(self, adapter):
        """Test handling empty response."""
        success, result, error = adapter.extract_json("")
        assert success is False
        assert result is None
        assert "Empty response" in error

    def test_extract_json_no_json_found(self, adapter):
        """Test handling response with no JSON."""
        text = "This is just plain text with no JSON structure."
        success, result, error = adapter.extract_json(text)
        assert success is False
        assert result is None

    def test_thinking_only_detection(self, adapter):
        """Test detection of thinking-only responses."""
        # Full thinking block
        assert adapter._is_thinking_only("<think>Processing...</think>") is True

        # Very short response
        assert adapter._is_thinking_only("ok") is True

        # Empty response
        assert adapter._is_thinking_only("") is True

        # Actual content should not be thinking-only
        assert adapter._is_thinking_only('{"name": "test"}') is False
        assert adapter._is_thinking_only("Here is the detailed response...") is False

    def test_schema_example_generation(self, adapter):
        """Test generating schema examples."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "config": {"type": "object"}
            },
            "required": ["name", "age"]
        }

        example = adapter.generate_schema_example(schema)

        assert "name" in example
        assert isinstance(example["name"], str)
        assert "age" in example
        assert isinstance(example["age"], int)
        assert "active" in example
        assert isinstance(example["active"], bool)
        assert "tags" in example
        assert isinstance(example["tags"], list)

    def test_validate_against_schema_required_fields(self, adapter):
        """Test schema validation for required fields."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            },
            "required": ["name", "value"]
        }

        # Valid object
        valid, error = adapter.validate_against_schema(
            {"name": "test", "value": 42}, schema
        )
        assert valid is True

        # Missing required field
        valid, error = adapter.validate_against_schema(
            {"name": "test"}, schema
        )
        assert valid is False
        assert "Missing required" in error

    def test_validate_against_schema_wrong_type(self, adapter):
        """Test schema validation for wrong types."""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"}
            }
        }

        # Wrong type
        valid, error = adapter.validate_against_schema(
            {"count": "not an integer"}, schema
        )
        assert valid is False
        assert "wrong type" in error.lower()

    def test_is_refusal_detection(self, adapter):
        """Test detection of model refusals."""
        assert adapter.is_refusal("I can't help with that request.") is True
        assert adapter.is_refusal("I'm sorry, but I cannot assist.") is True
        assert adapter.is_refusal("Here is the JSON response you requested.") is False
        assert adapter.is_refusal('{"status": "ok"}') is False

    def test_create_json_system_message(self, adapter):
        """Test creation of JSON system message."""
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "files": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["summary", "files"]
        }

        message = adapter.create_json_system_message(schema, "design_response")

        assert "design_response" in message
        assert "summary" in message
        assert "files" in message
        assert "CRITICAL RULES" in message
        assert "EXACT property names" in message


class TestMessageAdapter:
    """Tests for MessageAdapter message formatting."""

    @pytest.fixture
    def adapter(self):
        """Get MessageAdapter class."""
        from synx_developer.llm.watsonx_client.adapters.message_adapter import MessageAdapter
        return MessageAdapter

    def test_adapt_messages_null_content(self, adapter):
        """Test adapting messages with null content."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": None}
        ]

        adapted = adapter.adapt_messages(messages)

        # Content should never be None
        assert adapted[1]["content"] == ""

    def test_adapt_messages_tool_role(self, adapter):
        """Test converting tool role to user role."""
        messages = [
            {"role": "tool", "content": '{"result": "success"}'}
        ]

        adapted = adapter.adapt_messages(messages)

        assert adapted[0]["role"] == "user"
        assert "Function returned" in adapted[0]["content"]

    def test_inject_system_message_new(self, adapter):
        """Test injecting new system message."""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        modified = adapter.inject_system_message(
            messages, "You are a helpful assistant.", replace=True
        )

        assert len(modified) == 2
        assert modified[0]["role"] == "system"
        assert modified[0]["content"] == "You are a helpful assistant."

    def test_inject_system_message_replace(self, adapter):
        """Test replacing existing system message."""
        messages = [
            {"role": "system", "content": "Old system message"},
            {"role": "user", "content": "Hello"}
        ]

        modified = adapter.inject_system_message(
            messages, "New system message", replace=True
        )

        assert len(modified) == 2
        assert modified[0]["content"] == "New system message"

    def test_format_for_api(self, adapter):
        """Test formatting messages for API."""
        messages = [
            {"role": "system", "content": "System", "extra": "field"},
            {"role": "user", "content": "User message", "metadata": {"key": "value"}}
        ]

        formatted = adapter.format_for_api(messages)

        assert len(formatted) == 2
        assert formatted[0] == {"role": "system", "content": "System"}
        assert formatted[1] == {"role": "user", "content": "User message"}


class TestWatsonXConfig:
    """Tests for WatsonXConfig."""

    def test_from_env(self, monkeypatch):
        """Test creating config from environment variables."""
        from synx_developer.llm.watsonx_client.config import WatsonXConfig

        monkeypatch.setenv("WATSONX_API_KEY", "test-key")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test-project")
        monkeypatch.setenv("WATSONX_MODEL", "test-model")

        config = WatsonXConfig.from_env()

        assert config.api_key == "test-key"
        assert config.project_id == "test-project"
        assert config.model_id == "test-model"

    def test_validate_missing_fields(self):
        """Test validation with missing fields."""
        from synx_developer.llm.watsonx_client.config import WatsonXConfig

        config = WatsonXConfig()
        assert config.validate() is False

        config = WatsonXConfig(api_key="key", project_id="project")
        assert config.validate() is True

    def test_get_generation_params(self):
        """Test getting generation parameters."""
        from synx_developer.llm.watsonx_client.config import WatsonXConfig

        config = WatsonXConfig(
            api_key="key",
            project_id="project",
            max_tokens=8192,
            temperature=0.5,
            reasoning_effort="low"
        )

        params = config.get_generation_params()

        assert params["max_tokens"] == 8192
        assert params["temperature"] == 0.5
        assert params["reasoning_effort"] == "low"


class TestWatsonXClientMocked:
    """Tests for WatsonXClient with mocked IBM SDK."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model."""
        mock = Mock()
        return mock

    def test_format_response(self):
        """Test formatting string response to OpenAI format."""
        from synx_developer.llm.watsonx_client.client import WatsonXClient
        from synx_developer.llm.watsonx_client.config import WatsonXConfig

        # Create config
        config = WatsonXConfig(
            api_key="test-key",
            project_id="test-project"
        )

        # Manually create client without initialization
        client = object.__new__(WatsonXClient)
        client.config = config
        client._cleaned_up = False
        client._model = None
        client._active_streams = []

        # Test _format_response
        response = client._format_response("Hello, world!")

        assert "choices" in response
        assert response["choices"][0]["message"]["content"] == "Hello, world!"
        assert response["choices"][0]["message"]["role"] == "assistant"
        assert response["choices"][0]["finish_reason"] == "stop"

    def test_is_actual_response_json(self):
        """Test detection of actual JSON response."""
        from synx_developer.llm.watsonx_client.client import WatsonXClient
        from synx_developer.llm.watsonx_client.config import WatsonXConfig

        config = WatsonXConfig(api_key="test", project_id="test")
        client = object.__new__(WatsonXClient)
        client.config = config

        # JSON should be detected as actual response
        assert client._is_actual_response('{"name": "test"}') is True
        assert client._is_actual_response('```json\n{"key": "value"}\n```') is True

        # Plain thinking text should not be
        assert client._is_actual_response("Let me think about this...") is False

    def test_try_extract_json(self):
        """Test JSON extraction from various formats."""
        from synx_developer.llm.watsonx_client.client import WatsonXClient
        from synx_developer.llm.watsonx_client.config import WatsonXConfig

        config = WatsonXConfig(api_key="test", project_id="test")
        client = object.__new__(WatsonXClient)
        client.config = config

        # Pure JSON
        result = client._try_extract_json('{"test": 1}')
        assert result == {"test": 1}

        # JSON in markdown
        result = client._try_extract_json('```json\n{"test": 2}\n```')
        assert result == {"test": 2}

        # JSON embedded in text
        result = client._try_extract_json('The result is {"test": 3} as expected.')
        assert result == {"test": 3}

        # No JSON
        result = client._try_extract_json('Just plain text')
        assert result is None


class TestWatsonXGenerator:
    """Tests for WatsonXGenerator wrapper."""

    def test_initialization(self):
        """Test generator initialization."""
        from synx_developer.llm.generator import WatsonXGenerator

        generator = WatsonXGenerator(
            api_key="test-key",
            project_id="test-project",
            model="test-model"
        )

        assert generator.api_key == "test-key"
        assert generator.project_id == "test-project"
        assert generator.model == "test-model"
        assert generator._client is None  # Lazy init

    def test_extract_json_methods(self):
        """Test JSON extraction in generator."""
        from synx_developer.llm.generator import WatsonXGenerator

        generator = WatsonXGenerator(
            api_key="test",
            project_id="test"
        )

        # Pure JSON
        result = generator._extract_json('{"status": "ok"}')
        assert result == {"status": "ok"}

        # Markdown
        result = generator._extract_json('```json\n{"status": "ok"}\n```')
        assert result == {"status": "ok"}

        # Embedded
        result = generator._extract_json('Response: {"status": "ok"} done.')
        assert result == {"status": "ok"}


class TestIntegrationMocked:
    """Integration tests with mocked IBM SDK."""

    @patch('synx_developer.llm.watsonx_client.client.WatsonXClient._initialize')
    def test_chat_with_json_schema_flow(self, mock_init):
        """Test the full flow of chat_with_json_schema."""
        from synx_developer.llm.watsonx_client.client import WatsonXClient
        from synx_developer.llm.watsonx_client.config import WatsonXConfig

        # Create client with mocked initialization
        config = WatsonXConfig(
            api_key="test-key",
            project_id="test-project"
        )

        client = WatsonXClient.__new__(WatsonXClient)
        client.config = config
        client._cleaned_up = False
        client._active_streams = []

        # Set up mock model
        mock_model = Mock()
        mock_model.chat.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": '{"name": "Test Design", "files": []}'
                }
            }]
        }
        client._model = mock_model

        # Set up adapters
        from synx_developer.llm.watsonx_client.adapters import ToolAdapter, JSONSchemaAdapter
        client._tool_adapter = ToolAdapter(max_retries=3)
        client._json_adapter = JSONSchemaAdapter(max_retries=5)

        # Test schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "files": {"type": "array"}
            },
            "required": ["name", "files"]
        }

        # Call chat_with_json_schema
        response = client.chat_with_json_schema(
            messages=[{"role": "user", "content": "Generate a design"}],
            schema=schema
        )

        # Verify response
        assert "choices" in response
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        assert parsed["name"] == "Test Design"
        assert parsed["files"] == []

        # Verify model was called
        assert mock_model.chat.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
