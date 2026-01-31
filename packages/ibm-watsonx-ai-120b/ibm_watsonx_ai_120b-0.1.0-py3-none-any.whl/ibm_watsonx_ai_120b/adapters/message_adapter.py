"""Message adapter for WatsonX/vLLM compatibility.

Fixes message format issues that cause vLLM to crash or misbehave.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MessageAdapter:
    """Adapts messages for WatsonX/vLLM compatibility.

    Key fixes:
    - Ensures content is never None (vLLM crashes on null content)
    - Converts 'tool' role messages to user messages (not supported)
    - Strips tool_calls from history (causes issues)
    """

    @staticmethod
    def adapt_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Adapt messages for WatsonX compatibility.

        Args:
            messages: List of OpenAI-format messages

        Returns:
            Adapted messages safe for WatsonX/vLLM
        """
        adapted = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content")

            if role == "tool":
                # Convert tool responses to user messages
                # vLLM doesn't support the tool role
                tool_content = content or ""
                tool_call_id = msg.get("tool_call_id", "")
                adapted.append({
                    "role": "user",
                    "content": f"Function result{f' (id: {tool_call_id})' if tool_call_id else ''}: {tool_content}"
                })

            elif role == "assistant" and msg.get("tool_calls") and content is None:
                # For assistant messages with tool calls but no content,
                # represent the tool call as text
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    call_info = tool_calls[0]
                    func_name = call_info.get("function", {}).get("name", "unknown")
                    func_args = call_info.get("function", {}).get("arguments", {})
                    adapted.append({
                        "role": "assistant",
                        "content": f"I will call {func_name} with arguments: {func_args}"
                    })
                else:
                    adapted.append({
                        "role": "assistant",
                        "content": "I will call a function."
                    })

            else:
                # Copy message, ensuring content is not None
                msg_copy = msg.copy()
                if msg_copy.get("content") is None:
                    msg_copy["content"] = ""
                # Strip tool_calls to avoid vLLM issues
                msg_copy.pop("tool_calls", None)
                msg_copy.pop("tool_call_id", None)
                adapted.append(msg_copy)

        return adapted

    @staticmethod
    def format_for_api(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Format messages for the IBM API.

        Strips down to just role and content.

        Args:
            messages: Adapted messages

        Returns:
            Minimal message format for IBM API
        """
        return [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content") or ""
            }
            for msg in messages
        ]

    @staticmethod
    def inject_system_message(
        messages: list[dict[str, Any]],
        system_content: str,
        replace: bool = True
    ) -> list[dict[str, Any]]:
        """Inject or modify system message.

        Args:
            messages: Original messages
            system_content: New system message content
            replace: If True, replace existing; if False, prepend to existing

        Returns:
            Messages with system message injected
        """
        messages = [m.copy() for m in messages]
        system_message = {"role": "system", "content": system_content}

        # Find existing system message
        system_index = next(
            (i for i, msg in enumerate(messages) if msg.get("role") == "system"),
            None
        )

        if system_index is not None:
            if replace:
                messages[system_index] = system_message
            else:
                # Prepend to existing system message
                existing = messages[system_index].get("content", "")
                messages[system_index] = {
                    "role": "system",
                    "content": f"{system_content}\n\n{existing}"
                }
        else:
            # Insert at beginning
            messages.insert(0, system_message)

        return messages

    @staticmethod
    def extract_last_assistant_content(messages: list[dict[str, Any]]) -> str | None:
        """Extract content from the last assistant message.

        Args:
            messages: List of messages

        Returns:
            Content of last assistant message, or None
        """
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return msg.get("content")
        return None
