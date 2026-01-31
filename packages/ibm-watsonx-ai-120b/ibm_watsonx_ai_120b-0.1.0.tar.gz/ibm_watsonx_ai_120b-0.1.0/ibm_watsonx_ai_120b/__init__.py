"""
ibm-watsonx-ai-120b: Drop-in replacement for ibm-watsonx-ai.

Transparently fixes all known issues with IBM's vLLM-hosted
openai/gpt-oss-120b and openai/gpt-oss-20b models.

Usage:
    # Instead of:
    from ibm_watsonx_ai.foundation_models import ModelInference

    # Use:
    from ibm_watsonx_ai_120b.foundation_models import ModelInference

    # Everything else stays the same!
"""

from ibm_watsonx_ai_120b.config import Config
from ibm_watsonx_ai_120b.exceptions import (
    WatsonX120BError,
    ThinkingOnlyResponseError,
    ToolExtractionError,
    JSONExtractionError,
    SchemaValidationError,
    StreamingError,
    HarmonyFormatError,
)

# Re-export from ibm-watsonx-ai for drop-in compatibility
from ibm_watsonx_ai import Credentials, APIClient

__version__ = "0.1.0"

__all__ = [
    # Our exports
    "Config",
    "WatsonX120BError",
    "ThinkingOnlyResponseError",
    "ToolExtractionError",
    "JSONExtractionError",
    "SchemaValidationError",
    "StreamingError",
    "HarmonyFormatError",
    # Pass-through from ibm-watsonx-ai
    "Credentials",
    "APIClient",
]