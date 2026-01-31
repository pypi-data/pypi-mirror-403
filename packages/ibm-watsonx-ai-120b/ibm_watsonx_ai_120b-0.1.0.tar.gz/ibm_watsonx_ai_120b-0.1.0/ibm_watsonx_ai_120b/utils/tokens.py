"""Token constants and utilities for gpt-oss models."""

import re
from typing import List

# Stop tokens for gpt-oss-120b that signal end of generation
# These prevent the model from continuing after tool calls
GPT_OSS_STOP_TOKENS: List[int] = [
    199999,  # EOS token
    200002,  # End of turn
    200012,  # <|call|> token - end of tool call
]

# Harmony format special tokens that can leak into output
HARMONY_TOKENS = [
    "<|start|>",
    "<|end|>",
    "<|channel|>",
    "<|message|>",
    "<|constrain|>",
    "<|call|>",
    "<|return|>",
]

# Pattern to match harmony tokens and their common combinations
HARMONY_TOKEN_PATTERN = re.compile(
    r"<\|(?:start|end|channel|message|constrain|call|return)\|>",
    re.IGNORECASE
)

# Pattern for channel markers like "assistant<|channel|>analysis"
CHANNEL_MARKER_PATTERN = re.compile(
    r"(?:assistant|user|system)\s*<\|channel\|>\s*\w+",
    re.IGNORECASE
)

# Combined pattern for all harmony-related artifacts
HARMONY_CLEANUP_PATTERN = re.compile(
    r"(?:"
    r"<\|(?:start|end|channel|message|constrain|call|return)\|>"
    r"|(?:assistant|user|system)\s*<\|channel\|>\s*\w*"
    r")",
    re.IGNORECASE
)


def strip_harmony_tokens(text: str) -> str:
    """Remove all harmony format tokens from text.

    Args:
        text: Text that may contain harmony tokens

    Returns:
        Cleaned text with harmony tokens removed
    """
    if not text:
        return text

    # Remove harmony tokens and channel markers
    cleaned = HARMONY_CLEANUP_PATTERN.sub("", text)

    # Clean up any resulting double spaces or leading/trailing whitespace
    cleaned = re.sub(r"  +", " ", cleaned)
    cleaned = cleaned.strip()

    return cleaned