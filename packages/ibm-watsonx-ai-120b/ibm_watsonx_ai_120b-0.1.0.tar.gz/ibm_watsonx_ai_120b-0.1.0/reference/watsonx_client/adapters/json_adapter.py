"""JSON schema adapter for WatsonX.

Handles structured output (JSON mode) via prompt injection for models
that don't support native JSON response formatting.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Callable

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)

from ..exceptions import JSONExtractionError, SchemaValidationError

logger = logging.getLogger(__name__)

# Try to import json_repair
try:
    import json_repair
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False

# Try to import jsonschema for validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logger.warning("jsonschema not installed, schema validation will be limited")


class EmptyResponseError(JSONExtractionError):
    """Model returned empty or thinking-only response."""
    pass


class ThinkingOnlyError(JSONExtractionError):
    """Model returned only internal thinking without actual content."""
    pass


class JSONSchemaAdapter:
    """Adapts JSON schema responses for models without native support.

    Uses prompt injection with schema examples and detailed instructions
    to guide the model to output valid JSON matching the schema.
    """

    def __init__(self, max_retries: int = 5):
        """Initialize JSON schema adapter.

        Args:
            max_retries: Maximum attempts to get valid JSON (higher than tools
                        because JSON formatting is more finicky)
        """
        self.max_retries = max_retries

    def generate_schema_example(self, schema: Dict[str, Any]) -> Dict[str, Any]:
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
        required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            example[prop_name] = self._generate_example_value(prop_name, prop_schema)

        return example

    def _generate_example_value(self, name: str, schema: Dict[str, Any]) -> Any:
        """Generate an example value for a schema property.

        Args:
            name: Property name (used for context-aware examples)
            schema: Property schema

        Returns:
            Example value
        """
        prop_type = schema.get("type", "string")
        name_lower = name.lower()

        if prop_type == "string":
            # Context-aware string examples
            if "name" in name_lower:
                return "John Doe"
            elif "title" in name_lower:
                return "Example Title"
            elif "city" in name_lower:
                return "New York"
            elif "country" in name_lower:
                return "United States"
            elif "email" in name_lower:
                return "user@example.com"
            elif "url" in name_lower or "link" in name_lower:
                return "https://example.com"
            elif "date" in name_lower:
                return "2024-01-15"
            elif "time" in name_lower:
                return "14:30:00"
            elif "description" in name_lower:
                return "A detailed description of the item."
            elif "color" in name_lower:
                return "blue"
            elif "hex" in name_lower:
                return "#0066CC"
            else:
                return "example text"

        elif prop_type in ("number", "integer"):
            if "age" in name_lower:
                return 25
            elif "year" in name_lower:
                return 2024
            elif "count" in name_lower or "quantity" in name_lower:
                return 10
            elif "price" in name_lower or "cost" in name_lower:
                return 99.99
            elif "minutes" in name_lower or "time" in name_lower:
                return 30
            elif "level" in name_lower or "score" in name_lower:
                return 5
            elif "percent" in name_lower:
                return 75
            else:
                return 42

        elif prop_type == "boolean":
            return True

        elif prop_type == "array":
            items_schema = schema.get("items", {})
            items_type = items_schema.get("type", "string")

            if items_type == "string":
                if "step" in name_lower or "instruction" in name_lower:
                    return ["First step", "Second step", "Third step"]
                elif "tag" in name_lower:
                    return ["tag1", "tag2"]
                elif "ingredient" in name_lower:
                    return ["flour", "sugar", "eggs"]
                else:
                    return ["item1", "item2"]

            elif items_type == "object":
                # Generate example for nested object
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

    def get_property_reminders(self, schema: Dict[str, Any]) -> str:
        """Generate reminders for exact property names to use.

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
            if prop_type == "array":
                items_schema = prop_schema.get("items", {})
                if items_schema.get("type") == "object":
                    reminders.append(f'- Use "{prop_name}" as array of objects')
                else:
                    reminders.append(f'- Use "{prop_name}" as array')
            else:
                reminders.append(f'- Use "{prop_name}" (type: {prop_type})')

        return "\n".join(reminders)

    def create_json_system_message(
        self,
        schema: Dict[str, Any],
        schema_name: str = "response"
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
3. Follow the EXACT data types specified (string, number, boolean, array, object)
4. Include ALL required fields
5. Do NOT add extra wrapper objects like {{"data": ...}} or {{"result": ...}}
6. Do NOT rename properties (use exact names from schema)
7. Do NOT add any text before or after the JSON
8. Start with {{ and end with }}
9. The root level must match the schema root level exactly

PROPERTY NAME REMINDERS:
{reminders}

The JSON must be a valid response that matches the schema structure precisely."""

    def create_json_object_system_message(self) -> str:
        """Create system message for simple JSON object mode (no schema).

        Returns:
            System message content
        """
        return """You must respond with valid JSON only.
Output a JSON object without any additional text.
Start with { and end with }.
Do not include any markdown formatting or code blocks."""

    def extract_json(self, text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Extract JSON from text response.

        Args:
            text: Raw model response

        Returns:
            Tuple of (success, json_object, error_message)
        """
        if not text:
            return False, None, "Empty response"

        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            end_marker = text.find("```", 3)
            if end_marker != -1:
                text = text[3:end_marker].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

        # Find JSON boundaries
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            return False, None, "No valid JSON structure found"

        json_text = text[start:end + 1]

        # Try direct parse
        try:
            data = json.loads(json_text)
            if isinstance(data, dict):
                return True, data, None
        except json.JSONDecodeError as e:
            logger.debug(f"Initial JSON parse failed: {e}")

            # Try json_repair
            if HAS_JSON_REPAIR:
                try:
                    repaired = json_repair.repair_json(json_text)
                    data = json.loads(repaired)
                    if isinstance(data, dict):
                        logger.debug("Successfully repaired JSON")
                        return True, data, None
                except Exception as repair_error:
                    logger.debug(f"JSON repair failed: {repair_error}")

        return False, None, f"Failed to parse JSON: {json_text[:200]}..."

    def validate_against_schema(
        self,
        json_obj: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate JSON object against schema.

        Args:
            json_obj: Parsed JSON object
            schema: JSON schema to validate against

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try jsonschema if available
        if HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=json_obj, schema=schema)
                return True, None
            except jsonschema.exceptions.ValidationError as e:
                return False, f"Schema validation: {str(e)}"

        # Manual validation fallback
        return self._manual_validate(json_obj, schema)

    def _manual_validate(
        self,
        json_obj: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Manual schema validation (fallback when jsonschema unavailable).

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
            # Check if this might be due to token truncation
            end_fields = ["steps", "instructions", "conclusion", "results", "summary"]
            if any(f in end_fields for f in missing):
                return False, f"Missing required fields (possibly token limit): {missing}"
            return False, f"Missing required fields: {missing}"

        # Check field types
        for field, value in json_obj.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if not self._validate_type(value, expected_type, properties[field]):
                    return False, f"Field '{field}' has wrong type. Expected {expected_type}"

        # Validate nested objects and arrays
        for field, prop_schema in properties.items():
            if field in json_obj:
                value = json_obj[field]
                if prop_schema.get("type") == "array" and isinstance(value, list):
                    items_schema = prop_schema.get("items", {})
                    if items_schema.get("type") == "object":
                        for i, item in enumerate(value):
                            valid, error = self._manual_validate(item, items_schema)
                            if not valid:
                                return False, f"Array item {i} in '{field}': {error}"

                elif prop_schema.get("type") == "object" and isinstance(value, dict):
                    valid, error = self._manual_validate(value, prop_schema)
                    if not valid:
                        return False, f"Nested object '{field}': {error}"

        return True, None

    def _validate_type(self, value: Any, expected_type: str, prop_schema: Dict[str, Any]) -> bool:
        """Validate value against expected type.

        Args:
            value: Value to validate
            expected_type: Expected JSON type
            prop_schema: Property schema

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
        else:
            return True  # Unknown type, assume valid

    def is_refusal(self, content: str) -> bool:
        """Detect if response is a refusal.

        Args:
            content: Response content

        Returns:
            True if response appears to be a refusal
        """
        if not content:
            return False

        refusal_patterns = [
            "i can't", "i cannot", "i'm sorry", "i apologize",
            "unable to", "not able to", "can't help", "cannot help",
            "not appropriate", "against my", "violates", "harmful",
            "i don't feel comfortable", "i shouldn't", "i won't"
        ]

        content_lower = content.lower()[:200]  # Check start of response
        return any(pattern in content_lower for pattern in refusal_patterns)

    def _is_thinking_only(self, response_text: str) -> bool:
        """Check if response contains only thinking/reasoning without actual content.

        Args:
            response_text: Raw model response

        Returns:
            True if response appears to be thinking-only
        """
        if not response_text or not response_text.strip():
            return True

        text = response_text.strip().lower()

        # Common thinking-only patterns
        thinking_patterns = [
            r"^<think>.*</think>$",
            r"^<thinking>.*</thinking>$",
            r"^<reasoning>.*</reasoning>$",
            r"^\[thinking\].*\[/thinking\]$",
            r"^let me think.*$",
            r"^thinking:.*$",
        ]

        for pattern in thinking_patterns:
            if re.match(pattern, text, re.DOTALL | re.IGNORECASE):
                return True

        # Very short responses
        if len(text) < 3:
            return True

        # Harmony-style thinking blocks that consume the whole response
        if text.startswith("<think>") and "</think>" in text:
            after_think = text.split("</think>", 1)[-1].strip()
            if not after_think:
                return True

        return False

    def _validate_response(self, response_text: str) -> str:
        """Validate response is not empty or thinking-only.

        Args:
            response_text: Raw model response

        Returns:
            Cleaned response text

        Raises:
            EmptyResponseError: If response is empty
            ThinkingOnlyError: If response contains only thinking
        """
        if not response_text:
            raise EmptyResponseError("Model returned empty response")

        if self._is_thinking_only(response_text):
            raise ThinkingOnlyError(f"Model returned thinking-only response: {response_text[:100]}...")

        # Strip thinking blocks if present but there's content after
        text = response_text.strip()
        if "<think>" in text.lower() and "</think>" in text.lower():
            parts = re.split(r"</think>", text, flags=re.IGNORECASE)
            if len(parts) > 1:
                after_think = parts[-1].strip()
                if after_think:
                    logger.debug("Stripped thinking block from response")
                    return after_think

        return text

    def process_with_schema(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        model_call_fn: Callable[[List[Dict[str, Any]]], str],
        schema_name: str = "response"
    ) -> Dict[str, Any]:
        """Process a request with JSON schema via prompt injection.

        Uses tenacity for robust retry handling of transient failures,
        empty responses, and thinking-only outputs.

        Args:
            messages: Conversation messages
            schema: JSON schema to enforce
            model_call_fn: Function to call the model
            schema_name: Name for the schema

        Returns:
            OpenAI-compatible response with JSON content

        Raises:
            JSONExtractionError: If JSON extraction fails after all retries
            SchemaValidationError: If JSON doesn't match schema after retries
        """
        from .message_adapter import MessageAdapter

        # Create system message with schema instructions
        system_content = self.create_json_system_message(schema, schema_name)
        modified_messages = MessageAdapter.inject_system_message(
            messages.copy(), system_content, replace=True
        )

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type((JSONExtractionError, SchemaValidationError, EmptyResponseError, ThinkingOnlyError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        def attempt_json_generation():
            response_text = model_call_fn(modified_messages)

            # Validate response isn't empty or thinking-only
            response_text = self._validate_response(response_text)

            logger.info(f"JSON schema response: {response_text[:300]}...")

            # Check for refusal
            if self.is_refusal(response_text):
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "refusal": response_text
                        },
                        "finish_reason": "stop"
                    }]
                }

            # Extract JSON
            success, json_obj, error = self.extract_json(response_text)

            if not success:
                if any(char in response_text for char in ["{", "}", '"', ":"]):
                    raise JSONExtractionError(f"Failed to extract JSON: {error}")
                # No JSON markers - return as regular content
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                            "refusal": None
                        },
                        "finish_reason": "stop"
                    }]
                }

            logger.info(f"Extracted JSON: {json.dumps(json_obj, indent=2)[:500]}")

            # Validate against schema
            valid, validation_error = self.validate_against_schema(json_obj, schema)
            if not valid:
                raise SchemaValidationError(f"Schema validation failed: {validation_error}")

            logger.info("Schema validation passed")

            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(json_obj, ensure_ascii=False, separators=(",", ":")),
                        "refusal": None
                    },
                    "finish_reason": "stop"
                }]
            }

        try:
            return attempt_json_generation()
        except RetryError as e:
            last_error = e.last_attempt.exception() if e.last_attempt else e
            logger.error(f"JSON schema processing failed after {self.max_retries} attempts: {last_error}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "error": {
                                "message": str(last_error),
                                "type": "structured_output_error"
                            }
                        }),
                        "refusal": None
                    },
                    "finish_reason": "stop"
                }]
            }
        except (JSONExtractionError, SchemaValidationError, EmptyResponseError, ThinkingOnlyError) as e:
            logger.error(f"JSON schema processing failed: {e}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "error": {
                                "message": str(e),
                                "type": "structured_output_error"
                            }
                        }),
                        "refusal": None
                    },
                    "finish_reason": "stop"
                }]
            }

    def process_json_object(
        self,
        messages: List[Dict[str, Any]],
        model_call_fn: Callable[[List[Dict[str, Any]]], str]
    ) -> Dict[str, Any]:
        """Process a request with simple JSON object mode (no schema).

        Uses tenacity for robust retry handling.

        Args:
            messages: Conversation messages
            model_call_fn: Function to call the model

        Returns:
            OpenAI-compatible response with JSON content
        """
        from .message_adapter import MessageAdapter

        system_content = self.create_json_object_system_message()
        modified_messages = MessageAdapter.inject_system_message(
            messages.copy(), system_content, replace=True
        )

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type((JSONExtractionError, EmptyResponseError, ThinkingOnlyError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        def attempt_json_generation():
            response_text = model_call_fn(modified_messages)

            # Validate response
            response_text = self._validate_response(response_text)

            success, json_obj, error = self.extract_json(response_text)

            if not success:
                if any(char in response_text for char in ["{", "}", '"', ":"]):
                    raise JSONExtractionError(f"Failed to extract JSON: {error}")
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                            "refusal": None
                        },
                        "finish_reason": "stop"
                    }]
                }

            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(json_obj, ensure_ascii=False),
                        "refusal": None
                    },
                    "finish_reason": "stop"
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
                        "refusal": None
                    },
                    "finish_reason": "stop"
                }]
            }
        except (JSONExtractionError, EmptyResponseError, ThinkingOnlyError) as e:
            logger.error(f"JSON object processing failed: {e}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"error": str(e)}),
                        "refusal": None
                    },
                    "finish_reason": "stop"
                }]
            }
