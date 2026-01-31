"""Stream adapter for handling streaming quirks.

Streaming with tools/JSON is problematic on vLLM, so we provide
strategies to handle it: accumulate and reparse, or fallback to sync.
"""

import logging
from enum import Enum
from typing import Any, Iterator

from ibm_watsonx_ai_120b.config import get_config
from ibm_watsonx_ai_120b.adapters.harmony_adapter import HarmonyAdapter

logger = logging.getLogger(__name__)


class StreamStrategy(Enum):
    """Strategy for handling streaming requests."""

    PASSTHROUGH = "passthrough"  # Stream as-is (plain chat)
    ACCUMULATE = "accumulate"  # Collect all, reparse, re-emit
    FALLBACK = "fallback"  # Use non-streaming for tools/JSON


class StreamAdapter:
    """Handles streaming quirks for vLLM-hosted models.

    Problems with streaming:
    - Tool calls appear in reasoning_content instead of tool_calls
    - Chunks can be malformed
    - Hanging requests

    Strategies:
    - PASSTHROUGH: Clean each chunk and yield (for plain chat)
    - ACCUMULATE: Collect all chunks, reparse complete response
    - FALLBACK: Don't stream at all for tools/JSON (most reliable)
    """

    @staticmethod
    def determine_strategy(
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> StreamStrategy:
        """Determine streaming strategy based on request.

        Args:
            tools: Tool definitions if any
            response_format: Response format if any

        Returns:
            Appropriate streaming strategy
        """
        # If tools or JSON schema requested, check config
        if tools or response_format:
            config = get_config()
            if config.streaming_tool_strategy == "fallback":
                return StreamStrategy.FALLBACK
            else:
                return StreamStrategy.ACCUMULATE

        # Plain chat can stream directly
        return StreamStrategy.PASSTHROUGH

    @staticmethod
    def passthrough_stream(
        stream: Iterator[dict[str, Any]],
    ) -> Iterator[dict[str, Any]]:
        """Clean each chunk and yield.

        Args:
            stream: Original stream from model

        Yields:
            Cleaned chunks
        """
        for chunk in stream:
            if isinstance(chunk, dict):
                # Clean harmony tokens from chunk
                cleaned = HarmonyAdapter.clean_response(chunk)
                yield cleaned
            elif chunk is not None:
                yield chunk

    @staticmethod
    def accumulate_stream(
        stream: Iterator[dict[str, Any]],
    ) -> tuple[str, dict[str, Any] | None]:
        """Accumulate all chunks into complete response.

        Args:
            stream: Original stream from model

        Returns:
            Tuple of (accumulated_content, last_chunk_for_metadata)
        """
        content_parts: list[str] = []
        last_chunk: dict[str, Any] | None = None

        for chunk in stream:
            last_chunk = chunk

            if not isinstance(chunk, dict):
                if chunk is not None:
                    content_parts.append(str(chunk))
                continue

            # Extract content from chunk
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    content_parts.append(content)

        accumulated = "".join(content_parts)
        return accumulated, last_chunk

    @staticmethod
    def should_fallback_to_sync(
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> bool:
        """Check if we should fallback to synchronous call.

        Args:
            tools: Tool definitions if any
            response_format: Response format if any

        Returns:
            True if sync fallback is recommended
        """
        strategy = StreamAdapter.determine_strategy(tools, response_format)
        return strategy == StreamStrategy.FALLBACK
