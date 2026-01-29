"""Parse LLM responses into keystrokes."""

import json
import re
from dataclasses import dataclass


@dataclass
class ParsedStep:
    """Result of parsing an LLM step response."""

    keystrokes: str | None  # Regular text to send
    special_keys: list[str]  # Special keys like Enter, Up, Down
    then_special: str | None  # Special key to send after keystrokes
    duration: float


def parse_response(response: str) -> ParsedStep:
    """Parse LLM response into keystroke instructions."""
    # Extract JSON from response (handle markdown code blocks)
    json_str = response.strip()

    # Remove markdown code block if present
    if json_str.startswith("```"):
        lines = json_str.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [line for line in lines if not line.startswith("```")]
        json_str = "\n".join(lines)

    # Find JSON object
    match = re.search(r"\{[^{}]*\}", json_str, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response: {response[:100]}")

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    return ParsedStep(
        keystrokes=data.get("keystrokes"),
        special_keys=data.get("special_keys", []),
        then_special=data.get("then_special"),
        duration=data.get("duration", 0.5),
    )
