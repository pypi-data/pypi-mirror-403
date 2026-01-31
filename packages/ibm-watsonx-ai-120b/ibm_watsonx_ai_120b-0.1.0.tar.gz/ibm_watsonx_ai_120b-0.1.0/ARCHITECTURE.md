# ibm-watsonx-ai-120b Architecture

## Overview

`ibm-watsonx-ai-120b` is a **drop-in replacement** for `ibm-watsonx-ai` that transparently handles all the quirks and bugs in IBM's vLLM-hosted `openai/gpt-oss-120b` and `openai/gpt-oss-20b` models.

### Design Philosophy

```
# Before (with bugs):
from ibm_watsonx_ai.foundation_models import ModelInference
model = ModelInference(model_id="openai/gpt-oss-120b", ...)

# After (with fixes):
from ibm_watsonx_ai_120b.foundation_models import ModelInference  # Same API!
model = ModelInference(model_id="openai/gpt-oss-120b", ...)

# When IBM fixes their vLLM, user just changes import back:
from ibm_watsonx_ai.foundation_models import ModelInference  # Works now!
```

The package wraps `ibm-watsonx-ai` and intercepts only the broken functionality, passing through everything else unchanged.

---

## Problem Statement

IBM hosts `openai/gpt-oss-120b` and `openai/gpt-oss-20b` on their WatsonX platform using vLLM. However, the vLLM deployment has numerous issues that break standard functionality:

### Issue Categories

1. **Thinking/Reasoning Leakage** - Model outputs internal reasoning where content should be
2. **Streaming Bugs** - Tool calls appear in wrong fields when streaming
3. **Tool Calling Broken** - Native function calling doesn't work properly
4. **JSON Schema Ignored** - Structured output mode is completely broken
5. **Chat Template Errors** - Harmony format tokens leak into output
6. **Message Format Quirks** - vLLM crashes on null content and tool roles

---

## Complete Issue Catalog

### 1. Thinking/Reasoning Leakage

| Issue | Description | Workaround |
|-------|-------------|------------|
| `reasoning_content` without `content` | Model returns thinking in `reasoning_content` but leaves `content` empty | Retry automatically; if reasoning contains actual JSON/answer, promote it to content |
| Thinking in tool call arguments | Internal reasoning like "Oops, typo?" appears before JSON | Strip thinking patterns from tool arguments before parsing |
| Harmony tokens in output | `<\|channel\|>analysis` tokens leak into text | Regex strip harmony tokens from all output |
| `<think>...</think>` blocks | Thinking wrapped in XML-like tags | Strip thinking blocks, use content after if present |

**Sources:**
- [Ollama #12203](https://github.com/ollama/ollama/issues/12203)
- [HuggingFace Discussion #69](https://huggingface.co/openai/gpt-oss-120b/discussions/69)

### 2. Streaming Issues

| Issue | Description | Workaround |
|-------|-------------|------------|
| Tool calls in `reasoning_content` | With streaming + large tools + long prompts, tool calls appear in reasoning instead of `tool_calls` | Fall back to non-streaming for tool calls, or accumulate stream and reparse |
| Hanging requests | 1 in 2 queries hang indefinitely (v0.11.0+) | Implement timeout with retry |
| Incomplete chunks | Streaming chunks arrive malformed | Buffer and reassemble before processing |

**Sources:**
- [vLLM #27641](https://github.com/vllm-project/vllm/issues/27641)
- [vLLM #26480](https://github.com/vllm-project/vllm/issues/26480)

### 3. Tool/Function Calling Issues

| Issue | Description | Workaround |
|-------|-------------|------------|
| Empty `tool_calls` array | Model generates tool call structure in content, but `tool_calls=[]` | Extract tool calls from content field via JSON parsing |
| Malformed tool names | Tool name becomes `assistant<\|channel\|>analysis` | Regex clean tool names, match against known tools |
| Invalid JSON in arguments | Model returns malformed JSON in tool arguments | Use `json_repair` library, manual brace matching |
| Tools ignored entirely | Model returns plain text ignoring all tools | Retry with more forceful prompt injection |
| Missing EOS token handling | Model continues generating after `<\|call\|>` token (200012) | Add stop tokens: `[199999, 200002, 200012]` |
| Tool call in wrong field | Tool call JSON appears in `content` instead of `tool_calls` | Parse content for tool call structure, move to correct field |

**Sources:**
- [vLLM #22337](https://github.com/vllm-project/vllm/issues/22337)
- [Ollama #11704](https://github.com/ollama/ollama/issues/11704)
- [Ollama #11800](https://github.com/ollama/ollama/issues/11800)
- [Groq Forum - Tools Ignored](https://community.groq.com/t/gpt-oss-120b-ignoring-tools/385)
- [EXO #1100](https://github.com/exo-explore/exo/issues/1100)

### 4. JSON Schema / Structured Output Issues

| Issue | Description | Workaround |
|-------|-------------|------------|
| `response_format: json_schema` ignored | Model completely ignores schema, returns free text | Prompt injection with schema examples and explicit instructions |
| Extra commentary in JSON | Responses contain prose around JSON object | Extract JSON via brace matching, strip surrounding text |
| Schema validation failures | Output doesn't match provided schema | Validate and retry with error feedback; use `jsonschema` library |
| Incomplete JSON (token limit) | JSON truncated mid-object | Detect truncation, request continuation or increase max_tokens |

**Sources:**
- [Groq Forum - Structured Output](https://community.groq.com/t/structured-outputs-ignored-by-openai-gpt-oss-120b/687)
- [Glukhov Blog](https://www.glukhov.org/post/2025/10/ollama-gpt-oss-structured-output-issues/)
- [LiteLLM #16014](https://github.com/BerriAI/litellm/issues/16014)

### 5. Chat Template / Harmony Format Issues

| Issue | Description | Workaround |
|-------|-------------|------------|
| Missing `<\|constrain\|>` token | Template outputs `json` instead of `<\|constrain\|>json` | Handled by prompt injection approach |
| Preambles treated as CoT | Content before tool calls treated as chain-of-thought | Explicitly structure messages to avoid ambiguity |
| Old CoTs accumulate | Previous turns' chain-of-thought kept in context | Clean up reasoning from history before sending |
| Special tokens in output | `<\|start\|>`, `<\|end\|>`, `<\|channel\|>` appear in text | Regex strip all harmony special tokens |

**Sources:**
- [HuggingFace Discussion #69](https://huggingface.co/openai/gpt-oss-120b/discussions/69)
- [HuggingFace Discussion #76](https://huggingface.co/openai/gpt-oss-120b/discussions/76)

### 6. Message Format Issues

| Issue | Description | Workaround |
|-------|-------------|------------|
| Null content crashes vLLM | `"content": null` causes server errors | Ensure content is always string (empty string if needed) |
| `role: "tool"` not supported | Tool response messages cause errors | Convert to user messages with formatted content |
| `tool_calls` in message breaks things | Assistant messages with `tool_calls` field cause issues | Strip `tool_calls` from message history, represent as text |

---

## Architecture Design

### Package Structure

```
ibm_watsonx_ai_120b/
├── __init__.py                 # Re-exports matching ibm_watsonx_ai
├── foundation_models/
│   ├── __init__.py
│   ├── model_inference.py      # Wrapped ModelInference class
│   └── extensions/
│       └── __init__.py
├── adapters/
│   ├── __init__.py
│   ├── thinking_adapter.py     # Handles reasoning_content issues
│   ├── tool_adapter.py         # Emulates tool calling via prompt injection
│   ├── json_adapter.py         # Emulates JSON schema via prompt injection
│   ├── message_adapter.py      # Fixes message format issues
│   ├── stream_adapter.py       # Handles streaming quirks
│   └── harmony_adapter.py      # Strips harmony format tokens
├── utils/
│   ├── __init__.py
│   ├── json_repair.py          # JSON extraction and repair utilities
│   ├── retry.py                # Retry logic with tenacity
│   └── tokens.py               # Stop token configuration
├── exceptions.py               # Custom exceptions
├── config.py                   # Configuration management
└── _passthrough.py             # Dynamic passthrough for unchanged APIs
```

### Class Hierarchy

```
ibm_watsonx_ai.foundation_models.ModelInference (original)
                    │
                    ▼
ibm_watsonx_ai_120b.foundation_models.ModelInference (wrapper)
                    │
                    ├── _original: ModelInference  # Wrapped instance
                    │
                    ├── Intercepts:
                    │   ├── chat() → _adapted_chat()
                    │   ├── chat_stream() → _adapted_chat_stream()
                    │   ├── generate_text() → _adapted_generate()
                    │   └── generate_text_stream() → _adapted_generate_stream()
                    │
                    └── Passes through:
                        └── Everything else via __getattr__
```

### Adapter Pipeline

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    MessageAdapter                            │
│  • Ensure content not null                                   │
│  • Convert tool role to user role                            │
│  • Strip tool_calls from history                             │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│              ToolAdapter (if tools provided)                 │
│  • Inject tool descriptions into system prompt               │
│  • Add JSON format instructions                              │
│  • Configure stop tokens                                     │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│           JSONAdapter (if response_format provided)          │
│  • Inject schema into system prompt                          │
│  • Add format examples                                       │
│  • Add strict instructions                                   │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Original API Call                          │
│  • ibm_watsonx_ai.ModelInference.chat()                     │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                   HarmonyAdapter                             │
│  • Strip <|channel|>, <|start|>, <|end|> tokens             │
│  • Clean special token leakage                               │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                   ThinkingAdapter                            │
│  • Handle reasoning_content without content                  │
│  • Promote reasoning to content if it's actual answer        │
│  • Strip <think> blocks                                      │
│  • Retry if thinking-only response                           │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│              ToolAdapter (response processing)               │
│  • Extract tool calls from content if tool_calls empty       │
│  • Validate tool calls against available tools               │
│  • Fix malformed tool names                                  │
│  • Parse/repair JSON arguments                               │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│              JSONAdapter (response processing)               │
│  • Extract JSON from response                                │
│  • Validate against schema                                   │
│  • Repair malformed JSON                                     │
│  • Retry if validation fails                                 │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
User Response (OpenAI-compatible format)
```

### Streaming Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   StreamAdapter                              │
│                                                              │
│  Option A: Accumulate-and-Reparse (for tools/JSON)          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Accumulate all chunks                            │    │
│  │ 2. Parse complete response                          │    │
│  │ 3. Apply tool/JSON adapters                         │    │
│  │ 4. Yield synthetic chunks with corrected data       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Option B: Pass-through (for plain chat)                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Yield chunks as-is                               │    │
│  │ 2. Strip harmony tokens from each chunk             │    │
│  │ 3. Handle thinking blocks in real-time              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Option C: Fallback to Non-Streaming (safest for tools)     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Detect tools/JSON schema in request              │    │
│  │ 2. Make non-streaming call                          │    │
│  │ 3. Return complete response (no streaming)          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## API Compatibility

### Supported Classes (Wrapped)

| Original Class | Wrapped Class | Notes |
|----------------|---------------|-------|
| `ModelInference` | `ModelInference` | Primary wrapper, all fixes applied |
| `Credentials` | `Credentials` | Pass-through |
| `APIClient` | `APIClient` | Pass-through |

### Supported Methods (Intercepted)

| Method | Behavior |
|--------|----------|
| `chat(messages, ...)` | Full adapter pipeline |
| `chat_stream(messages, ...)` | Streaming with fixes |
| `generate_text(prompt, ...)` | Adapter pipeline |
| `generate_text_stream(prompt, ...)` | Streaming with fixes |

### Supported Parameters (Enhanced)

| Parameter | Original Behavior | Enhanced Behavior |
|-----------|-------------------|-------------------|
| `tools` | Broken/ignored | Emulated via prompt injection |
| `tool_choice` | Broken/ignored | Emulated via prompt injection |
| `response_format` | Broken/ignored | Emulated via prompt injection |
| `response_format.json_schema` | Broken/ignored | Schema injected + validated |
| `reasoning_effort` | Works | Pass-through |
| `max_tokens` | Works | Pass-through |
| `temperature` | Works | Pass-through |

---

## Configuration

### Environment Variables

```bash
# Standard WatsonX config (unchanged)
WATSONX_API_KEY=your-api-key
WATSONX_PROJECT_ID=your-project-id
WATSONX_REGION_URL=https://us-south.ml.cloud.ibm.com

# 120b-specific config
WATSONX_120B_MAX_RETRIES=3          # Retries for thinking-only responses
WATSONX_120B_DISABLE_STREAMING=false # Force non-streaming for tools
WATSONX_120B_DEBUG=false             # Enable debug logging
```

### Programmatic Configuration

```python
from ibm_watsonx_ai_120b import Config

Config.max_retries = 5
Config.streaming_tool_strategy = "accumulate"  # or "fallback"
Config.json_repair_enabled = True
```

---

## Migration Guide

### From Direct ibm-watsonx-ai Usage

```python
# Before
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

# After (just change import)
from ibm_watsonx_ai_120b import Credentials
from ibm_watsonx_ai_120b.foundation_models import ModelInference

# Everything else stays the same!
```

### From Custom Workarounds (synx-sf-issue-worker style)

```python
# Before: Custom WatsonXClient with adapters
from synx_sf_issue_worker.llm import WatsonXClient, WatsonXConfig

config = WatsonXConfig(api_key=..., project_id=...)
client = WatsonXClient(config)
response = client.chat_with_tools(messages, tools)

# After: Standard API, fixes automatic
from ibm_watsonx_ai_120b.foundation_models import ModelInference

model = ModelInference(model_id="openai/gpt-oss-120b", ...)
response = model.chat(messages=messages, tools=tools)  # Just works!
```

### When IBM Fixes vLLM

```python
# Just change the import back!
from ibm_watsonx_ai.foundation_models import ModelInference  # Original package

# Same code works because we maintained API compatibility
```

---

## Testing Strategy

### Unit Tests
- Each adapter tested in isolation
- Mock responses covering all known failure modes
- JSON repair edge cases

### Integration Tests
- Real API calls to WatsonX
- Comparison: same request to 120b wrapper vs raw API
- Verify fixes actually work

### Compatibility Tests
- Ensure all `ibm-watsonx-ai` public APIs accessible
- Verify pass-through for non-broken functionality
- Test migration from existing workarounds

---

## Dependencies

```toml
[project]
dependencies = [
    "ibm-watsonx-ai>=1.0.0",    # Wrapped package
    "tenacity>=8.0.0",           # Retry logic
    "json-repair>=0.1.0",        # JSON fixing
    "jsonschema>=4.0.0",         # Schema validation
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "responses>=0.23.0",         # HTTP mocking
]
```