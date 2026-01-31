"""
Usage examples from synx-developer.

This shows more advanced patterns including:
- JSON schema with complex nested structures
- Code generation with file changes
- Design document generation

Sources:
- synx_developer/services/design.py
- synx_developer/adapters/code_generator.py
"""

import os
from typing import Any, Dict, List

# =============================================================================
# INITIALIZATION
# =============================================================================

from synx_developer.llm import WatsonXGenerator

def get_generator() -> WatsonXGenerator:
    """Create a WatsonXGenerator from environment variables."""
    return WatsonXGenerator(
        api_key=os.environ.get("WATSONX_API_KEY", ""),
        project_id=os.environ.get("WATSONX_PROJECT_ID", ""),
        region_url=os.environ.get("WATSONX_REGION_URL", "https://us-south.ml.cloud.ibm.com"),
    )


# =============================================================================
# COMPLEX JSON SCHEMA (from design.py)
# =============================================================================

def identify_file_changes_example():
    """Pattern from DesignService._identify_file_changes.

    Shows complex nested JSON schema with arrays of objects.
    """
    generator = get_generator()

    requirements = """
    Add user authentication to the API.
    - Support JWT tokens
    - Add login/logout endpoints
    - Protect existing endpoints
    """

    project_structure = """
    src/
    ├── api/
    │   ├── routes.py
    │   └── handlers.py
    ├── models/
    │   └── user.py
    └── main.py
    """

    prompt = f"""Analyze these requirements and identify all files that need to be created or modified.

REQUIREMENTS:
{requirements}

PROJECT STRUCTURE:
{project_structure}

OUTPUT JSON with two arrays:
1. "create" - new files to create with: path, purpose
2. "modify" - existing files to modify with: path, purpose

```json
{{
  "create": [
    {{"path": "src/new_file.py", "purpose": "Description of what this creates"}}
  ],
  "modify": [
    {{"path": "src/existing.py", "purpose": "What changes are needed"}}
  ]
}}
```

Be specific about file paths. Consider existing patterns in the codebase.
"""

    # No explicit schema needed - the prompt describes it clearly
    # Generator will extract the JSON from the response
    response = generator.generate_json(prompt, max_tokens=4000)

    # Process results
    files_to_create = response.get("create", [])
    files_to_modify = response.get("modify", [])

    print(f"Files to create: {len(files_to_create)}")
    for f in files_to_create:
        print(f"  - {f.get('path')}: {f.get('purpose')}")

    print(f"Files to modify: {len(files_to_modify)}")
    for f in files_to_modify:
        print(f"  - {f.get('path')}: {f.get('purpose')}")

    return files_to_create, files_to_modify


# =============================================================================
# CODE GENERATION WITH SCHEMA (from code_generator.py)
# =============================================================================

def generate_code_example():
    """Pattern from CodeGenerator.execute.

    Shows code generation with explicit JSON schema for file changes.
    """
    generator = get_generator()

    task = {
        "title": "Implement user authentication middleware",
        "description": "Create middleware that validates JWT tokens",
        "files": ["src/middleware/auth.py"],
        "acceptance_criteria": [
            "Validate JWT tokens from Authorization header",
            "Return 401 for invalid tokens",
            "Attach user info to request context",
        ]
    }

    existing_file_content = """
# src/middleware/__init__.py
from .logging import LoggingMiddleware
"""

    system_prompt = """You are an expert software developer implementing tasks.
Generate clean, well-structured code that:
1. Follows the project's existing patterns and conventions
2. Includes appropriate error handling
3. Is well-documented where necessary
4. Meets all acceptance criteria

Return complete file contents, not diffs or patches."""

    criteria_text = "\n".join(f"- {c}" for c in task["acceptance_criteria"])

    prompt = f"""Implement the following task:

## Task
**Title**: {task["title"]}
**Operation**: CREATE
**Description**: {task["description"]}

**Files to create**: {', '.join(task["files"])}

**Acceptance Criteria**:
{criteria_text}

## Existing Files
### src/middleware/__init__.py
```
{existing_file_content}
```

## Requirements

Generate the complete content for each file that needs to be created.

Return as JSON with file_changes array.

Each file_change should have:
- path: File path relative to repo root
- action: "create" or "modify"
- content: Complete file content"""

    # Explicit schema for code generation output
    schema = {
        "type": "object",
        "properties": {
            "file_changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "action": {"type": "string", "enum": ["create", "modify"]},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "action", "content"],
                },
            },
        },
        "required": ["file_changes"],
    }

    response = generator.generate_json(
        prompt=prompt,
        system_prompt=system_prompt,
        schema=schema,
        max_tokens=8000,
    )

    # Process results
    file_changes = response.get("file_changes", [])

    for change in file_changes:
        print(f"\n{'='*60}")
        print(f"File: {change['path']} ({change['action']})")
        print(f"{'='*60}")
        print(change["content"][:500] + "..." if len(change["content"]) > 500 else change["content"])

    return file_changes


# =============================================================================
# IMPLEMENTATION STEPS GENERATION (from design.py)
# =============================================================================

def generate_implementation_steps_example():
    """Pattern from DesignService._generate_implementation_steps.

    Shows generating ordered steps with dependencies.
    """
    generator = get_generator()

    files_summary = """
- [CREATE] src/auth/jwt.py: JWT token handling utilities
- [CREATE] src/auth/middleware.py: Authentication middleware
- [MODIFY] src/api/routes.py: Add auth to protected routes
- [MODIFY] src/main.py: Register auth middleware
"""

    requirements = "Add JWT authentication to protect API endpoints"

    prompt = f"""Generate implementation steps for these file changes.

REQUIREMENTS:
{requirements}

FILES TO IMPLEMENT:
{files_summary}

OUTPUT JSON array of steps with: order (int), description, files (array of paths involved)

```json
[
  {{"order": 1, "description": "Step description", "files": ["path/to/file.py"]}}
]
```

Order steps logically - dependencies first. Each step should be atomic and clear.
"""

    response = generator.generate_json(prompt, max_tokens=2000)

    # Handle both array response and wrapped response
    if isinstance(response, list):
        steps = response
    elif isinstance(response, dict) and "steps" in response:
        steps = response["steps"]
    else:
        steps = []

    print("Implementation Steps:")
    for step in sorted(steps, key=lambda s: s.get("order", 0)):
        print(f"\n{step['order']}. {step['description']}")
        print(f"   Files: {', '.join(step.get('files', []))}")

    return steps


# =============================================================================
# LONG-FORM TEXT GENERATION (from design.py)
# =============================================================================

def generate_design_sections_example():
    """Pattern from DesignService._generate_design_sections.

    Shows generating markdown content (not JSON).
    """
    generator = get_generator()

    prompt = """Generate technical design sections for this implementation.

REQUIREMENTS:
Add user authentication using JWT tokens

FILES TO CREATE:
- src/auth/jwt.py: JWT token handling
- src/auth/middleware.py: Auth middleware

FILES TO MODIFY:
- src/api/routes.py: Add auth decorators
- src/main.py: Register middleware

Generate markdown sections for:
1. Technical Approach - How will this be implemented?
2. API/Interface Design - What APIs or interfaces are needed?
3. Data Models - What data structures are involved?
4. Integration Points - How does this integrate with existing code?
5. Error Handling - How will errors be handled?
6. Testing Strategy - How will this be tested?

Output as markdown text. Be specific and reference actual code patterns.
"""

    # Use plain generate() for markdown output (not JSON)
    response = generator.generate(prompt, max_tokens=6000)

    print(response)
    return response


# =============================================================================
# USING WATSONX CLIENT DIRECTLY (lower level)
# =============================================================================

def direct_client_usage_example():
    """Example of using WatsonXClient directly for more control.

    The client provides:
    - chat() - Basic chat with thinking-only retry
    - chat_with_tools() - Tool calling emulation
    - chat_with_json_schema() - JSON schema emulation
    """
    from synx_developer.llm.watsonx_client import WatsonXClient, WatsonXConfig

    config = WatsonXConfig(
        api_key=os.environ.get("WATSONX_API_KEY", ""),
        project_id=os.environ.get("WATSONX_PROJECT_ID", ""),
        region_url=os.environ.get("WATSONX_REGION_URL", "https://us-south.ml.cloud.ibm.com"),
        max_tokens=8192,
        temperature=0.1,
        reasoning_effort="low",  # Minimize thinking output
    )

    client = WatsonXClient(config)

    # Basic chat
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"}
    ]

    response = client.chat(messages)
    content = response["choices"][0]["message"]["content"]
    print(f"Response: {content}")

    # Chat with JSON schema
    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "integer"},
            "explanation": {"type": "string"}
        },
        "required": ["answer", "explanation"]
    }

    messages = [
        {"role": "user", "content": "What is 2+2? Return as JSON with answer and explanation."}
    ]

    response = client.chat_with_json_schema(messages, schema)
    content = response["choices"][0]["message"]["content"]
    print(f"JSON Response: {content}")

    # Cleanup
    client.cleanup()


# =============================================================================
# TOOL CALLING EXAMPLE (if tools are needed)
# =============================================================================

def tool_calling_example():
    """Example of tool calling via prompt injection.

    Note: Native tool calling is BROKEN in IBM's vLLM deployment.
    The client emulates it via prompt injection.
    """
    from synx_developer.llm.watsonx_client import WatsonXClient, WatsonXConfig

    config = WatsonXConfig(
        api_key=os.environ.get("WATSONX_API_KEY", ""),
        project_id=os.environ.get("WATSONX_PROJECT_ID", ""),
    )

    client = WatsonXClient(config)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    messages = [
        {"role": "user", "content": "What's the weather like in Tokyo?"}
    ]

    response = client.chat_with_tools(messages, tools)

    message = response["choices"][0]["message"]
    if message.get("tool_calls"):
        for tool_call in message["tool_calls"]:
            print(f"Tool: {tool_call['function']['name']}")
            print(f"Args: {tool_call['function']['arguments']}")
    else:
        print(f"No tool called. Response: {message.get('content')}")

    client.cleanup()


# =============================================================================
# NOTES ON ERROR HANDLING
# =============================================================================

"""
Error handling patterns used in synx-developer:

1. EMPTY RESPONSE HANDLING
   if not response:
       return ExecutionResult(
           success=False,
           message="Generator returned empty response",
           ...
       )

2. EXCEPTION HANDLING
   try:
       response = generator.generate_json(...)
   except Exception as e:
       logger.exception(f"Generation failed: {e}")
       return ExecutionResult(
           success=False,
           message=f"Generation failed: {e}",
           ...
       )

3. JSON VALIDATION
   # Generator validates against schema internally
   # If it returns, it's valid. If schema fails, it raises.

4. GRACEFUL DEGRADATION
   # Always have a fallback for when LLM fails
   if not generator:
       logger.warning("No generator available. Using fallback.")
       return default_value

The key is: NEVER assume the LLM will succeed. Always have fallbacks.
"""