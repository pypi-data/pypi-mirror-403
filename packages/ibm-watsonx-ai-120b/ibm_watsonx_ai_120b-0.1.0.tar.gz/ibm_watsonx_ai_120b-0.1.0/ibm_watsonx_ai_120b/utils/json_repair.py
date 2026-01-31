"""JSON extraction and repair utilities."""

import json
import logging
import re
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import json_repair library
try:
    import json_repair as _json_repair

    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False
    logger.debug("json_repair not installed, using built-in repair")


def extract_json(text: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """Extract JSON object from text that may contain other content.

    Handles:
    - Pure JSON
    - JSON in markdown code blocks
    - JSON embedded in explanatory text
    - Minor formatting issues

    Args:
        text: Text that may contain JSON

    Returns:
        Tuple of (success, json_object, error_message)
    """
    if not text:
        return False, None, "Empty text"

    original = text.strip()

    # Try markdown code block extraction first
    extracted = _extract_from_code_block(original)
    if extracted:
        text = extracted
    else:
        text = original

    # Try direct parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return True, data, None
    except json.JSONDecodeError:
        pass

    # Find JSON object in text using brace matching
    json_str = _find_json_object(original)
    if not json_str:
        return False, None, "No JSON object found"

    # Try to parse the extracted JSON
    try:
        data = json.loads(json_str)
        if isinstance(data, dict):
            return True, data, None
    except json.JSONDecodeError as e:
        logger.debug(f"Initial parse failed: {e}")

    # Try repair
    repaired = repair_json(json_str)
    if repaired:
        try:
            data = json.loads(repaired)
            if isinstance(data, dict):
                logger.debug("Successfully repaired JSON")
                return True, data, None
        except json.JSONDecodeError:
            pass

    return False, None, f"Failed to parse JSON: {json_str[:200]}..."


def repair_json(json_str: str) -> Optional[str]:
    """Attempt to repair malformed JSON.

    Args:
        json_str: Potentially malformed JSON string

    Returns:
        Repaired JSON string or None if repair failed
    """
    if not json_str:
        return None

    # Use json_repair library if available
    if HAS_JSON_REPAIR:
        try:
            return _json_repair.repair_json(json_str)
        except Exception:
            pass

    # Built-in repairs
    repaired = json_str

    # Fix trailing commas before } or ]
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # Fix single quotes to double quotes (simple cases)
    # Only do this if there are no double quotes (to avoid breaking valid JSON)
    if '"' not in repaired and "'" in repaired:
        repaired = repaired.replace("'", '"')

    # Try to fix unquoted keys (simple cases like {key: "value"})
    repaired = re.sub(r"{\s*(\w+)\s*:", r'{"\1":', repaired)
    repaired = re.sub(r",\s*(\w+)\s*:", r',"\1":', repaired)

    return repaired


def _extract_from_code_block(text: str) -> Optional[str]:
    """Extract JSON from markdown code blocks.

    Args:
        text: Text that may contain code blocks

    Returns:
        Extracted content or None
    """
    # Try ```json block first
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return text[start:end].strip()
        except ValueError:
            pass

    # Try generic ``` block
    if "```" in text:
        try:
            start = text.index("```") + 3
            # Skip language identifier if present
            newline = text.find("\n", start)
            if newline != -1 and newline - start < 20:
                start = newline + 1
            end = text.index("```", start)
            extracted = text[start:end].strip()
            if extracted.startswith("{"):
                return extracted
        except ValueError:
            pass

    return None


def _find_json_object(text: str) -> Optional[str]:
    """Find a JSON object in text using brace matching.

    Args:
        text: Text containing JSON

    Returns:
        Extracted JSON string or None
    """
    brace_start = text.find("{")
    if brace_start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False
    brace_end = -1

    for i in range(brace_start, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                brace_end = i + 1
                break

    if brace_end == -1:
        return None

    return text[brace_start:brace_end]


def strip_markdown_code_blocks(text: str) -> str:
    """Remove markdown code block markers from text.

    Args:
        text: Text with potential code blocks

    Returns:
        Text with code block markers removed
    """
    if not text:
        return text

    text = text.strip()

    # Remove ```json or ``` at start
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
        # Skip language identifier on first line
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            if len(first_line) < 20 and not first_line.strip().startswith("{"):
                text = rest

    # Remove ``` at end
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()