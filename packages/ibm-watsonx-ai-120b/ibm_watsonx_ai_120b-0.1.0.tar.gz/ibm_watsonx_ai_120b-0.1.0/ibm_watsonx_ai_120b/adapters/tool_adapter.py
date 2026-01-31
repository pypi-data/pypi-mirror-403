"""Tool adapter for emulating function calling via prompt injection.

Native tool calling is broken on vLLM-hosted gpt-oss models, so we
inject tool descriptions into the prompt and parse the response.
"""

import json
import logging
import re
import time
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
from ibm_watsonx_ai_120b.exceptions import ToolExtractionError, ThinkingOnlyResponseError
from ibm_watsonx_ai_120b.utils.json_repair import extract_json

logger = logging.getLogger(__name__)

# System prompt template for tool use
TOOL_SYSTEM_PROMPT = """You are an AI assistant with access to tools/functions.

AVAILABLE TOOLS:
{tools_description}

TOOL USAGE INSTRUCTIONS:
When you need to use a tool, you MUST respond with ONLY a JSON object in this exact format:
{{
  "tool_calls": [
    {{
      "id": "call_<unique_id>",
      "type": "function",
      "function": {{
        "name": "<function_name>",
        "arguments": {{<arguments_as_json_object>}}
      }}
    }}
  ]
}}

CRITICAL RULES:
1. When using tools, output ONLY the JSON structure above - no other text
2. Start with {{ and end with }}
3. Use proper JSON syntax (double quotes, no trailing commas)
4. Arguments must be a valid JSON object, not a string
5. Multiple tools can be called by adding more objects to the tool_calls array

When NOT using tools, respond normally with helpful text.

{tool_choice_instruction}"""


class ToolAdapter:
    """Emulates tool/function calling via prompt injection.

    Since native tool calling doesn't work, we:
    1. Inject tool descriptions into the system prompt
    2. Instruct the model to output tool calls as JSON
    3. Parse and validate the JSON response
    """

    def __init__(self, max_retries: int | None = None):
        """Initialize tool adapter.

        Args:
            max_retries: Maximum attempts to extract valid tool calls
        """
        self.max_retries = max_retries or get_config().max_retries

    def format_tools_description(self, tools: list[dict[str, Any]]) -> str:
        """Format tools into human-readable description.

        Args:
            tools: List of tool definitions in OpenAI format

        Returns:
            Formatted string describing available tools
        """
        if not tools:
            return "No tools available."

        descriptions = []
        for tool in tools:
            if tool.get("type") != "function":
                continue

            func = tool.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "No description")

            tool_desc = f"- {name}: {desc}"

            # Add parameter details
            params = func.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])

            if properties:
                param_lines = []
                for param_name, param_info in properties.items():
                    param_type = param_info.get("type", "any")
                    req_marker = " (required)" if param_name in required else ""
                    param_desc = param_info.get("description", "")
                    if param_desc:
                        param_lines.append(
                            f"    - {param_name}: {param_type}{req_marker} - {param_desc}"
                        )
                    else:
                        param_lines.append(f"    - {param_name}: {param_type}{req_marker}")

                if param_lines:
                    tool_desc += "\n" + "\n".join(param_lines)

            descriptions.append(tool_desc)

        return "\n".join(descriptions)

    def create_tool_system_message(
        self,
        tools: list[dict[str, Any]],
        tool_choice: str | dict[str, Any] = "auto",
    ) -> str:
        """Create system message for tool use.

        Args:
            tools: List of tool definitions
            tool_choice: Tool selection mode

        Returns:
            System message content
        """
        if tool_choice == "none":
            return "You are a helpful assistant. Do not use any tools for this response."

        tools_description = self.format_tools_description(tools)
        tool_choice_instruction = ""

        if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            # Forcing a specific function
            func_name = tool_choice.get("function", {}).get("name", "")

            # Find the function details
            func_details = None
            for tool in tools:
                if tool.get("type") == "function":
                    if tool.get("function", {}).get("name") == func_name:
                        func_details = tool.get("function")
                        break

            if func_details:
                params_json = json.dumps(func_details.get("parameters", {}), indent=2)
                tool_choice_instruction = f"""
IMPORTANT: You MUST use the '{func_name}' function to respond.
The '{func_name}' function expects these parameters:
{params_json}

You MUST call this function with appropriate arguments."""

        elif tool_choice == "auto":
            tool_choice_instruction = "\nUse tools when appropriate to answer the user's query."

        return TOOL_SYSTEM_PROMPT.format(
            tools_description=tools_description,
            tool_choice_instruction=tool_choice_instruction,
        )

    def extract_tool_calls(
        self, response_text: str
    ) -> tuple[bool, list[dict[str, Any]] | None, str | None]:
        """Extract tool calls from model response.

        Args:
            response_text: Raw model response

        Returns:
            Tuple of (success, tool_calls, error_message)
        """
        if not response_text:
            return False, None, "Empty response"

        cleaned = response_text.strip()

        # Remove markdown code blocks if present
        if "```" in cleaned:
            pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
            matches = re.findall(pattern, cleaned, re.DOTALL)
            if matches:
                cleaned = matches[0].strip()

        # Try to extract JSON
        success, data, error = extract_json(cleaned)

        if success and data:
            if "tool_calls" in data and isinstance(data["tool_calls"], list):
                return True, data["tool_calls"], None

        # Check if it looks like a failed tool call attempt
        indicators = ["tool_calls", '"name":', "function", "arguments"]
        if any(ind in cleaned.lower() for ind in indicators):
            return False, None, f"Response contains tool markers but invalid JSON: {cleaned[:200]}..."

        return False, None, "No tool calls found in response"

    def validate_tool_call(
        self,
        tool_call: dict[str, Any],
        available_tools: list[dict[str, Any]],
    ) -> tuple[bool, str | None]:
        """Validate a single tool call.

        Args:
            tool_call: Extracted tool call
            available_tools: List of available tool definitions

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check structure
        required_fields = ["id", "type", "function"]
        if not all(k in tool_call for k in required_fields):
            missing = [k for k in required_fields if k not in tool_call]
            return False, f"Missing required fields: {missing}"

        if tool_call.get("type") != "function":
            return False, f"Invalid type: {tool_call.get('type')}"

        func = tool_call.get("function", {})
        if not all(k in func for k in ["name", "arguments"]):
            return False, "Function missing name or arguments"

        # Find matching tool
        func_name = func.get("name")
        matching_tool = None
        for tool in available_tools:
            if tool.get("type") == "function":
                if tool.get("function", {}).get("name") == func_name:
                    matching_tool = tool
                    break

        if not matching_tool:
            return False, f"Unknown function: {func_name}"

        # Ensure arguments is a dict
        if isinstance(func.get("arguments"), str):
            try:
                func["arguments"] = json.loads(func["arguments"])
            except json.JSONDecodeError:
                return False, "Invalid arguments JSON"
        elif not isinstance(func.get("arguments"), dict):
            return False, "Arguments must be a JSON object"

        # Check required parameters
        tool_params = matching_tool.get("function", {}).get("parameters", {})
        required_params = tool_params.get("required", [])
        for param in required_params:
            if param not in func.get("arguments", {}):
                return False, f"Missing required parameter: {param}"

        return True, None

    def format_response(
        self,
        response_text: str,
        tools: list[dict[str, Any]],
        tool_choice: str | dict[str, Any] = "auto",
    ) -> dict[str, Any]:
        """Format model response to OpenAI-compatible format.

        Args:
            response_text: Raw model response
            tools: Available tools
            tool_choice: Tool selection mode

        Returns:
            OpenAI-compatible response dict
        """
        if tool_choice == "none":
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }

        success, tool_calls, error = self.extract_tool_calls(response_text)

        if not success:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }

        # Validate and collect valid tool calls
        valid_calls = []
        for tc in tool_calls or []:
            is_valid, err = self.validate_tool_call(tc, tools)
            if is_valid:
                if not tc.get("id"):
                    tc["id"] = f"call_{int(time.time() * 1000)}_{len(valid_calls)}"
                valid_calls.append(tc)
            else:
                logger.warning(f"Invalid tool call: {err}")

        if valid_calls:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": valid_calls,
                        "refusal": None,
                    },
                    "finish_reason": "tool_calls",
                }]
            }
        else:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }

    def process_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model_call_fn: Callable[[list[dict[str, Any]]], str],
        tool_choice: str | dict[str, Any] = "auto",
    ) -> dict[str, Any]:
        """Process a request with tools via prompt injection.

        Args:
            messages: Conversation messages
            tools: Tool definitions
            model_call_fn: Function to call the model
            tool_choice: Tool selection mode

        Returns:
            OpenAI-compatible response with tool calls if applicable
        """
        from ibm_watsonx_ai_120b.adapters.message_adapter import MessageAdapter

        if tool_choice == "none":
            response = model_call_fn(messages)
            return self.format_response(response, tools, tool_choice)

        # Create system message with tool instructions
        system_content = self.create_tool_system_message(tools, tool_choice)
        modified_messages = MessageAdapter.inject_system_message(
            messages.copy(), system_content, replace=True
        )

        forced_function = None
        if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            forced_function = tool_choice.get("function", {}).get("name", "")

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type((ToolExtractionError, ThinkingOnlyResponseError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def attempt_tool_call():
            response_text = model_call_fn(modified_messages)

            if not response_text or not response_text.strip():
                raise ThinkingOnlyResponseError("Empty response")

            logger.debug(f"Tool call response: {response_text[:300]}...")

            result = self.format_response(response_text, tools, tool_choice)

            # Check if we got tool calls
            message = result.get("choices", [{}])[0].get("message", {})
            if message.get("tool_calls"):
                # If forcing a specific function, verify it was called
                if forced_function:
                    actual = message["tool_calls"][0].get("function", {}).get("name", "")
                    if actual != forced_function:
                        raise ToolExtractionError(
                            f"Model called {actual} instead of forced {forced_function}"
                        )
                return result

            # If forcing a function but got no tool calls, retry
            if forced_function:
                raise ToolExtractionError("Model did not use the forced function")

            # Otherwise it's a valid text response (for auto mode)
            return result

        try:
            return attempt_tool_call()
        except RetryError as e:
            last_error = e.last_attempt.exception() if e.last_attempt else e
            logger.error(f"Tool calling failed after {self.max_retries} attempts: {last_error}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"I understand you want me to use the tools, but I'm having trouble formatting the response correctly. Error: {last_error}",
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }
        except (ToolExtractionError, ThinkingOnlyResponseError) as e:
            logger.error(f"Tool calling failed: {e}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"I understand you want me to use the tools, but I'm having trouble formatting the response correctly. Error: {e}",
                        "refusal": None,
                    },
                    "finish_reason": "stop",
                }]
            }
