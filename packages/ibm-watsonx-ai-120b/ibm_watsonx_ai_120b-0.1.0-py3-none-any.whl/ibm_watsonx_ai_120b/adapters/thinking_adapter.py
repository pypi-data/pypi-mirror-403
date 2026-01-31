"""Thinking adapter for handling reasoning_content issues.

The gpt-oss models sometimes return only reasoning_content without actual
content, or include <think> blocks in their output.
"""

import logging
import re
from typing import Any

from ibm_watsonx_ai_120b.exceptions import ThinkingOnlyResponseError

logger = logging.getLogger(__name__)


class ThinkingAdapter:
    """Handles reasoning_content and thinking block issues.

    Problems fixed:
    - reasoning_content returned without content
    - <think>...</think> blocks in output
    - Thinking text mixed with actual response
    """

    # Patterns that indicate actual content vs just thinking
    CONTENT_INDICATORS = [
        r"^\s*\{",  # Starts with JSON
        r"^\s*#",  # Starts with markdown heading
        r"^\s*```",  # Starts with code block
        r"^\s*\[",  # Starts with array
        r"^\s*<\w+>",  # Starts with XML/HTML tag (but not <think>)
    ]

    # Patterns for thinking-only responses
    THINKING_PATTERNS = [
        r"^<think>.*</think>\s*$",
        r"^<thinking>.*</thinking>\s*$",
        r"^<reasoning>.*</reasoning>\s*$",
        r"^\[thinking\].*\[/thinking\]\s*$",
    ]

    @staticmethod
    def process_response(response: dict[str, Any]) -> dict[str, Any]:
        """Process response to handle thinking/reasoning issues.

        Args:
            response: OpenAI-format response dict

        Returns:
            Processed response

        Raises:
            ThinkingOnlyResponseError: If response is thinking-only and
                                       cannot be salvaged
        """
        if not isinstance(response, dict) or "choices" not in response:
            return response

        response = response.copy()
        response["choices"] = [
            ThinkingAdapter._process_choice(choice)
            for choice in response["choices"]
        ]

        return response

    @staticmethod
    def _process_choice(choice: dict[str, Any]) -> dict[str, Any]:
        """Process a single choice.

        Args:
            choice: Choice dict

        Returns:
            Processed choice

        Raises:
            ThinkingOnlyResponseError: If thinking-only
        """
        choice = choice.copy()

        if "message" not in choice:
            return choice

        message = choice["message"] = choice["message"].copy()
        content = message.get("content", "")
        reasoning = message.get("reasoning_content", "")

        # If we have content, strip any thinking blocks from it
        if content:
            cleaned = ThinkingAdapter.strip_thinking_blocks(content)
            if cleaned != content:
                logger.debug("Stripped thinking blocks from content")
                message["content"] = cleaned
                content = cleaned

        # If content is empty but reasoning has actual content, promote it
        if not content and reasoning:
            if ThinkingAdapter._is_actual_content(reasoning):
                logger.info("Promoting reasoning_content to content")
                cleaned_reasoning = ThinkingAdapter.strip_thinking_blocks(reasoning)
                message["content"] = cleaned_reasoning
            else:
                # It's just thinking, raise for retry
                raise ThinkingOnlyResponseError(reasoning[:200])

        # Check for completely empty response
        if not message.get("content") and not message.get("tool_calls"):
            raise ThinkingOnlyResponseError("(empty response)")

        return choice

    @staticmethod
    def strip_thinking_blocks(text: str) -> str:
        """Remove <think>...</think> and similar blocks from text.

        Args:
            text: Text that may contain thinking blocks

        Returns:
            Text with thinking blocks removed
        """
        if not text:
            return text

        # Remove <think>...</think> blocks
        patterns = [
            r"<think>.*?</think>",
            r"<thinking>.*?</thinking>",
            r"<reasoning>.*?</reasoning>",
            r"\[thinking\].*?\[/thinking\]",
        ]

        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

        # Clean up whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        text = text.strip()

        return text

    @staticmethod
    def _is_actual_content(text: str) -> bool:
        """Check if text contains actual content vs just thinking.

        Args:
            text: Text to check

        Returns:
            True if text appears to be actual content
        """
        if not text:
            return False

        # Strip thinking blocks first to see what remains
        cleaned = ThinkingAdapter.strip_thinking_blocks(text)
        if not cleaned:
            return False

        stripped = cleaned.strip()

        # Check for content indicators
        for pattern in ThinkingAdapter.CONTENT_INDICATORS:
            if pattern == r"^\s*<\w+>":
                # Special case: don't match <think> as content
                if re.match(r"^\s*<think", stripped, re.IGNORECASE):
                    continue
            if re.match(pattern, stripped, re.DOTALL):
                return True

        # Check if it looks like structured content (JSON)
        if "{" in stripped and "}" in stripped:
            # Has JSON-like structure
            return True

        # If it's reasonably long and doesn't look like thinking, accept it
        if len(stripped) > 50:
            thinking_indicators = [
                "let me think",
                "let me analyze",
                "i need to consider",
                "thinking about",
                "reasoning through",
            ]
            lower = stripped.lower()
            if not any(ind in lower for ind in thinking_indicators):
                return True

        return False

    @staticmethod
    def has_thinking_only(response: dict[str, Any]) -> bool:
        """Check if response is thinking-only without actual content.

        Args:
            response: Response dict to check

        Returns:
            True if response appears to be thinking-only
        """
        if not isinstance(response, dict) or "choices" not in response:
            return False

        for choice in response.get("choices", []):
            message = choice.get("message", {})
            content = message.get("content", "")
            reasoning = message.get("reasoning_content", "")

            # Has tool calls - not thinking only
            if message.get("tool_calls"):
                return False

            # Has content that's not just thinking
            if content:
                cleaned = ThinkingAdapter.strip_thinking_blocks(content)
                if cleaned:
                    return False

            # Has reasoning but it's actual content
            if reasoning and ThinkingAdapter._is_actual_content(reasoning):
                return False

        return True
