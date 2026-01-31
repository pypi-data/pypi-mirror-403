"""JSON adapter for emulating structured output via prompt injection.

JSON schema mode is ignored by vLLM-hosted gpt-oss models, so we
inject schema instructions into the prompt and validate the response.
"""

import json
import logging
import re
from typing import Any, Callable

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

from ibm_watsonx_ai_120b.config import get_config
from ibm_watsonx_ai_120b.exceptions import (
    JSONExtractionError,
    SchemaValidationError,
    ThinkingOnlyResponseError,
)
from ibm_watsonx_ai_120b.utils.json_repair import extract_json

logger = logging.getLogger(__name__)

# Try to import jsonschema for validation
try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logger.debug("jsonschema not installed, using basic validation")


class JSONAdapter:
    """Emulates JSON schema mode via prompt injection.

    Since native JSON schema mode doesn't work, we:
    1. Inject schema description and examples into prompt
    2. Parse JSON from the response
    3. Validate against the schema
    """

    def __init__(self, max_retries: int | None = None):
        """Initialize JSON adapter.

        Args:
            max_retries: Maximum attempts to get valid JSON
        """
        # JSON is finicky, use more retries than default
        self.max_retries = (max_retries or get_config().max_retries) + 2

    def generate_schema_example(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate an example JSON object matching the schema.

        Args:
            schema: JSON schema definition

        Returns:
            Example object matching the schema
        """
        if not isinstance(schema, dict) or schema.get("type") != "object":
            return {}

        example = {}
        properties = schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            example[prop_name] = self._generate_example_value(prop_name, prop_schema)

        return example

    def _generate_example_value(self, name: str, schema: dict[str, Any]) -> Any:
        """Generate an example value for a schema property.

        Args:
            name: Property name
            schema: Property schema

        Returns:
            Example value
        """
        prop_type = schema.get("type", "string")
        name_lower = name.lower()

        if prop_type == "string":
            # Context-aware examples
            if "name" in name_lower:
                return "John Doe"
            elif "title" in name_lower:
                return "Example Title"
            elif "description" in name_lower:
                return "A detailed description."
            elif "email" in name_lower:
                return "user@example.com"
            elif "url" in name_lower:
                return "https://example.com"
            elif "date" in name_lower:
                return "2024-01-15"
            else:
                return "example text"

        elif prop_type in ("number", "integer"):
            if "year" in name_lower:
                return 2024
            elif "count" in name_lower:
                return 10
            elif "price" in name_lower:
                return 99.99
            else:
                return 42

        elif prop_type == "boolean":
            return True

        elif prop_type == "array":
            items_schema = schema.get("items", {})
            items_type = items_schema.get("type", "string")

            if items_type == "string":
                return ["item1", "item2"]
            elif items_type == "object":
                item_example = self.generate_schema_example(items_schema)
                return [item_example] if item_example else []
            elif items_type in ("number", "integer"):
                return [1, 2, 3]
            else:
                return []

        elif prop_type == "object":
            return self.generate_schema_example(schema)

        else:
            return None

    def get_property_reminders(self, schema: dict[str, Any]) -> str:
        """Generate reminders for exact property names.

        Args:
            schema: JSON schema

        Returns:
            Formatted string with property reminders
        """
        if not isinstance(schema, dict) or schema.get("type") != "object":
            return ""

        properties = schema.get("properties", {})
        if not properties:
            return ""

        reminders = []
        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            reminders.append(f'- Use "{prop_name}" (type: {prop_type})')

        return "\n".join(reminders)

    def create_json_system_message(
        self,
        schema: dict[str, Any],
        schema_name: str = "response",
    ) -> str:
        """Create system message for JSON schema mode.

        Args:
            schema: JSON schema to enforce
            schema_name: Name for the schema

        Returns:
            System message content
        """
        schema_str = json.dumps(schema, indent=2)
        example = self.generate_schema_example(schema)
        example_str = json.dumps(example, indent=2) if example else "{}"
        reminders = self.get_property_reminders(schema)

        return f"""You must respond with valid JSON that EXACTLY matches this schema.

Schema name: {schema_name}
Required JSON schema:
{schema_str}

EXAMPLE of correct format:
{example_str}

CRITICAL RULES:
1. Output ONLY valid JSON that matches the schema EXACTLY
2. Use the EXACT property names from the schema - do NOT change them
3. Follow the EXACT data types specified
4. Include ALL required fields
5. Do NOT add extra wrapper objects
6. Do NOT add any text before or after the JSON
7. Start with {{ and end with }}

PROPERTY NAME REMINDERS:
{reminders}"""

    def validate_against_schema(
        self,
        json_obj: dict[str, Any],
        schema: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate JSON object against schema.

        Args:
            json_obj: Parsed JSON object
            schema: JSON schema to validate against

        Returns:
            Tuple of (is_valid, error_message)
        """
        if HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=json_obj, schema=schema)
                return True, None
            except jsonschema.exceptions.ValidationError as e:
                return False, f"Schema validation: {e.message}"

        # Manual validation fallback
        return self._manual_validate(json_obj, schema)

    def _manual_validate(
        self,
        json_obj: dict[str, Any],
        schema: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Manual schema validation fallback.

        Args:
            json_obj: Parsed JSON object
            schema: JSON schema

        Returns:
            Tuple of (is_valid, error_message)
        """
        if schema.get("type") != "object":
            return True, None

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        missing = [f for f in required if f not in json_obj]
        if missing:
            return False, f"Missing required fields: {missing}"

        # Check field types
        for field, value in json_obj.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if not self._validate_type(value, expected_type):
                    return False, f"Field '{field}' has wrong type. Expected {expected_type}"

        return True, None

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value against expected type.

        Args:
            value: Value to validate
            expected_type: Expected JSON type

        Returns:
            True if valid
        """
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        return True

    def process_with_schema(
        self,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
        model_call_fn: Callable[[list[dict[str, Any]]], str],
        schema_name: str = "response",
    ) -> dict[str, Any]:
        """Process a request with JSON schema via prompt injection.

        Args:
            messages: Conversation messages
            schema: JSON schema to enforce
            model_call_fn: Function to call the model
            schema_name: Name for the schema

        Returns:
            OpenAI-compatible response with JSON content
        """
        from ibm_watsonx_ai_120b.adapters.message_adapter import MessageAdapter

        # Create system message with schema instructions
        system_content = self.create_json_system_message(schema, schema_name)
        modified_messages = MessageAdapter.inject_system_message(
            messages.copy(), system_content, replace=True
        )

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type(
                (JSONExtractionError, SchemaValidationError, ThinkingOnlyResponseError)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def attempt_json_generation():
            response_text = model_call_fn(modified_messages)

            if not response_text or not response_text.strip():
                raise ThinkingOnlyResponseError("Empty response")

            logger.debug(f"JSON schema response: {response_text[:300]}...")

            # Extract JSON
            success, json_obj, error = extract_json(response_text)

            if not success:
                raise JSONExtractionError(f"Failed to extract JSON: {error}")

            logger.debug(f"Extracted JSON: {json.dumps(json_obj)[:500]}")

            # Validate against schema
            valid, validation_error = self.validate_against_schema(json_obj, schema)
            if not valid:
                raise SchemaValidationError(validation_error or "Validation failed", schema_name)

            logger.debug("Schema validation passed")

            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(json_obj, ensure_ascii=False),
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }

        try:
            return attempt_json_generation()
        except RetryError as e:
            last_error = e.last_attempt.exception() if e.last_attempt else e
            logger.error(f"JSON schema processing failed after retries: {last_error}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "error": {
                                "message": str(last_error),
                                "type": "structured_output_error",
                            }
                        }),
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }
        except (JSONExtractionError, SchemaValidationError, ThinkingOnlyResponseError) as e:
            logger.error(f"JSON schema processing failed: {e}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "error": {
                                "message": str(e),
                                "type": "structured_output_error",
                            }
                        }),
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }

    def process_json_object(
        self,
        messages: list[dict[str, Any]],
        model_call_fn: Callable[[list[dict[str, Any]]], str],
    ) -> dict[str, Any]:
        """Process a request with simple JSON object mode (no schema).

        Args:
            messages: Conversation messages
            model_call_fn: Function to call the model

        Returns:
            OpenAI-compatible response with JSON content
        """
        from ibm_watsonx_ai_120b.adapters.message_adapter import MessageAdapter

        system_content = """You must respond with valid JSON only.
Output a JSON object without any additional text.
Start with { and end with }.
Do not include any markdown formatting or code blocks."""

        modified_messages = MessageAdapter.inject_system_message(
            messages.copy(), system_content, replace=True
        )

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type((JSONExtractionError, ThinkingOnlyResponseError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def attempt_json_generation():
            response_text = model_call_fn(modified_messages)

            if not response_text or not response_text.strip():
                raise ThinkingOnlyResponseError("Empty response")

            success, json_obj, error = extract_json(response_text)

            if not success:
                raise JSONExtractionError(f"Failed to extract JSON: {error}")

            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(json_obj, ensure_ascii=False),
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }

        try:
            return attempt_json_generation()
        except RetryError as e:
            last_error = e.last_attempt.exception() if e.last_attempt else e
            logger.error(f"JSON object processing failed: {last_error}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"error": str(last_error)}),
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }
        except (JSONExtractionError, ThinkingOnlyResponseError) as e:
            logger.error(f"JSON object processing failed: {e}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"error": str(e)}),
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }
