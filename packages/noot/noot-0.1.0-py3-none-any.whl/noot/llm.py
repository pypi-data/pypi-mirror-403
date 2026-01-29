"""Simple Anthropic API wrapper for step execution."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import anthropic
from anthropic.types import TextBlock

if TYPE_CHECKING:
    from noot.cache import Cache

from noot.cache import CacheMissError

STEP_SYSTEM_PROMPT = """\
You are controlling an interactive CLI application. Given the current terminal screen
and a user instruction, determine the exact keystrokes needed to perform the action.

Respond with JSON only:
{
  "keystrokes": "exact keys to send",
  "duration": 0.5
}

Keystroke rules:
- For regular text input, just type the text (no special characters)
- Special keys (send separately via special_keys array):
  - "Enter" - press enter
  - "Up", "Down", "Left", "Right" - arrow keys
  - "C-c" - Ctrl+C
  - "C-d" - Ctrl+D
  - "Tab" - tab key
  - "Escape" - escape key

If the action requires special keys (like arrow navigation), use this format:
{
  "special_keys": ["Down", "Down", "Enter"],
  "duration": 0.3
}

For text input followed by Enter (most common case):
{
  "keystrokes": "my_input",
  "then_special": "Enter",
  "duration": 0.3
}

Keep duration short (0.1-0.5s) for immediate actions, longer (1-5s) for
commands that take time.
"""

ASSERTION_SYSTEM_PROMPT = """\
You are generating Python assertion code to verify terminal screen content.

Given the current screen and an expected state description, generate Python code
using the `ctx` object.

Available methods on `ctx`:
- ctx.contains(text, normalize=True) - Assert screen contains text
- ctx.contains_any(texts, normalize=True) - Assert contains at least one of the texts
- ctx.contains_all(texts, normalize=True) - Assert contains all of the texts
- ctx.matches_regex(pattern, flags=0) - Assert regex matches (re.IGNORECASE)
- ctx.not_contains(text, normalize=True) - Assert does NOT contain text
- ctx.normalize(text) - Normalize whitespace and strip ANSI codes

Guidelines:
1. Verify SEMANTIC INTENT, not exact formatting - normalize=True handles whitespace/ANSI
2. Use regex with .* for variable parts (paths, timestamps, usernames)
3. Keep assertions MINIMAL - only what's needed to verify the expected state
4. For case-insensitive matching, use ctx.matches_regex(r'(?i)pattern')
5. DO NOT check exact paths, timestamps, or user-specific data unless required

Respond with ONLY the Python code, no explanations or markdown:

Example expected state: "Welcome wizard is displayed"
Example response:
ctx.contains("Welcome")
ctx.matches_regex(r'(?i)wizard')

Example expected state: "Error message about invalid input"
Example response:
ctx.matches_regex(r'(?i)(error|invalid)')
"""


class LLM:
    """Simple Anthropic Claude wrapper with optional caching."""

    def __init__(
        self, model: str = "claude-sonnet-4-20250514", cache: Cache | None = None
    ):
        self._model = model
        self._cache = cache
        self._logger = _get_logger()
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        """Lazily initialize the Anthropic client."""
        if self._client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable required")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def complete(self, screen: str, instruction: str) -> str:
        """Send screen + instruction to LLM and get response."""
        # Check cache first
        if self._cache is not None:
            cached = self._cache.get(instruction, screen, method="complete")
            if cached is not None:
                self._logger.info(
                    json.dumps(
                        {
                            "event": "llm_cache_hit",
                            "method": "complete",
                            "instruction": instruction,
                        }
                    )
                )
                return cached
            # In replay mode, cache miss is an error
            if self._cache.fail_on_miss:
                raise CacheMissError(instruction, "complete")

        user_message = (
            f"Current terminal screen:\n```\n{screen}\n```\n\n"
            f"Instruction: {instruction}"
        )

        self._logger.info(
            json.dumps(
                {
                    "event": "llm_request",
                    "model": self._model,
                    "system": STEP_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                }
            )
        )
        response = self._get_client().messages.create(
            model=self._model,
            max_tokens=256,
            system=STEP_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        content_block = response.content[0]
        if not isinstance(content_block, TextBlock):
            raise TypeError("Expected TextBlock response")
        response_text = content_block.text
        self._logger.info(
            json.dumps(
                {
                    "event": "llm_response",
                    "model": self._model,
                    "content": response_text,
                }
            )
        )

        # Store in cache if recording
        if self._cache is not None:
            self._cache.put(instruction, screen, response_text, method="complete")

        return response_text

    def generate_assertion(self, screen: str, expected_state: str) -> str:
        """
        Generate Python assertion code for verifying screen content.

        Args:
            screen: Current terminal screen content
            expected_state: Description of expected state

        Returns:
            Python code string using `ctx` assertion methods
        """
        # Check cache first
        if self._cache is not None:
            cached = self._cache.get(expected_state, screen, method="expect")
            if cached is not None:
                self._logger.info(
                    json.dumps(
                        {
                            "event": "llm_cache_hit",
                            "method": "expect",
                            "instruction": expected_state,
                        }
                    )
                )
                return cached
            # In replay mode, cache miss is an error
            if self._cache.fail_on_miss:
                raise CacheMissError(expected_state, "expect")

        user_message = (
            "Current terminal screen:\n```\n"
            f"{screen}\n"
            "```\n\n"
            f"Expected state: {expected_state}"
        )

        self._logger.info(
            json.dumps(
                {
                    "event": "llm_assertion_request",
                    "model": self._model,
                    "system": ASSERTION_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                }
            )
        )
        response = self._get_client().messages.create(
            model=self._model,
            max_tokens=512,
            system=ASSERTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        content_block = response.content[0]
        if not isinstance(content_block, TextBlock):
            raise TypeError("Expected TextBlock response")
        assertion_code = content_block.text.strip()

        # Clean up code block formatting if present
        if assertion_code.startswith("```"):
            lines = assertion_code.split("\n")
            # Remove first line (```python or ```)
            lines = lines[1:]
            # Remove last line if it's just ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            assertion_code = "\n".join(lines).strip()

        self._logger.info(
            json.dumps(
                {
                    "event": "llm_assertion_response",
                    "model": self._model,
                    "assertion_code": assertion_code,
                }
            )
        )

        # Store in cache if recording
        if self._cache is not None:
            self._cache.put(
                expected_state,
                screen,
                assertion_code,
                method="expect",
                assertion_code=assertion_code,
            )

        return assertion_code


def _extract_json(response: str) -> dict:
    candidate = response.strip()
    if candidate.startswith("```"):
        lines = [line for line in candidate.split("\n") if not line.startswith("```")]
        candidate = "\n".join(lines).strip()
    if "{" in candidate and "}" in candidate:
        start = candidate.find("{")
        end = candidate.rfind("}")
        candidate = candidate[start : end + 1]
    match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if match:
        candidate = match.group(0)
    return json.loads(candidate)


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("noot")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    log_dir = Path(__file__).resolve().parents[2] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"noot_{timestamp}.log"
    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
