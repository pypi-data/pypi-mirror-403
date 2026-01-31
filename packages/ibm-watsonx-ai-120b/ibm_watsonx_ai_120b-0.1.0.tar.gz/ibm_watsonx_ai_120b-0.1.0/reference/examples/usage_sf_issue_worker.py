"""
Usage examples from synx-sf-issue-worker.

This shows how the WatsonXGenerator is used in the comment_generator worker
to handle all the vLLM quirks transparently.

Source: synx_sf_issue_worker/workers/comment_generator.py
"""

import os
from typing import Any

# =============================================================================
# INITIALIZATION
# =============================================================================

# The WatsonXGenerator handles all vLLM quirks:
# - Thinking-only response retry
# - JSON extraction and repair
# - Proper parameter handling (max_tokens not max_new_tokens)

from synx_sf_issue_worker.llm import WatsonXGenerator

def get_generator() -> WatsonXGenerator:
    """Create a WatsonXGenerator from environment variables."""
    return WatsonXGenerator(
        api_key=os.environ.get("WATSONX_API_KEY", ""),
        project_id=os.environ.get("WATSONX_PROJECT_ID", ""),
        region_url=os.environ.get("WATSONX_REGION_URL", "https://us-south.ml.cloud.ibm.com"),
    )


# =============================================================================
# BASIC TEXT GENERATION
# =============================================================================

def generate_text_example():
    """Basic text generation with the generator."""
    generator = get_generator()

    prompt = """Analyze this issue and provide a summary:

    Title: ARCH014 - Architecture compliance review
    Body: Need to verify OSS scanning is configured...
    """

    # Simple text generation
    result = generator.generate(
        prompt=prompt,
        max_tokens=8000,
        temperature=0.1,
    )

    return result


# =============================================================================
# JSON GENERATION (WITH SCHEMA)
# =============================================================================

def generate_json_example():
    """JSON generation with schema validation.

    The generator handles:
    - Injecting schema into the prompt
    - Extracting JSON from response (even if wrapped in text/markdown)
    - Validating against the schema
    - Automatic retry on failure
    """
    generator = get_generator()

    prompt = """Extract requirement information from this issue.

    Title: BCDR001 - Business continuity review needed
    Body: We need to verify backup procedures are in place...
    """

    # JSON generation with schema
    schema = {
        "type": "object",
        "properties": {
            "requirement_code": {"type": "string"},
            "pillar": {"type": "string"},
            "summary": {"type": "string"},
            "action_items": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["requirement_code", "pillar", "summary"]
    }

    result = generator.generate_json(
        prompt=prompt,
        schema=schema,
        max_tokens=4000,
    )

    # Result is already parsed JSON dict
    print(f"Requirement: {result.get('requirement_code')}")
    print(f"Pillar: {result.get('pillar')}")
    print(f"Summary: {result.get('summary')}")

    return result


# =============================================================================
# MULTI-PASS GENERATION PATTERN
# =============================================================================

def multi_pass_generation_example():
    """Multi-pass generation pattern used in comment_generator.

    This shows the pattern of:
    1. Generate questions
    2. For each question, analyze content
    3. Synthesize findings
    """
    generator = get_generator()

    issue_body = """
    ## ARCH014 Compliance

    - [x] Mend scanning configured
    - [ ] SBOM generated
    - [ ] Approved repos documented
    """

    # Step 1: Generate questions from the issue body
    questions_prompt = f"""Given this issue body, generate questions to verify compliance:

    {issue_body}

    Output JSON array of questions.
    """

    questions_result = generator.generate_json(
        prompt=questions_prompt,
        schema={
            "type": "array",
            "items": {"type": "string"}
        },
    )

    questions = questions_result if isinstance(questions_result, list) else []

    # Step 2: For each question, analyze the issue
    findings = []
    for question in questions[:5]:  # Limit to 5 questions
        analysis_prompt = f"""Analyze this issue against the question:

        Question: {question}

        Issue Body:
        {issue_body}

        Output JSON with: answered (bool), evidence (string), confidence (float 0-1)
        """

        analysis = generator.generate_json(
            prompt=analysis_prompt,
            schema={
                "type": "object",
                "properties": {
                    "answered": {"type": "boolean"},
                    "evidence": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["answered", "evidence", "confidence"]
            },
        )

        findings.append({
            "question": question,
            "analysis": analysis
        })

    # Step 3: Synthesize final comment
    findings_text = "\n".join([
        f"Q: {f['question']}\nA: {f['analysis']}"
        for f in findings
    ])

    synthesis_prompt = f"""Based on these findings, generate an advisory comment:

    {findings_text}

    Write a helpful comment for the issue author.
    """

    final_comment = generator.generate(
        prompt=synthesis_prompt,
        max_tokens=4000,
        temperature=0.3,  # Slightly higher for more natural language
    )

    return final_comment


# =============================================================================
# ERROR HANDLING PATTERN
# =============================================================================

def error_handling_example():
    """Pattern for handling generator errors gracefully."""
    generator = get_generator()

    prompt = "Generate analysis..."

    try:
        result = generator.generate_json(
            prompt=prompt,
            schema={"type": "object", "properties": {"status": {"type": "string"}}},
            max_tokens=4000,
        )

        if not result:
            # Generator returned empty - use fallback
            print("Generator returned empty, using fallback")
            return {"status": "fallback"}

        return result

    except Exception as e:
        print(f"Generation failed: {e}")
        # Return sensible default
        return {"status": "error", "error": str(e)}


# =============================================================================
# HUMANIZATION PATTERN (from comment_generator.py)
# =============================================================================

def humanize_comment_example():
    """Pattern for humanizing formal content.

    Uses higher temperature and specific prompting to get
    conversational output.
    """
    generator = get_generator()

    formal_content = """
    ## Summary
    ARCH014 compliance review completed.

    ## Findings
    - Mend scanning: Configured
    - SBOM: Not provided
    - Approved repos: Missing documentation

    ## Recommendations
    1. Generate and attach SBOM
    2. Document approved repositories
    """

    humanize_prompt = f"""Transform this formal review into a friendly comment:

{formal_content}

Write like you're chatting with a colleague. Ask questions about missing items.
Don't use headers or formal language.
"""

    # Higher temperature for more natural language
    result = generator.generate(
        prompt=humanize_prompt,
        max_tokens=2000,
        temperature=0.85,
    )

    return result


# =============================================================================
# NOTES ON WHAT THE GENERATOR HANDLES INTERNALLY
# =============================================================================

"""
The WatsonXGenerator handles these vLLM quirks internally:

1. THINKING-ONLY RESPONSES
   - Model sometimes returns only `reasoning_content` with empty `content`
   - Generator automatically retries up to 3 times
   - If reasoning contains actual JSON, it's promoted to content

2. JSON EXTRACTION
   - Model often wraps JSON in markdown code blocks
   - Model sometimes adds explanatory text around JSON
   - Generator extracts JSON from any of these formats
   - Uses json_repair for malformed JSON

3. PARAMETER NAMING
   - vLLM uses `max_tokens` not `max_new_tokens`
   - Generator translates parameters correctly

4. THINKING BLOCKS
   - Model sometimes outputs `<think>...</think>` blocks
   - Generator strips these from the response

5. RETRY LOGIC
   - Uses tenacity for exponential backoff
   - Retries on empty responses, thinking-only, schema validation failures

This is all transparent to the caller - you just call generate() or generate_json()
and get clean output.
"""