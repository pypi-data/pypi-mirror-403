"""
Target API Usage for ibm-watsonx-ai-120b

This shows what the API SHOULD look like when the package is complete.
Users should only need to change their import statement.

GOAL: Drop-in replacement for ibm-watsonx-ai
"""

# =============================================================================
# THE DREAM: ONE IMPORT CHANGE
# =============================================================================

# Instead of:
# from ibm_watsonx_ai import Credentials
# from ibm_watsonx_ai.foundation_models import ModelInference

# Users write:
from ibm_watsonx_ai_120b import Credentials
from ibm_watsonx_ai_120b.foundation_models import ModelInference

# Everything else stays EXACTLY the same!

# =============================================================================
# BASIC USAGE (unchanged from ibm-watsonx-ai)
# =============================================================================

def basic_chat_example():
    """Basic chat - identical to ibm-watsonx-ai API."""

    credentials = Credentials(
        api_key="your-api-key",
        url="https://us-south.ml.cloud.ibm.com"
    )

    model = ModelInference(
        model_id="openai/gpt-oss-120b",
        credentials=credentials,
        project_id="your-project-id"
    )

    # Standard chat call - SAME AS ORIGINAL
    response = model.chat(
        messages=[
            {"role": "user", "content": "Hello, how are you?"}
        ]
    )

    # Response format - SAME AS ORIGINAL
    content = response["choices"][0]["message"]["content"]
    print(content)

    # BEHIND THE SCENES:
    # - ibm-watsonx-ai-120b handles thinking-only responses
    # - Automatically retries if model returns only reasoning
    # - Strips <think> blocks and harmony tokens


# =============================================================================
# TOOL CALLING (broken in ibm-watsonx-ai, WORKS with -120b)
# =============================================================================

def tool_calling_example():
    """Tool calling - BROKEN in original, WORKS with -120b."""

    credentials = Credentials(
        api_key="your-api-key",
        url="https://us-south.ml.cloud.ibm.com"
    )

    model = ModelInference(
        model_id="openai/gpt-oss-120b",
        credentials=credentials,
        project_id="your-project-id"
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    # Standard tool calling API - SAME AS ORIGINAL
    response = model.chat(
        messages=[
            {"role": "user", "content": "What's the weather in Tokyo?"}
        ],
        tools=tools,
        tool_choice="auto"
    )

    # Check for tool calls
    message = response["choices"][0]["message"]
    if message.get("tool_calls"):
        for tool_call in message["tool_calls"]:
            print(f"Tool: {tool_call['function']['name']}")
            print(f"Args: {tool_call['function']['arguments']}")

    # BEHIND THE SCENES:
    # - Original ibm-watsonx-ai: tool_calls is always empty!
    # - ibm-watsonx-ai-120b: Emulates tool calling via prompt injection
    # - Extracts tool calls from model's text response
    # - Validates against available tools
    # - Returns proper OpenAI-format tool_calls


# =============================================================================
# JSON SCHEMA MODE (broken in ibm-watsonx-ai, WORKS with -120b)
# =============================================================================

def json_schema_example():
    """JSON schema mode - BROKEN in original, WORKS with -120b."""

    credentials = Credentials(
        api_key="your-api-key",
        url="https://us-south.ml.cloud.ibm.com"
    )

    model = ModelInference(
        model_id="openai/gpt-oss-120b",
        credentials=credentials,
        project_id="your-project-id"
    )

    # Standard JSON schema API - SAME AS ORIGINAL
    response = model.chat(
        messages=[
            {"role": "user", "content": "List 3 colors with their hex codes"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "colors",
                "schema": {
                    "type": "object",
                    "properties": {
                        "colors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "hex": {"type": "string"}
                                },
                                "required": ["name", "hex"]
                            }
                        }
                    },
                    "required": ["colors"]
                }
            }
        }
    )

    # Response is valid JSON matching schema
    import json
    content = response["choices"][0]["message"]["content"]
    data = json.loads(content)

    for color in data["colors"]:
        print(f"{color['name']}: {color['hex']}")

    # BEHIND THE SCENES:
    # - Original ibm-watsonx-ai: Schema is IGNORED, returns free text
    # - ibm-watsonx-ai-120b: Injects schema into prompt
    # - Extracts JSON from response (even if wrapped in text/markdown)
    # - Validates against schema
    # - Retries if validation fails


# =============================================================================
# STREAMING (works, but with quirk handling)
# =============================================================================

def streaming_example():
    """Streaming - works but -120b handles quirks."""

    credentials = Credentials(
        api_key="your-api-key",
        url="https://us-south.ml.cloud.ibm.com"
    )

    model = ModelInference(
        model_id="openai/gpt-oss-120b",
        credentials=credentials,
        project_id="your-project-id"
    )

    # Standard streaming API - SAME AS ORIGINAL
    for chunk in model.chat_stream(
        messages=[
            {"role": "user", "content": "Tell me a story"}
        ]
    ):
        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
        print(content, end="", flush=True)

    # BEHIND THE SCENES:
    # - Strips harmony tokens from chunks
    # - Handles thinking blocks in stream
    # - For tools/JSON: may accumulate and reparse (configurable)


# =============================================================================
# WHEN IBM FIXES THEIR VLLM
# =============================================================================

"""
When IBM fixes their vLLM deployment, users just change the import:

# Before (with -120b wrapper):
from ibm_watsonx_ai_120b import Credentials
from ibm_watsonx_ai_120b.foundation_models import ModelInference

# After (original, now fixed):
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

That's it! No other code changes needed.

This is the ENTIRE VALUE PROPOSITION of the package:
1. Use it now with all the fixes
2. Drop it later with one import change
"""


# =============================================================================
# CONFIGURATION (optional)
# =============================================================================

def configuration_example():
    """Optional configuration for the 120b wrapper."""

    from ibm_watsonx_ai_120b import Config

    # Adjust retry behavior
    Config.max_retries = 5  # Default: 3

    # Force non-streaming for tools (most reliable)
    Config.streaming_tool_strategy = "fallback"  # Options: "passthrough", "accumulate", "fallback"

    # Enable debug logging
    Config.debug = True

    # Or via environment variables:
    # WATSONX_120B_MAX_RETRIES=5
    # WATSONX_120B_STREAMING_TOOL_STRATEGY=fallback
    # WATSONX_120B_DEBUG=true


# =============================================================================
# WHAT PASSES THROUGH UNCHANGED
# =============================================================================

"""
The following work exactly the same as ibm-watsonx-ai (pass-through):

- Basic text generation (generate_text)
- Embeddings
- Tokenization
- Model listing
- Project/space management
- All other methods not related to chat/tools/JSON

Only the broken features are intercepted and fixed:
- chat() - thinking-only handling, harmony token stripping
- chat() with tools - emulated via prompt injection
- chat() with response_format - emulated via prompt injection
- chat_stream() - chunk cleaning, optional accumulation
"""