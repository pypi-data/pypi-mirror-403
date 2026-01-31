# ibm-watsonx-ai-120b

A **drop-in replacement** for `ibm-watsonx-ai` that fixes all known issues with IBM's vLLM-hosted `openai/gpt-oss-120b` and `openai/gpt-oss-20b` models.

## The Problem

IBM hosts OpenAI's gpt-oss models on WatsonX using vLLM, but the deployment has numerous bugs:

- **Tool calling doesn't work** - `tool_calls` array is always empty
- **JSON schema mode is ignored** - Model returns free text instead of JSON
- **Thinking leaks into output** - `reasoning_content` appears without actual `content`
- **Streaming breaks with tools** - Tool calls appear in wrong fields
- **Harmony tokens leak** - Special tokens like `<|channel|>` appear in output

## The Solution

Change one import and everything works:

```python
# Before (broken)
from ibm_watsonx_ai.foundation_models import ModelInference

# After (fixed!)
from ibm_watsonx_ai_120b.foundation_models import ModelInference

# Your code stays exactly the same
model = ModelInference(
    model_id="openai/gpt-oss-120b",
    credentials=credentials,
    project_id=project_id
)

# Tool calling now works!
response = model.chat(
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }]
)

# JSON schema mode now works!
response = model.chat(
    messages=[{"role": "user", "content": "List 3 colors"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "colors",
            "schema": {
                "type": "object",
                "properties": {
                    "colors": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["colors"]
            }
        }
    }
)
```

## Installation

```bash
pip install ibm-watsonx-ai-120b
```

## When IBM Fixes Their vLLM

Just change your import back:

```python
# Fixed by IBM - just use the original!
from ibm_watsonx_ai.foundation_models import ModelInference
```

Your code stays exactly the same because we maintained full API compatibility.

## What Gets Fixed

| Feature | Original Behavior | With This Package |
|---------|-------------------|-------------------|
| Tool Calling | `tool_calls=[]` always | Works correctly |
| JSON Schema | Ignored, returns text | Enforced and validated |
| Thinking Responses | Empty content, only reasoning | Automatically handled |
| Streaming + Tools | Tools in wrong field | Falls back to sync |
| Harmony Tokens | Leak into output | Stripped automatically |
| Null Content | Crashes vLLM | Converted to empty string |

## Configuration

```python
from ibm_watsonx_ai_120b import Config

# Adjust retry behavior
Config.max_retries = 5

# Force non-streaming for tools (most reliable)
Config.streaming_tool_strategy = "fallback"

# Enable debug logging
Config.debug = True
```

Or via environment variables:

```bash
export WATSONX_120B_MAX_RETRIES=5
export WATSONX_120B_DISABLE_STREAMING=true
export WATSONX_120B_DEBUG=true
```

## How It Works

The package wraps `ibm-watsonx-ai` and applies fixes through an adapter pipeline:

1. **MessageAdapter** - Fixes null content and tool role issues
2. **ToolAdapter** - Emulates tool calling via prompt injection
3. **JSONAdapter** - Emulates JSON schema via prompt injection
4. **ThinkingAdapter** - Handles reasoning-only responses
5. **HarmonyAdapter** - Strips leaked special tokens
6. **StreamAdapter** - Handles streaming quirks

Everything else passes through unchanged to the original library.

## Requirements

- Python 3.9+
- `ibm-watsonx-ai >= 1.0.0`

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical design and issue catalog
- [TASKS.md](TASKS.md) - Development roadmap

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

This package was developed to centralize workarounds originally implemented in:
- [synx-sf-issue-worker](https://github.com/...)
- [synx-developer](https://github.com/...)

## Links

- [vLLM gpt-oss-120b Issues](https://github.com/vllm-project/vllm/issues?q=gpt-oss-120b)
- [HuggingFace Model Card](https://huggingface.co/openai/gpt-oss-120b)
- [OpenAI Harmony Format](https://github.com/openai/openai-harmony)