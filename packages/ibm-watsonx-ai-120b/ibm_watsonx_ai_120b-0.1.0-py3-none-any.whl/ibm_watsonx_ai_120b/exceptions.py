"""Custom exceptions for ibm-watsonx-ai-120b."""


class WatsonX120BError(Exception):
    """Base exception for ibm-watsonx-ai-120b errors."""

    pass


class ThinkingOnlyResponseError(WatsonX120BError):
    """Model returned only reasoning_content without actual content.

    This happens when WatsonX returns a response with 'reasoning_content' but
    empty 'content'. The wrapper will automatically retry when this occurs.
    """

    def __init__(self, reasoning_preview: str = ""):
        self.reasoning_preview = reasoning_preview
        super().__init__(
            f"Model returned only thinking content without actual response. "
            f"Preview: {reasoning_preview[:200]}..."
        )


class ToolExtractionError(WatsonX120BError):
    """Failed to extract tool calls from model response."""

    pass


class JSONExtractionError(WatsonX120BError):
    """Failed to extract valid JSON from model response."""

    pass


class SchemaValidationError(WatsonX120BError):
    """JSON response doesn't match expected schema."""

    def __init__(self, message: str, schema_name: str = "", errors: list | None = None):
        self.schema_name = schema_name
        self.errors = errors or []
        super().__init__(message)


class StreamingError(WatsonX120BError):
    """Streaming-specific failures."""

    pass


class HarmonyFormatError(WatsonX120BError):
    """Harmony format token leakage issues."""

    pass