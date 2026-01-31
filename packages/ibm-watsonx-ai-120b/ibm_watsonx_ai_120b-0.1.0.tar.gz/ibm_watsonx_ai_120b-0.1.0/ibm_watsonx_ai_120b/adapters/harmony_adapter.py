"""Harmony adapter for stripping leaked format tokens.

The gpt-oss models use "Harmony" format internally, and special tokens
sometimes leak into the output. This adapter strips them.
"""

import logging
from typing import Any

from ibm_watsonx_ai_120b.utils.tokens import strip_harmony_tokens

logger = logging.getLogger(__name__)


class HarmonyAdapter:
    """Strips harmony format token leakage from model output.

    Tokens that leak:
    - <|start|>, <|end|>
    - <|channel|>, <|message|>
    - <|constrain|>, <|call|>, <|return|>
    - Combined forms like "assistant<|channel|>analysis"
    """

    @staticmethod
    def clean_response(response: dict[str, Any]) -> dict[str, Any]:
        """Clean harmony tokens from a response object.

        Args:
            response: OpenAI-format response dict

        Returns:
            Cleaned response with harmony tokens removed
        """
        if not isinstance(response, dict):
            return response

        response = response.copy()

        # Clean choices
        if "choices" in response:
            response["choices"] = [
                HarmonyAdapter._clean_choice(choice)
                for choice in response["choices"]
            ]

        return response

    @staticmethod
    def _clean_choice(choice: dict[str, Any]) -> dict[str, Any]:
        """Clean a single choice object.

        Args:
            choice: Choice dict from response

        Returns:
            Cleaned choice
        """
        choice = choice.copy()

        if "message" in choice:
            choice["message"] = HarmonyAdapter._clean_message(choice["message"])

        if "delta" in choice:
            choice["delta"] = HarmonyAdapter._clean_message(choice["delta"])

        return choice

    @staticmethod
    def _clean_message(message: dict[str, Any]) -> dict[str, Any]:
        """Clean a message object.

        Args:
            message: Message dict

        Returns:
            Cleaned message
        """
        message = message.copy()

        # Clean content
        if "content" in message and isinstance(message["content"], str):
            original = message["content"]
            cleaned = strip_harmony_tokens(original)
            if cleaned != original:
                logger.debug(f"Stripped harmony tokens from content")
            message["content"] = cleaned

        # Clean reasoning_content if present
        if "reasoning_content" in message and isinstance(message["reasoning_content"], str):
            message["reasoning_content"] = strip_harmony_tokens(message["reasoning_content"])

        # Clean tool calls if present
        if "tool_calls" in message and isinstance(message["tool_calls"], list):
            message["tool_calls"] = [
                HarmonyAdapter._clean_tool_call(tc)
                for tc in message["tool_calls"]
            ]

        return message

    @staticmethod
    def _clean_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
        """Clean a tool call object.

        Args:
            tool_call: Tool call dict

        Returns:
            Cleaned tool call
        """
        tool_call = tool_call.copy()

        # Clean function name (can get mangled like "assistant<|channel|>analysis")
        if "function" in tool_call:
            func = tool_call["function"] = tool_call["function"].copy()
            if "name" in func and isinstance(func["name"], str):
                func["name"] = strip_harmony_tokens(func["name"])

        return tool_call

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean harmony tokens from text.

        Args:
            text: Text that may contain harmony tokens

        Returns:
            Cleaned text
        """
        return strip_harmony_tokens(text)
