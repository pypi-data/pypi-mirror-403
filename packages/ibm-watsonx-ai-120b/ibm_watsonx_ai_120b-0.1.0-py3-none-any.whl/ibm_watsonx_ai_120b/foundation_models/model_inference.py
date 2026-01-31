"""ModelInference wrapper with vLLM bug fixes.

Drop-in replacement for ibm_watsonx_ai.foundation_models.ModelInference
that transparently fixes all known issues with gpt-oss-120b/20b models.
"""

import logging
import time
import uuid
from typing import Any, Iterator

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ibm_watsonx_ai.foundation_models import ModelInference as _OriginalModelInference

from ibm_watsonx_ai_120b.config import get_config
from ibm_watsonx_ai_120b.exceptions import ThinkingOnlyResponseError
from ibm_watsonx_ai_120b.adapters.message_adapter import MessageAdapter
from ibm_watsonx_ai_120b.adapters.harmony_adapter import HarmonyAdapter
from ibm_watsonx_ai_120b.adapters.thinking_adapter import ThinkingAdapter
from ibm_watsonx_ai_120b.adapters.tool_adapter import ToolAdapter
from ibm_watsonx_ai_120b.adapters.json_adapter import JSONAdapter
from ibm_watsonx_ai_120b.adapters.stream_adapter import StreamAdapter

logger = logging.getLogger(__name__)


class ModelInference:
    """Drop-in replacement for ibm_watsonx_ai.foundation_models.ModelInference.

    Wraps the original ModelInference and applies fixes for vLLM bugs:
    - Tool calling via prompt injection
    - JSON schema via prompt injection
    - Harmony token stripping
    - Thinking/reasoning handling
    - Message format fixes

    Everything not broken passes through unchanged.

    Example:
        # Just change your import:
        from ibm_watsonx_ai_120b.foundation_models import ModelInference

        model = ModelInference(
            model_id="openai/gpt-oss-120b",
            credentials=credentials,
            project_id=project_id
        )

        # Tool calling now works!
        response = model.chat(
            messages=[{"role": "user", "content": "What's the weather?"}],
            tools=[...]
        )
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize wrapper around original ModelInference.

        Accepts all arguments that the original ModelInference accepts.
        """
        self._original = _OriginalModelInference(*args, **kwargs)
        self._model_id = kwargs.get("model_id", "")

        # Initialize adapters
        config = get_config()
        self._tool_adapter = ToolAdapter(max_retries=config.max_retries)
        self._json_adapter = JSONAdapter(max_retries=config.max_retries)

        logger.debug(f"Initialized wrapped ModelInference for {self._model_id}")

    def __getattr__(self, name: str) -> Any:
        """Pass through all non-intercepted attributes to original.

        This enables drop-in compatibility - any method or attribute
        not explicitly overridden here goes to the original.
        """
        return getattr(self._original, name)

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_format: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat completion request with automatic bug fixes.

        Args:
            messages: List of messages in OpenAI format
            tools: Tool definitions (emulated via prompt injection)
            tool_choice: Tool selection mode ('auto', 'none', or specific tool)
            response_format: Response format specification (emulated)
            **kwargs: Additional parameters passed to original

        Returns:
            OpenAI-compatible response dict
        """
        # Route based on what's requested
        if tools:
            return self._chat_with_tools(messages, tools, tool_choice or "auto", **kwargs)

        if response_format:
            return self._chat_with_response_format(messages, response_format, **kwargs)

        # Plain chat - apply basic fixes
        return self._chat_basic(messages, **kwargs)

    def _chat_basic(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Basic chat with message fixing and thinking handling.

        Args:
            messages: Conversation messages
            **kwargs: Additional parameters

        Returns:
            Cleaned response
        """
        # Adapt messages for vLLM compatibility
        adapted_messages = MessageAdapter.adapt_messages(messages)
        formatted_messages = MessageAdapter.format_for_api(adapted_messages)

        config = get_config()

        @retry(
            stop=stop_after_attempt(config.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type(ThinkingOnlyResponseError),
            reraise=True,
        )
        def call_with_retry():
            result = self._original.chat(messages=formatted_messages, **kwargs)
            result = self._process_response(result)
            return result

        try:
            return call_with_retry()
        except ThinkingOnlyResponseError as e:
            logger.error(f"Failed after retries - thinking only: {e}")
            # Return error response rather than raising
            return self._format_error_response(
                f"Model failed to produce content after retries: {e}"
            )

    def _chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: str | dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Chat with tool calling via prompt injection.

        Args:
            messages: Conversation messages
            tools: Tool definitions
            tool_choice: Tool selection mode
            **kwargs: Additional parameters

        Returns:
            Response with tool_calls if applicable
        """
        # Adapt messages
        adapted_messages = MessageAdapter.adapt_messages(messages)

        def model_call_fn(msgs: list[dict[str, Any]]) -> str:
            """Call the model and extract content."""
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._original.chat(messages=formatted, **kwargs)

            # Handle different response formats
            if isinstance(result, dict) and "choices" in result:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                # Also check reasoning_content
                if not content:
                    reasoning = message.get("reasoning_content", "")
                    if reasoning and ThinkingAdapter._is_actual_content(reasoning):
                        content = ThinkingAdapter.strip_thinking_blocks(reasoning)
                return content
            elif isinstance(result, str):
                return result
            return str(result) if result else ""

        response = self._tool_adapter.process_with_tools(
            messages=adapted_messages,
            tools=tools,
            model_call_fn=model_call_fn,
            tool_choice=tool_choice,
        )

        # Clean and add metadata
        response = HarmonyAdapter.clean_response(response)
        return self._add_response_metadata(response)

    def _chat_with_response_format(
        self,
        messages: list[dict[str, Any]],
        response_format: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Chat with response format via prompt injection.

        Args:
            messages: Conversation messages
            response_format: Response format specification
            **kwargs: Additional parameters

        Returns:
            Response with formatted content
        """
        adapted_messages = MessageAdapter.adapt_messages(messages)

        def model_call_fn(msgs: list[dict[str, Any]]) -> str:
            """Call the model and extract content."""
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._original.chat(messages=formatted, **kwargs)

            if isinstance(result, dict) and "choices" in result:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                if not content:
                    reasoning = message.get("reasoning_content", "")
                    if reasoning and ThinkingAdapter._is_actual_content(reasoning):
                        content = ThinkingAdapter.strip_thinking_blocks(reasoning)
                return content
            elif isinstance(result, str):
                return result
            return str(result) if result else ""

        format_type = response_format.get("type")

        if format_type == "json_schema":
            json_schema = response_format.get("json_schema", {})
            schema = json_schema.get("schema", {})
            schema_name = json_schema.get("name", "response")

            response = self._json_adapter.process_with_schema(
                messages=adapted_messages,
                schema=schema,
                model_call_fn=model_call_fn,
                schema_name=schema_name,
            )

        elif format_type == "json_object":
            response = self._json_adapter.process_json_object(
                messages=adapted_messages,
                model_call_fn=model_call_fn,
            )

        else:
            # Unknown format, fall back to basic chat
            return self._chat_basic(messages, **kwargs)

        response = HarmonyAdapter.clean_response(response)
        return self._add_response_metadata(response)

    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_format: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Stream chat completion with automatic bug fixes.

        Note: For tools/JSON, streaming may fall back to non-streaming
        depending on configuration, as streaming with tools is unreliable.

        Args:
            messages: List of messages
            tools: Tool definitions (may cause sync fallback)
            tool_choice: Tool selection mode
            response_format: Response format (may cause sync fallback)
            **kwargs: Additional parameters

        Yields:
            Streaming chunks or single complete response
        """
        # Check if we should fall back to sync
        if StreamAdapter.should_fallback_to_sync(tools, response_format):
            logger.debug("Falling back to sync for tools/JSON request")
            response = self.chat(
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                response_format=response_format,
                **kwargs,
            )
            # Yield as single chunk
            yield response
            return

        # Plain streaming
        adapted_messages = MessageAdapter.adapt_messages(messages)
        formatted_messages = MessageAdapter.format_for_api(adapted_messages)

        try:
            stream = self._original.chat_stream(messages=formatted_messages, **kwargs)

            for chunk in StreamAdapter.passthrough_stream(stream):
                yield chunk

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield self._format_stream_error(str(e))

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from a prompt.

        Args:
            prompt: Text prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        result = self._original.generate_text(prompt=prompt, **kwargs)

        # Clean harmony tokens if present
        if isinstance(result, str):
            result = HarmonyAdapter.clean_text(result)

        return result

    def generate_text_stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream text generation.

        Args:
            prompt: Text prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks
        """
        stream = self._original.generate_text_stream(prompt=prompt, **kwargs)

        for chunk in stream:
            if isinstance(chunk, str):
                yield HarmonyAdapter.clean_text(chunk)
            elif chunk is not None:
                yield str(chunk)

    def _process_response(self, response: Any) -> dict[str, Any]:
        """Process a response through the adapter pipeline.

        Args:
            response: Raw response from model

        Returns:
            Processed response
        """
        # Handle string response
        if isinstance(response, str):
            if not response.strip():
                raise ThinkingOnlyResponseError("(empty string response)")
            response = self._format_string_response(response)

        # Handle None
        if response is None:
            raise ThinkingOnlyResponseError("(None response)")

        # Apply adapters
        response = HarmonyAdapter.clean_response(response)
        response = ThinkingAdapter.process_response(response)

        return response

    def _format_string_response(self, content: str) -> dict[str, Any]:
        """Format a string into OpenAI response format.

        Args:
            content: Response content

        Returns:
            Formatted response dict
        """
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self._model_id,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                    "refusal": None,
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }

    def _format_error_response(self, error: str) -> dict[str, Any]:
        """Format an error into response format.

        Args:
            error: Error message

        Returns:
            Error response dict
        """
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self._model_id,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Error: {error}",
                    "refusal": None,
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }

    def _format_stream_error(self, error: str) -> dict[str, Any]:
        """Format a streaming error chunk.

        Args:
            error: Error message

        Returns:
            Error chunk dict
        """
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self._model_id,
            "choices": [{
                "index": 0,
                "delta": {"content": f"[ERROR: {error}]"},
                "finish_reason": "error",
            }],
        }

    def _add_response_metadata(self, response: dict[str, Any]) -> dict[str, Any]:
        """Add standard metadata fields to response.

        Args:
            response: Response dict

        Returns:
            Response with metadata
        """
        if "id" not in response:
            response["id"] = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        if "object" not in response:
            response["object"] = "chat.completion"
        if "created" not in response:
            response["created"] = int(time.time())
        if "model" not in response:
            response["model"] = self._model_id
        if "usage" not in response:
            response["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        # Ensure refusal field exists in messages
        for choice in response.get("choices", []):
            if "message" in choice and "refusal" not in choice["message"]:
                choice["message"]["refusal"] = None

        return response
