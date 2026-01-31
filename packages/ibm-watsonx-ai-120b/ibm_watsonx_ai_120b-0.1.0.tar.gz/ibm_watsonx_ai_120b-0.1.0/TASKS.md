# ibm-watsonx-ai-120b Tasks

## Project Status: Planning Complete

This document tracks all tasks required to build the `ibm-watsonx-ai-120b` package.

---

## Phase 1: Project Setup

### 1.1 Package Structure
- [ ] Create `pyproject.toml` with package metadata and dependencies
- [ ] Create package directory structure:
  ```
  ibm_watsonx_ai_120b/
  ├── __init__.py
  ├── foundation_models/
  ├── adapters/
  ├── utils/
  ├── exceptions.py
  └── config.py
  ```
- [ ] Set up `__init__.py` with proper re-exports
- [ ] Create `py.typed` marker for type hints
- [ ] Add `.gitignore` for Python projects

### 1.2 Development Environment
- [ ] Create `requirements-dev.txt` or dev dependencies in pyproject.toml
- [ ] Set up pytest configuration
- [ ] Create initial test structure

---

## Phase 2: Core Infrastructure

### 2.1 Configuration (`config.py`)
- [ ] Create `Config` class with defaults
- [ ] Support environment variable overrides:
  - `WATSONX_120B_MAX_RETRIES` (default: 3)
  - `WATSONX_120B_DISABLE_STREAMING` (default: false)
  - `WATSONX_120B_DEBUG` (default: false)
  - `WATSONX_120B_JSON_REPAIR` (default: true)
- [ ] Add programmatic configuration API

### 2.2 Exceptions (`exceptions.py`)
- [ ] `WatsonX120BError` - Base exception
- [ ] `ThinkingOnlyResponseError` - Model returned only reasoning
- [ ] `ToolExtractionError` - Failed to extract tool calls
- [ ] `JSONExtractionError` - Failed to extract JSON
- [ ] `SchemaValidationError` - JSON doesn't match schema
- [ ] `StreamingError` - Streaming-specific failures
- [ ] `HarmonyFormatError` - Token leakage issues

### 2.3 Utilities (`utils/`)

#### 2.3.1 JSON Utilities (`utils/json_repair.py`)
- [ ] `extract_json(text)` - Find JSON in mixed text
- [ ] `repair_json(text)` - Fix common JSON errors
- [ ] `find_json_boundaries(text)` - Locate `{...}` with proper nesting
- [ ] `strip_markdown_code_blocks(text)` - Remove ```json``` wrappers
- [ ] `fix_trailing_commas(json_str)` - Remove trailing commas
- [ ] `fix_unquoted_keys(json_str)` - Quote unquoted keys

#### 2.3.2 Retry Utilities (`utils/retry.py`)
- [ ] `create_retry_decorator(max_attempts, exceptions)` - Configurable tenacity wrapper
- [ ] `is_retryable_error(exception)` - Determine if error is transient

#### 2.3.3 Token Utilities (`utils/tokens.py`)
- [ ] `GPT_OSS_STOP_TOKENS` - List: `[199999, 200002, 200012]`
- [ ] `HARMONY_SPECIAL_TOKENS` - Regex patterns for harmony tokens
- [ ] `strip_harmony_tokens(text)` - Remove all harmony format tokens

---

## Phase 3: Adapters

### 3.1 Message Adapter (`adapters/message_adapter.py`)

**Purpose:** Fix message format issues before sending to API

- [ ] `adapt_messages(messages)` - Main entry point
- [ ] `ensure_content_not_null(message)` - Replace `None` with `""`
- [ ] `convert_tool_role(message)` - Convert `role: "tool"` to `role: "user"`
- [ ] `strip_tool_calls_from_history(messages)` - Remove `tool_calls` field
- [ ] `format_tool_result(tool_call_id, result)` - Format tool response as user message

**Tests:**
- [ ] Test null content handling
- [ ] Test tool role conversion
- [ ] Test tool_calls stripping
- [ ] Test mixed message histories

### 3.2 Harmony Adapter (`adapters/harmony_adapter.py`)

**Purpose:** Strip harmony format token leakage from output

- [ ] `strip_harmony_tokens(text)` - Remove all harmony tokens
- [ ] `strip_channel_markers(text)` - Remove `<|channel|>analysis` etc.
- [ ] `strip_special_tokens(text)` - Remove `<|start|>`, `<|end|>`, etc.
- [ ] `clean_response(response)` - Apply all cleaning to response object

**Tokens to strip:**
```
<|start|>
<|end|>
<|channel|>
<|message|>
<|constrain|>
<|call|>
<|return|>
assistant<|channel|>analysis
assistant<|channel|>commentary
```

**Tests:**
- [ ] Test each token pattern
- [ ] Test combinations
- [ ] Test tokens mid-sentence
- [ ] Test tokens in JSON values (should preserve)

### 3.3 Thinking Adapter (`adapters/thinking_adapter.py`)

**Purpose:** Handle reasoning_content without content issues

- [ ] `process_response(response)` - Main entry point
- [ ] `has_thinking_only(response)` - Detect thinking-only response
- [ ] `is_actual_content(text)` - Check if reasoning contains real answer
- [ ] `promote_reasoning_to_content(response)` - Move reasoning to content
- [ ] `strip_think_blocks(text)` - Remove `<think>...</think>` blocks
- [ ] `extract_content_after_thinking(text)` - Get content after thinking block

**Detection patterns for "actual content":**
- Starts with `{` (JSON)
- Starts with `#` (Markdown)
- Starts with ``` (Code block)
- Contains valid JSON object

**Tests:**
- [ ] Test thinking-only detection
- [ ] Test reasoning promotion
- [ ] Test think block stripping
- [ ] Test mixed thinking + content

### 3.4 Tool Adapter (`adapters/tool_adapter.py`)

**Purpose:** Emulate tool calling via prompt injection

#### Request Processing
- [ ] `inject_tool_instructions(messages, tools, tool_choice)` - Add tool prompt
- [ ] `format_tools_description(tools)` - Human-readable tool descriptions
- [ ] `create_tool_system_prompt(tools, tool_choice)` - Full system prompt
- [ ] `inject_forced_function_example(messages, function_name)` - Add example for required tools

#### Response Processing
- [ ] `extract_tool_calls(response)` - Find tool calls in response
- [ ] `extract_from_content(content)` - Parse tool calls from content field
- [ ] `validate_tool_call(tool_call, available_tools)` - Validate structure
- [ ] `fix_tool_name(name, available_tools)` - Match against known tools
- [ ] `parse_tool_arguments(arguments)` - Parse/repair JSON arguments
- [ ] `format_tool_response(tool_calls)` - Create proper OpenAI format

#### Tool Call JSON Structure
```json
{
  "tool_calls": [
    {
      "id": "call_xxx",
      "type": "function",
      "function": {
        "name": "function_name",
        "arguments": {"arg": "value"}
      }
    }
  ]
}
```

**Tests:**
- [ ] Test tool description formatting
- [ ] Test system prompt generation
- [ ] Test tool call extraction from content
- [ ] Test tool name fixing
- [ ] Test argument JSON repair
- [ ] Test forced function behavior

### 3.5 JSON Adapter (`adapters/json_adapter.py`)

**Purpose:** Emulate JSON schema mode via prompt injection

#### Request Processing
- [ ] `inject_json_instructions(messages, response_format)` - Add JSON prompt
- [ ] `create_json_system_prompt(schema, schema_name)` - System prompt with schema
- [ ] `create_json_object_prompt()` - Simple JSON object mode prompt
- [ ] `generate_schema_example(schema)` - Create example matching schema
- [ ] `get_property_reminders(schema)` - List property names/types

#### Response Processing
- [ ] `extract_json(response)` - Find JSON in response
- [ ] `validate_against_schema(json_obj, schema)` - Schema validation
- [ ] `format_json_response(json_obj)` - Create proper response format

**Tests:**
- [ ] Test schema example generation
- [ ] Test property type handling (string, number, boolean, array, object)
- [ ] Test nested schema handling
- [ ] Test JSON extraction from mixed text
- [ ] Test schema validation
- [ ] Test validation error messages

### 3.6 Stream Adapter (`adapters/stream_adapter.py`)

**Purpose:** Handle streaming quirks

#### Strategies
- [ ] `StreamStrategy.PASSTHROUGH` - Stream as-is (plain chat)
- [ ] `StreamStrategy.ACCUMULATE` - Collect all, reparse, re-emit
- [ ] `StreamStrategy.FALLBACK` - Use non-streaming for tools/JSON

#### Implementation
- [ ] `determine_strategy(request)` - Choose strategy based on request
- [ ] `passthrough_stream(stream)` - Clean each chunk, yield
- [ ] `accumulate_stream(stream)` - Collect, process, re-emit
- [ ] `fallback_to_sync(request)` - Make sync call, return single response

**Tests:**
- [ ] Test strategy selection
- [ ] Test passthrough cleaning
- [ ] Test accumulation and re-parsing
- [ ] Test fallback behavior

---

## Phase 4: Main Wrapper

### 4.1 ModelInference Wrapper (`foundation_models/model_inference.py`)

- [ ] Create `ModelInference` class wrapping original
- [ ] Implement `__init__` matching original signature
- [ ] Implement `__getattr__` for pass-through
- [ ] Intercept `chat()` method
- [ ] Intercept `chat_stream()` method
- [ ] Intercept `generate_text()` method
- [ ] Intercept `generate_text_stream()` method
- [ ] Add adapter pipeline orchestration
- [ ] Add retry logic for thinking-only responses

#### Method Signatures to Match
```python
def chat(
    self,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict]] = None,
    tool_choice: Optional[Union[str, Dict]] = None,
    response_format: Optional[Dict] = None,
    **kwargs
) -> Dict[str, Any]:
    ...

def chat_stream(
    self,
    messages: List[Dict[str, Any]],
    **kwargs
) -> Iterator[Dict[str, Any]]:
    ...
```

**Tests:**
- [ ] Test basic chat pass-through
- [ ] Test tool calling integration
- [ ] Test JSON schema integration
- [ ] Test streaming
- [ ] Test retry on thinking-only
- [ ] Test error handling

### 4.2 Pass-through Module (`_passthrough.py`)

- [ ] Dynamic import forwarding for unchanged APIs
- [ ] `Credentials` pass-through
- [ ] `APIClient` pass-through
- [ ] Any other public classes

---

## Phase 5: Package Exports

### 5.1 Root `__init__.py`
```python
from ibm_watsonx_ai_120b.foundation_models import ModelInference
from ibm_watsonx_ai_120b._passthrough import Credentials, APIClient
from ibm_watsonx_ai_120b.config import Config
from ibm_watsonx_ai_120b.exceptions import (
    WatsonX120BError,
    ThinkingOnlyResponseError,
    # ... etc
)

__all__ = [
    "ModelInference",
    "Credentials",
    "APIClient",
    "Config",
    # ... exceptions
]
```

### 5.2 `foundation_models/__init__.py`
```python
from ibm_watsonx_ai_120b.foundation_models.model_inference import ModelInference

__all__ = ["ModelInference"]
```

---

## Phase 6: Testing

### 6.1 Unit Tests
- [ ] `tests/test_message_adapter.py`
- [ ] `tests/test_harmony_adapter.py`
- [ ] `tests/test_thinking_adapter.py`
- [ ] `tests/test_tool_adapter.py`
- [ ] `tests/test_json_adapter.py`
- [ ] `tests/test_stream_adapter.py`
- [ ] `tests/test_json_repair.py`
- [ ] `tests/test_model_inference.py`

### 6.2 Integration Tests
- [ ] `tests/integration/test_real_api.py` - Requires credentials
- [ ] `tests/integration/test_tool_calling.py`
- [ ] `tests/integration/test_json_schema.py`
- [ ] `tests/integration/test_streaming.py`

### 6.3 Compatibility Tests
- [ ] `tests/test_api_compatibility.py` - Verify API matches ibm-watsonx-ai

---

## Phase 7: Documentation

### 7.1 README.md
- [ ] Project description and purpose
- [ ] Installation instructions
- [ ] Quick start example
- [ ] Migration guide from ibm-watsonx-ai
- [ ] Migration guide from custom workarounds
- [ ] Configuration options
- [ ] Known limitations

### 7.2 Additional Docs
- [ ] `CHANGELOG.md`
- [ ] `CONTRIBUTING.md`
- [ ] Inline code documentation (docstrings)

---

## Phase 8: Release

### 8.1 Package Preparation
- [ ] Final version number in pyproject.toml
- [ ] Verify all tests pass
- [ ] Update README with final instructions
- [ ] Create release tag

### 8.2 Distribution
- [ ] Build wheel: `python -m build`
- [ ] Upload to PyPI (or internal registry)
- [ ] Verify installation: `pip install ibm-watsonx-ai-120b`

---

## Reference: Existing Code to Port

The following code from `synx-sf-issue-worker` should be adapted:

| Source File | Target | Notes |
|-------------|--------|-------|
| `llm/watsonx_client/client.py` | `foundation_models/model_inference.py` | Main wrapper logic |
| `llm/watsonx_client/adapters/message_adapter.py` | `adapters/message_adapter.py` | Direct port |
| `llm/watsonx_client/adapters/tool_adapter.py` | `adapters/tool_adapter.py` | Direct port |
| `llm/watsonx_client/adapters/json_adapter.py` | `adapters/json_adapter.py` | Direct port |
| `llm/watsonx_client/config.py` | `config.py` | Simplify, remove bob-specific |
| `llm/watsonx_client/exceptions.py` | `exceptions.py` | Rename, add new ones |

---

## Priority Order

1. **Phase 1** - Project Setup (required for everything)
2. **Phase 2** - Core Infrastructure (exceptions, config, utilities)
3. **Phase 3.1-3.3** - Message, Harmony, Thinking adapters (most common issues)
4. **Phase 4.1** - Basic ModelInference wrapper (enables testing)
5. **Phase 3.4** - Tool Adapter (complex, high value)
6. **Phase 3.5** - JSON Adapter (complex, high value)
7. **Phase 3.6** - Stream Adapter (lower priority, can fallback)
8. **Phase 5-6** - Exports and Testing
9. **Phase 7-8** - Documentation and Release

---

## Success Criteria

- [ ] All existing `synx-sf-issue-worker` LLM tests pass with new package
- [ ] All existing `synx-developer` LLM tests pass with new package
- [ ] API is 100% compatible with `ibm-watsonx-ai` for supported methods
- [ ] Drop-in replacement works: only import change required
- [ ] Tool calling works reliably (>95% success rate)
- [ ] JSON schema works reliably (>95% success rate)
- [ ] Streaming works for plain chat (tools can fallback)