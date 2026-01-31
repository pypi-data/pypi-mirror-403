"""Tests for JSON repair utilities."""

import pytest
from ibm_watsonx_ai_120b.utils.json_repair import (
    extract_json,
    repair_json,
    strip_markdown_code_blocks,
)


class TestExtractJson:
    """Tests for extract_json function."""

    def test_extract_pure_json(self):
        """Test extracting pure JSON."""
        text = '{"name": "John", "age": 30}'
        success, result, error = extract_json(text)

        assert success
        assert result == {"name": "John", "age": 30}
        assert error is None

    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown code block."""
        text = '''Here's the response:
```json
{"name": "John", "age": 30}
```
'''
        success, result, error = extract_json(text)

        assert success
        assert result == {"name": "John", "age": 30}

    def test_extract_json_from_text(self):
        """Test extracting JSON embedded in text."""
        text = 'The result is: {"name": "John", "age": 30} as shown above.'
        success, result, error = extract_json(text)

        assert success
        assert result == {"name": "John", "age": 30}

    def test_extract_json_nested_objects(self):
        """Test extracting nested JSON objects."""
        text = '{"person": {"name": "John", "address": {"city": "NYC"}}}'
        success, result, error = extract_json(text)

        assert success
        assert result["person"]["address"]["city"] == "NYC"

    def test_extract_json_empty_input(self):
        """Test handling empty input."""
        success, result, error = extract_json("")

        assert not success
        assert result is None
        assert "Empty" in error

    def test_extract_json_no_json(self):
        """Test handling text with no JSON."""
        text = "This is just plain text with no JSON."
        success, result, error = extract_json(text)

        assert not success
        assert result is None

    def test_extract_json_with_trailing_comma(self):
        """Test handling JSON with trailing comma."""
        text = '{"name": "John", "age": 30,}'
        success, result, error = extract_json(text)

        # Should succeed after repair
        assert success
        assert result == {"name": "John", "age": 30}


class TestRepairJson:
    """Tests for repair_json function."""

    def test_repair_trailing_comma(self):
        """Test repairing trailing comma."""
        json_str = '{"name": "John",}'
        result = repair_json(json_str)

        assert result is not None
        # The repaired JSON should be parseable
        import json
        parsed = json.loads(result)
        assert parsed["name"] == "John"

    def test_repair_trailing_comma_in_array(self):
        """Test repairing trailing comma in array."""
        json_str = '{"items": [1, 2, 3,]}'
        result = repair_json(json_str)

        assert result is not None
        import json
        parsed = json.loads(result)
        assert parsed["items"] == [1, 2, 3]

    def test_repair_returns_none_for_empty(self):
        """Test that repair returns None for empty input."""
        assert repair_json("") is None
        assert repair_json(None) is None


class TestStripMarkdownCodeBlocks:
    """Tests for strip_markdown_code_blocks function."""

    def test_strip_json_code_block(self):
        """Test stripping ```json code block."""
        text = '```json\n{"key": "value"}\n```'
        result = strip_markdown_code_blocks(text)

        assert result == '{"key": "value"}'

    def test_strip_generic_code_block(self):
        """Test stripping generic ``` code block."""
        text = '```\n{"key": "value"}\n```'
        result = strip_markdown_code_blocks(text)

        assert '{"key": "value"}' in result

    def test_strip_preserves_non_code_block(self):
        """Test that non-code-block text is preserved."""
        text = '{"key": "value"}'
        result = strip_markdown_code_blocks(text)

        assert result == text

    def test_strip_empty_input(self):
        """Test handling empty input."""
        assert strip_markdown_code_blocks("") == ""
