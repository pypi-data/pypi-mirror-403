"""
WatsonX Client - Facade for openai/gpt-oss-120b with vLLM bug adaptations.

This client provides a standard WatsonX interface while internally handling
the quirks of IBM's vLLM backend for the gpt-oss-120b model.

Features that work directly:
- Basic chat completions
- Streaming responses

Features that require adaptation (prompt injection):
- Tool/function calling
- JSON schema responses
- JSON object mode

Known WatsonX quirks handled:
- Model sometimes returns only 'reasoning_content' without actual 'content'
  (thinking-only responses) - we retry automatically
"""

import json
import logging
import time
import uuid
import threading
import atexit
from typing import Dict, List, Any, Optional, Union, Iterator, Generator, Tuple

from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential

from .config import WatsonXConfig
from .exceptions import (
    WatsonXError,
    WatsonXConnectionError,
    WatsonXAuthError,
    ModelNotReadyError,
    ToolExtractionError,
    JSONExtractionError,
    ThinkingOnlyResponseError,
)
from .adapters import ToolAdapter, JSONSchemaAdapter, MessageAdapter

logger = logging.getLogger(__name__)


# Connection pool for client reuse
_client_pool: Dict[str, Any] = {}
_client_pool_lock = threading.Lock()
_max_clients = 5


class WatsonXClient:
    """WatsonX client with transparent adaptation for gpt-oss-120b quirks.

    This client presents a standard interface matching what a properly-working
    WatsonX model would expose. Internally, it adapts requests as needed to
    work around vLLM backend bugs.

    Example:
        config = WatsonXConfig(
            api_key="your-key",
            project_id="your-project",
            region_url="https://us-south.ml.cloud.ibm.com"
        )
        client = WatsonXClient(config)

        # Basic chat (works directly)
        response = client.chat([{"role": "user", "content": "Hello"}])

        # With tools (adapted via prompt injection)
        response = client.chat_with_tools(
            messages=[{"role": "user", "content": "What's the weather?"}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "parameters": {...}
                }
            }]
        )
    """

    def __init__(self, config: WatsonXConfig):
        """Initialize client.

        Args:
            config: WatsonX configuration

        Raises:
            WatsonXAuthError: If credentials are invalid
            WatsonXConnectionError: If connection fails
        """
        self.config = config
        self._model: Optional[Any] = None
        self._api_client: Optional[Any] = None
        self._cleaned_up = False
        self._active_streams: List[Any] = []

        # Adapters for handling quirks
        self._tool_adapter = ToolAdapter(max_retries=config.max_retries)
        self._json_adapter = JSONSchemaAdapter(max_retries=config.max_retries + 2)

        # Initialize connection
        self._initialize()

    def _initialize(self):
        """Initialize IBM API client and model."""
        if not self.config.validate():
            raise WatsonXAuthError("Invalid configuration: missing required fields")

        try:
            from ibm_watsonx_ai.foundation_models import ModelInference
            from ibm_watsonx_ai import APIClient, Credentials
            from ibm_watsonx_ai.wml_client_error import WMLClientError

            # Get or create cached client
            self._api_client = self._get_cached_client()

            # Create model instance
            credentials = Credentials(
                url=self.config.region_url,
                api_key=self.config.api_key
            )

            self._model = ModelInference(
                model_id=self.config.model_id,
                params=self.config.get_generation_params(),
                credentials=credentials,
                project_id=self.config.project_id,
                api_client=self._api_client
            )

            logger.info(f"Initialized WatsonX client for model: {self.config.model_id}")

        except ImportError:
            logger.warning("ibm_watsonx_ai not installed, using mock client")
            self._model = MockWatsonXModel()
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise WatsonXAuthError(f"Authentication failed: {e}")
            raise WatsonXConnectionError(f"Failed to initialize: {e}")

    def _get_cached_client(self) -> Any:
        """Get or create a cached API client."""
        try:
            from ibm_watsonx_ai import APIClient, Credentials
        except ImportError:
            return None

        client_key = f"{self.config.region_url}:{self.config.project_id}"

        with _client_pool_lock:
            if client_key in _client_pool:
                logger.debug(f"Reusing cached client for {client_key}")
                return _client_pool[client_key]

            # Evict oldest if at capacity
            if len(_client_pool) >= _max_clients:
                oldest_key = next(iter(_client_pool))
                old_client = _client_pool.pop(oldest_key)
                if hasattr(old_client, "close"):
                    try:
                        old_client.close()
                    except:
                        pass
                logger.info(f"Evicted cached client: {oldest_key}")

            # Create new client
            credentials = Credentials(
                url=self.config.region_url,
                api_key=self.config.api_key
            )
            client = APIClient(credentials=credentials, project_id=self.config.project_id)
            _client_pool[client_key] = client
            logger.info(f"Created new cached client for {client_key}")

            return client

    def _ensure_ready(self):
        """Ensure model is ready for use."""
        if self._cleaned_up or self._model is None:
            raise ModelNotReadyError("Client has been cleaned up or not initialized")

    def cleanup(self):
        """Clean up resources."""
        if self._cleaned_up:
            return

        # Cancel active streams
        for stream in self._active_streams:
            try:
                if hasattr(stream, "close"):
                    stream.close()
            except:
                pass
        self._active_streams.clear()

        # Clear model reference (keep client cached)
        self._model = None
        self._api_client = None
        self._cleaned_up = True

        logger.debug(f"Cleaned up WatsonX client for {self.config.model_id}")

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    # =========================================================================
    # Core Chat Methods
    # =========================================================================

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Send a chat completion request.

        This is the basic chat method that works directly with the model.

        Args:
            messages: List of messages in OpenAI format
            stream: If True, return a streaming iterator
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
                - max_tokens or max_new_tokens: Maximum output tokens
                - temperature: Sampling temperature

        Returns:
            OpenAI-compatible response dict, or iterator if streaming
        """
        self._ensure_ready()

        # Normalize parameter names (convert max_new_tokens to max_tokens)
        params = self._normalize_params(kwargs)

        # Adapt messages for WatsonX compatibility
        adapted_messages = MessageAdapter.adapt_messages(messages)
        formatted_messages = MessageAdapter.format_for_api(adapted_messages)

        if stream:
            return self._stream_chat(formatted_messages, params)
        else:
            return self._sync_chat(formatted_messages, params)

    def _normalize_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameter names for the API.

        Converts common aliases to the correct API parameter names.
        """
        params = {}

        # Handle max_tokens / max_new_tokens
        if "max_new_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_new_tokens"]
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]

        # Pass through other known parameters
        for key in ["temperature", "top_p", "repetition_penalty", "reasoning_effort"]:
            if key in kwargs:
                params[key] = kwargs[key]

        return params

    def _sync_chat(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous chat completion with automatic retry for thinking-only responses.

        Uses tenacity to retry when the model returns only 'reasoning_content'
        without actual 'content'. This is a known WatsonX quirk.

        However, if reasoning_content contains the actual answer (JSON, markdown),
        we use it as the content rather than retrying.

        Args:
            messages: Formatted messages for the API
            params: Optional per-call parameter overrides (max_tokens, temperature, etc.)
        """
        # Build call kwargs - params override defaults from model init
        call_kwargs = {"messages": messages}
        if params:
            call_kwargs["params"] = params

        @retry(
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(ThinkingOnlyResponseError),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True
        )
        def _call_with_retry():
            result = self._model.chat(**call_kwargs)

            # Handle string response
            if isinstance(result, str):
                if not result.strip():
                    raise ThinkingOnlyResponseError("(empty string response)")
                return self._format_response(result)

            # Handle dict response
            if isinstance(result, dict):
                if "choices" in result and result["choices"]:
                    message = result["choices"][0].get("message", {})
                    content = message.get("content", "")
                    reasoning = message.get("reasoning_content", "")

                    # If content is empty but reasoning has the actual answer, use it
                    if not content and reasoning:
                        # Check if reasoning contains the actual answer (JSON or markdown)
                        if self._is_actual_response(reasoning):
                            logger.info("Using reasoning_content as response (contains answer)")
                            # Promote reasoning_content to content
                            result["choices"][0]["message"]["content"] = reasoning
                            content = reasoning
                        else:
                            # It's just thinking text, retry
                            logger.warning(
                                f"Model returned thinking-only response, retrying. "
                                f"Reasoning preview: {reasoning[:100]}..."
                            )
                            raise ThinkingOnlyResponseError(reasoning)

                    # Check for completely empty response
                    if not content and not reasoning:
                        logger.warning("Model returned empty response, retrying.")
                        raise ThinkingOnlyResponseError("(empty response)")

                    # Ensure refusal field exists
                    for choice in result["choices"]:
                        if "message" in choice and "refusal" not in choice["message"]:
                            choice["message"]["refusal"] = None

                return result

            # Unknown response type
            if result is None:
                raise ThinkingOnlyResponseError("(None response)")

            return self._format_response(str(result))

        try:
            return _call_with_retry()
        except ThinkingOnlyResponseError as e:
            # All retries exhausted - raise as WatsonXError
            logger.error(f"Failed after retries: {e}")
            raise WatsonXError(
                f"Model failed to produce content after 3 retries. "
                f"Last response was thinking-only: {e.reasoning_preview[:200]}"
            )
        except Exception as e:
            logger.error(f"WatsonX API error: {e}")
            raise WatsonXError(f"Chat failed: {e}")

    def _is_actual_response(self, text: str) -> bool:
        """Check if text contains an actual response vs just thinking/planning.

        Returns True if the text appears to contain the actual answer
        (JSON object, markdown content, etc.) rather than just thinking.

        This uses ACTUAL JSON PARSING, not pattern matching, to detect responses.
        If we can extract valid JSON from the text, it's a response.
        """
        if not text:
            return False

        stripped = text.strip()

        # If it starts with JSON or markdown, it's definitely a response
        if stripped.startswith("{") or stripped.startswith("#") or stripped.startswith("```"):
            return True

        # If it contains a markdown code block with json, it's a response
        if '```json' in text:
            return True

        # Try to actually extract JSON from the text
        # This is the definitive test - if we can parse JSON, it's a response
        extracted_json = self._try_extract_json(text)
        if extracted_json is not None:
            return True

        # Otherwise it's probably just thinking text
        return False

    def _try_extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON from text. Returns parsed dict or None.

        This handles:
        - Pure JSON
        - JSON in markdown code blocks
        - JSON embedded in explanatory text
        """
        if not text:
            return None

        original = text

        # Try extracting from markdown code blocks first
        if "```json" in text:
            try:
                start = text.index("```json") + 7
                end = text.index("```", start)
                text = text[start:end].strip()
            except ValueError:
                pass
        elif "```" in text:
            try:
                start = text.index("```") + 3
                end = text.index("```", start)
                extracted = text[start:end].strip()
                if extracted.startswith("{"):
                    text = extracted
            except ValueError:
                pass

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find JSON object embedded in text
        text = original
        brace_start = text.find("{")
        if brace_start == -1:
            return None

        # Find matching closing brace
        depth = 0
        in_string = False
        escape_next = False
        brace_end = -1

        for i in range(brace_start, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    brace_end = i + 1
                    break

        if brace_end == -1:
            return None

        json_str = text[brace_start:brace_end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Try fixing trailing commas
        import re
        fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        return None

    def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Streaming chat completion.

        Args:
            messages: Formatted messages for the API
            params: Optional per-call parameter overrides (max_tokens, temperature, etc.)
        """
        stream = None
        try:
            # Build call kwargs - params override defaults from model init
            call_kwargs = {"messages": messages}
            if params:
                call_kwargs["params"] = params
            stream = self._model.chat_stream(**call_kwargs)
            self._active_streams.append(stream)

            for chunk in stream:
                if isinstance(chunk, dict) and "choices" in chunk:
                    yield chunk
                elif chunk is not None:
                    yield self._format_stream_chunk(str(chunk))

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield self._format_stream_chunk(f"[ERROR: {e}]", finish_reason="error")
        finally:
            if stream and stream in self._active_streams:
                self._active_streams.remove(stream)
                if hasattr(stream, "close"):
                    try:
                        stream.close()
                    except:
                        pass

    # =========================================================================
    # Tool/Function Calling (Adapted via Prompt Injection)
    # =========================================================================

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with tool/function calling support.

        Since openai/gpt-oss-120b on vLLM doesn't support native function calling,
        this method uses prompt injection to emulate tool use.

        Args:
            messages: Conversation messages
            tools: Tool definitions in OpenAI format
            tool_choice: 'auto', 'none', or specific tool dict
            **kwargs: Additional parameters

        Returns:
            OpenAI-compatible response with tool_calls if applicable
        """
        self._ensure_ready()

        # Adapt messages
        adapted_messages = MessageAdapter.adapt_messages(messages)

        # Use tool adapter for prompt injection
        def model_call_fn(msgs: List[Dict[str, Any]]) -> str:
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._model.chat(messages=formatted)
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0].get("message", {}).get("content", "")
            return str(result) if result else ""

        response = self._tool_adapter.process_with_tools(
            messages=adapted_messages,
            tools=tools,
            model_call_fn=model_call_fn,
            tool_choice=tool_choice
        )

        # Add standard response fields
        return self._add_response_metadata(response)

    # =========================================================================
    # JSON Schema Responses (Adapted via Prompt Injection)
    # =========================================================================

    def chat_with_json_schema(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        schema_name: str = "response",
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with JSON schema enforcement.

        Since the model doesn't support native structured output, this method
        uses prompt injection with schema examples and validation.

        Args:
            messages: Conversation messages
            schema: JSON schema to enforce
            schema_name: Name for the schema (used in prompts)
            **kwargs: Additional parameters

        Returns:
            OpenAI-compatible response with JSON content
        """
        self._ensure_ready()

        adapted_messages = MessageAdapter.adapt_messages(messages)

        def model_call_fn(msgs: List[Dict[str, Any]]) -> str:
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._model.chat(messages=formatted)
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0].get("message", {}).get("content", "")
            return str(result) if result else ""

        response = self._json_adapter.process_with_schema(
            messages=adapted_messages,
            schema=schema,
            model_call_fn=model_call_fn,
            schema_name=schema_name
        )

        return self._add_response_metadata(response)

    def chat_with_json_object(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with simple JSON object mode (no schema validation).

        Args:
            messages: Conversation messages
            **kwargs: Additional parameters

        Returns:
            OpenAI-compatible response with JSON content
        """
        self._ensure_ready()

        adapted_messages = MessageAdapter.adapt_messages(messages)

        def model_call_fn(msgs: List[Dict[str, Any]]) -> str:
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._model.chat(messages=formatted)
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0].get("message", {}).get("content", "")
            return str(result) if result else ""

        response = self._json_adapter.process_json_object(
            messages=adapted_messages,
            model_call_fn=model_call_fn
        )

        return self._add_response_metadata(response)

    # =========================================================================
    # Unified Chat Method (Matches OpenAI Interface)
    # =========================================================================

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        response_format: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Unified chat completion matching OpenAI's interface.

        Automatically routes to the appropriate method based on parameters.

        Args:
            messages: Conversation messages
            tools: Tool definitions (triggers adapted path)
            tool_choice: Tool selection mode
            response_format: Response format specification
            stream: Enable streaming (only for basic chat)
            **kwargs: Additional parameters

        Returns:
            OpenAI-compatible response
        """
        # Route based on parameters
        if tools:
            if stream:
                logger.warning("Streaming not supported with tools, falling back to sync")
            return self.chat_with_tools(messages, tools, tool_choice, **kwargs)

        if response_format:
            if stream:
                logger.warning("Streaming not supported with response_format, falling back to sync")

            format_type = response_format.get("type")

            if format_type == "json_schema":
                json_schema = response_format.get("json_schema", {})
                schema = json_schema.get("schema", {})
                schema_name = json_schema.get("name", "response")
                return self.chat_with_json_schema(messages, schema, schema_name, **kwargs)

            elif format_type == "json_object":
                return self.chat_with_json_object(messages, **kwargs)

        # Basic chat
        return self.chat(messages, stream=stream, **kwargs)

    # =========================================================================
    # Text Generation (Non-Chat)
    # =========================================================================

    def generate(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate text from a prompt (non-chat mode).

        Args:
            prompt: Text prompt
            stream: Enable streaming
            **kwargs: Additional parameters

        Returns:
            Generated text or stream iterator
        """
        self._ensure_ready()

        if stream:
            return self._stream_generate(prompt)
        else:
            result = self._model.generate_text(prompt=prompt)
            return result

    def _stream_generate(self, prompt: str) -> Iterator[str]:
        """Streaming text generation."""
        stream = None
        try:
            stream = self._model.generate_text_stream(prompt=prompt)
            self._active_streams.append(stream)

            for chunk in stream:
                if chunk:
                    yield str(chunk) if not isinstance(chunk, str) else chunk

        finally:
            if stream and stream in self._active_streams:
                self._active_streams.remove(stream)

    # =========================================================================
    # JSON Generation with Retry
    # =========================================================================

    def generate_json(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Generate JSON from a prompt with automatic retry for thinking text.

        This method handles the common case where the LLM outputs "thinking"
        or analysis text instead of the requested JSON. It will:
        1. Try the initial prompt
        2. If non-JSON output is detected, retry with a forceful follow-up
        3. Attempt to extract JSON from mixed text responses

        Args:
            prompt: The prompt requesting JSON output
            max_retries: Maximum retry attempts (default 3)

        Returns:
            Tuple of (parsed JSON dict or None, error message if failed)

        Example:
            result, error = client.generate_json('''
                Analyze this and output JSON:
                {"name": "example", "count": 5}
            ''')
            if result:
                print(result["name"])
            else:
                print(f"Failed: {error}")
        """
        self._ensure_ready()

        last_response = ""

        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    # First attempt: use original prompt
                    response = self._model.generate_text(prompt=prompt)
                else:
                    # Retry: use a forceful follow-up prompt
                    retry_prompt = f"""Your previous response was text/analysis, not JSON.

PREVIOUS OUTPUT (DO NOT REPEAT THIS - this is what you said wrong):
{last_response[:500]}

REQUIREMENT: Output ONLY a valid JSON object.
- No explanation before or after
- No markdown code blocks
- Start with {{ and end with }}

JSON output:"""
                    response = self._model.generate_text(prompt=retry_prompt)

                if not response:
                    last_response = "(empty response)"
                    continue

                last_response = response

                # Try to parse JSON from response
                parsed = self._extract_json(response)
                if parsed:
                    return parsed, ""

                # Check if response looks like thinking/planning text
                if self._is_thinking_text(response) and attempt < max_retries - 1:
                    # Model is outputting thinking text, retry
                    logger.debug(f"Attempt {attempt + 1}: detected thinking text, retrying")
                    continue

            except Exception as e:
                last_response = f"(error: {str(e)})"
                logger.warning(f"generate_json attempt {attempt + 1} failed: {e}")
                continue

        # All retries failed
        preview = last_response[:500] if last_response else "(no response)"
        return None, f"Failed to generate JSON after {max_retries} attempts. Last response: {preview}"

    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from LLM response.

        Handles various output formats:
        - Pure JSON
        - JSON in markdown code blocks
        - JSON embedded in explanatory text
        - JSON with minor formatting issues
        """
        import re

        if not response:
            return None

        original_response = response

        # Method 1: Try markdown code block extraction
        if "```json" in response:
            try:
                start = response.index("```json") + 7
                end = response.index("```", start)
                response = response[start:end].strip()
            except ValueError:
                pass
        elif "```" in response:
            try:
                start = response.index("```") + 3
                end = response.index("```", start)
                extracted = response[start:end].strip()
                if extracted.startswith("{"):
                    response = extracted
            except ValueError:
                pass

        # Method 2: Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Method 3: Find JSON object in text
        response = original_response
        brace_start = response.find("{")
        if brace_start == -1:
            return None

        # Find matching closing brace
        depth = 0
        in_string = False
        escape_next = False
        brace_end = -1

        for i in range(brace_start, len(response)):
            char = response[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    brace_end = i + 1
                    break

        if brace_end == -1:
            return None

        json_str = response[brace_start:brace_end]

        # Try to parse extracted JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Method 4: Try fixing common JSON issues (trailing commas)
        fixed_json = re.sub(r',\s*([}\]])', r'\1', json_str)
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            pass

        return None

    def _is_thinking_text(self, response: str) -> bool:
        """Check if response appears to be thinking/planning text rather than JSON."""
        if not response:
            return False

        # If it starts with { it's probably JSON (even if malformed)
        stripped = response.strip()
        if stripped.startswith("{"):
            return False

        # Check for thinking indicators
        thinking_indicators = [
            "we need to", "let's ", "let me", "i need to", "i will",
            "first,", "step 1", "analyzing", "looking at",
            "the solution", "this is a", "we must", "i'll ",
            "here's my", "my analysis", "based on",
        ]
        response_lower = response.lower()[:300]
        return any(ind in response_lower for ind in thinking_indicators)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _format_response(self, content: str) -> Dict[str, Any]:
        """Format a string response to OpenAI-compatible format."""
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.config.model_id,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                    "refusal": None
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }

    def _format_stream_chunk(
        self,
        content: str,
        finish_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a streaming chunk."""
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self.config.model_id,
            "choices": [{
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason
            }]
        }

    def _add_response_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Add standard metadata fields to response."""
        if "id" not in response:
            response["id"] = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        if "object" not in response:
            response["object"] = "chat.completion"
        if "created" not in response:
            response["created"] = int(time.time())
        if "model" not in response:
            response["model"] = self.config.model_id
        if "usage" not in response:
            response["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        return response


class MockWatsonXModel:
    """Mock model for testing without WatsonX SDK."""

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Mock chat response."""
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "[Mock response - WatsonX SDK not installed]",
                    "refusal": None
                },
                "finish_reason": "stop"
            }]
        }

    def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """Mock streaming response."""
        yield "[Mock streaming response - WatsonX SDK not installed]"

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Mock text generation."""
        return "[Mock response - WatsonX SDK not installed]"

    def generate_text_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Mock streaming text generation."""
        yield "[Mock streaming response - WatsonX SDK not installed]"


# Cleanup all cached clients on exit
def _cleanup_all_clients():
    """Clean up all cached clients."""
    with _client_pool_lock:
        for key, client in _client_pool.items():
            try:
                if hasattr(client, "close"):
                    client.close()
            except:
                pass
        _client_pool.clear()

atexit.register(_cleanup_all_clients)
