# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Drop-in replacement wrapper for `ibm-watsonx-ai` that fixes vLLM bugs with IBM's hosted `openai/gpt-oss-120b` and `openai/gpt-oss-20b` models. Users change only their import statement.

```python
# Users change this:
from ibm_watsonx_ai.foundation_models import ModelInference
# To this:
from ibm_watsonx_ai_120b.foundation_models import ModelInference
```

## Commands

```bash
pip install -e ".[dev]"           # Install in dev mode
pytest tests/                      # Run all tests
pytest tests/test_tool_adapter.py -v  # Run specific test
python -m build                    # Build package
mypy ibm_watsonx_ai_120b/         # Type checking
```

## Key Documents

- **ARCHITECTURE.md** - Complete technical design, issue catalog, adapter pipeline diagrams
- **TASKS.md** - All development tasks with checkboxes, priority order
- **reference/** - Working adapter implementations to port from synx-sf-issue-worker

## Architecture

The wrapper intercepts `ModelInference.chat()` and applies an adapter pipeline:

**Request path:** MessageAdapter → ToolAdapter → JSONAdapter → Original API
**Response path:** HarmonyAdapter → ThinkingAdapter → ToolAdapter → JSONAdapter

Key adapters:
- **MessageAdapter** - Fix null content, convert `tool` role to `user`
- **ToolAdapter** - Emulate tool calling via prompt injection (native tool calling is broken)
- **JSONAdapter** - Emulate JSON schema via prompt injection (schema mode is ignored)
- **HarmonyAdapter** - Strip leaked tokens (`<|channel|>`, `<|start|>`, etc.)
- **ThinkingAdapter** - Handle `reasoning_content` without `content`, retry if needed

Everything not broken passes through via `__getattr__`.

## Critical Design Constraints

1. **API Compatibility** - Must be drop-in replacement; match `ibm-watsonx-ai` signatures exactly
2. **Pass-through First** - Only intercept broken functionality
3. **Retry Expected** - Model often needs 2-3 attempts for tools/JSON
4. **Streaming + Tools** - Fall back to non-streaming for reliability

## Code Style

- Type hints throughout
- `tenacity` for retry logic
- `logging` module (not print)
- Google-style docstrings
- Follow patterns in `reference/watsonx_client/`