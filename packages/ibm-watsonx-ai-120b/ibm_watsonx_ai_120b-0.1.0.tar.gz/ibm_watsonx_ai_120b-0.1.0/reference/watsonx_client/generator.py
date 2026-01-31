"""
WatsonX Generator for synx-developer.

Provides API-based text and JSON generation using WatsonX models.
This module wraps the WatsonXClient to provide a simpler interface
for the synx-developer workers.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from synx_sf_issue_worker.llm.watsonx_client import WatsonXClient, WatsonXConfig
from synx_sf_issue_worker.llm.watsonx_client.exceptions import WatsonXError

logger = logging.getLogger(__name__)


class WatsonXGenerator:
    """WatsonX-based text generator.

    Uses the WatsonX client for text generation with support for:
    - Plain text generation
    - JSON-structured output with schema validation
    - Automatic retry for thinking-only responses
    - Proper handling of vLLM/harmony quirks
    """

    DEFAULT_MODEL = "openai/gpt-oss-120b"
    DEFAULT_MAX_TOKENS = 16384  # High default for comprehensive document generation
    DEFAULT_TEMPERATURE = 0.1  # Lower for more consistent output

    def __init__(
        self,
        api_key: str,
        project_id: str,
        region_url: str = "https://us-south.ml.cloud.ibm.com",
        model: str | None = None,
    ):
        """Initialize the generator.

        Args:
            api_key: WatsonX API key
            project_id: WatsonX project ID
            region_url: WatsonX region URL
            model: Model ID to use (default: openai/gpt-oss-120b)
        """
        self.api_key = api_key
        self.project_id = project_id
        self.region_url = region_url

        # Use environment variable or default
        self.model = model or os.environ.get("WATSONX_MODEL") or self.DEFAULT_MODEL

        self._client: Optional[WatsonXClient] = None

    @property
    def client(self) -> WatsonXClient:
        """Lazy initialization of WatsonX client."""
        if self._client is None:
            config = WatsonXConfig(
                api_key=self.api_key,
                project_id=self.project_id,
                region_url=self.region_url,
                model_id=self.model,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                temperature=self.DEFAULT_TEMPERATURE,
                reasoning_effort="low",  # Minimize thinking output
            )
            self._client = WatsonXClient(config)
            logger.info(f"Initialized WatsonXGenerator with model: {self.model}")

        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop_sequences: Sequences that stop generation

        Returns:
            Generated text
        """
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE

        # Build messages
        messages: List[Dict[str, Any]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            # Use chat interface for better handling
            response = self.client.chat(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Extract content from response
            if isinstance(response, dict) and "choices" in response:
                content = response["choices"][0].get("message", {}).get("content", "")
                return content.strip() if content else ""

            return str(response).strip()

        except WatsonXError as e:
            logger.error(f"Generation failed: {e}")
            raise

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise WatsonXError(f"Generation failed: {e}")

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON output.

        Uses the proper WatsonX client with JSON schema adapter for
        robust JSON generation with:
        - Schema validation
        - Automatic retry for thinking-only responses
        - JSON repair for malformed output

        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt
            schema: JSON schema for the expected output
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON as dictionary
        """
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

        # Build messages
        messages: List[Dict[str, Any]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            if schema:
                # Use JSON schema mode with proper adapter
                response = self.client.chat_with_json_schema(
                    messages=messages,
                    schema=schema,
                    schema_name="response",
                    max_tokens=max_tokens,
                )
            else:
                # Use simple JSON object mode
                response = self.client.chat_with_json_object(
                    messages=messages,
                    max_tokens=max_tokens,
                )

            # Extract content from response
            if isinstance(response, dict) and "choices" in response:
                message = response["choices"][0].get("message", {})
                content = message.get("content", "")
                refusal = message.get("refusal")

                # Sometimes vLLM/WatsonX puts valid JSON in the refusal field
                # instead of content - check if refusal looks like valid JSON
                if refusal:
                    # Check if it's actually JSON (starts with { or [)
                    refusal_stripped = refusal.strip() if isinstance(refusal, str) else ""
                    if refusal_stripped.startswith("{") or refusal_stripped.startswith("["):
                        # Try to parse it - if it works, use it
                        try:
                            return self._extract_json(refusal_stripped)
                        except (ValueError, json.JSONDecodeError):
                            pass  # Fall through to actual refusal handling

                    # It's a real refusal (not misplaced JSON)
                    raise WatsonXError(f"Model refused to generate: {refusal}")

                # Parse JSON from content
                if content:
                    return self._extract_json(content)

            raise WatsonXError("No valid JSON in response")

        except WatsonXError:
            raise

        except Exception as e:
            logger.error(f"JSON generation failed: {e}")
            raise WatsonXError(f"JSON generation failed: {e}")

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text, handling markdown code blocks."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        import re

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in text
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_start != -1 and brace_end > brace_start:
            try:
                return json.loads(text[brace_start:brace_end])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")

    def cleanup(self):
        """Clean up resources."""
        if self._client:
            self._client.cleanup()
            self._client = None
