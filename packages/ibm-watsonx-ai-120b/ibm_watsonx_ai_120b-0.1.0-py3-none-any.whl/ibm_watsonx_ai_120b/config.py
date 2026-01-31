"""Configuration management for ibm-watsonx-ai-120b."""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Config:
    """Global configuration for ibm-watsonx-ai-120b.

    Can be configured programmatically or via environment variables.

    Environment variables:
        WATSONX_120B_MAX_RETRIES: Max retries for thinking-only responses (default: 3)
        WATSONX_120B_DISABLE_STREAMING: Force non-streaming for tools (default: false)
        WATSONX_120B_DEBUG: Enable debug logging (default: false)
        WATSONX_120B_JSON_REPAIR: Enable JSON repair (default: true)

    Example:
        from ibm_watsonx_ai_120b import Config

        # Programmatic configuration
        Config.max_retries = 5
        Config.streaming_tool_strategy = "fallback"

        # Or use environment variables
        # export WATSONX_120B_MAX_RETRIES=5
    """

    # Retry configuration
    max_retries: int = field(
        default_factory=lambda: int(os.environ.get("WATSONX_120B_MAX_RETRIES", "3"))
    )

    # Streaming strategy for tools: "accumulate" or "fallback"
    # - accumulate: collect stream, reparse, re-emit
    # - fallback: use non-streaming for tools/JSON (most reliable)
    streaming_tool_strategy: str = field(
        default_factory=lambda: "fallback"
        if os.environ.get("WATSONX_120B_DISABLE_STREAMING", "").lower() in ("true", "1", "yes")
        else "accumulate"
    )

    # JSON repair
    json_repair_enabled: bool = field(
        default_factory=lambda: os.environ.get("WATSONX_120B_JSON_REPAIR", "true").lower()
        in ("true", "1", "yes")
    )

    # Debug mode
    debug: bool = field(
        default_factory=lambda: os.environ.get("WATSONX_120B_DEBUG", "").lower()
        in ("true", "1", "yes")
    )

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_retries < 0:
            self.max_retries = 0
        if self.streaming_tool_strategy not in ("accumulate", "fallback"):
            self.streaming_tool_strategy = "fallback"


# Global config instance - can be modified at runtime
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(**kwargs: Any) -> None:
    """Update global configuration.

    Example:
        set_config(max_retries=5, debug=True)
    """
    global _config
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)