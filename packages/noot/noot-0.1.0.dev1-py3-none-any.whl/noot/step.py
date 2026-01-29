"""Step execution logic."""

import json
from dataclasses import dataclass

from noot.llm import LLM, _get_logger
from noot.parser import parse_response
from noot.terminal import Terminal


@dataclass
class StepResult:
    """Result of executing a step."""

    instruction: str
    keystrokes_sent: str
    special_keys_sent: list[str]
    screen_before: str
    screen_after: str
    duration: float


def execute_step(
    terminal: Terminal,
    instruction: str,
    llm: LLM,
    stability_timeout: float = 5.0,
) -> StepResult:
    """
    Execute a single step: LLM interprets instruction → keystrokes → execute.

    Args:
        terminal: Active terminal session
        instruction: Natural language instruction (e.g., "Enter 'sample_project'")
        llm: LLM client for interpreting instructions
        stability_timeout: Max seconds to wait for terminal to stabilize

    Returns:
        StepResult with details of what was executed
    """
    # 1. Capture current state
    screen_before = terminal.capture()
    logger = _get_logger()
    logger.info(
        json.dumps(
            {
                "event": "step_start",
                "instruction": instruction,
                "screen_before": screen_before,
            }
        )
    )

    # 2. Query LLM
    response = llm.complete(screen=screen_before, instruction=instruction)

    # 3. Parse response
    parsed = parse_response(response)
    logger.info(
        json.dumps(
            {
                "event": "step_parsed",
                "instruction": instruction,
                "keystrokes": parsed.keystrokes,
                "special_keys": parsed.special_keys,
                "then_special": parsed.then_special,
                "duration": parsed.duration,
            }
        )
    )

    # 4. Execute keystrokes
    keystrokes_sent = ""
    special_keys_sent = []

    if parsed.keystrokes:
        terminal.send_keys(parsed.keystrokes, wait_sec=0.05)
        keystrokes_sent = parsed.keystrokes

    if parsed.then_special:
        terminal.send_special(parsed.then_special, wait_sec=parsed.duration)
        special_keys_sent.append(parsed.then_special)

    for key in parsed.special_keys:
        terminal.send_special(key, wait_sec=0.1)
        special_keys_sent.append(key)

    # 5. Wait for stability
    if parsed.duration > 0 and not parsed.special_keys and not parsed.then_special:
        # Only sleep if we didn't already wait during special key sending
        import time

        time.sleep(parsed.duration)

    screen_after = terminal.wait_for_stability(timeout_sec=stability_timeout)
    logger.info(
        json.dumps(
            {
                "event": "step_actions",
                "instruction": instruction,
                "keystrokes_sent": keystrokes_sent,
                "special_keys_sent": special_keys_sent,
                "duration": parsed.duration,
            }
        )
    )
    logger.info(
        json.dumps(
            {
                "event": "step_end",
                "instruction": instruction,
                "screen_after": screen_after,
            }
        )
    )

    return StepResult(
        instruction=instruction,
        keystrokes_sent=keystrokes_sent,
        special_keys_sent=special_keys_sent,
        screen_before=screen_before,
        screen_after=screen_after,
        duration=parsed.duration,
    )
