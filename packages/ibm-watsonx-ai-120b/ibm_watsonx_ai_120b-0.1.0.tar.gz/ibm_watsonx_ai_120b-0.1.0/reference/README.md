# Reference Code

This directory contains the working code from `synx-sf-issue-worker` that handles all the vLLM/Harmony format quirks for `openai/gpt-oss-120b`.

**This code is for REFERENCE ONLY** - it should not be used directly in `ibm-watsonx-ai-120b`. Instead, it should inform the design and implementation of the new package.

## Directory Structure

```
reference/
├── watsonx_client/          # Core client and adapters
│   ├── __init__.py          # Exports WatsonXClient, WatsonXConfig
│   ├── client.py            # Main WatsonXClient class
│   ├── config.py            # Configuration management
│   ├── exceptions.py        # Custom exceptions
│   ├── generator.py         # WatsonXGenerator (simplified interface)
│   └── adapters/
│       ├── __init__.py
│       ├── json_adapter.py      # JSON schema emulation
│       ├── tool_adapter.py      # Tool calling emulation
│       └── message_adapter.py   # Message format fixes
└── examples/
    ├── test_watsonx_client.py   # Unit tests (great examples!)
    ├── usage_sf_issue_worker.py # Usage from synx-sf-issue-worker
    └── usage_synx_developer.py  # Usage from synx-developer
```

## Key Classes

### WatsonXClient (`client.py`)
The main client class that wraps IBM's ModelInference. Key methods:
- `chat(messages)` - Basic chat with thinking-only retry
- `chat_with_tools(messages, tools)` - Tool calling emulation
- `chat_with_json_schema(messages, schema)` - JSON schema emulation

### WatsonXGenerator (`generator.py`)
A simplified interface on top of WatsonXClient:
- `generate(prompt)` - Text generation
- `generate_json(prompt, schema)` - JSON generation with schema

### Adapters

#### JSONSchemaAdapter (`adapters/json_adapter.py`)
- Injects schema instructions into system prompt
- Generates schema examples
- Extracts and validates JSON from response
- Handles thinking blocks, markdown code fences
- Uses `json_repair` for malformed JSON

#### ToolAdapter (`adapters/tool_adapter.py`)
- Injects tool descriptions into system prompt
- Extracts tool calls from response content
- Validates tool calls against available tools
- Handles forced function calling

#### MessageAdapter (`adapters/message_adapter.py`)
- Ensures content is never null
- Converts `role: "tool"` to `role: "user"`
- Strips `tool_calls` from message history

## What Needs to Change for ibm-watsonx-ai-120b

The current code:
1. Creates its own `WatsonXClient` class
2. Directly calls IBM SDK internally
3. Has project-specific configuration

The new package needs:
1. Wrap `ibm_watsonx_ai.ModelInference` instead
2. Match the exact API surface of `ibm-watsonx-ai`
3. Use `__getattr__` for pass-through of unchanged methods
4. Generic configuration via environment variables

## Adapters That Port Directly

The adapter classes (`json_adapter.py`, `tool_adapter.py`, `message_adapter.py`) are largely reusable with minimal changes:
- Remove project-specific imports
- Add type hints
- Adjust logging

## New Components Needed

1. **HarmonyAdapter** - Strip leaked harmony tokens (currently inline in client.py)
2. **StreamAdapter** - Handle streaming quirks (partially exists)
3. **Pass-through mechanism** - Forward unknown methods to original