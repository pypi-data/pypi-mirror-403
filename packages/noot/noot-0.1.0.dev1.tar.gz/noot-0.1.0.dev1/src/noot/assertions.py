"""Assertion context and executor for LLM-generated assertion code."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class AssertionContext:
    """
    Context object passed to LLM-generated assertion code.

    Provides safe assertion methods that operate on terminal screen content.
    All methods raise AssertionError on failure.
    """

    screen: str

    def normalize(self, text: str) -> str:
        """
        Normalize text by stripping ANSI codes and collapsing whitespace.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Strip ANSI escape sequences
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
        text = ansi_pattern.sub("", text)
        # Collapse whitespace
        text = " ".join(text.split())
        return text

    def contains(self, text: str, normalize: bool = True) -> None:
        """
        Assert screen contains text.

        Args:
            text: Text to search for
            normalize: If True, normalize both screen and text before comparison

        Raises:
            AssertionError: If text is not found
        """
        screen = self.normalize(self.screen) if normalize else self.screen
        search_text = self.normalize(text) if normalize else text
        if search_text not in screen:
            raise AssertionError(f"Screen does not contain: {text!r}")

    def contains_any(self, texts: list[str], normalize: bool = True) -> None:
        """
        Assert screen contains at least one of the given texts.

        Args:
            texts: List of texts to search for
            normalize: If True, normalize before comparison

        Raises:
            AssertionError: If none of the texts are found
        """
        screen = self.normalize(self.screen) if normalize else self.screen
        for text in texts:
            search_text = self.normalize(text) if normalize else text
            if search_text in screen:
                return
        raise AssertionError(f"Screen does not contain any of: {texts!r}")

    def contains_all(self, texts: list[str], normalize: bool = True) -> None:
        """
        Assert screen contains all of the given texts.

        Args:
            texts: List of texts that must all be present
            normalize: If True, normalize before comparison

        Raises:
            AssertionError: If any text is not found
        """
        screen = self.normalize(self.screen) if normalize else self.screen
        missing = []
        for text in texts:
            search_text = self.normalize(text) if normalize else text
            if search_text not in screen:
                missing.append(text)
        if missing:
            raise AssertionError(f"Screen does not contain: {missing!r}")

    def matches_regex(self, pattern: str, flags: int = 0) -> None:
        """
        Assert screen matches regex pattern.

        Args:
            pattern: Regular expression pattern
            flags: Regex flags (e.g., re.IGNORECASE)

        Raises:
            AssertionError: If pattern does not match
        """
        if not re.search(pattern, self.screen, flags):
            raise AssertionError(f"Screen does not match pattern: {pattern!r}")

    def not_contains(self, text: str, normalize: bool = True) -> None:
        """
        Assert screen does NOT contain text.

        Args:
            text: Text that should not be present
            normalize: If True, normalize before comparison

        Raises:
            AssertionError: If text is found
        """
        screen = self.normalize(self.screen) if normalize else self.screen
        search_text = self.normalize(text) if normalize else text
        if search_text in screen:
            raise AssertionError(f"Screen should not contain: {text!r}")


# Restricted builtins for safe code execution
_SAFE_BUILTINS = {
    "True": True,
    "False": False,
    "None": None,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sorted": sorted,
    "reversed": reversed,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "all": all,
    "any": any,
    "isinstance": isinstance,
    "hasattr": hasattr,
    "getattr": getattr,
}


def execute_assertion(
    code: str, screen: str, expected_state: str
) -> tuple[bool, str | None]:
    """
    Execute LLM-generated assertion code safely.

    Args:
        code: Python assertion code using `ctx` variable
        screen: Current terminal screen content
        expected_state: The original expectation description (for error messages)

    Returns:
        Tuple of (passed: bool, error_message: str | None)
    """
    ctx = AssertionContext(screen=screen)

    # Build restricted execution environment
    restricted_globals = {
        "__builtins__": _SAFE_BUILTINS,
        "ctx": ctx,
        "re": re,
    }

    try:
        exec(code, restricted_globals)
        return True, None
    except AssertionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Assertion code error: {type(e).__name__}: {e}"
